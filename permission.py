def role_permission(role,userName,department,category,q_obj=Q(isDelete=False)role&(0x01|0x04)!=0:
		return q_obj
	q1 = q2 = q3 = Q(id=-1)
	if category == "product":
		if role & 0x80 != 0:
			q1 = q_obj & Q(pDirector__icontains=userName)
	...
	return q1 | q2 | q3

# 根据角色进行横向鉴权
def permission_validator(func):
	def wrapper(request,*args,**kwargs):
		role = request.session['role']
		userName = request.session.get('userName')
		department = request.session['sso'].get('department')
		# 返回Q对象
		if request.path in role_permission_dict and request.method in role_permisson_dict[request.path]:
			category = role_permission_dict[request.path][request.method]
			q_obj role_permission(role,userName,department,category)
		else:
			q_obj = Q(id=-1)
			print(f"路径未在role_permission_dict中配置{request.path}")

		result = func(request,q_obj,*args,**kwargs)
		return result
	return wrapper

# 视图中使用
from django.utils.decorators import method_decorator
from pre.permission import permission_validator

class DemoWrapper(APIView):
	@method_decorator(permission_validator)
	def delete(self,request,q_obj):
		res_data = {
		"code":200,
		"msg":"delete success",
		"data":[]
		}
		query_set = A.objects.filter(q_obj)
		....