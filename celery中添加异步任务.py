# clery中添加异步任务

# 1. 在tasks.py中添加一个任务类,继承自Task,给任务添加一个名字name,具体任务写在run中
from celery.task import task

class Portal(Task):
	name = "portal-task"
	def run(self,*args,**kwargs):
		# do something
		pass

# 2. 任务调用,在某个views需要执行异步任务的地方,直接调用就行了
from CeleryTasks.tasks import Portal

Portal.delay()

# 3. 定时任务
# 在CeleryTasks/celery_setting.py 中的 CELERYBEAT_SCHEDULE 增加一个task
'task4':{
	'task':'portal-task',
	# every 10 minutes
	'schedule': crontab(minute='*/10'),
	'option':{
	'queue':'beat_tasks'
	}
}
# option中的queue默认用beat_tasks