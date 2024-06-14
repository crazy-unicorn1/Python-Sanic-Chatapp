# -*- coding: utf-8 -*-

CMS_USER_SESSION_KEY = 'cms_user_session_@131411520990'
FRONT_USER_SESSION_KEY = 'front_user_session_@131411520990'

# 缓存机制
SITE_CONFIG_CACHE = type('SiteConfigCache', (object,), {})()
FRONT_CONFIG_CACHE = type('FrontConfigCache', (object,), {})()

# 主域名
MAIN_DOMAIN = []

# 默认头像
DEFAULT_PORTRAIT = '/assets/chat/images/keFuLogo.png'

# 导出文件夹名称
EXPORT_FOLDER = 'export_data'

# 静态文件夹名称
STATIC_FOLDER = 'static'
ASSETS_FOLDER = 'assets'
# 私有目录
PRIVATE_FOLDER = 'private'
# 公开目录
PUBLIC_FOLDER = 'public'

# 上传文件夹
UPLOAD_FOLDER = 'upload'
# 备份文件夹
DATA_BACKUP_FOLDER = 'backup'
# 图片文件夹名称
IMAGES_FOLDER = 'images'
# 图片类型限制
IMAGES_TYPES = ['.png', '.jpeg', '.jpg', '.svg', '.gif']
# 文件类型格式
FIEL_TYPES = ['.txt', '.xlsx', '.csv', '.word', '.doc', '.dot']
# 音频类型格式
AUDIO_TYPES = ['.wav', '.flac', '.ape', '.alac', '.mp3', '.aac', '.vorbis', '.opus']
# 视频类型格式
VIDEO_TYPES = ['.wmv', '.saf', '.rm', '.rmvb', '.mp4', '.3gp', '.mov', '.m4v', '.avi', '.dat', '.mkv']

DEFAULT_FILE_SIZE = 1024 * 1024 * 10

# SOCKET 客服连接
SERVICE_CONNECTION = {}

# SOCKET 客户端连接
CLIENT_CONNECTION = {}

##############
CHAT_NAMESPACE_CONNECTIONS = {}
SERVICECHAT_NAMESPACE_CONNECTIONS = {}
#
# 接入网站缓存
SITE_DICT_CACHE = {}

# 语言JSON
LANGUAGE_JSON = []

# CMS语言_JSON
CMS_LANGUAGE_JSON = []


class UrlPrefix:
    """URL前缀"""
    FRONT_PREFIX = '/'
    API_PREFIX = '/api'
    COMMON_PREFIX = '/common'
    CMS_PREFIX = '/site_admin'



class ExportStatu:
    """导出状态"""
    successed = 'successed'
    failed = 'failed'
    ongoing = 'ongoing'
    name_arr = (successed, failed, ongoing,)
    name_dict = {
        successed: '导出成功', failed: '导出失败', ongoing: '导出中',
    }
    class_dict = {
        successed: 'btn-success', failed: 'btn-danger', ongoing: 'btn-warning',
    }


class CodingType:
    """编码类型"""
    UTF8 = 'UTF-8'
    GB2312 = 'GB2312'
    GBK = 'GBK'
    GB18030 = 'GB18030'
    name_arr = (UTF8, GB2312, GBK, GB18030,)
    name_dict = {UTF8: 'UTF-8', GB2312: 'GB2312', GBK: 'GBK', GB18030: 'GB18030',}


class PermissionCls:
    SUPERADMIN = 'superadmin'
    Administrator = 'administrator'
    AgentAdmin = 'agentadmin'
    CustomerService = 'customerservice'

    name_arr = (
        SUPERADMIN,
        Administrator,
        CustomerService
    )

    kfshare_arr = (
        SUPERADMIN,
        Administrator,
        CustomerService,
        AgentAdmin
    )

    name_dict = {
        SUPERADMIN: '[系统]管理员',
        Administrator: '管理员',
        CustomerService: '客服',
        AgentAdmin: '代理商',
    }


class OnlineStatu:
    online = 'online'
    bebusy = 'bebusy'
    offline = 'offline'

    name_arr = [online, bebusy, offline]

    name_dict = {
        online: '在线',
        bebusy: '忙碌',
        offline: '离线',
    }



class ClientTypes:
    PC = 'pc'
    Mobile = 'mobile'
    name_arr = [PC, Mobile]

    name_dict = {
        PC: '电脑端',
        Mobile: '移动端',
    }



class BrowserTypes:
    Chrome = 'chrome'
    Firefox = 'firefox'
    Edge = 'edge'
    coccoc = 'coccoc'
    Safari = 'safari'
    name_arr = [Chrome, Firefox, Edge, coccoc, Safari]

    name_dict = {
        Chrome: '谷歌浏览器',
        Firefox: '火狐浏览器',
        Edge: 'Edge浏览器',
        coccoc: 'CocCoc浏览器',
        Safari: 'Safari',
    }


class SystemTypes:
    windows = 'windows'
    linux = 'linux'
    macos = 'mac os x'
    IOS = 'ios'

    name_arr = (windows, linux, macos, IOS)

    name_dict = {
        windows: 'Windows',
        linux: 'Linux',
        macos: 'Mac OS X',
        IOS: 'IOS',
    }


class ConversationStatu:
    normal = 'normal'
    waiting = 'waiting'
    finished = 'finished'

    name_arr = (normal, waiting, finished)
    name_dict = {
        normal: '正常',
        waiting: '等待中',
        finished: '已结束',
    }



class translateStatu:
    TSCS = 'tscs'
    WTCSS = 'wtcss'
    TFBS = 'tfbs'
    CLOSED = 'closed'

    name_arr = (TSCS, WTCSS, TFBS, CLOSED)
    name_dict = {
        TSCS: '开启客户端翻译，关闭客服端翻译',
        WTCSS: '开启客服端翻译，关闭客户端翻译',
        TFBS: '开启双向翻译',
        CLOSED: '关闭翻译',
    }



class ContentTypes():
    TEXT = 'text'
    PICTURE = 'picture'
    VIDEO = 'video'
    AUDIO = 'audio'
    FILE = 'file'

    name_arr = (TEXT, PICTURE, VIDEO, FILE, AUDIO)

    name_dict = {
        TEXT: '文本',
        PICTURE: '图片',
        VIDEO: '视频',
        AUDIO: '音频',
        FILE: '文件',
    }


class LANGUAGE:
    zh_CN = 'zh_CN' # 中文
    en_US = 'en_US' # 英文
    vi_VN = 'vi_VN' # 越南
    ba_IDN = 'ba_IDN' # 印尼
    bx_Pr = 'bx_Pr' # 巴西-葡萄牙语
    ja = 'ja' # 日语
    ko = 'ko' # 韩语
    ms = 'ms' # 马来语

    name_arr = (zh_CN, en_US, vi_VN, ba_IDN, bx_Pr, ja, ko, ms)

    name_dict = {
        zh_CN: '中文简体',
        en_US: 'English',
        vi_VN: 'Tiếng Việt',
        ba_IDN: 'bahasa Indonesia',
        bx_Pr: 'Brasil-Português',
        ja: '日本語',
        ko: '한국인',
        ms: 'Melayu',
    }
    lang_code = {
        zh_CN: "zh-CN",
        vi_VN: "vi",
        bx_Pr: "pt",
        ba_IDN: "id",
        en_US: "en",
        ja: "ja",
        ko: "ko",
        ms: "ms",
    }


LANGUAGE_HINT_ALL = [
    {
        'title': '更新语言',
        'text': '您确定要将语言更新为中文简体吗?',
        'code': LANGUAGE.zh_CN,
    },
    {
        'title': 'update language',
        'text': 'Are you sure you want to update the language to English？',
        'code': LANGUAGE.en_US,
    },
    {
        'title': 'cập nhật ngôn ngữ',
        'text': 'Bạn có chắc chắn muốn cập nhật ngôn ngữ sang tiếng Việt không?',
        'code': LANGUAGE.vi_VN,
    },
    {
        'title': 'memperbarui bahasa',
        'text': 'Apakah Anda yakin ingin memperbarui bahasa ke bahasa Indonesia?',
        'code': LANGUAGE.ba_IDN,
    },
    {
        'title': 'atualizar idioma',
        'text': 'Tem certeza de que deseja atualizar o idioma para português?',
        'code': LANGUAGE.bx_Pr,
    },
    {
        'title': '言語を更新する',
        'text': '言語を日本語に更新してもよろしいですか?',
        'code': LANGUAGE.ja,
    },
    {
        'title': '언어 업데이트',
        'text': '언어를 중국어 간체로 업데이트하시겠습니까?',
        'code': LANGUAGE.ko,
    },
    {
        'title': '马来语',
        'text': '언어를 중국어 간체로 업데이트하시겠습니까?',
        'code': LANGUAGE.ms,
    },
]



# #4d70ff

duration_dcit = {
    '1': '1小时',
    '3': '3小时',
    '5': '5小时',
    '10': '10小时',
    '24': '一天',
    '48': '两天',
    '168': '一周',
    '336': '两周',
    '720': '一个月',
    '2160': '三个月',
    '4320': '半年',
    '999999': '永久',
}

class OPERATION_TYPES:
    LOGIN = 'login'
    OUTLOG = 'outlog'
    ADD = 'add'
    DEL = 'del'
    UPDATE = 'update'
    ACCESS = 'access'
    ONLINE = 'online'
    BEBUSY = 'bebusy'
    OFFLINE = 'offline'
    name_arr = (LOGIN, OUTLOG, ADD, DEL, UPDATE, ACCESS, ONLINE, BEBUSY, OFFLINE)
    name_dict = {
        LOGIN: '登录',
        OUTLOG: '退出登录',
        ADD: '添加数据',
        DEL: '删除数据',
        UPDATE: '更新数据',
        ACCESS: '访问页面',
        ONLINE: '上线',
        BEBUSY: '忙碌',
        OFFLINE: '离线',
    }



'''
依赖库
eventlet==0.30.2
gevent
gunicorn
'''

'''
另外，Nginx还提供了一个reload的命令，可以在不停止服务器的情况下重新加载配置文件。例如，可以执行以下命令来重新加载Nginx的配置文件：
$ nginx -s reload

1. 在首页增加一个统计表格，带搜索框，可以根据搜索条件统计（都是再搜索条件内积累统计，默认数据为空， 搜索后才出数据）。
表格列项：客服名称、客服在线时长、忙碌时长、登入时长、登出时长、平均对话时长、平均首次回复时长、正在对话数量、总会话数、有效会话数、总消息数
在线时长：积累在线时长（有三种状态，在线离线和忙碌，这个只统计在线状态的时长）。
忙碌时长：积累忙碌时长。
登出时长：退出账户登录的时长。
有效会话数：指客户有回复的对话。
平均首次回复时长：指从创建会话到客服首次回复的平均时长。
2. 对话增加小窗口方便回复和多开，类似QQ独立的会话窗口一样

滑动验证码
https://docs.hcaptcha.com/

https://dashboard.hcaptcha.com/welcome#
site key 
1.6b25cde0-f40e-430e-80ca-6f4d1238f661
2.（easychat.one）
7563be13-5e47-4e8b-be06-77714bb0c1fe
scret ES_7de49fbc5b9d40eaac25d5f6b01b9e22

https://www.hcaptcha.com/pricing?utm_source=docs6
'''


