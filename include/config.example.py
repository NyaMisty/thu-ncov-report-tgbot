SQLITE_DB_FILE_PATH = 'my_app.db'

API_TIMEOUT = 20 # in seconds

CRON_TIMEZONE = 'Asia/Shanghai'
CHECKIN_ALL_CRON_HOUR = 0
CHECKIN_ALL_CRON_MINUTE = 10
CHECKIN_ALL_CRON_RETRY_HOUR   = 0
CHECKIN_ALL_CRON_RETRY_MINUTE = 25

REASONABLE_LENGTH = 24

TG_BOT_PROXY = None # example: {'proxy_url': 'socks5h://127.0.0.1:1080/'}
TG_BOT_TOKEN = ""   # Bot Token
TG_BOT_MASTER = 0   # Master Telegram User ID

CHECKIN_PROXY = {} # example: {'http': 'socks5://user:pass@host:port', 'https': 'socks5://user:pass@host:port'}

BOT_DEBUG = False

HELP_MARKDOWN='''
自动签到时间：每日0点10分
自动晨午晚检时间：每日12点10分、18点10分
请在使用本 bot 前，确保已经正确提交过一次上报。
本 bot 的目标签到系统为：[thos.tsinghua.edu.cn/...](https://thos.tsinghua.edu.cn/fp/view?m=fp#from=hall&serveID=b44e2daf-0ef6-4d11-a115-0eb0d397934f&act=fp/serveapply)

/list
  列出所有签到用户
/checkin
  立即执行签到

/add\_by\_uid `用户名/学号` `密码` 
  用户信息为统一身份认证 https://id.tsinghua.edu.cn 系统
  通过用户名与密码添加签到用户
  **建议您修改密码为随机密码后再进行本操作**
  例：/add\_by\_uid `2021200100 password123`

工作原理与位置变更须知：
从网页上获取上一次成功签到的数据，处理后再次提交。
因此，如果您改变了城市（如返回北京），请先使用 /pause 暂停自动签到，并 **【连续两天】** 手动签到成功后，再使用 /resume 恢复自动签到。
'''

START_TEXT = '''
Welcome, {}. try /help.
Special Thanks to:
https://github.com/HenryzhaoH/bupt-ncov-report-tgbot
https://github.com/ipid/bupt-ncov-report
'''