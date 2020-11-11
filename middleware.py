import json
import re
import time

import casbin
import bleach
import yaml
from django.http import JsonResponse
from django_redis import get_redis_connection
from pre.settings import PERIOD_SEC_LOGIN,MAX_REQUEST_PERIOD_LOGIN,PERIOD_SEC_API,MAX_REQUEST_PERIOD_API
from pre.utils import get_client_ip


NO_LOGIN_URLS = ['/users/login/']
OPEN_PERM_URLS = []

class LoginMiddleware:
	def __init__(self,get_response):
		self.get_response = get_response

	def __call__(self,request):
		# 判断是否已经登陆
		if request.path not in NO_LOGIN_URLS:
			if 'sso' not in request.session:
				return JsonResponse({'code':401,'msg':'未登录','data':[]})
			# 防止会话窃取
			if request.session.get('loginIP','') != get_client_ip(request):
				request.session.flush()
				return JsonResponse({'code':401,'msg':'非法访问'，'data':[]})
		response = self.get_response(request)
		return response

class AntiCsrfMiddleware:
	def __init__(self,get_response):
		self.get_response = get_response
	def __call__(self,request):
		if request.path not in NO_LOGIN_URLS:
			csrf_header = request.META.get('HTTP_X_CSRFTOKEN','')
			csrf_cookie = request.COOKIES.get('csrftoken','')
			if csrf_header == "" or csrf_header != csrf_cookie:
				request.session.flush()
				return JsonResponse({'code':401,'msg':"非法访问",'data':[]})

		response = self.get_response(request)
		return response

class RateLimitMiddleware:
	def __init__(self,get_response):
		self.get_response = get_response
		self.conn = get_redis_connection()

	def __call__(self,request):
		if request.path in NO_LOGIN_URLS:
			if self.check(get_client_ip(request),request.path) is False:
				return JsonResponse({'code':403,'msg':'访问速度太快了'，'data':[]})
		else:
			# 针对已登陆用户的请求频率限制
			now = time.time()
			request_queue = request.session.get('request_queue',[])
			if len(request_queue) < MAX_REQUEST_PERIOD_API:
				request_queue.append(now)
				request.session['request_queue'] = request_queue
			else:
				if (now - request_queue[0]) < PERIOD_SEC_API:
					time.sleep(5)
				request_queue.append(time.time())
				request.session['request_queue'] = request_queue[1:]

		response = self.get_response(request)
		return response

	def check(self,ip,path):
		store_key = 'rate_%s_%s'%(ip,path)
		timers = self.conn.get(store_key)
		timers = int(timers) if timers else 0
		if timers:
			if timers <= MAX_REQUEST_PERIOD_API:
				timers = self.conn.incr(store_key)
				if timers == 1: # 并发控制，如果刚好过期，则要重新设置过期时间
					self.conn.expire(store_key,PERIOD_SEC_LOGIN)
		else:
			self.conn.set(store_key,1,ex=PERIOD_SEC_LOGIN)

		return timers <= MAX_REQUEST_PERIOD_LOGIN

class PermissionMiddleware:
	def __init__(self,get_response):
		self.get_response = get_response
		# 初始化casbin，导入keyMatch方法
		self.enforcer = casbin.Enforcer('pre/authz_model.conf','pre/authz_policy.csv')		

	def __call_(self,request):
		if request.path not in NO_LOGIN_URLS:
			# 所有角色都可以访问的接口
			if request.path in OPEN_PERM_URLS:
				response = self.get_response(request)
				return response

			enforcer = request.session.get('enforcer')
			username = request.session.get('sso').get('userName')
			if not enforcer.enforce(username,request.path,request.method):
				# 可以选择request.session.flush()
				return JsonResponse({'code':403,'msg':'无权限访问','data':[]})

		response = self.get_response(request)
		return response

# xss过滤
class XssFilterMiddleware:
	def __init__(self,get_response):
		self.get_response = get_response
		self.__escape_param_list = []
	def __call__(self,request):
		# 主要限制富文本接口
		if request.path.startswith('vuln/'):
			if request.method in ['GET','DELETE']:
				return self.get_response(request)
			if request.method in ['POST','PUT'] and request.content_type == 'application/json':
				request._body = json.dumps(self._sanitize(request.body)).encode()
		response = self.get_response(request)
		return response
	def _sanitize(self,query_dict):
		raw_dict = json.loads(query_dict.decode())
		clean_dict = {}
		for key,value in raw_dict.items():
			new_value = bleach.clean(text=value,tags=['img','br','div','p'],attributes={'img':['src']},strip=True,protocols=['data'],strip_comments=True).replace('<img>','')
			clean_dict[key] = new_value

		return clean_dict

class ParamsFilterMiddleware:
	def __init__(self,get_response):
		self.get_response = get_response
		self.method_list = ['GET','POST','PUT','DELETE']
		self.no_get_list = ['POST','PUT','DELETE']
		with open('pre/param.yml','r',encoding='utf-8') as cfg:
			self.rules = yaml.load(cfg.read(),loader=yaml.FullLoader)
		# 预编译正则表达式
		for r in self.rules:
			for m in self.method_list:
				if m in r:
					for k in r[m]:
						if r[m][k]:
							r[m][k] = re.compile(r[m][k])

	def __call__(self,request.*args,**kwargs):
		if requst.path not in NO_LOGIN_URLS:
			if request.method == "GET":
				if self._validate(request.path,'GET',request.GET) is False:
					return JsonResponse({'code':403,'msg':'参数非法','data':[]})
			else:
				for i in self.no_get_list:
					if request.method == i and reqeust.content_type == "application/json":
						request._body = json.loads(request.body.decode())
						if request._validate(request.path,i,request.body) is False:
							return JsonResponse({'code':403,'msg':'参数非法','data':[]})
						break
			response = self.get_response(request)
			return response

	def _validate(self,path,method,query_dict):
		# todo: 所有参数在URL里的后面都要改掉
		# 保证传入带参数的url时能正确匹配规则，规则中无带参数
		# 为了功能兼容性，暂时对未配置的path都返回True
		if path not in self.rules:
			print(path,"还未在param.yml中配置")
			return True
		if method not in self.rules[path]:
			return False
		# 未配置参数的，都可以放通
		if not self.rules[path][method]:
			return True
		for key,value in query_dict.items():
			if key not in self.rules[path][method]:
				print("不存在参数：",key)
				continue
			if self.rules[path][method][key]:
				if self.rules[path][method][key]:
					if type(value) is list:
						value = ",".join([str(i) for i in value])
					else:
						value = str(value)
					if not re.match(self.rules[path][method][key],value):
						print("不匹配的参数是：",key,self.rules[path][method][key])
						return False
		# 未配置也让通过
		return True
		



















