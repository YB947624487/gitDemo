class Singleton(object):
	def __new__(cls,*args,**kwargs):
		if not hasattr(cls,'_instance'):
			orig = super(Singleton,cls)
			cls._instance = orig.__new__(cls,*args,**kwargs)
		return cls.__instance

# 发送邮件
class MailSender(Singleton):
	def __init__(self):
		self.mail_server = mail_server
		self.mail_username = mail_username
		self.mail_password = mail_password
		self.mail_sender = mail_sender
		self.debug_receiver = debug_receiver
		self.mail_cc = mail_cc

	def __mail_config(self,mail_subject,mail_content,mail_receiver,mail_cc):
		msg_root = MIMEMultipart()
		msg_root['Subject'] mail_subject
		msg_root['From'] = self.mail_sender
		msg_root['To'] = debug_receiver if self.debug_receiver else mail_receiver
		msg_root['Cc'] = debug_receiver if self.debug_receiver else mail_cc
		msg_root.attach(MIMEText(mail_content,'html','utf-8'))
		return msg_root

	def _send_mail(self,mail_subject,mail_content,mail_receiver,mail_cc=mail_cc):
		if not mail_receiver:
			print("邮件接收人为空，邮件发送失败")
			return False
		msg_root = self.__mail_config(mail_subject,mail_content,mail_receiver,mail_cc)
		if not msg_root:
			print("邮件内容为空，不发送邮件提醒")
			return False
		try：
			server = smtplib.SMTP(self.mail_server,465)
			server.starttls() # tls发送
			server.login(self.mail_username,self.mail_password)
			receiver_list = [self.debug_receiver] if self.debug_receiver else mail_receiver.split(",")+mail_cc.split(",")
			server.sendmail(self.mail_sender,receiver_list,msg_root.as_string())
			print("邮件发送成功")
			server.quit()
			return True
		except Exception as e:
			print("邮件发送失败"，e)
			return False






