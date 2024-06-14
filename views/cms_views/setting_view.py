import os, datetime, shortuuid
from .cms_base import CmsFormViewBase
from modules.view_helpres.view_func import update_language
from models.cms_user import CmsUserModel
from models.kefu_table import ChatConversationTable, BlacklistTable, CustomerTable, problemTable, categoryTable, systemLogTable, QuickReplyTable
from models.site_table import SiteTable, ExportDataModel
from models.cms_table import SiteConfigModel
from constants import PermissionCls, LANGUAGE, DEFAULT_FILE_SIZE, SITE_DICT_CACHE, OPERATION_TYPES, SITE_CONFIG_CACHE
from common_utils.utils_funcs import PagingCLS, get_ip, render_template
from modules.view_helpres.view_func import site_form_html, del_site_data
from sanic.exceptions import NotFound
from sanic.request import Request
from sanic import Sanic
import aiofiles
# 设置页面
class SettingView(CmsFormViewBase):
    add_url_rules = [['/setting', 'SettingView']]

    # 设置
    async def get_setup_html(self):

        other_nav_html = ''
        siteDomain_nav_html = ''
        site_setting_html = ''
        if self.current_admin_dict.get('role_code') in [PermissionCls.SUPERADMIN, PermissionCls.AgentAdmin, PermissionCls.Administrator]:

            if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
                siteDomain_nav_html = '''
                    <li class="classItem siteDomainLi" onclick="loadingTabFunc($(this), 'siteDomainManage')">
                        <span class="iconbox" style="background: rgb(85, 167, 247);">
                            <i class="iconfont icon-yumingyuwangzhan"></i>
                        </span>
                        <span>网站域名</span>
                    </li>            
                '''
            if self.current_admin_dict.get('role_code') in [PermissionCls.SUPERADMIN, PermissionCls.AgentAdmin]:
                site_setting_html += '''
                    <li class="classItem active siteAccessNav" onclick="loadingTabFunc($(this), 'siteAccess')">
                        <i class="iconfont icon-zcpt-wangzhanguanli" style="color: #60b2fb;"></i>
                        <span>网站接入</span>
                    </li>            
                '''
            else:
                responsible_site = self.current_admin_dict.get('responsible_site')
                _crr_site_data = SiteTable.find_one({'site_code': responsible_site}) or {}
                site_setting_html += f'''
                    <li class="classItem siteJieRu" onclick="loadingTabFunc($(this), 'siteAccessCode', '{_crr_site_data.get('site_code') or ''}')">
                        <span class="iconbox" style="background: #76a99c;">
                            <i class="iconfont icon-code"></i>
                        </span>
                        <span>网站接入</span>
                    </li>                        
                    <li class="classItem siteSettingLi" onclick="loadingTabFunc($(this), 'siteSetting', '{_crr_site_data.get('site_code') or ''}')">
                        <span class="iconbox" style="background: #3eb0b0;">
                            <i class="iconfont icon-xitongpeizhi"></i>
                        </span>
                        <span>网站配置</span>
                    </li>
                    <li class="classItem" onclick="loadingTabFunc($(this), 'siteColor', '{_crr_site_data.get('site_code') or ''}')">
                        <span class="iconbox" style="background: #dbeaff;">
                            <i class="iconfont icon-pifuguanli"></i>
                        </span>
                        <span>个性化</span>
                    </li>
                '''
            if self.current_admin_dict.get('role_code') in [PermissionCls.SUPERADMIN, PermissionCls.AgentAdmin]:
                other_nav_html = '''
                    <li class="classItem" onclick="loadingTabFunc($(this), 'otherSetup')">
                        <span class="iconbox" style="background: #7fa7da;">
                            <i class="iconfont icon-qita"></i>
                        </span>
                        <span>其它</span>
                    </li>                
                '''
        else:
            responsible_site = self.current_admin_dict.get('responsible_site')
            _crr_site_data = SiteTable.find_one({'site_code': responsible_site}) or {}
            site_setting_html += f'''
                <li class="classItem siteJieRu" onclick="loadingTabFunc($(this), 'siteAccessCode', '{_crr_site_data.get('site_code') or ''}')">
                    <span class="iconbox" style="background: #76a99c;">
                        <i class="iconfont icon-code"></i>
                    </span>
                    <span>网站接入</span>
                </li>                        
            '''

        self.context['siteDomain_nav_html'] = siteDomain_nav_html
        self.context['site_setting_html'] = site_setting_html
        self.context['other_nav_html'] = other_nav_html
        self.context['current_admin_dict'] = self.current_admin_dict
        self.context['PermissionCls'] = PermissionCls
        html = await render_template('easychat/setting/setup.html', self.context)
        html = update_language(self.language, html)
        return html

    # 获取网站配置
    def getSiteData_func(self, site_code):
        site_data = SiteTable.find_one({'site_code': site_code}) or {}
        if not site_data:
            return self.xtjson.json_params_error()
        data_from = {}
        data_from['site_code'] = site_code
        data_from['site_name'] = site_data.get('site_name') or ''
        data_from['site_title'] = site_data.get('site_title') or ''
        data_from['clew_text'] = site_data.get('clew_text') or ''
        data_from['site_icon'] = site_data.get('site_icon') or ''
        data_from['use_domain'] = site_data.get('use_domain') or self.MAIN_DOMAIN
        data_from['site_main_color'] = site_data.get('site_main_color') or ''
        data_from['site_announcement'] = site_data.get('site_announcement') or ''
        data_from['site_right_info_img'] = site_data.get('site_right_info_img') or ''
        data_from['site_right_info_back_color'] = site_data.get('site_right_info_back_color') or ''
        data_from['default_comment'] = site_data.get('default_comment') or ''

        data_from['control_file_type_state'] = site_data.get('control_file_type_state') or False
        data_from['site_google_verify_statu'] = site_data.get('site_google_verify_statu') or False
        data_from['fast_state'] = site_data.get('fast_state') or False
        data_from['beep_switch'] = site_data.get('beep_switch') or False
        data_from['control_file_types'] = site_data.get('control_file_types') or []
        data_from['automati_creply'] = site_data.get('automati_creply') or ''
        data_from['automati_creply_time'] = site_data.get('automati_creply_time') or ''
        data_from['automati_close_time'] = site_data.get('automati_close_time') or ''
        data_from['control_file_size'] = site_data.get('control_file_size') or DEFAULT_FILE_SIZE
        data_from['ip_whitelist'] = site_data.get('ip_whitelist') or ''

        data_from['translate_statu'] = site_data.get('translate_statu') or False
        data_from['client_language'] = site_data.get('client_language') or ''
        data_from['service_language'] = site_data.get('service_language') or ''
        data_from['client_service_language'] = site_data.get('client_service_language') or ''
        data_from['service_client_language'] = site_data.get('service_client_language') or ''
        return self.xtjson.json_result(data=data_from)

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_setup_html()
            return self.xtjson.json_result(data={'html': html})
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'getSiteData':
            site_code = self.request_data.get('site_code')
            if not site_code:
                return self.xtjson.json_params_error()
            return self.getSiteData_func(site_code)


# 网站管理
class SiteManageView(CmsFormViewBase):
    add_url_rules = [['/siteManage', 'siteManageView']]
    per_page = 15

    # 获取网站数据
    def getSiteData_func(self, site_code):
        site_data = SiteTable.find_one({'site_code': site_code}) or {}
        if not site_data:
            return
        data_from = {}
        data_from['site_code'] = site_code
        data_from['site_name'] = site_data.get('site_name') or ''
        data_from['site_title'] = site_data.get('site_title') or ''
        data_from['clew_text'] = site_data.get('clew_text') or ''
        data_from['site_icon'] = site_data.get('site_icon') or ''
        data_from['use_domain'] = site_data.get('use_domain') or self.MAIN_DOMAIN
        data_from['site_main_color'] = site_data.get('site_main_color') or ''
        data_from['site_announcement'] = site_data.get('site_announcement') or ''
        data_from['site_right_info_img'] = site_data.get('site_right_info_img') or ''
        data_from['site_right_info_back_color'] = site_data.get('site_right_info_back_color') or ''
        data_from['default_comment'] = site_data.get('default_comment') or ''

        data_from['control_file_type_state'] = site_data.get('control_file_type_state') or False
        data_from['site_google_verify_statu'] = site_data.get('site_google_verify_statu') or False
        data_from['fast_state'] = site_data.get('fast_state') or False
        data_from['control_file_types'] = site_data.get('control_file_types') or []
        data_from['automati_creply'] = site_data.get('automati_creply') or ''
        data_from['automati_creply_time'] = site_data.get('automati_creply_time') or ''
        data_from['automati_close_time'] = site_data.get('automati_close_time') or ''
        data_from['control_file_size'] = site_data.get('control_file_size') or DEFAULT_FILE_SIZE
        data_from['ip_whitelist'] = site_data.get('ip_whitelist') or ''

        data_from['translate_statu'] = site_data.get('translate_statu') or False
        data_from['client_language'] = site_data.get('client_language') or ''
        data_from['service_language'] = site_data.get('service_language') or ''
        data_from['client_service_language'] = site_data.get('client_service_language') or ''
        data_from['service_client_language'] = site_data.get('service_client_language') or ''
        return data_from

    # 获取网站列表
    async def get_siteList_html(self):
        request = Request.get_current()
        siteTable_html = ''
        not_data_html = ''
        site_data = {}
        if self.context.get('tabName') == 'siteAccess':
            try:
                page = int(request.args.get('page') or 1)
            except:
                page = 1
            
            SiteList = []
            total = 0
            skip = (page - 1) * self.per_page

            if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
                total = SiteTable.count({})
                SiteList = SiteTable.find_many({}, limit=self.per_page, skip=skip, sort=[['_create_time', -1]])

            if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                _uds = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
                if _uds:
                    scodes = []
                    for _ud in _uds:
                        _sd = _ud.get('responsible_site')
                        if _sd not in scodes:
                            scodes.append(_sd)
                    total = SiteTable.count({'site_code': {'$in': scodes}})
                    SiteList = SiteTable.find_many({'site_code': {'$in': scodes}}, limit=self.per_page, skip=skip, sort=[['_create_time', -1]])

            pages, total_page = PagingCLS.ustom_pagination(page, total, self.per_page)
            pages, total_page = PagingCLS.ustom_pagination(page, total, self.per_page)
            pages, total_page = PagingCLS.ustom_pagination(page, total, self.per_page)
            
            self.context['datas'] = SiteList

            page_html = f'''
                    <span>总信息条数：{total}</span>
                    <ul class="pages" data-crrpage="{page}">
            '''

            if total == 0:
                page_html += f'''                
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>                
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                            
                '''
            else:
                if page == 1:
                    page_html += f'''
                            <li class="left_page forbid">
                                <span class="iconfont icon-fangxiang-zuo"></span>
                            </li>
                    '''
                else:
                    page_html += f'''
                            <li class="left_page" onclick="fatch_data_list({page - 1});">
                                <span class="iconfont icon-fangxiang-zuo"></span>
                            </li>
                    '''
                for crrpage in pages:
                    if crrpage == page:
                        page_html += f'''
                        <li class="active"><span>{crrpage}</span></li>
                        '''
                    else:
                        page_html += f'''
                        <li onclick="fatch_data_list({crrpage});"><span>{crrpage}</span></li>
                        '''
                if page == total_page:
                    page_html += f'''
                            <li class="right_page forbid">
                                <span class="iconfont icon-fangxiang-you"></span>
                            </li>
                        </ul>                    
                    '''
                else:
                    page_html += f'''
                            <li class="right_page" onclick="fatch_data_list({page + 1});">
                                <span class="iconfont icon-fangxiang-you"></span>
                            </li>
                        </ul>                    
                    '''
            self.context['page_html'] = page_html
            
        if self.context.get('tabName') == 'siteAccessCode':
            site_data = self.getSiteData_func(self.context.get('site_code'))

        if self.context.get('tabName') == 'siteColor':
            site_data = self.getSiteData_func(self.context.get('site_code'))

        if self.context.get('tabName') == 'siteSetting':
            site_data = self.getSiteData_func(self.context.get('site_code'))

        self.context['LANGUAGE'] = LANGUAGE
        self.context['site_data'] = site_data
        self.context['siteTable_html'] = siteTable_html or not_data_html
        html = await render_template('easychat/setting/siteManage.html', self.context)
        html = update_language(self.language, html)
        return html

    # 修改网站个性化
    def updateSiteColor(self):
        site_code = self.request_data.get('site_code')
        site_title = self.request_data.get('site_title')
        site_icon = self.request_data.get('site_icon') or ''
        site_main_color = self.request_data.get('site_main_color')
        site_right_info_img = self.request_data.get('site_right_info_img') or ''
        site_right_info_back_color = self.request_data.get('site_right_info_back_color')
        if not site_code:
            return self.xtjson.json_params_error()
        if not site_title:
            return self.xtjson.json_params_error('请输入网站标题')
        site_data = SiteTable.find_one({'site_code': site_code})
        if not site_data:
            return self.xtjson.json_params_error()
        data_from = {}
        data_from['site_title'] = site_title.strip()
        data_from['site_icon'] = site_icon
        data_from['site_main_color'] = site_main_color
        data_from['site_right_info_img'] = site_right_info_img
        data_from['site_right_info_back_color'] = site_right_info_back_color
        SiteTable.update_one({'site_code': site_code}, {'$set': data_from})
        SiteTable.update_site_config()
        return self.xtjson.json_result()

    # 更新网站配置
    def edit_siteSetting_func(self):
        site_code = self.request_data.get('site_code')
        clew_text = self.request_data.get('clew_text')
        control_file_type_state = self.request_data.get('control_file_type_state')
        site_google_verify_statu = self.request_data.get('site_google_verify_statu')
        fast_state = self.request_data.get('fast_state')
        beep_switch = self.request_data.get('beep_switch')
        control_file_types = self.request_data.getlist('control_file_types[]') or []
        automati_creply = self.request_data.get('automati_creply') or ''
        automati_creply_time = self.request_data.get('automati_creply_time') or ''
        automati_close_time = self.request_data.get('automati_close_time') or ''
        default_comment = self.request_data.get('default_comment') or ''
        site_announcement = self.request_data.get('site_announcement') or ''
        control_file_size = self.request_data.get('control_file_size') or 0
        ip_whitelist = self.request_data.get('ip_whitelist') or ''
        translate_statu = self.request_data.get('translate_statu') or ''
        client_language = self.request_data.get('client_language') or ''
        service_language = self.request_data.get('service_language') or ''
        client_service_language = self.request_data.get('client_service_language') or ''
        service_client_language = self.request_data.get('service_client_language') or ''
        control_file_size = float(control_file_size)

        if not site_code:
            return self.xtjson.json_params_error()

        state = False
        if control_file_type_state == '1':
            state = True
        if control_file_type_state == '0':
            state = False

        _site_google_verify_statu = False
        if site_google_verify_statu == '1':
            _site_google_verify_statu = True
        if site_google_verify_statu == '0':
            _site_google_verify_statu = False

        _fast_state = False
        if fast_state == '1':
            _fast_state = True
        if fast_state == '0':
            _fast_state = False

        _beep_switch = False
        if beep_switch == '1':
            _beep_switch = True
        if beep_switch == '0':
            _beep_switch = False

        data_form = {
            'clew_text': clew_text,
            'control_file_type_state': state,
            'control_file_types': control_file_types,
            'site_announcement': site_announcement,
            'automati_creply': automati_creply,
            'automati_creply_time': automati_creply_time,
            'automati_close_time': automati_close_time,
            'default_comment': default_comment,
            'control_file_size': control_file_size,
            'site_google_verify_statu': _site_google_verify_statu,
            'fast_state': _fast_state,
            'beep_switch': _beep_switch,
            'translate_statu': translate_statu,
            'client_language': client_language,
            'service_language': service_language or '',
            'client_service_language': client_service_language or '',
            'service_client_language': service_client_language or '',
        }
        if ip_whitelist and ip_whitelist.strip():
            ip_whitelist = ip_whitelist.strip()
        data_form['ip_whitelist'] = ip_whitelist or ''

        SiteTable.update_one({'site_code': site_code}, {'$set': data_form})
        while SITE_DICT_CACHE:
            for k in list(SITE_DICT_CACHE):
                SITE_DICT_CACHE.pop(k)
        _sds = SiteTable.find_many({}) or []
        for sd in _sds:
            SITE_DICT_CACHE[sd.get('site_code')] = sd
        return self.xtjson.json_result()

    def siteAccess_list_html(self):
        request = Request.get_current()
        __context = {}
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        skip = (page - 1) * self.per_page
        filter_dict, context_res = {}, {}
        
        SiteList = []
        total = 0

        filter_dict = {}
        if request.args.get('site_name'):
            filter_dict["site_name"] = request.args.get('site_name')
        if request.args.get('link'):
            filter_dict["link"] = request.args.get('link')
        if request.args.get('finish_day'):
            days = int(request.args.get('finish_day'))
            finish_time = datetime.datetime.now() + datetime.timedelta(days = days)
            filter_dict["finish_time"] = {"$lt": finish_time}


        if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
            total = SiteTable.count(filter_dict)
            SiteList = SiteTable.find_many(filter_dict, limit=self.per_page, skip=skip, sort=[['_create_time', -1]])

        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            _uds = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
            if _uds:
                scodes = []
                for _ud in _uds:
                    _sd = _ud.get('responsible_site')
                    if _sd not in scodes:
                        scodes.append(_sd)
                filter_dict['site_code'] = {'$in': scodes}
                total = SiteTable.count(filter_dict)
                SiteList = SiteTable.find_many(filter_dict, limit=self.per_page, skip=skip, sort=[['_create_time', -1]])

        pages, total_page = PagingCLS.ustom_pagination(page, total, self.per_page)
        pages, total_page = PagingCLS.ustom_pagination(page, total, self.per_page)
        
        __context['page'] = page
        __context['pages'] = pages
        __context['total_page'] = total_page
        __context['total'] = total
        __context['context_res'] = context_res

        html = ''
        if SiteList:
            for data in SiteList:
                html += f'''
                    <tr>
                        <td>{data.get("site_name")}</td>
                        <td>{data.get("create_cust_service_count")}</td>
                        <td>{data.get("link")}</td>
                        <td>{ LANGUAGE.name_dict[data.get("site_language")]}</td>
                        <td>{data.get("use_domain")}</td>
                        <td>{self.format_time_func(data.get("finish_time"), "%Y-%m-%d")} </td>
                        <td width="300">{self.format_time_func(data.get("_create_time"), "%Y-%m-%d %H:%M:%S")}</td>
                        <td width="160">
                            <div class="d-flex justify-content-between">
                                <i class="iconfont icon-xitongpeizhi" style="font-size: 20px;"
                                    onclick="loadingTabFunc($(this), 'siteSetting', '{data.get('site_code') or ''}')"></i>
                                <i class="iconfont icon-pifuguanli" style="font-size: 14px;"
                                    onclick="loadingTabFunc($(this), 'siteColor', '{data.get('site_code') or ''}')"></i>
                                <i class="iconfont icon-code"
                                    onclick="loadingTabFunc($(this), 'siteAccessCode', '{data.get('site_code') or ''}')"></i>
                                <i class="iconfont icon-bianji"
                                    onclick="post_from_html('edit_site_html', '{data.get('uuid')}', '编辑网站信息', 700, '/site_admin/siteManage')"></i>
                                <i class="iconfont icon-shanchu" onclick="delSite_func('{data.get('uuid')}')"></i>
                            </div>
                        </td>
                    </tr>
                '''
        else:
            html += '''
                <div style="width: 100%; height: 100%; position: relative; overflow: hidden; box-sizing: border-box; display: flex; justify-content: center; align-items: center; flex-direction:column; margin-top: 3%;">
                    <img src="/assets/pic/not_data.png" alt="" style="width: 130px; position: relative; display: block;">
                    <p style="color: #666;">暂无数据</p>
                </div>
            '''
        page_html = f'''
                <span>总信息条数：{total}</span>
                <ul class="pages" data-crrpage="{page}">
        '''

        if total == 0:
            page_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                page_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                page_html += f'''
                        <li class="left_page" onclick="fatch_data_list({page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    page_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    page_html += f'''
                    <li onclick="fatch_data_list({crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                page_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                page_html += f'''
                        <li class="right_page" onclick="fatch_data_list({page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''

        html = update_language(self.language, html)
        page_html = update_language(self.language, page_html)

        __context['html'] = html
        __context['page_html'] = page_html
        return self.xtjson.json_result(data=__context)


    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound(404)
        action = request.args.get('action')
        site_code = request.args.get('site_code')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_siteAccess':
            return self.siteAccess_list_html()
        
        if action == 'siteAccess':
            self.context['tabName'] = 'siteAccess'
        
        elif action == 'siteAccessCode':
            if not site_code:
                return self.xtjson.json_params_error()
            self.context['tabName'] = 'siteAccessCode'
            self.context['site_code'] = site_code
        elif action == 'siteColor':
            if not site_code:
                return self.xtjson.json_params_error()
            self.context['tabName'] = 'siteColor'
            self.context['site_code'] = site_code
        elif action == 'siteSetting':
            if not site_code:
                return self.xtjson.json_params_error()
            self.context['tabName'] = 'siteSetting'
            self.context['site_code'] = site_code
            lang_html = ''
            for lag in LANGUAGE.name_arr:
                lang_html += f'''
                <option value="{lag}">{LANGUAGE.name_dict.get(lag)}</option>            
                '''
            self.context['lang_html'] = lang_html
        else:
            return self.xtjson.json_params_error()
        html = await self.get_siteList_html()
        return self.xtjson.json_result(data={'html': html})

    async def post_other_way(self, request):
        if self.action == 'edit_site_html':
            html = site_form_html(self.language, self.data_uuid, self.MAIN_DOMAIN)
            return self.xtjson.json_result(message=html)
        if self.action == 'add_site_html':
            html = site_form_html(self.language, '', self.MAIN_DOMAIN)
            return self.xtjson.json_result(message=html)
        if self.action == 'postSiteColor':
            return self.updateSiteColor()
        if self.action == 'uploadSiteBack':
            if not self.data_uuid:
                return self.xtjson.json_params_error()
            fileobj = request.files['upload']
            

            fname, fext = os.path.splitext(request.files["upload"][0].name)
            relatively_path = f'/assets/upload/{self.data_uuid}/sitefile/images/'
            import_folder = self.project_static_folder + relatively_path
            if not os.path.exists(import_folder):
                os.makedirs(import_folder)

            new_filename = shortuuid.uuid()
            async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                await f.write(request.files["upload"][0].body)

            filePath = relatively_path + new_filename + fext
            
            return self.xtjson.json_result(message=filePath)
        if self.action == 'uploadSiteIcon':
            if not self.data_uuid:
                return self.xtjson.json_params_error()
            fileobj = request.files['upload']
            

            fname, fext = os.path.splitext(request.files["upload"][0].name)
            relatively_path = f'/assets/upload/{self.data_uuid}/sitefile/images/'
            import_folder = self.project_static_folder + relatively_path
            if not os.path.exists(import_folder):
                os.makedirs(import_folder)

            new_filename = shortuuid.uuid()
            async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                await f.write(request.files["upload"][0].body)

            filePath = relatively_path + new_filename + fext
            
            return self.xtjson.json_result(message=filePath)
        if self.action == 'edit_siteSetting':
            return self.edit_siteSetting_func()
        if self.action == 'delSiteInfo':
            _log = {
                'user_id': self.current_admin_dict.get('uuid'),
                'note': '删除网站！',
                'ip': get_ip() or '',
            }
            systemLogTable.insert_one(_log)
            site_data = SiteTable.find_one({'uuid': self.data_uuid})
            if site_data:
                site_code = site_data.get('site_code')
                del_site_data(site_code)
                SiteTable.delete_one({'uuid': site_data.get('uuid')})
            SiteTable.update_site_config()
            return self.xtjson.json_result()
        if self.action == 'edit_site_info':
            link = self.request_data.get('link')
            site_name = self.request_data.get('site_name')
            use_domain = self.request_data.get('use_domain')
            site_language = self.request_data.get('site_language')
            finish_time = self.request_data.get('finish_time')
            create_cust_service_count = self.request_data.get('create_cust_service_count')
            if not link or not site_name or not finish_time or not create_cust_service_count:
                return self.xtjson.json_params_error('缺少参数！')

            crr_data = SiteTable.find_one({'uuid': self.data_uuid}) or {}
            if not crr_data:
                return self.xtjson.json_params_error('数据不存在！')

            crr_u_role = self.current_admin_dict.get('role_code')
            if crr_u_role == PermissionCls.AgentAdmin:
                _ccc = 0
                for d in CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid'), 'role_code': PermissionCls.Administrator}):
                    _sddata = SiteTable.find_one({'uuid': d.get('responsible_site')}) or {}
                    if _sddata and _sddata.get('uuid') != self.data_uuid:
                        _c_create_cust_service_count = _sddata.get('create_cust_service_count') or 0
                        _ccc += _c_create_cust_service_count

                _low_create_cust_service_count = int(self.current_admin_dict.get('create_cust_service_count') or 0)
                if int(create_cust_service_count) > _low_create_cust_service_count - _ccc:
                    return self.xtjson.json_params_error('当前分配客服余量不足！')
            if crr_u_role == PermissionCls.SUPERADMIN:
                _sdd = CmsUserModel.find_one({'responsible_site': crr_data.get('site_code'), 'role_code': PermissionCls.Administrator}) or {}
                if _sdd:
                    super_admin_data = CmsUserModel.find_one({'uuid': _sdd.get('super_admin_id')}) or {}
                    if super_admin_data and super_admin_data.get('role_code') == PermissionCls.AgentAdmin:
                        _ccc = 0
                        for d in CmsUserModel.find_many({'super_admin_id': super_admin_data.get('uuid'),'role_code': PermissionCls.Administrator}):
                            _sddata = SiteTable.find_one({'uuid': d.get('responsible_site')}) or {}
                            if _sddata and _sddata.get('uuid') != self.data_uuid:
                                _c_create_cust_service_count = _sddata.get('create_cust_service_count') or 0
                                _ccc += _c_create_cust_service_count

                        _low_create_cust_service_count = int(super_admin_data.get('create_cust_service_count') or 0)
                        if int(create_cust_service_count) > _low_create_cust_service_count - _ccc:
                            return self.xtjson.json_params_error('当前分配客服余量不足！')

            self.data_from['link'] = link
            self.data_from['site_name'] = site_name
            self.data_from['use_domain'] = use_domain or self.MAIN_DOMAIN
            self.data_from['site_language'] = site_language or LANGUAGE.zh_CN
            self.data_from['create_cust_service_count'] = int(create_cust_service_count or 0)
            self.data_from['finish_time'] = datetime.datetime.strptime(finish_time, '%Y-%m-%d')
            crr_data.update(self.data_from)
            SiteTable.save(crr_data)
            while SITE_DICT_CACHE:
                for k in list(SITE_DICT_CACHE):
                    SITE_DICT_CACHE.pop(k)
            _sds = SiteTable.find_many({}) or []
            for sd in _sds:
                SITE_DICT_CACHE[sd.get('site_code')] = sd
            return self.xtjson.json_result()

# 黑名单
class BlacklistView(CmsFormViewBase):
    add_url_rules = [['/blacklist', 'blackList']]

    # 黑名单Table
    def blacklistTable_html(self):
        request = Request.get_current()
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        fields = BlacklistTable.fields()
        statu, res = self.search_from_func(BlacklistTable, fields)
        if not statu:
            return res
        filter_dict.update(res[0])
        context_res.update(res[1])

        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
            site_dis = []
            for _cd in _cdas:
                site_dis.append(_cd.get('responsible_site'))
            filter_dict['site_code'] = {'$in': site_dis}
        if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
            filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')

        total = BlacklistTable.count(filter_dict)
        all_datas = BlacklistTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)

        table_html = ''
        for _dd in all_datas:
            _cdata = CustomerTable.find_one({'uuid': _dd.get('customer_id')}) or {}
            _udata = CmsUserModel.find_one({'uuid': _dd.get('operation_uuid')}) or {}
            table_html += f'''
                <tr>
                    <td>{ _cdata.get('name') or '' }</td>
                    <td>{ _dd.get('ip') or '' }</td>
                    <td>{ self.format_time_func(_dd.get('_create_time') or '', '%Y-%m-%d') }</td>
                    <td>{self.format_time_func(_dd.get('expire_time') or '', '%Y-%m-%d') }</td>
                    <td>{ _udata.get('nickname') or '' }</td>
                    <td>{ _dd.get('note') or '' }</td>
                    <td>
                        <i class="iconfont icon-delete" onclick="rescind_blacklist_func('rescind_blacklist','{ _dd.get('uuid') }','确认删除该用户黑名单？')"></i>
                    </td>
                </tr>
            '''
        dataTableBottom_html = f'''
        <span>总信息条数：{total}</span>
        <ul class="pages" data-crrpage="{page}">
        '''
        if total == 0:
            dataTableBottom_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                dataTableBottom_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                dataTableBottom_html += f'''
                        <li class="left_page" onclick="request_data({page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    dataTableBottom_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    dataTableBottom_html += f'''
                    <li onclick="request_data({crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                dataTableBottom_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                dataTableBottom_html += f'''
                        <li class="right_page" onclick="request_data({page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
        return table_html, dataTableBottom_html, context_res

    # 黑名单页面HTML
    async def blacklist_html(self):
        table_html, dataTableBottom_html, context_res = self.blacklistTable_html()
        self.context['table_html'] = table_html
        self.context['context_res'] = context_res
        self.context['dataTableBottom_html'] = dataTableBottom_html
        html = await render_template('easychat/blacklist.html', self.context)
        return html

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.blacklist_html()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_blacklist_html':
            table_html, dataTableBottom_html, context_res = self.blacklistTable_html()
            table_html = update_language(self.language, table_html)
            dataTableBottom_html = update_language(self.language, dataTableBottom_html)
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html})
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'rescind_blacklist':
            if not self.data_uuid:
                return self.xtjson.json_params_error()

            BlacklistTable.delete_one({'uuid':self.data_uuid})
            return self.xtjson.json_result()
    

# 问题
class problemListView(CmsFormViewBase):
    add_url_rules = [['/problemList', 'problemList']]
    
    # 获取问题HTML
    async def get_problemList_html(self):
        html = await render_template('easychat/setting/problemList.html', {})
        return html

    # 获取表格数据
    def problem_list_html(self):
        request = Request.get_current()
        __context = {}
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 30
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        
        if self.current_admin_dict.get('role_code') in [PermissionCls.CustomerService, PermissionCls.Administrator]:
            _site_code = self.current_admin_dict.get('responsible_site')
            filter_dict['site_code'] = _site_code
        elif self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            udatas = CmsUserModel.find_many({'role_code': PermissionCls.Administrator, 'super_admin_id': self.current_admin_dict.get('uuid')})
            site_codes = []
            for ud in udatas:
                site_codes.append(ud.get('responsible_site'))
            filter_dict['site_code'] = {'$in': site_codes}
        elif self.is_superdamin:
            pass
        else:
            return self.xtjson.json_params_error()
        
        total = problemTable.count(filter_dict)
        all_datas = problemTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
        __context['page'] = page
        __context['pages'] = pages
        __context['total_page'] = total_page
        __context['total'] = total
        __context['context_res'] = context_res
        html = ''
        if all_datas:
            for data in all_datas:
                html += f'''
                    <tr>
                        <td>{data.get('title') or ''}</td>
                        <td>{data.get('answer') or ''}</td>
                        <td>{data.get('create_time').strftime('%Y-%m-%d %H:%M:%S')}</td>
                        <td>
                            <i class="iconfont icon-wenbenshuru mr-2" onclick="post_from_html('edit_problem_html', '{data.get('uuid')}', '修改', '', '/site_admin/problemList')"></i>
                            <i class="iconfont icon-delete" onclick="del_problem_func('{data.get('uuid')}')"></i>
                        </td>
                    </tr>              
                '''
        else:
            html += '''
                <div style="width: 100%; height: 100%; position: relative; overflow: hidden; box-sizing: border-box; display: flex; justify-content: center; align-items: center; flex-direction:column; margin-top: 3%;">
                    <img src="/assets/pic/not_data.png" alt="" style="width: 130px; position: relative; display: block;">
                    <p style="color: #666;">暂无数据</p>
                </div>
            '''
        page_html = f'''
                <span>总信息条数：{total}</span>
                <ul class="pages" data-crrpage="{page}">
        '''

        if total == 0:
            page_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                page_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                page_html += f'''
                        <li class="left_page" onclick="fatch_data_list({page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    page_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    page_html += f'''
                    <li onclick="fatch_data_list({crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                page_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                page_html += f'''
                        <li class="right_page" onclick="fatch_data_list({page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''

        html = update_language(self.language, html)
        page_html = update_language(self.language, page_html)

        __context['html'] = html
        __context['page_html'] = page_html
        return self.xtjson.json_result(data=__context)

    # 添加问题
    def problem_html(self):
        problem_data = {}
        if self.data_uuid:
            problem_data = problemTable.find_one({'uuid': self.data_uuid}) or {}
            
        site_option_html = ''
        if self.is_superdamin or self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            site_datas = SiteTable.find_many({})
            for data in site_datas:
                if problem_data:
                    site_option_html += f'''
                    <option value="{data.get('site_code')}" { 'selected' if data.get('site_code') == problem_data.get('site_code')  else '' }>{ data.get('site_name') or '' }</option>
                    '''
                else:
                    site_option_html += f'''
                    <option value="{data.get('site_code')}">{ data.get('site_name') or '' }</option>
                    '''

        site_html = ''
        if site_option_html:
            site_html = f'''
            <div class="list-group-item">           
                <span style="width: 80px; text-align: right; display: inline-block; position: relative;">选择网站：</span>             
                <select class="form-control" name="" aria-label="" id="site_code" style="display: inline-block; width: calc(100% - 100px)">
                    <option value="" >选择网站</option>
                    { site_option_html or '' }
                </select>            
            </div>                
            '''
            
        html = f'''
        <div class="addQuickReplyBox">

            <div style="height: 20rem; position: relative; box-sizing: border-box; overflow-y: auto;">
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">标题：</span>
                    <input type="text" class="form-control" id="pr_title" placeholder="标题" value="{problem_data.get('title') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 100px)">
                </div>
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">答案：</span>
                    <textarea class="form-control" id="pr_content" rows="5" style="display: inline-block; width: calc(100% - 100px)">{problem_data.get('answer') or ''}</textarea>
                </div>
                { site_html }
            </div>
            <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>
            <div style="position: relative; text-align: center">
        '''
        if self.data_uuid:
            html += f'''
                <span class="kfConfirmBtn" onclick="post_problem_data('edit_problem_data', '{self.data_uuid}')">确定</span>
            '''
        else:
            html += '''
                <span class="kfConfirmBtn" onclick="post_problem_data('add_problem_data')">确定</span>            
            '''
        html += '''
                <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
            </div>

        </div>        
        '''
        html = update_language(self.language, html)
        return self.xtjson.json_result(message=html)

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_problemList_html()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        if action == 'problem_list_html':
            return self.problem_list_html()
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'add_problem_html':
            return self.problem_html()
        if self.action == 'edit_problem_html':
            return self.problem_html()
        if self.action == 'edit_problem_data':
            pr_title = self.request_data.get('pr_title')
            pr_content = self.request_data.get('pr_content')
            site_code = self.request_data.get('site_code')
            if not pr_title or not pr_content or not site_code:
                return self.xtjson.json_params_error('添加失败，缺少数据！')

            if not self.data_uuid:
                return self.xtjson.json_params_error()

            _update_data = {
                'title': pr_title.strip(),
                'answer': pr_content.strip(),
                'site_code': site_code.strip(),
            }

            _site_code = ''
            if self.current_admin_dict.get('role_code') in [PermissionCls.CustomerService, PermissionCls.Administrator]:
                _site_code = self.current_admin_dict.get('responsible_site')
            elif self.is_superdamin or self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                if not site_code:
                    return self.xtjson.json_params_error()
                _site_code = site_code
            else:
                return self.xtjson.json_params_error()

            _update_data['site_code'] = _site_code
            problemTable.update_one({'uuid': self.data_uuid}, {'$set': _update_data})
            return self.xtjson.json_result()
        if self.action == 'del_problem':
            if not self.data_uuid:
                return self.xtjson.json_params_error()

            problemTable.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()
        if self.action == 'add_problem_data':
            pr_title = self.request_data.get('pr_title')
            pr_content = self.request_data.get('pr_content')
            site_code = self.request_data.get('site_code')
            if not pr_title or not pr_content:
                return self.xtjson.json_params_error('添加失败，缺少数据！')
            if problemTable.find_one({'title': pr_title}):
                return self.xtjson.json_params_error('添加失败，当前标题已存在！')
            _data = {
                'title': pr_title.strip(),
                'answer': pr_content.strip(),
            }

            _site_code = ''
            if self.current_admin_dict.get('role_code') in [PermissionCls.CustomerService, PermissionCls.Administrator]:
                _site_code = self.current_admin_dict.get('responsible_site')
            elif self.is_superdamin or self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                if not site_code:
                    return self.xtjson.json_params_error()
                _site_code = site_code
            else:
                return self.xtjson.json_params_error()
            _data['site_code'] = _site_code

            problemTable.insert_one(_data)
            return self.xtjson.json_result()


        
class categoryCustomersView(CmsFormViewBase):
    add_url_rules = [['/categoryCustomers', 'categoryCustomers']]

    async def get_categoryCustomers_html(self):
        html = await render_template('easychat/setting/customercategories.html')
        return html

    def category_customers_html(self):
        request = Request.get_current()
        __context = {}
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1

        per_page = 10
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}

        if self.current_admin_dict.get('role_code') in [PermissionCls.CustomerService, PermissionCls.Administrator]:
            _site_code = self.current_admin_dict.get('responsible_site')
            filter_dict['site_code'] = _site_code
        elif self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            udatas = CmsUserModel.find_many({'role_code': PermissionCls.Administrator, 'super_admin_id': self.current_admin_dict.get('uuid')})
            site_codes = []
            for ud in udatas:
                site_codes.append(ud.get('responsible_site'))
            filter_dict['site_code'] = {'$in': site_codes}
        elif self.is_superdamin:
            pass
        else:
            return self.xtjson.json_params_error()
        
        total = categoryTable.count(filter_dict)
        all_datas = categoryTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
        __context['page'] = page
        __context['pages'] = pages
        __context['total_page'] = total_page
        __context['total'] = total
        __context['context_res'] = context_res
        html = ''
        if all_datas:
            for data in all_datas:
                html += f'''
                            <tr>
                                <td>{data.get('category') or ''}</td>
                                <td>{data.get('create_time').strftime('%Y-%m-%d %H:%M:%S')}</td>
                                <td>
                                    <i class="iconfont icon-wenbenshuru mr-2" onclick="post_from_html('edit_category_customers_html', '{data.get('uuid')}', '修改', '', '/site_admin/categoryCustomers')"></i>
                                    <i class="iconfont icon-delete" onclick="del_category_func('{data.get('uuid')}')"></i>
                                </td>
                            </tr>              
                '''
        else:
            html += '''
                <div style="width: 100%; height: 100%; position: relative; overflow: hidden; box-sizing: border-box; display: flex; justify-content: center; align-items: center; flex-direction:column; margin-top: 3%;">
                    <img src="/assets/pic/not_data.png" alt="" style="width: 130px; position: relative; display: block;">
                    <p style="color: #666;">暂无数据</p>
                </div>
            '''
        page_html = f'''
                <span>总信息条数：{total}</span>
                <ul class="pages" data-crrpage="{page}">
        '''
        if total == 0:
            page_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                page_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                page_html += f'''
                        <li class="left_page" onclick="fatch_data_list({page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    page_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    page_html += f'''
                    <li onclick="fatch_data_list({crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                page_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                page_html += f'''
                        <li class="right_page" onclick="fatch_data_list({page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
        html = update_language(self.language, html)
        page_html = update_language(self.language, page_html)
        __context['html'] = html
        __context['page_html'] = page_html
        return self.xtjson.json_result(data=__context)

    # 添加分类
    def add_category_customers_html(self):
        problem_data = {}
        if self.data_uuid:
            problem_data = categoryTable.find_one({'uuid': self.data_uuid}) or {}
        
        site_option_html = ''
        if self.is_superdamin or self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            site_datas = SiteTable.find_many({})
            for data in site_datas:
                if problem_data:
                    site_option_html += f'''
                    <option value="{data.get('site_code')}" { 'selected' if data.get('site_code') == problem_data.get('site_code')  else '' }>{ data.get('site_name') or '' }</option>
                    '''
                else:
                    site_option_html += f'''
                    <option value="{data.get('site_code')}">{ data.get('site_name') or '' }</option>
                    '''
        site_html = ''
        if site_option_html:
            site_html = f'''
            <div class="list-group-item">           
                <span style="width: 80px; text-align: right; display: inline-block; position: relative;">选择网站：</span>             
                <select class="form-control" name="" aria-label="" id="site_code" style="display: inline-block; width: calc(100% - 100px)">
                    <option value="" >选择网站</option>
                    { site_option_html or '' }
                </select>            
            </div>                
            '''

        html = f'''
        <div class="addQuickReplyBox">
            <div style="height: 20rem; position: relative; box-sizing: border-box; overflow-y: auto;">
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">Category：</span>
                    <input type="text" class="form-control" id="category_title" placeholder="Category" value="{problem_data.get('category') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 100px)">
                </div>
                { site_html }
            </div>
            <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>
            <div style="position: relative; text-align: center">
        '''
        if self.data_uuid:
            html += f'''
                <span class="kfConfirmBtn" onclick="post_category_data('edit_category_data', '{self.data_uuid}')">确定</span>
            '''
        else:
            html += '''
                <span class="kfConfirmBtn" onclick="post_category_data('add_category_data')">确定</span>            
            '''
        html += '''
                <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
            </div>

        </div>        
        '''
        html = update_language(self.language, html)
        return self.xtjson.json_result(message=html)

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_categoryCustomers_html()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        if action == 'category_customers_html':
            return self.category_customers_html()
        return self.xtjson.json_params_error()

    def post_other_way(self, request):   
        if self.action == 'add_category_customers_html':
            return self.add_category_customers_html()
        if self.action == 'del_category':
            if not self.data_uuid:
                return self.xtjson.json_params_error()

            categoryTable.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()
        if self.action == 'add_category_data':
            category_title = self.request_data.get('category_title')
            site_code = self.request_data.get('site_code')
            if not category_title:
                return self.xtjson.json_params_error('添加失败，缺少数据！')
            if categoryTable.find_one({'category': category_title}):
                return self.xtjson.json_params_error('添加失败，当前标题已存在！')
            _data = {
                'category': category_title.strip(),
            }
            _site_code = ''
            if self.current_admin_dict.get('role_code') in [PermissionCls.CustomerService, PermissionCls.Administrator]:
                _site_code = self.current_admin_dict.get('responsible_site')
            elif self.is_superdamin or self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                if not site_code:
                    return self.xtjson.json_params_error()
                _site_code = site_code
            else:
                return self.xtjson.json_params_error()
            _data['site_code'] = _site_code
            categoryTable.insert_one(_data)
            return self.xtjson.json_result()
        if self.action == 'edit_category_customers_html':
            return self.add_category_customers_html()
        if self.action == 'edit_category_data':
            category_title = self.request_data.get('category_title')
            site_code = self.request_data.get('site_code')

            if not category_title:
                return self.xtjson.json_params_error('添加失败，缺少数据！')

            if not self.data_uuid:
                return self.xtjson.json_params_error()
            _update_data = {
                'category': category_title.strip(),
            }
            _site_code = ''
            if self.current_admin_dict.get('role_code') in [PermissionCls.CustomerService, PermissionCls.Administrator]:
                _site_code = self.current_admin_dict.get('responsible_site')
            elif self.is_superdamin or self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                if not site_code:
                    return self.xtjson.json_params_error()
                _site_code = site_code
            else:
                return self.xtjson.json_params_error()
            _update_data['site_code'] = _site_code
            categoryTable.update_one({'uuid': self.data_uuid}, {'$set': _update_data})
            return self.xtjson.json_result()



# 系统日志
class systemLogView(CmsFormViewBase):
    add_url_rules = [['/systemLog', 'systemLog']]

    async def systemlog_html(self):
        option_html = ''
        for ll in OPERATION_TYPES.name_arr:
            option_html += f'''
            <option value="{ ll }">{ OPERATION_TYPES.name_dict.get(ll) }</option>            
            '''
        operation_type_select = '''
            <select class="form-control mb-2 mr-sm-2" name="operation_type">
                <option value="">选择操作类型</option>
                %s                                        
            </select>        
        ''' % option_html
        self.context['operation_type_select'] = operation_type_select
        html = await render_template('easychat/systemLog.html', self.context)
        return html

    def sysytemLogTable_html(self):
        request = Request.get_current()
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        fields = systemLogTable.fields()
        statu, res = self.search_from_func(systemLogTable, fields)
        if not statu:
            return res
        filter_dict.update(res[0])
        context_res.update(res[1])

        account = request.args.get('account')
        if account and account.strip():
            _ud = CmsUserModel.find_one({'account': account.strip()}) or {}
            if _ud:
                filter_dict['user_id'] = _ud.get('uuid')

        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
            site_dis = []
            for _cd in _cdas:
                site_dis.append({'site_code': _cd.get('responsible_site')})
            site_dis.append({'user_id': self.current_admin_dict.get('uuid')})
            filter_dict['$or'] = site_dis
        if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
            filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')

        total = systemLogTable.count(filter_dict)
        all_datas = systemLogTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
        table_html = ''
        for _dd in all_datas:
            _site_data = SITE_DICT_CACHE.get(_dd.get('site_code')) or {}
            _udata = CmsUserModel.find_one({'uuid': _dd.get('user_id')}) or {}
            table_html += f'''
                <tr>
                    <td>{self.format_time_func(_dd.get('create_time') or '', '%Y-%m-%d %H:%M:%S')}</td>
                    <td>{_site_data.get('site_name') or ''}</td>
                    <td>{_udata.get('account') or ''}</td>
                    <td>{ OPERATION_TYPES.name_dict.get(_dd.get('operation_type') or '') or '' }</td>
                    <td>{_dd.get('ip') or ''}</td>
                    <td>{_dd.get('note') or ''}</td>
                </tr>
            '''
        dataTableBottom_html = f'''
        <span>总信息条数：{total}</span>
        <ul class="pages" data-crrpage="{page}">
        '''
        if total == 0:
            dataTableBottom_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                dataTableBottom_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                dataTableBottom_html += f'''
                        <li class="left_page" onclick="request_data({page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    dataTableBottom_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    dataTableBottom_html += f'''
                    <li onclick="request_data({crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                dataTableBottom_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                dataTableBottom_html += f'''
                        <li class="right_page" onclick="request_data({page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                    </ul>                    
                '''
        return table_html, dataTableBottom_html, context_res

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.systemlog_html()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_systemlog_datas':
            table_html, dataTableBottom_html, context_res = self.sysytemLogTable_html()
            table_html = update_language(self.language, table_html)
            dataTableBottom_html = update_language(self.language, dataTableBottom_html)
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html})
        return self.xtjson.json_params_error()



# 其它设置
class OtherSetupView(CmsFormViewBase):
    add_url_rules = [['/otherSetup', 'otherSetup']]

    # 获取HTML
    async def otherSetupHtml(self):
        html = await render_template('easychat/setting/otherSetup.html', {})
        return html

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.otherSetupHtml()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'getOtherConfig':
            _conf = SiteConfigModel.find_one({}) or {}
            _data = {}
            if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
                _data['cms_ip_whitelist'] = _conf.get('cms_ip_whitelist') or ''
                _data['google_verify_statu'] = _conf.get('google_verify_statu') or '0'
            return self.xtjson.json_result(data=_data)
        if self.action == 'saveOtherSetupData':
            cms_ip_whitelist = self.request_data.get('cms_ip_whitelist')
            google_verify_statu = self.request_data.get('google_verify_statu')
            if not cms_ip_whitelist or not cms_ip_whitelist.strip():
                cms_ip_whitelist = ''

            _google_verify_statu = False
            if google_verify_statu == '1':
                _google_verify_statu = True
            if google_verify_statu == '0':
                _google_verify_statu = False

            cms_ip_whitelist = cms_ip_whitelist.strip()
            new_daat_form = {}
            if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
                new_daat_form['cms_ip_whitelist'] = cms_ip_whitelist
                new_daat_form['google_verify_statu'] = _google_verify_statu
            if new_daat_form:
                _conf = SiteConfigModel.find_one({}) or {}
                _conf.update(new_daat_form)
                SiteConfigModel.save(_conf)
                SiteConfigModel.update_site_config()
            return self.xtjson.json_result()



# 快捷语句
class quickReplyView(CmsFormViewBase):
    add_url_rules = [['/quickReply', 'quickReply']]

    def quickReply_list_html(self):
        request = Request.get_current()
        __context = {}
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        filter_dict['service_id'] = self.current_admin_dict.get('uuid')
        total = QuickReplyTable.count(filter_dict)
        print('filter_dict:', filter_dict)
        print('total:', total)
        print('total 11:', QuickReplyTable.count({}))
        all_datas = QuickReplyTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
        __context['page'] = page
        __context['pages'] = pages
        __context['total_page'] = total_page
        __context['total'] = total
        __context['context_res'] = context_res
        html = ''
        if all_datas:
            for data in all_datas:
                html += f'''
                            <tr>
                                <td>{data.get('title') or ''}</td>
                                <td>{data.get('text') or ''}</td>
                                <td>{data.get('_create_time').strftime('%Y-%m-%d %H:%M:%S')}</td>
                                <td>
                                    <i class="iconfont icon-wenbenshuru mr-2" onclick="post_from_html('edit_QuickReply_html', '{data.get('uuid')}', '修改','', '/site_admin/quickReply')"></i>
                                    <i class="iconfont icon-delete" onclick="del_QuickReply_func('{data.get('uuid')}')"></i>
                                </td>
                            </tr>              
                '''
        page_html = f'''
                <span>总信息条数：{total}</span>
                <ul class="pages" data-crrpage="{page}">
        '''

        if total == 0:
            page_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                page_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                page_html += f'''
                        <li class="left_page" onclick="fatch_data_list('quickReply_list_html', {page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    page_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    page_html += f'''
                    <li onclick="fatch_data_list('quickReply_list_html', {crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                page_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                page_html += f'''
                        <li class="right_page" onclick="fatch_data_list('quickReply_list_html', {page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''

        html = update_language(self.language, html)
        page_html = update_language(self.language, page_html)

        __context['html'] = html
        __context['page_html'] = page_html
        return self.xtjson.json_result(data=__context)

    async def get_quickReply_html(self):
        html = await render_template('easychat/setting/quickReply.html')
        return html

    def add_QuickReply_html(self):
        html = '''
        <div class="addQuickReplyBox">
            <div style="height: 20rem; position: relative; box-sizing: border-box; overflow-y: auto;">

                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">标题：</span>
                    <input type="text" class="form-control" id="qr_title" placeholder="标题" aria-label="" style="display: inline-block; width: calc(100% - 100px)">
                </div>
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">内容：</span>
                    <textarea class="form-control" id="qr_content" rows="5" style="display: inline-block; width: calc(100% - 100px)"></textarea>                    
                </div>
            </div>
            <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>
            <div style="position: relative; text-align: center">
                <span class="kfConfirmBtn" onclick="post_QuickReply_data('add_QuickReply_data')">确定</span>
                <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
            </div>

        </div>        
        '''

        html = update_language(self.language, html)

        return self.xtjson.json_result(message=html)

    def edit_QuickReply_html(self):
        if not self.data_uuid:
            return self.xtjson.json_params_error('缺少数据id!')
        QuickReply_data = QuickReplyTable.find_one({'uuid': self.data_uuid}) or {}
        html = f'''
        <div class="addQuickReplyBox">
            <div style="height: 20rem; position: relative; box-sizing: border-box; overflow-y: auto;">

                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">标题：</span>
                    <input type="text" class="form-control" id="qr_title" placeholder="标题" value="{QuickReply_data.get('title') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 100px)">
                </div>
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">内容：</span>
                    <textarea class="form-control" id="qr_content" rows="5" style="display: inline-block; width: calc(100% - 100px)">{QuickReply_data.get('text') or ''}</textarea>
                </div>
            </div>
            <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>
            <div style="position: relative; text-align: center">
                <span class="kfConfirmBtn" onclick="post_QuickReply_data('edit_QuickReply_data', '{self.data_uuid}')">确定</span>
                <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
            </div>
        </div>        
        '''

        html = update_language(self.language, html)

        return self.xtjson.json_result(message=html)

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_quickReply_html()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_quickReply_datas':
            return self.quickReply_list_html()
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'add_QuickReply_html':
            return self.add_QuickReply_html()
        if self.action == 'add_QuickReply_data':
            qr_title = self.request_data.get('qr_title')
            qr_content = self.request_data.get('qr_content')
            if not qr_title or not qr_content:
                return self.xtjson.json_params_error('添加失败，缺少数据！')
            if QuickReplyTable.find_one({'title': qr_title, 'service_id': self.current_admin_dict.get('uuid')}):
                return self.xtjson.json_params_error('添加失败，当前标题已存在！')
            _data = {
                'title': qr_title.strip(),
                'text': qr_content.strip(),
                'service_id': self.current_admin_dict.get('uuid'),
            }
            QuickReplyTable.insert_one(_data)
            return self.xtjson.json_result()
        if self.action == 'edit_QuickReply_html':
            return self.edit_QuickReply_html()
        if self.action == 'edit_QuickReply_data':
            qr_title = self.request_data.get('qr_title')
            qr_content = self.request_data.get('qr_content')
            if not qr_title or not qr_content:
                return self.xtjson.json_params_error('添加失败，缺少数据！')
            _d = QuickReplyTable.find_one({'title': qr_title})
            if _d and _d.get('uuid') != self.data_uuid:
               return self.xtjson.json_params_error('添加失败，当前标题已存在！')
            _d = QuickReplyTable.find_one({'uuid': self.data_uuid}) or {}
            _data = {
                'title': qr_title.strip(),
                'text': qr_content.strip(),
            }
            _d.update(_data)
            req = QuickReplyTable.save(_d)
            return self.xtjson.json_result()
        if self.action == 'empty_QuickReply':
            QuickReplyTable.delete_many({})
            return self.xtjson.json_result()
        if self.action == 'del_QuickReply':
            if not self.data_uuid:
                return self.xtjson.json_params_error('缺少数据id！')
            QuickReplyTable.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()



# 网站域名
class SiteDomainManageView(CmsFormViewBase):
    add_url_rules = [['/siteDomainManage', 'siteDomainManage']]

    # 获取HTML
    async def otherSetupHtml(self):
        html = await render_template('easychat/setting/siteDomainManage.html')
        return html

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.otherSetupHtml()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'getSiteDomainData':
            if hasattr(SITE_CONFIG_CACHE, 'site_domain'):
                site_domain = SITE_CONFIG_CACHE.site_domain or ''
            else:
                site_domain = ''
            return self.xtjson.json_result(data={'site_domain': site_domain})
        if self.action == 'siteState':
            return self.xtjson.json_result()
        if self.action == 'edit_site_domain':
            if self.current_admin_dict.get('role_code') != PermissionCls.SUPERADMIN:
                return self.xtjson.json_unauth_error()
            site_domian_text = self.request_data.get('site_domain')
            if site_domian_text is None:
                return self.xtjson.json_params_error()
            domain_ls = []
            site_config = SiteConfigModel.find_one({}) or {}
            if not site_domian_text:
                site_config['site_domain'] = ''
            else:
                for doamin in site_domian_text.split('\n'):
                    doamin = doamin.strip()
                    if not doamin:
                        continue
                    if doamin.count('.') > 2 or 'http' in doamin:
                        return self.xtjson.json_params_error(f'域名：{doamin}，格式错误！')
                    if not doamin.replace('.', '').isalnum():
                        return self.xtjson.json_params_error(f'域名："{doamin}"，格式错误！')
                    domain_ls.append(doamin)
                site_config['site_domain'] = site_domian_text
            SiteConfigModel.save(site_config)
            SiteConfigModel.update_site_config()

            if self.MAIN_DOMAIN not in domain_ls:
                domain_ls.append(self.MAIN_DOMAIN)
            if not ''.startswith('www'):
                dd = 'www.' + self.MAIN_DOMAIN
                if dd not in domain_ls:
                    domain_ls.append(dd)
            PROJECT_ROOT_PATH = Sanic.get_app().config.get('PROJECT_ROOT_PATH')
            domain_text = '''
    server {
        listen 80;
        server_name {#domain#};
        root %s;

        location / {
            include proxy_params;
            proxy_pass http://127.0.0.1:5021;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            client_max_body_size 600M;
            client_body_buffer_size 600M;
        }

        location /static {
            alias %s/static;
            expires 7d;
        }

        location /socket.io {
            include proxy_params;
            proxy_http_version 1.1;
            proxy_buffering off;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_pass http://127.0.0.1:5021/socket.io;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            client_max_body_size 300M;
            client_body_buffer_size 300M;
        }
    }            
                ''' % (PROJECT_ROOT_PATH, PROJECT_ROOT_PATH)
            domain_text = domain_text.replace('{#domain#}', ' '.join(domain_ls))
            conf_path = PROJECT_ROOT_PATH + f'/{self.project_name}/{self.project_name}.conf'

            cmd = 'nginx -s reload'
            os.popen(cmd)

            return self.xtjson.json_result()



# 导出文件
class downloadFileListView(CmsFormViewBase):
    add_url_rules = [['/downloadFileList', 'downloadFileList']]

    def get_exportList_datas(self):
        request = Request.get_current()
        __context = {}
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}

        fields = ExportDataModel.fields()
        statu, res = self.search_from_func(ExportDataModel, fields)
        if not statu:
            return res
        filter_dict.update(res[0])

        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
            site_dis = []
            for _cd in _cdas:
                site_dis.append(_cd.get('responsible_site'))
            filter_dict['$or'] = [{'site_code': {'$in': site_dis}, 'operator_id': _cdas.get('uuid')}]
        if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
            filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')

        total = ExportDataModel.count(filter_dict)
        all_datas = ExportDataModel.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
        __context['page'] = page
        __context['pages'] = pages
        __context['total_page'] = total_page
        __context['total'] = total
        __context['context_res'] = context_res
        html = ''
        if all_datas:
            for data in all_datas:
                ant_tag_html = ''
                if data.get('statu') == 'successed':
                    ant_tag_html += '<span class="ant-tag ant-tag-green">成功</span>'
                elif data.get('statu') == 'failed':
                    ant_tag_html += '<span class="ant-tag ant-tag-red">失败</span>'
                else:
                    ant_tag_html += '<span class="ant-tag ant-tag-yellow">导出中</span>'

                html += f'''
                    <tr>
                        <td>{ data.get('filename') or '' }</td>
                        <td>{ data.get('path') or '' }</td>
                        <td>{ data.get('file_size') or '' }</td>
                        <td>{ data.get('total') or 0 }</td>
                        <td>{ data.get('out_count') or 0 }</td>
                        <td>{ ant_tag_html }</td>
                        <td>{ self.format_time_func(data.get('create_time')) }</td>
                        <td>{ data.get('note') or '' }</td>
                        <td width="100">
                            <a class="btn btn-primary btn-xs" href="{ data.get('path') }"  style="color: #FFFFFF;">下载</a>
                            <span class="btn btn-danger btn-xs" onclick="delExportFile('{ data.get('uuid') }');">删除</span>
                        </td>
                    </tr>              
                '''
        else:
            html += '''
                <div style="width: 100%; height: 100%; position: relative; overflow: hidden; box-sizing: border-box; display: flex; justify-content: center; align-items: center; flex-direction:column; margin-top: 3%;">
                    <img src="/assets/pic/not_data.png" alt="" style="width: 130px; position: relative; display: block;">
                    <p style="color: #666;">暂无数据</p>
                </div>
            '''


        page_html = f'''
                <span>总信息条数：{total}</span>
                <ul class="pages" data-crrpage="{page}">
        '''

        if total == 0:
            page_html += f'''                
                    <li class="left_page forbid">
                        <span class="iconfont icon-fangxiang-zuo"></span>
                    </li>                
                    <li class="right_page forbid">
                        <span class="iconfont icon-fangxiang-you"></span>
                    </li>
                </ul>                            
            '''
        else:
            if page == 1:
                page_html += f'''
                        <li class="left_page forbid">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            else:
                page_html += f'''
                        <li class="left_page" onclick="fatch_data_list('quickReply_list_html', {page - 1});">
                            <span class="iconfont icon-fangxiang-zuo"></span>
                        </li>
                '''
            for crrpage in pages:
                if crrpage == page:
                    page_html += f'''
                    <li class="active"><span>{crrpage}</span></li>
                    '''
                else:
                    page_html += f'''
                    <li onclick="fatch_data_list('quickReply_list_html', {crrpage});"><span>{crrpage}</span></li>
                    '''
            if page == total_page:
                page_html += f'''
                        <li class="right_page forbid">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
            else:
                page_html += f'''
                        <li class="right_page" onclick="fatch_data_list('quickReply_list_html', {page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''

        html = update_language(self.language, html)
        page_html = update_language(self.language, page_html)

        __context['html'] = html
        __context['page_html'] = page_html
        return html, page_html

    async def get_downloadFile_html(self):
        html = await render_template('easychat/setting/exportList.html')
        return html

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_downloadFile_html()
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_exportList_datas':
            table_html, dataTableBottom_html = self.get_exportList_datas()
            table_html = update_language(self.language, table_html)
            dataTableBottom_html = update_language(self.language, dataTableBottom_html)
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html})
        return self.xtjson.json_params_error()

