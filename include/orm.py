import datetime
import pickle

from peewee import *
from playhouse.migrate import *
from .config import *
from .function import *

database_proxy = DatabaseProxy()
_logger = logging.getLogger(__name__)

class BaseModel(Model):
    class Meta:
        database = database_proxy

class THUUserStatus:
    normal  = 0
    stopped = 1
    removed = 2
    warning = 3

class TGUser(BaseModel):
    id = AutoField()
    userid = IntegerField(unique=True)
    username = CharField(null=True, index=True)
    create_time = DateTimeField(default=datetime.datetime.now, index=True)

    def get_thuusers_by_seqids(self, seqids: [int]):
        available_targets = self.get_thuusers()
        assert max(seqids) <= len(available_targets), "Seqid out of range."

        return [available_targets[i-1] for i in seqids]

    def get_thuusers(self, include_all=False):
        if include_all:
            return self.thuusers
        else:
            return self.thuusers.where(THUUser.status != THUUserStatus.removed)

class THUUser(BaseModel):
    id = AutoField()
    owner = ForeignKeyField(model=TGUser, backref='thuusers', lazy_load=False, index=True, on_delete="CASCADE", on_update="CASCADE")
    username = CharField(null=True)
    password = CharField(null=True)
    cookie_data = CharField(null=True)
    latest_data = TextField(null=True)
    latest_response_data = TextField(null=True)
    latest_response_time = DateTimeField(null=True, index=True)

    status = IntegerField(index=True, default=THUUserStatus.normal)
    create_time = DateTimeField(default=datetime.datetime.now, index=True)
    update_time = DateTimeField(default=datetime.datetime.now, index=True)

    def save(self, *args, **kwargs):
        self.update_time = datetime.datetime.now()
        return super(THUUser, self).save(*args, **kwargs)

    def check_status(self):
        assert self.status != THUUserStatus.stopped
        assert self.status != THUUserStatus.removed

    def login(self):
        self.check_status()
        assert self.username != None
        _logger.info(f"[login] Trying user: {self.username}")
        session = requests.Session()
        session.proxies.update(CHECKIN_PROXY)

        LOGIN_PAGE = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/form/a585295b8da408afdda9979801383d0c/0?/fp/'
        _ = session.get(LOGIN_PAGE, timeout=API_TIMEOUT)
        _logger.debug(session.cookies.get_dict())
        LOGIN_API = 'https://id.tsinghua.edu.cn/do/off/ui/auth/login/check'
        login_resp = session.post(LOGIN_API, data={
            'i_user': self.username,
            'i_pass': self.password,
            'i_captcha': '',
        }, timeout=API_TIMEOUT)
        _logger.debug(login_resp.text)
        if login_resp.status_code != 200:
            raise RuntimeError('Login Server ERROR!')

        if not re.search(r'登录成功', login_resp.text):
            _logger.warning(f'[login] Failed! user: {self.username}, ret: {login_resp.text}')
            raise RuntimeWarning(f'Login failed! Server return: `{login_resp.text}`')
        else:
            redirectedUrl = match_re_group1(r'href="(.*?)"', login_resp.text)
            redirect_resp = session.get(redirectedUrl, headers={
                'Referer': 'https://id.tsinghua.edu.cn/',
            })
            if redirect_resp.status_code != 200:
                raise RuntimeError('Login Ticket Callback ERROR!')
            _logger.debug(f"[login] id server succ, redirected to {redirect_resp.url}, code {redirect_resp.status_code}")

            self.cookie_data = bytes.hex(pickle.dumps(session.cookies))
            self.save()
            _logger.info(f'[login] Succeed! user: {self.username}.')
            return session

    def ncov_checkin(self, force=False):
        if not force:
            self.check_status()
        session = requests.Session()
        session.proxies.update(CHECKIN_PROXY)
        if self.cookie_data != None:
            # cookies={
            #     'eai-sess': self.cookie_eaisess,
            #     'UUKey': self.cookie_uukey
            # }
            # requests.utils.add_dict_to_cookiejar(session.cookies, cookies)
            session.cookies.update(pickle.loads(bytes.fromhex(self.cookie_data)))

        REPORT_FORM = 'https://thos.tsinghua.edu.cn/fp/formParser?status=select' \
                      '&formid=6cfd2789-3251-4e86-8059-13a85b1b' \
                      '&service_id=b44e2daf-0ef6-4d11-a115-0eb0d397934f' \
                      '&process=&seqId=&seqPid=&privilegeId='

        report_form_resp = session.get(REPORT_FORM, allow_redirects=False, timeout=API_TIMEOUT)
        _logger.debug(f'[report page] status: {report_form_resp.status_code}')
        if report_form_resp.status_code == 302:
            if self.username != None:
                session = self.login()
            else:
                # TODO: warning status update
                self.status = THUUserStatus.warning
                self.save()
                raise RuntimeWarning(f'Cookies expired with no login info set. Please update your cookie.')
            report_form_resp = session.get(REPORT_FORM, allow_redirects=False, timeout=API_TIMEOUT)
        if report_form_resp.status_code != 200:
            RuntimeError(f'Report Page returned {report_form_resp.status_code}.')

        page_html = report_form_resp.text
        assert 'rowSet' in page_html, "报告页面返回信息不正确"

        # 从上报页面中提取 POST 的参数
        post_data = extract_post_data(page_html)
        self.latest_data = post_data
        self.save()
        _logger.debug(f'[report api] Final data: {post_data}')

        REPORT_API = 'https://thos.tsinghua.edu.cn/fp/formParser?status=update' \
                     '&formid=6cfd2789-3251-4e86-8059-13a85b1b' \
                     '&workflowAction=startProcess' \
                     '&seqId=&unitId=&workitemid=' \
                     '&process='
        # 最终 POST
        report_api_resp = session.post(REPORT_API, post_data,
            headers={'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
            timeout=API_TIMEOUT
        )
        assert report_api_resp.status_code == 200, "提交 API 状态异常"

        self.latest_response_data = report_api_resp.text.strip()
        self.latest_response_time = datetime.datetime.now()
        self.save()

        if report_api_resp.json().get('SYS_PK', None) and report_api_resp.json().get('SYS_FK', None):
            return report_api_resp.text.strip()
        else:
            raise Exception(report_api_resp.text.strip())

def db_init():
    database_proxy.connect()
    database_proxy.create_tables([TGUser, THUUser])

