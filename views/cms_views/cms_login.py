# -*- coding: utf-8 -*-
import datetime
from sanic import Sanic, request, response, views
from sanic.response import redirect, text, html
from sanic_session import Session, InMemorySessionInterface
from sanic_ext import render
from common_utils import xtjson
from common_utils.utils_funcs import get_ip
from models.cms_user import CmsUserModel
from models.kefu_table import signLogTable
from constants import CMS_USER_SESSION_KEY, PermissionCls, SITE_CONFIG_CACHE, OPERATION_TYPES
from modules.view_helpres.tool_func import current_admin_data_dict
from common_utils.lqredis import SiteRedis
from models.kefu_table import FinishListTable
from models.site_table import SiteTable
from modules.google_verify import GooleVerifyCls
from constants import CHAT_NAMESPACE_CONNECTIONS, SERVICECHAT_NAMESPACE_CONNECTIONS


class CmsLoginOut(views.HTTPMethodView):
    add_url_rules = [['/login_out/', 'cms_login_out']]

    def get(self, request):
        session = request.ctx.session

        FinishListTable.delete_many({'service_id': session.get(CMS_USER_SESSION_KEY)})
        syslog = {
            "user_id": session.get(CMS_USER_SESSION_KEY),
            "operation_type": OPERATION_TYPES.OUTLOG,
            "ip": get_ip(),
        }
        signLogTable.insert_one(syslog)

        try:
            if request.ctx.session.sid in SERVICECHAT_NAMESPACE_CONNECTIONS:
                SERVICECHAT_NAMESPACE_CONNECTIONS.pop(request.ctx.session.sid)
            session.pop(CMS_USER_SESSION_KEY)

        except:
            pass
        return redirect("/site_admin/admin/login")


class CmsLogin(views.HTTPMethodView):
    add_url_rules = [['/admin/login/', 'cms_login']]

    def login_limit(self, account):
        ip = get_ip()
        if not ip:
            return
        key = 'ADMIN_LOGIN_LIMIT_NUM_%s'%account
        _crr_num = SiteRedis.get(key)
        if not _crr_num:
            return
        if int(_crr_num.decode()) >= 5:
            return True
        if not _crr_num:
            SiteRedis.set(key, 1, expire=600)
        else:
            SiteRedis.incrby(key, 1)
            SiteRedis.expire(key, 600)
        return

    def get(self, request):
        dd = current_admin_data_dict()
        if dd:
            return redirect("/site_admin/")

        return render('easychat/login.html')

    def post(self, request):
        action = request.form.get('action')
        if action == 'pwdLogin':
            account = request.form.get('account')
            password = request.form.get('password')
            verify_code = request.form.get('verify_code')
            if not account or not password or not account.strip() or not password.strip():
                return xtjson.json_params_error('登录失败1!')
            if self.login_limit(account):
                return xtjson.json_params_error('尝试次数过多！请稍后再试...')
            user_data = CmsUserModel.find_one({'account': account.strip()})
            if not user_data:
                return xtjson.json_params_error('该用户不存在!')
            if not CmsUserModel.check_password(user_data.get('password'), password.strip()):
                return xtjson.json_params_error('登录失败2!')
            if not user_data.get('statu'):
                return xtjson.json_params_error('该账户已被锁定!')

            googleObj = GooleVerifyCls(pwd=user_data.get('uuid'), s_label='kfShare', account=user_data.get('account'))
            is_activate = None
            if user_data.get('role_code') in [PermissionCls.SUPERADMIN, PermissionCls.AgentAdmin]:
                if hasattr(SITE_CONFIG_CACHE, 'google_verify_statu') and getattr(SITE_CONFIG_CACHE, 'google_verify_statu'):
                    if user_data.get('is_activate'):
                        if not verify_code:
                            return xtjson.json_result(code=401, message='请输入验证码！', data={'is_show_qrcode': False})
                        if not googleObj.check_goole_code(verify_code):
                            return xtjson.json_result(code=401, message='验证码输入错误！', data={'is_show_qrcode': False})
                    else:
                        is_activate = True
                        generate_qrcode = googleObj.secret_generate_qrcode()
                        if not verify_code:
                            return xtjson.json_result(code=401, message='请输入验证码！', data={'is_show_qrcode': True, 'generate_qrcode': generate_qrcode})
                        if not googleObj.check_goole_code(verify_code):
                            return xtjson.json_result(code=401, message='验证码输入错误！', data={'is_show_qrcode': True, 'generate_qrcode': generate_qrcode})

            if user_data.get('role_code') == PermissionCls.SUPERADMIN:
                if hasattr(SITE_CONFIG_CACHE, 'cms_ip_whitelist'):
                    cms_ip_whitelist = getattr(SITE_CONFIG_CACHE, 'cms_ip_whitelist')
                    if cms_ip_whitelist or cms_ip_whitelist.strip():
                        crr_ip = get_ip()
                        _ip_statu = False
                        for _ip in crr_ip.split(','):
                            if _ip in cms_ip_whitelist:
                                _ip_statu = True
                        if not _ip_statu:
                            return xtjson.json_params_error('登录失败3！')

            if user_data.get('role_code') == PermissionCls.AgentAdmin:
                zy_finish_time = user_data.get('zy_finish_time')
                if zy_finish_time:
                    if datetime.datetime.now() > zy_finish_time:
                        return xtjson.json_params_error('您的使用权限已到期！请联系客服！')

            if user_data.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
                responsible_site = user_data.get('responsible_site')
                if responsible_site:
                    _site_data = SiteTable.find_one({'site_code': responsible_site}) or {}
                    if _site_data:

                        finish_time = _site_data.get('finish_time')
                        if finish_time and datetime.datetime.now() > finish_time:
                            return xtjson.json_params_error('您的使用权限已到期，请联系代理！')

                        ip_whitelist = _site_data.get('ip_whitelist') or ''
                        if ip_whitelist and ip_whitelist.strip():
                            REMOTE_ADDR = get_ip()
                            crrip = str(REMOTE_ADDR or '').split(',')[0]
                            if crrip not in ip_whitelist:
                                print(11)
                                return xtjson.json_params_error('登录失败4！')

                        site_google_verify_statu = _site_data.get('site_google_verify_statu') or ''
                        if site_google_verify_statu:
                            if user_data.get('is_activate'):
                                if not verify_code:
                                    return xtjson.json_result(code=401, message='请输入验证码！', data={'is_show_qrcode': False})
                                if not googleObj.check_goole_code(verify_code):
                                    return xtjson.json_result(code=401, message='验证码输入错误！', data={'is_show_qrcode': False})
                            else:
                                is_activate = True
                                generate_qrcode = googleObj.secret_generate_qrcode()
                                if not verify_code:
                                    return xtjson.json_result(code=401, message='请输入验证码！', data={'is_show_qrcode': True, 'generate_qrcode': generate_qrcode})
                                if not googleObj.check_goole_code(verify_code):
                                    return xtjson.json_result(code=401, message='验证码输入错误！', data={'is_show_qrcode': True, 'generate_qrcode': generate_qrcode})
                        ip_whitelist = _site_data.get('ip_whitelist') or ''
                        if ip_whitelist and ip_whitelist.strip():
                            crr_ip = get_ip()
                            _ip_statu = False
                            for _ip in crr_ip.split(','):
                                if _ip in ip_whitelist:
                                    _ip_statu = True
                            if not _ip_statu:
                                return xtjson.json_params_error('登录失败5！')

            if user_data.get('role_code') == PermissionCls.Administrator:
                super_admin_id = user_data.get('super_admin_id')
                super_admin_data =  CmsUserModel.find_one({'uuid': super_admin_id}) or {}
                if super_admin_data and super_admin_data.get('role_code') == PermissionCls.AgentAdmin:
                    zy_finish_time = super_admin_data.get('zy_finish_time')
                    if zy_finish_time:
                        if datetime.datetime.now() > zy_finish_time:
                            return xtjson.json_params_error('您的使用权限已到期！')

            if user_data.get('role_code') == PermissionCls.CustomerService:
                super_admin_id = user_data.get('super_admin_id')
                super_admin_data =  CmsUserModel.find_one({'uuid': super_admin_id}) or {}
                super_admin_id = super_admin_data.get('super_admin_id')
                super_admin_data =  CmsUserModel.find_one({'uuid': super_admin_id}) or {}
                if super_admin_data and super_admin_data.get('role_code') == PermissionCls.AgentAdmin:
                    zy_finish_time = super_admin_data.get('zy_finish_time')
                    if zy_finish_time:
                        if datetime.datetime.now() > zy_finish_time:
                            return xtjson.json_params_error('您的使用权限已到期！')

            _ccu = CmsUserModel.find_one({'account': account.strip()})
            upda_dict = {
                '_last_login_ip': get_ip(),
                '_last_login_time': _ccu.get('_current_login'),
                '_current_login': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            if is_activate is not None:
                upda_dict['is_activate'] = is_activate
            CmsUserModel.update_one({'account': account.strip()},{'$set': upda_dict})
            FinishListTable.delete_many({'service_id': user_data.get('uuid')})

            syslog = {
                "user_id": user_data.get('uuid'),
                "operation_type": OPERATION_TYPES.LOGIN,
                "ip": get_ip(),
                "site_code": user_data.get("reponsible_site")
            }
            signLogTable.insert_one(syslog)

            request.ctx.session[CMS_USER_SESSION_KEY] = user_data.get('uuid')

            #SERVICECHAT_NAMESPACE_CONNECTIONS.clear()
            return xtjson.json_result()
        return xtjson.json_params_error('操作失败6!')

