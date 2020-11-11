import os
import pymysql
from pre.utils import aes_256_dec

AES_KEY = os.getenv("AES_KEY")

MIDDLEWARE = [
'django.middleware.security.SecurityMiddleware',
'django.contrib.sessions.middleware.SessionMiddleware',
'django.middleware.common.CommonMiddlewaer',
# 登陆
'pre.middleware.LoginMiddleware',
# 限流
'pre.middleware.RateLimitMiddleware',
# 防csrf
'pre.middleware.AntiCsrfMiddleware',
# 鉴权
'pre.middleware.PermissionMiddleware',
# xss
'pre.middleware.XssFilterMiddleware',
# 参数过滤
'pre.middleware.ParamsFilterMiddleware'
]

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'
SESSION_COOKIE_AGE = 60*30

LANGUAGE_CODE = 'zh-Hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# 共享session时需要保证secret_key相同
SECRET_KEY = aes_256_dec(AES_KEY,os.getenv('SECRET_KEY'))
DEBUG = os.getenv('DEBUG',False)
pymysql.install_as_MySQLdb()
DATABASES = {
	'default':{
	'ENGINE':'django.db.backends.mysql', #数据库引擎
	'NAME': 'asap',
	'USER': aes_256_dec(AES_KEY,os.getenv('DBUSER')),
	'PASSWORD': aes_256_dec(AES_KEY,os.getenv('DBPASS')),
	'HOST': os.getenv('DBHOST'),
	'PORT': os.getenv('DBPORT')
	}
}

redis_host = os.getenv('REDIS_HOST')
redis_pass = aes_256_dec(AES_KEY,os.getenv('REDIS_PASS'))

CACHES = {
	"default":{
	"BACKEND":"django_redis.cache.RedisCache",
	"LOCATION":"redis://%s/0"%redis_host,
	"OPTIONs":{
	"CLIENT_CLASS":"django_redis.client.DefaultClient"，
	"CONNECTION_POOL_KWARGS":{"max_connections":300},
	"PASSWORD":redis_pass,
	}
	},
	"session":{
	"BACKEND":"django_redis.cache.RedisCache",
	"LOCATION": "redis://%s/1"%redis_host,
	"OPTIONS":{
	"CLIENT_CLASS":"django_redis.client.DefaultClient",
	"CONNECTION_POOL_KWARGS":{"max_connections":300},
	"PASSWORD":redis_pass,
	}
	}
}

# 登陆限流配置
PERIOD_SEC_LOGIN = 5
MAX_REQUEST_PERIOD_LOGIN = int(os.getenv("MAX_REQUEST_PERIOD_LOGIN",5))

# 接口限流配置
PERIOD_SEC_API = 5
MAX_REQUEST_PERIOD_API = int(os.getenv('MAX_REQUEST_PERIOD_API',10))

# 横向鉴权校验
role_permission_dict = {
	"/product/productEntry/": {"GET":"product","POST":"product","PUT":"product","DELETE":"product"}
}

MEDIA_ROOT = os.getenv("MEDIA_ROOT"，r"C:\Temp")

try:
	from pre.local_settions import *
except ImportError:
	pass

# celery
from CeleryTasks.celery_setting import *
BROKER_BACKEND = 'redis'
BROKER_URL = 'redis://:%s@%s/2'%(redis_pass,redis_host)
CELERY_RESULT_BACKEND = 'redis://:%s@%s/3'%(redis_pass,redis_host)













