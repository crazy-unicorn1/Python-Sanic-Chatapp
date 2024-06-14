from constants import SITE_CONFIG_CACHE, CMS_USER_SESSION_KEY
from models.cms_user import CmsUserModel
from common_utils.utils_funcs import get_ip
from sanic.request import Request

def current_admin_data_dict():
    ''' 获取后台当前登录用户数据 '''
    request = Request.get_current()
    uuid = request.ctx.session.get(CMS_USER_SESSION_KEY)
    if not uuid:
        return {}
    user_dict = CmsUserModel.find_one({'uuid': uuid})
    return user_dict

def check_front_domain():
    ''' 检测网站前端域名 '''
    if not hasattr(SITE_CONFIG_CACHE, 'front_domain'):
        return False, '网站前端域名未设置!'
    front_domain = getattr(SITE_CONFIG_CACHE, 'front_domain')
    if not front_domain:
        return False, '网站前端域名未设置'
    return True, front_domain

def check_ip():
    """检测黑名单"""
    if hasattr(SITE_CONFIG_CACHE, 'cms_ip_whitelist'):
        cms_ip_whitelist = getattr(SITE_CONFIG_CACHE, 'cms_ip_whitelist')
        if cms_ip_whitelist or cms_ip_whitelist.strip():
            crr_ip = get_ip()
            for _ip in crr_ip.split(','):
                if _ip in crr_ip:
                    return True
            return

    return True


def front_risk_control():
    ''' 前端风控 '''
    from flask import request, abort
    # if 'chat_LaUETT' in request.url:
    #     raise NotFound("404")

    return True, None



def cms_risk_control():
    ''' 后端风控 '''
    # if not check_ip():
    #     raise NotFound("404")
    pass



def proejct_template_path(path):
    ''' 模板文件路径前缀 '''
    if path.startswith('/'):
        _path = 'project_kfShare' + path
    else:
        _path = 'project_kfShare' + '/' + path
    return _path.replace('//', '/')

