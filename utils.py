import hashlib
import ipaddress
import secrets
from Crypto.Cipher import AES
from django.core.cache import cache

def get_client_ip(request):
	try:
		ip = request.META.get("HTTP_X_FORWARDED_FOR").split(",")[0].strip()
		ipaddress.IPv4Address(ip)
		return ip
	except:
		return "unknown"

def aes_256_enc(key,data):
	key = hashlib.sha256(key.encode()).digest()
	iv = secrets.token_bytes(16)
	cipher = AES.new(key,AES.MODE_GCM,nonce=iv)
	cipher_text,tag = cipher.encrypt_and_digest(data.encode())
	return b64encode(iv+cipher_text+tag).decode()

def aes_256_dec(key,data):
	if not key:
		return ""
	key = hashlib.sha256(key.encode()).digest()
	data_bin = b64decode(data.encode())
	cipher = AES.new(key,AES.MODE_GCM,nonce=data_bin[:16])
	plain_text = cipher.decrypt_and_verify(data_bin[16:-16],data_bin[-16:])
	return plain_text.decode()


# 自定义TinIntField
class TinyIntField(models.IntegerField):
	def db_type(self,connection):
		return "tinyint(1)"

# 自定义无符号整型
class UnsignedBigIntegerField(models.UnsignedBigIntegerField):
	def db_type(self,connection):
		return "bigint UNSIGNED"

class Singleton(object):
	def __new__(cls,*args,**kwargs):
		if not hasattr(cls,'_instance'):
			orig = super(Singleton,cls)
			cls._instance = orig.__new__(cls,*args,**kwargs)		
		return cls._instance

