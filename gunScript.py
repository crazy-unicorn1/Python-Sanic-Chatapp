# 是否开启debug模式
debug = True
# 设置守护进程,将进程交给supervisor管理
daemon = 'false'
# 访问地址
bind = "0.0.0.0:5021"
# 工作模式协程
worker_class = 'eventlet'
# 任务数量
workers = 1
# 多线程
threads = 100
# 超时时间
timeout = 600
# 输出日志级别
loglevel = 'error'
# 存放访问日志路径
accesslog = "/www/project_kfShare/project_kfShare/access.log"
# 存放错误日志路径
errorlog = "/www/project_kfShare/project_kfShare/error.log"
# 设置最大并发量
worker_connections = 2000
max_requests = 2000
