# -*- coding: utf-8 -*-
import os, shortuuid, datetime, time, random
from sanic import request, Sanic, response
from sanic.response import html, redirect
from sanic_ext import render
from sanic.request import Request

from .cms_base import CmsFormViewBase
from common_utils.utils_funcs import PagingCLS
from constants import PermissionCls, CMS_USER_SESSION_KEY, OnlineStatu, SITE_DICT_CACHE, DEFAULT_FILE_SIZE, duration_dcit, SERVICE_CONNECTION, \
    LANGUAGE, LANGUAGE_HINT_ALL, CLIENT_CONNECTION, ASSETS_FOLDER, EXPORT_FOLDER, OPERATION_TYPES
from models.cms_user import CmsUserModel
from models.site_table import SiteTable, ExportStatu, ExportDataModel
from models.kefu_table import ChatConversationTable, ChatContentTable, LeavingMessageTable, systemLogTable, signLogTable, BlacklistTable, StatisticTable
from common_utils.utils_funcs import update_language
from modules.google_verify import GooleVerifyCls
from modules.view_helpres.view_func import exportDataLy
from common_utils.utils_funcs import render_template



class CmsIndexView(CmsFormViewBase):
    add_url_rules = [['/', 'cms_index']]

    def search_from_func(self, MCLS, FIELDS):
        request = Request.get_current()
        """get数据搜索处理"""
        s_filter_dict, s_context_res = {}, {}
        if hasattr(MCLS, 'field_search'):
            field_search = getattr(MCLS, 'field_search')()
            for db_field in field_search:
                col_value = request.args.get(db_field)
                if col_value is None:
                    continue
                s_context_res[db_field] = col_value
                if col_value and col_value.strip():
                    col_value = col_value.strip()
                    field_cls = FIELDS.get(db_field)
                    if not field_cls:
                        return  False, '%s: 无处理属性!' % db_field
                    if field_cls.field_type == 'UUIDField':
                        s_filter_dict[db_field] = col_value
                    elif field_cls.field_type == 'IDField':
                        s_filter_dict[db_field] = int(col_value)
                    else:
                        statu, res = field_cls.search_validate(col_value)
                        if not statu:
                            return False, res
                        s_filter_dict[db_field] = res
        return True, [s_filter_dict, s_context_res]

    def get_heimingdan_html(self):
        html = '''
        <div class="addQuickReplyBox" style="background: #FFFFFF;padding: 20px;position: relative;width: 100%;">
            <div style="height: 20rem; position: relative; box-sizing: border-box; overflow-y: auto;">

                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;">风控时长：</span>
                    <select name="" id="duration" class="form-control" style="display: inline-block; width: calc(100% - 100px)">
                        <option value="">选择时长</option>
        '''
        for k,v in duration_dcit.items():
            html += f'''
            <option value="{k}">{v}</option>
            '''
        html += f'''
                    </select>
                </div>
            </div>
            <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>
            <div style="position: relative; text-align: center">
                <span class="kfConfirmBtn" onclick="post_heimingdan_data('{self.data_uuid}')">确定</span>
                <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
            </div>

        </div>          
        '''

        html = update_language(self.language, html)

        return self.xtjson.json_result(message=html)

    def parse_time(self, time_str):
        if time_str is None:
            # Handle the case where time_str is None
            return None
        elif isinstance(time_str, datetime):
            # If time_str is already a datetime object
            return time_str
        try:
            return datetime.datetime.fromisoformat(time_str)
        except TypeError:
            # Handle the case where time_str is not a string
            # print(f"Invalid time_str format: {time_str}")
            return None

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    def getJianKong_table(self):
        request = Request.get_current()
        page = int(request.args.get('page'))
        per_page = 10
        skip = (page - 1) * per_page
        table_datas = []
        zx_datas = []
        ml_datas = []
        lx_datas = []
        crr_role_code = self.current_admin_dict.get('role_code')
        filter_dict = {}
        for filed in ['su_account', 'su_data_date', 'su_online_statu']:
            _v = request.args.get(filed)
            if not _v or not _v.strip():
                continue
            _v = _v.strip()
            if filed == 'su_data_date':
                pass
            elif filed == 'su_account':
                filter_dict['account'] = _v
            elif filed == 'su_online_statu':
                if _v == OnlineStatu.offline:
                    pass
                else:
                    filter_dict['online_statu'] = _v

        if crr_role_code  == PermissionCls.AgentAdmin:
            _cds = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid'), 'role_code': PermissionCls.Administrator})
            _sdis = []
            for cd in _cds:
                _sitecode = cd.get('responsible_site')
                if _sitecode not in _sdis:
                    _sdis.append(_sitecode)
            filter_dict['responsible_site'] = {'$in': _sdis}
        if crr_role_code == PermissionCls.SUPERADMIN:
            filter_dict['role_code'] = {'$in': [PermissionCls.AgentAdmin, PermissionCls.Administrator, PermissionCls.CustomerService, PermissionCls.SUPERADMIN]}
        if crr_role_code == PermissionCls.Administrator:
            filter_dict['responsible_site'] = self.current_admin_dict.get('responsible_site')
        if crr_role_code == PermissionCls.CustomerService:
            return True, '', ''
        udatas = CmsUserModel.find_many(filter_dict) or []
        zx_ls, ml_ls, lx_ls = [], [], []
        for uda in udatas:
            if uda.get('uuid') == self.current_admin_dict.get('uuid'):
                continue
            if uda.get('uuid') in SERVICE_CONNECTION:
                if uda.get('online_statu') == OnlineStatu.online:
                    zx_ls.append(uda)
                if uda.get('online_statu') == OnlineStatu.bebusy:
                    ml_ls.append(uda)
            else:
                lx_ls.append(uda)

        _utts = zx_ls+ml_ls+lx_ls
        if len(_utts) < skip:
            return True, '', ''
        total = len(_utts)

        _utts = _utts[skip: skip+per_page]
        for index, uda in enumerate(_utts):
            su_online_statu = request.args.get('su_online_statu')
            if su_online_statu:
                if su_online_statu in [OnlineStatu.online, OnlineStatu.bebusy]:
                    if uda.get('uuid') not in SERVICE_CONNECTION:
                        continue
                if su_online_statu == OnlineStatu.offline:
                    if uda.get('uuid') in SERVICE_CONNECTION:
                        continue
            _ddd = {
                'service_id': uda.get('uuid'),
                'nickname': uda.get('nickname') or '',
                'account': uda.get('account') or '',
                'portrait': uda.get('portrait') or '/assets/chat/images/keFuLogo.png',
                'role_name': PermissionCls.name_dict.get(uda.get('role_code')),
                'role_code': uda.get('role_code'),
            }
            if uda.get('role_code') == PermissionCls.Administrator:
                _uad = CmsUserModel.find_one({'uuid': uda.get('super_admin_id'), 'role_code': PermissionCls.AgentAdmin}) or {}
                if _uad:
                    _ddd['agent_admin'] = _uad.get('account')
            elif uda.get('role_code') == PermissionCls.CustomerService:
                _asd = CmsUserModel.find_one({'responsible_site': uda.get('responsible_site'), 'role_code': PermissionCls.Administrator})
                if _asd:
                    _aad = CmsUserModel.find_one({'uuid': _asd.get('super_admin_id'), 'role_code': PermissionCls.AgentAdmin})
                    if _aad:
                        _ddd['agent_admin'] = _aad.get('account')
            else:
                _ddd['agent_admin'] = ''

            new_time = datetime.datetime.now()
            if uda.get('uuid') not in SERVICE_CONNECTION:
                _ddd['online_statu'] = OnlineStatu.offline
                _ddd['online_time'] = '少于1秒'
                _ddd['ip'] = ''
            else:
                _ddd['online_statu'] = uda.get('online_statu')
                _ddd['ip'] = SERVICE_CONNECTION.get(uda.get('uuid')).get('ip') or ''
                _ddd['online_time'] = str(new_time - SERVICE_CONNECTION.get(uda.get('uuid')).get('online_time')).split('.')[0]

            if uda.get('uuid') in SERVICE_CONNECTION:
                if uda.get('online_statu') == OnlineStatu.online:
                    zx_datas.append(_ddd)
                if uda.get('online_statu') == OnlineStatu.bebusy:
                    ml_datas.append(_ddd)
            else:
                lx_datas.append(_ddd)

        table_datas += zx_datas + ml_datas + lx_datas
        if not table_datas:
            return True, '', ''

        table_html = ''
        for index, tdata in enumerate(table_datas):
            table_html += '''<tr>'''
            table_html += f'''
            <td>{index+1}</td>
            '''

            table_html += f'''
            <td id="td_{tdata.get('service_id')}" style="display: flex; justify-content: left; align-items: center;">
            '''
            if self.current_admin_dict.get('uuid') == tdata.get('service_id') and not SERVICE_CONNECTION:
                table_html += f'''
                <div style="padding: 5px 20px; position: relative; overflow: hidden; background-color: #eeeeee; cursor: pointer; border-radius: 20px; font-size: 13px;display: inline-block;" data-toggle="dropdown" aria-expanded="false">
                '''
                if self.current_admin_dict.get('online_statu') == OnlineStatu.online:
                    state_text = '在线'
                    state_color = 'uonline_statu_succcess'
                elif self.current_admin_dict.get('online_statu') == OnlineStatu.bebusy:
                    state_text = '忙碌'
                    state_color = 'uonline_statu_ml'
                else:
                    state_text = '离线'
                    state_color = 'uonline_statu_lx'
                table_html += f'''
                <span class="uonline_statu { state_color }"></span>
                <span class="ustateText" data-state="{ self.current_admin_dict.get('online_statu') }">{ state_text }</span>
                </div>
                <div class="dropdown-menu">
                    <span class="dropdown-item" onclick="uploadOnlieState('{tdata.get('service_id')}', '{ OnlineStatu.online }')"><span class="uonline_statu uonline_statu_succcess"></span>在线</span>
                    <span class="dropdown-item" onclick="uploadOnlieState('{tdata.get('service_id')}', '{ OnlineStatu.bebusy }')"><span class="uonline_statu uonline_statu_ml"></span>忙碌</span>
                </div>            
            </td>                          
                '''
            else:
                if tdata.get('online_statu') == OnlineStatu.online:
                    table_html += f'''
                <div style="padding: 5px 20px; position: relative; overflow: hidden; background-color: #eeeeee; cursor: pointer; border-radius: 20px; font-size: 13px;display: inline-block;" data-toggle="dropdown" aria-expanded="false">                        
                    <span class="uonline_statu uonline_statu_succcess"></span>
                    <span class="ustateText" data-state="{ OnlineStatu.online }">在线</span>
                </div>
                <div class="dropdown-menu">
                    <span class="dropdown-item" onclick="uploadOnlieState('{tdata.get('service_id')}', '{ OnlineStatu.online }')"><span class="uonline_statu uonline_statu_succcess"></span>在线</span>
                    <span class="dropdown-item" onclick="uploadOnlieState('{tdata.get('service_id')}', '{ OnlineStatu.bebusy }')"><span class="uonline_statu uonline_statu_ml"></span>忙碌</span>
                </div>            
            </td>                         
                    '''
                elif tdata.get('online_statu') == OnlineStatu.bebusy:
                    table_html += f'''
                <div style="padding: 5px 20px; position: relative; overflow: hidden; background-color: #eeeeee; cursor: pointer; border-radius: 20px; font-size: 13px;display: inline-block;" data-toggle="dropdown" aria-expanded="false">                        
                    <span class="uonline_statu uonline_statu_ml"></span>
                    <span class="ustateText" data-state="{ OnlineStatu.bebusy }">忙碌</span>
                </div>
                <div class="dropdown-menu">
                    <span class="dropdown-item" onclick="uploadOnlieState('{tdata.get('service_id')}', '{ OnlineStatu.online }')"><span class="uonline_statu uonline_statu_succcess"></span>在线</span>
                    <span class="dropdown-item" onclick="uploadOnlieState('{tdata.get('service_id')}', '{ OnlineStatu.bebusy }')"><span class="uonline_statu uonline_statu_ml"></span>忙碌</span>
                </div>            
            </td>                        
                    '''
                elif tdata.get('online_statu') == OnlineStatu.offline:
                    table_html += '''
                <div style="padding: 5px 20px; position: relative; overflow: hidden; background-color: #eeeeee; cursor: pointer; border-radius: 20px; font-size: 13px;display: inline-block;" data-toggle="dropdown" aria-expanded="false">                        
                    <span class="uonline_statu uonline_statu_lx"></span>
                    <span class="ustateText">离线</span>
                </div>         
            </td>                        
                    '''
                else:
                    table_html += '''
                    </td> 
                            '''

            table_html += f'''
            <td>
                <img src="{tdata.get('portrait')}" alt="" style="width: 35px;height: 35px; display: inline-block; border-radius: 100%; overflow: hidden; margin-right: 8px;">
                <span>{ tdata.get('account') or '' }</span>
            </td>
            <td>{ tdata.get('nickname') }</td>
            <td>{ tdata.get('role_name') }</td>
            <td>{ tdata.get('agent_admin') or '' }</td>
            <td>{ tdata.get('ip') }</td>
            '''
            if self.current_admin_dict.get('uuid') == tdata.get('service_id') and not SERVICE_CONNECTION:
                table_html += '''
                <td>0:00:00</td>
                '''
            else:
                table_html += f'''
                    <td>{ tdata.get('online_time') }</td>
                '''
            # table_html += f'''
            # <td>{ tdata.get('onoingCount') }</td>
            # <td>{ tdata.get('successCount') }</td>
            # <td>{ tdata.get('efficientCount') }</td>
            # <td>{ tdata.get('msgCount') }</td>
            # '''
            if not tdata.get('ip'):
                table_html += f'''
                <td></td>          
                '''
            else:
                if self.current_admin_dict.get('role_code') == PermissionCls.Administrator:
                    if tdata.get('service_id') == self.current_admin_dict.get('uuid') or tdata.get('role_code') == PermissionCls.CustomerService:
                        table_html += f'''
                        <td style="cursor: pointer; color: #0babfe;">
                            <svg style="margin-right: 8px;" onclick="forceOutLogin('{tdata.get('service_id')}')" viewBox="64 64 896 896" focusable="false" data-icon="delete-row" width="1.3em" height="1.3em" fill="currentColor" aria-hidden="true"><defs><style></style></defs><path d="M819.8 512l102.4-122.9a8.06 8.06 0 00-6.1-13.2h-54.7c-2.4 0-4.6 1.1-6.1 2.9L782 466.7l-73.1-87.8a8.1 8.1 0 00-6.1-2.9H648c-1.9 0-3.7.7-5.1 1.9a7.97 7.97 0 00-1 11.3L744.2 512 641.8 634.9a8.06 8.06 0 006.1 13.2h54.7c2.4 0 4.6-1.1 6.1-2.9l73.1-87.8 73.1 87.8a8.1 8.1 0 006.1 2.9h55c1.9 0 3.7-.7 5.1-1.9 3.4-2.8 3.9-7.9 1-11.3L819.8 512zM536 464H120c-4.4 0-8 3.6-8 8v80c0 4.4 3.6 8 8 8h416c4.4 0 8-3.6 8-8v-80c0-4.4-3.6-8-8-8zm-84 204h-60c-3.3 0-6 2.7-6 6v166H136c-3.3 0-6 2.7-6 6v60c0 3.3 2.7 6 6 6h292c16.6 0 30-13.4 30-30V674c0-3.3-2.7-6-6-6zM136 184h250v166c0 3.3 2.7 6 6 6h60c3.3 0 6-2.7 6-6V142c0-16.6-13.4-30-30-30H136c-3.3 0-6 2.7-6 6v60c0 3.3 2.7 6 6 6z"></path></svg>
                            <svg onclick="getTotalInfo('{ tdata.get('service_id') }')" viewBox="64 64 896 896" focusable="false" data-icon="info-circle" width="1.2em" height="1.2em" fill="currentColor" aria-hidden="true"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"></path><path d="M464 336a48 48 0 1096 0 48 48 0 10-96 0zm72 112h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V456c0-4.4-3.6-8-8-8z"></path></svg>                            
                        </td>
                        '''
                    else:
                        table_html += f'''
                        <td></td>
                        '''
                else:
                    table_html += f'''
                    <td style="cursor: pointer; color: #0babfe;">
                        <svg style="margin-right: 8px;" onclick="forceOutLogin('{tdata.get('service_id')}')" viewBox="64 64 896 896" focusable="false" data-icon="delete-row" width="1.3em" height="1.3em" fill="currentColor" aria-hidden="true"><defs><style></style></defs><path d="M819.8 512l102.4-122.9a8.06 8.06 0 00-6.1-13.2h-54.7c-2.4 0-4.6 1.1-6.1 2.9L782 466.7l-73.1-87.8a8.1 8.1 0 00-6.1-2.9H648c-1.9 0-3.7.7-5.1 1.9a7.97 7.97 0 00-1 11.3L744.2 512 641.8 634.9a8.06 8.06 0 006.1 13.2h54.7c2.4 0 4.6-1.1 6.1-2.9l73.1-87.8 73.1 87.8a8.1 8.1 0 006.1 2.9h55c1.9 0 3.7-.7 5.1-1.9 3.4-2.8 3.9-7.9 1-11.3L819.8 512zM536 464H120c-4.4 0-8 3.6-8 8v80c0 4.4 3.6 8 8 8h416c4.4 0 8-3.6 8-8v-80c0-4.4-3.6-8-8-8zm-84 204h-60c-3.3 0-6 2.7-6 6v166H136c-3.3 0-6 2.7-6 6v60c0 3.3 2.7 6 6 6h292c16.6 0 30-13.4 30-30V674c0-3.3-2.7-6-6-6zM136 184h250v166c0 3.3 2.7 6 6 6h60c3.3 0 6-2.7 6-6V142c0-16.6-13.4-30-30-30H136c-3.3 0-6 2.7-6 6v60c0 3.3 2.7 6 6 6z"></path></svg>
                        <svg onclick="getTotalInfo('{ tdata.get('service_id') }')" viewBox="64 64 896 896" focusable="false" data-icon="info-circle" width="1.2em" height="1.2em" fill="currentColor" aria-hidden="true"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"></path><path d="M464 336a48 48 0 1096 0 48 48 0 10-96 0zm72 112h-48c-4.4 0-8 3.6-8 8v272c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V456c0-4.4-3.6-8-8-8z"></path></svg>                                                                          
                    </td>
                    '''
            table_html += '''</tr>'''

        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
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
                        <li class="left_page" onclick="get_user_list('', {page - 1});">
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
                    <li onclick="get_user_list('', {crrpage});"><span>{crrpage}</span></li>
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
                        <li class="right_page" onclick="get_user_list('', {page + 1});">
                            <span class="iconfont icon-fangxiang-you"></span>
                        </li>
                    </ul>                    
                '''
        return True, table_html, dataTableBottom_html

    def getTimeDatas(self):
        request = Request.get_current()
        dataId = request.args.get('dataId')
        if dataId:
            u_id = dataId
        else:
            if self.current_admin_dict.get('role_code') in [PermissionCls.AgentAdmin, PermissionCls.SUPERADMIN]:
                return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            u_id = self.current_admin_dict.get('uuid')

        time_datas = []
        new_time = datetime.datetime.now()
        for t in range(24):
            if t == 23:
                start_time = datetime.datetime(new_time.year, new_time.month, new_time.day, t)
                end_time = datetime.datetime(new_time.year, new_time.month, new_time.day, t, 59, 59)
                _c = ChatConversationTable.count({'service_id': u_id, 'end_time': {'$gte': start_time, '$lte': end_time}}) or 0
            else:
                start_time = datetime.datetime(new_time.year, new_time.month, new_time.day, t)
                et = t+1
                end_time = datetime.datetime(new_time.year, new_time.month, new_time.day, et)
                _c = ChatConversationTable.count({'service_id': u_id, 'end_time': {'$gte': start_time, '$lt': end_time}}) or 0
            time_datas.append(_c)

        return time_datas

    async def get_home_html(self):

        use_expire_time = ''
        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            use_expire_time = self.current_admin_dict.get('zy_finish_time').strftime('%Y-%m-%d')
        if self.current_admin_dict.get('role_code') == PermissionCls.Administrator:
            site_data = SITE_DICT_CACHE.get(self.current_admin_dict.get('responsible_site'))
            if site_data:
                use_expire_time = site_data.get('finish_time').strftime('%Y-%m-%d')
        if self.current_admin_dict.get('role_code') == PermissionCls.CustomerService:
            site_data = SITE_DICT_CACHE.get(self.current_admin_dict.get('responsible_site'))
            if site_data:
                use_expire_time = site_data.get('finish_time').strftime('%Y-%m-%d')

        if use_expire_time:
            use_expire_time = '系统到期时间：'+use_expire_time
        optionDatas = self.getTimeDatas()
        nickname = self.current_admin_dict.get('nickname') or self.current_admin_dict.get('account')+'客服'
        self.context['nickname'] = nickname
        self.context['use_expire_time'] = use_expire_time
        self.context['optionDatas'] = str(optionDatas)
        html = await render_template('easychat/index.html', self.context)
        
        return html

    # xhr get请求
    def is_xhr(self, request):
        X_Requested_With = request.headers.get('X-Requested-With')
        if not X_Requested_With or X_Requested_With.lower() != 'xmlhttprequest':
            return
        return True

    async def ajax_get(self, request):
        action = request.args.get('action')
        html_code = request.args.get('html_code')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            if not html_code:
                return self.xtjson.json_params_error()
            if html_code == 'home':
                html = await self.get_home_html()
            elif html_code == 'get_jk_user_list_html':
                state, html, dataTableBottom_html = self.getJianKong_table()
                if not state:
                    return self.xtjson.json_params_error()
                html = update_language(self.language, html)
                dataTableBottom_html = update_language(self.language, dataTableBottom_html)
                return self.xtjson.json_result(data={'html': html, 'dataTableBottom_html': dataTableBottom_html})
            else:
                return self.xtjson.json_params_error()
            
            html = update_language(self.language, html)
            return self.xtjson.json_result(data={'html': html})
        return self.xtjson.json_params_error()

    async def view_get(self, request):
        if str(request.url).endswith('/#'):
            return redirect("/site_admin/")
        if self.is_xhr(request):
            return await self.ajax_get(request)
        index_html = await self.get_home_html()
        role_name = PermissionCls.name_dict.get(self.current_admin_dict.get('role_code') or '') or ''
        self.context['role_name'] = role_name
        self.context['index_html'] = index_html
        self.context['PermissionCls'] = PermissionCls
        self.context['LANGUAGE'] = LANGUAGE
        self.context['LANGUAGE_HINT_ALL'] = LANGUAGE_HINT_ALL
        html_str = await render_template('easychat/base.html', context=self.context)

        return html(update_language(self.language, html_str))

    def post_other_way(self, request):
        if self.action == 'get_heimingdan_html':
            return self.get_heimingdan_html()
        
        if self.action == 'getSiteData':
            site_code = self.request_data.get('site_code')
            if not site_code:
                return self.xtjson.json_params_error()
            site_data = SiteTable.find_one({'site_code': site_code}) or {}
            if not site_data:
                return self.xtjson.json_params_error()
            data_from = {}
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
            return self.xtjson.json_result(data=data_from)
        if self.action == 'outLogin':
            Request.get_current().session.pop(CMS_USER_SESSION_KEY)
            return self.xtjson.json_result()
        if self.action == 'getAutomatiCreplyText':
            conversation_id = self.request_data.get('conversation_id')
            if not conversation_id:
                return self.xtjson.json_params_error()
            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id}) or {}
            if not conversation_data:
                return self.xtjson.json_params_error()
            site_code = conversation_data.get('site_code')
            site_data = SITE_DICT_CACHE.get(site_code)
            if not site_data:
                return self.xtjson.json_params_error()
            automati_creply = site_data.get('automati_creply') or ''
            return self.xtjson.json_result(data={'automati_creply': automati_creply})
        if self.action == 'converTotal':
            conver_date = self.request_data.get('conver_date')
            if not conver_date:
                return self.xtjson.json_params_error('请选择日期范围！')
            conver_date = PagingCLS.by_silce(conver_date)
        if self.action == 'getGoogleQrcode':
            if not self.data_uuid:
                return self.xtjson.json_params_error()

            user_dict = CmsUserModel.find_one({'uuid': self.data_uuid})
            if not user_dict:
                return self.xtjson.json_params_error()

            google_cls = GooleVerifyCls(pwd=self.data_uuid, account=user_dict.get('account'), s_label='kfShare')
            generate_qrcode = google_cls.secret_generate_qrcode()
            return self.xtjson.json_result(data={'generate_qrcode': generate_qrcode})
        if self.action == 'allLyCl':
            filter_dict = {}
            if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
                site_dis = []
                for _cd in _cdas:
                    site_dis.append({'site_code': _cd.get('responsible_site')})
                site_dis.append({'user_id': self.current_admin_dict.get('uuid')})
                filter_dict['$or'] = site_dis
            if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
                filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')
            LeavingMessageTable.update_many(filter_dict, {'$set': {'statu': True}})
            return self.xtjson.json_result()
        if self.action == 'leaMexportData':
            filter_dict = {}
            fields = LeavingMessageTable.fields()
            statu, res = self.search_from_func(LeavingMessageTable, fields)
            if not statu:
                return res
            filter_dict.update(res[0])

            site_name = request.args.get('site_name') or ''
            if site_name:
                _ids = []
                for k, v in SITE_DICT_CACHE.items():
                    if v.get('site_name') == site_name.strip():
                        _ids.append(v.get('site_code'))
                filter_dict.update({'site_code': {'$in': _ids}})

            if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
                _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
                site_dis = []
                for _cd in _cdas:
                    site_dis.append(_cd.get('responsible_site'))
                filter_dict['site_code'] = {'$in': site_dis}
            if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
                filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')
            all_datas = LeavingMessageTable.find_many(filter_dict, sort=[['_create_time', -1]])
            
            crr_site_code = ''
            if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
                crr_site_code = self.current_admin_dict.get('responsible_site')

            absolute_folter = os.path.join(self.project_static_folder)
            export_folder = os.path.join(absolute_folter, ASSETS_FOLDER, EXPORT_FOLDER, self.current_admin_dict.get('uuid'))
            filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S_') + str(random.choice(range(100, 999))) + '.xlsx'
            _out_data_dict = {
                'filename': filename,
                'statu': ExportStatu.ongoing,
                'path': os.path.join(export_folder, filename).replace(absolute_folter, ''),
                'total': len(all_datas),
                'out_count': 0,
                'note': '留言-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                'site_code': crr_site_code,
                'operator_id': self.current_admin_dict.get('uuid'),
            }
            fuuid = ExportDataModel.insert_one(_out_data_dict)
            exportDataLy(all_datas, fuuid, export_folder, filename)
            return self.xtjson.json_result(message='数据导出中，请稍后到"导出文件"中查看数据！')
        if self.action == 'delExportFile':
            ExportDataModel.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()
        if self.action == 'get_serviceTotal_info':
            if not self.data_uuid:
                return self.xtjson.json_params_error()

            new_time = datetime.datetime.now()
            tyear = new_time.year
            tmonth = new_time.month
            tday = new_time.day
            su_data_date = self.request_data.get('su_data_date')
            su_data_date2 = self.request_data.get('su_data_date2')
            if su_data_date:
                if su_data_date2:
                    if su_data_date > su_data_date2:
                        return False, '日期数据错误！'
                    su_data_date = su_data_date +'|'+ su_data_date2
                else:
                    su_data_date = su_data_date +'|'+ f'{tyear}-{tmonth}-{tday} 23:59:59'
                start_time, end_time = PagingCLS.by_silce(su_data_date)
            else:
                time_by = f'{tyear}-{tmonth}-{tday} 00:00:00|{tyear}-{tmonth}-{tday} 23:59:59'
                start_time, end_time = PagingCLS.by_silce(time_by)

            ser = {
                'service_id': self.data_uuid,
                'create_time': {'$gte': start_time, '$lte': end_time},
            }
            conversDatas = ChatConversationTable.find_many(ser) or []
            totalCounts = len(conversDatas) or 0

            msgCount = 0
            efficientCount = 0
            for cd in ChatConversationTable.find_many(ser):
                conCount = ChatContentTable.count({'conversation_id': cd.get('uuid')}) or 0
                msgCount += conCount

                cdd = ChatContentTable.find_one({'customer_id': cd.get('customer_id')})
                sdd = ChatContentTable.count({'service_id': cd.get('service_id')}) or 0
                if cdd and sdd > 1:
                    efficientCount += 1

            onoingCount = 0
            for cid, v in CLIENT_CONNECTION.items():
                if v.get('service_id') == self.data_uuid:
                    onoingCount += 1
            _data = {
                'totalCounts': totalCounts,
                'msgCount': msgCount,
                'onoingCount': onoingCount,
                'efficientCount': efficientCount,
            }
            return self.xtjson.json_result(data=_data)

        if self.action == 'get_customer_service_statistics_info':
            start_time = self.request_data.get('start_time')
            try:
                page = int(request.args.get('page') or 1)
            except:
                page = 1
            per_page = 20
            skip = (page - 1) * per_page
            filter_dict, context_res = {}, {}
                
            fields = CmsUserModel.fields()
            statu, res = self.search_from_func(CmsUserModel, fields)
            if not statu:
                return res
            filter_dict.update(res[0])
            context_res.update(res[1])
            crr_role_code = self.current_admin_dict.get('role_code')

            site_name = request.args.get('site_name')
            agentadmin_account = request.args.get('agentadmin_account')

            filter_dict['uuid'] = {'$ne': self.current_admin_dict.get('uuid')}
            if crr_role_code  == PermissionCls.Administrator:
                filter_dict['responsible_site'] = self.current_admin_dict.get('responsible_site')
            if crr_role_code == PermissionCls.AgentAdmin:
                _cds = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
                _sdis = []
                for cd in _cds:
                    _sitecode = cd.get('responsible_site')
                    if _sitecode not in _sdis:
                        _sdis.append(_sitecode)
                filter_dict['responsible_site'] = {'$in': _sdis}
                if site_name and site_name.strip():
                    site_data = SiteTable.find_one({'site_name': site_name.strip()}) or {}
                    filter_dict['responsible_site'] = site_data.get('site_code')

            if crr_role_code == PermissionCls.SUPERADMIN:
                if not filter_dict.get('role_code'):
                    filter_dict['role_code'] = {'$in': [PermissionCls.AgentAdmin, PermissionCls.Administrator, PermissionCls.CustomerService]}
                if site_name and site_name.strip():
                    site_data = SiteTable.find_one({'site_name': site_name.strip()}) or {}
                    filter_dict['responsible_site'] = site_data.get('site_code')
                if agentadmin_account and agentadmin_account.strip():
                    agentadmin_data = CmsUserModel.find_one({'account': agentadmin_account.strip()}) or {}
                    if agentadmin_data:
                        _cds = CmsUserModel.find_many({'super_admin_id': agentadmin_data.get('uuid')})
                        _sdis = []
                        for cd in _cds:
                            _sitecode = cd.get('responsible_site')
                            if _sitecode not in _sdis:
                                _sdis.append(_sitecode)
                        filter_dict['responsible_site'] = {'$in': _sdis}
            if crr_role_code == PermissionCls.CustomerService:
                return self.xtjson.json_result("")

            _start_time = ''
            _end_time = ''
            if start_time:
                _start_time, _end_time = PagingCLS.by_silce(start_time)
            else:
                current_time = datetime.datetime.now()
                _start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                _end_time = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
                start_str = _start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_str = _end_time.strftime("%Y-%m-%d %H:%M:%S")
                start_time = start_str + "|" + end_str
                

            total = CmsUserModel.count(filter_dict)
            all_datas = CmsUserModel.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
            pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
            table_html =f'''<tr style="background-color: #fafafa;">
                                <td style="line-height:normal;">客服账号</td>
                                <td style="line-height:normal;">客服名称</td>
                                <td style="line-height:normal;">网站管理员</td>
                                <td style="line-height:normal;">首回时长</td>
                                <td style="line-height:normal;">平均回复时长</td>
                                <td style="line-height:normal;">好评率</td>
                                <td style="line-height:normal;">差评率</td>
                                <td style="line-height:normal;">登录时间</td>
                                <td style="line-height:normal;">在线时间</td>
                                <td style="line-height:normal;">忙碌时长</td>
                                <td style="line-height:normal;">未回复对话量</td>
                            </tr>
            '''
            for _dd in all_datas:
                table_html += f'''
                    <tr>
                        <td style="line-height:normal;">{ _dd.get('account') or '' }</td>
                        <td style="line-height:normal;">{ _dd.get('username') or '' }</td>              
                '''
                table_html += f'''
                    <td style="line-height:normal;">{ PermissionCls.name_dict.get(_dd.get('role_code') or '') or '' }</td>
                '''

                filter_criteria = {
                    'user_uuid': _dd.get('uuid'),
                    'create_time': {'$gte': _start_time, '$lte': _end_time}
                }

                # Aggregate to get the sum of specific fields with a filter
                pipeline = [
                    {"$match": filter_criteria},  # Filter documents
                    {
                        "$group": {
                            "_id": None,
                            "total_delay_duration": {'$sum': f"${'total_delay_duration'}"} ,# {"$sum": "total_delay_duration"},
                            "total_delay_count": {'$sum': f"${'total_delay_count'}"} ,# {"$sum": "total_delay_count"},
                            "positive_score_count": {'$sum': f"${'positive_score_count'}"} ,# {"$sum": "positive_score_count"},
                            "score_count": {'$sum': f"${'score_count'}"} ,# {"$sum": "score_count"},
                            "login_time": {'$sum': f"${'login_time'}"} ,# {"$sum": "login_time"},
                            "online_time": {'$sum': f"${'online_time'}"} ,# {"$sum": "online_time"},
                            "offline_time": {'$sum': f"${'offline_time'}"} ,# {"$sum": "offline_time"},
                            "busy_time": {'$sum': f"${'busy_time'}"} ,# {"$sum": "busy_time"},
                            "no_reply_count": {'$sum': f"${'no_reply_count'}"} ,# {"$sum": "no_reply_count"},
                        }
                    }
                ]

                # Execute the aggregation pipeline
                result = list(StatisticTable.collection().aggregate(pipeline))

                # Extract sums from the result
                total_delay_duration = result[0]["total_delay_duration"] if result else 0
                total_delay_count = result[0]["total_delay_count"] if result else 0
                positive_score_count = result[0]["positive_score_count"] if result else 0
                score_count = result[0]["score_count"] if result else 0
                login_time = result[0]["login_time"] if result else 0
                online_time = result[0]["online_time"] if result else 0
                offline_time = result[0]["offline_time"] if result else 0
                busy_time = result[0]["busy_time"] if result else 0
                no_reply_count = result[0]["no_reply_count"] if result else 0
                first_reply_delay_time = StatisticTable.find_one().get("first_reply_delay_time")
                

                if first_reply_delay_time == 0:
                    table_html += f'''
                        <td style="line-height:normal;"> 0秒 </td>    
                    '''
                else:
                    total_seconds = first_reply_delay_time
                    first_reply_delay_time_minutes = total_seconds // 60
                    first_reply_delay_time_seconds = total_seconds % 60
                    formatted_duration = f"{int(first_reply_delay_time_minutes)}分钟:{int(first_reply_delay_time_seconds)}秒"

                    table_html += f'''
                        <td style="line-height:normal;"> { formatted_duration } </td>    
                    '''
                if total_delay_count > 0:
                    average_reply_time = total_delay_duration / total_delay_count
                else:
                    average_reply_time = 0

                minutes = average_reply_time // 60
                seconds = average_reply_time % 60

                # Format the string in the desired format
                formatted_duration = f"{int(minutes)}分钟:{int(seconds)}秒"


                table_html += f'''
                    <td style="line-height:normal;">{ formatted_duration }</td>
                '''
                positive_rating = 0
                negative_rating = 0
                if score_count != 0:
                    positive_rating = round(float(positive_score_count / score_count) * 100, 2)
                    negative_rating = round(100 - positive_rating, 2)

                table_html += f'''
                    <td style="line-height:normal;"> { positive_rating }% </td>
                    <td style="line-height:normal;"> { negative_rating }% </td>
                '''

                ########################################################
                if start_time:
                    sign_logs = signLogTable.find_many({
                        'user_id': _dd.get('uuid'),
                         'create_time': {'$gte': _start_time, '$lte': _end_time}, 
                        }) or []
                else:
                    sign_logs = signLogTable.find_many({'user_id': _dd.get('uuid')}) or []
                
                login_time = 0
                previous_log = None
                for log in sign_logs:
                    if previous_log:
                        cur_parse_time = log.get('create_time')
                        prev_parse_time = previous_log.get('create_time')

                        time_diff = ( cur_parse_time - prev_parse_time ).total_seconds()
                        if previous_log.get('operation_type') == OPERATION_TYPES.LOGIN:
                            login_time += time_diff

                    previous_log = log

                login_formatted_duration = self.format_duration(login_time)
                table_html += f'''
                    <td style="line-height:normal;"> {login_formatted_duration} </td>
                '''
                ################################################################
                if start_time:
                    system_logs = systemLogTable.find_many({
                        'user_id': _dd.get('uuid'),
                         'create_time': {'$gte': _start_time, '$lte': _end_time}, 
                        }) or []
                else:
                    system_logs = systemLogTable.find_many({'user_id': _dd.get('uuid')}) or []

                online_time = 0
                offline_time = 0
                busy_time = 0
                previous_log = None

                for log in system_logs:
                    
                    if previous_log:
                        cur_parse_time = log.get('create_time')
                        prev_parse_time = previous_log.get('create_time')

                        time_diff = ( cur_parse_time - prev_parse_time ).total_seconds()
                        if previous_log.get('operation_type') == 'online':
                            online_time += time_diff
                        elif previous_log.get('operation_type') == 'offline':
                            offline_time += time_diff
                        elif previous_log.get('operation_type') == 'bebusy':
                            busy_time += time_diff

                    previous_log = log

                online_formatted_duration = self.format_duration(online_time)
                offline_formatted_duration = self.format_duration(offline_time)
                busy_formatted_duration = self.format_duration(busy_time)
                # Format the string in the desired format
                #  Start Online time, busy time, no reply time(offline time)    
                table_html += f'''
                    <td style="line-height:normal;"> {online_formatted_duration} </td>
                    <td style="line-height:normal;"> {busy_formatted_duration} </td>
                '''

                ####
                # No reply count 
                table_html += f'''
                    <td style="line-height:normal;"> {no_reply_count}  </td>
                    </tr>
                '''
            html = update_language(self.language, table_html)
            return self.xtjson.json_result(data=html)
        if self.action == 'downloadFile_list_html':
            return self.xtjson.json_result()
        if self.action == 'empty_blacklist':
            BlacklistTable.delete_many({})
            return self.xtjson.json_result()        
    def format_duration(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        formatted_duration = ""
        if hours > 0:
            formatted_duration += f"{int(hours)}小时:"
        
        formatted_duration += f"{int(minutes)}分钟:{int(seconds)}秒"
        
        return formatted_duration
    