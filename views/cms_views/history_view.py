import os, datetime
from .cms_base import CmsFormViewBase
from sanic.request import Request
from sanic.exceptions import NotFound
from modules.view_helpres.view_func import update_language
from models.cms_user import CmsUserModel
from models.kefu_table import CustomerTable, IpTable, BlacklistTable, ChatConversationTable, ChatContentTable, LeavingMessageTable, categoryTable
from constants import SITE_DICT_CACHE, PermissionCls
from common_utils.utils_funcs import PagingCLS, render_template


# 会话历史
class ChatHistoryView(CmsFormViewBase):
    add_url_rules = [['/chat/history', 'ChatHistoryView']]

    # 获取历史页面
    async def get_history_html(self):
        html = await render_template('easychat/history.html')
        html = update_language(self.language, html)
        return html

    # 获取表单数据
    def get_historyTable_html(self):
        request = Request.get_current()
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        fields = ChatConversationTable.fields()
        statu, res = self.search_from_func(ChatConversationTable, fields)
        if not statu:
            return res
        filter_dict.update(res[0])
        context_res.update(res[1])

        crr_u_role_Code = self.current_admin_dict.get('role_code')
        _siteid = []
        if crr_u_role_Code == PermissionCls.AgentAdmin:
            for d in CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')}):
                _siteid.append(d.get('responsible_site'))
        if crr_u_role_Code == PermissionCls.Administrator:
            _siteid.append(self.current_admin_dict.get('responsible_site'))
        if _siteid:
            filter_dict.update({'site_code': {'$in': _siteid}})

        site_name = request.args.get('site_name') or ''
        if site_name:
            s_site_code = ''
            for k, v in SITE_DICT_CACHE.items():
                if v.get('site_name') == site_name.strip():
                    if crr_u_role_Code == PermissionCls.AgentAdmin:
                        if v.get('site_code') not in _siteid:
                            s_site_code = 'allall'
                    elif crr_u_role_Code == PermissionCls.Administrator:
                        if v.get('site_code') != self.current_admin_dict.get('site_code'):
                            s_site_code = 'allall'
                    else:
                        s_site_code = v.get('site_code')
            filter_dict.update({'site_code': s_site_code})
        context_res.update({'site_name': site_name})

        customer_name = request.args.get('customer_name') or ''
        if customer_name:
            _cdata = CustomerTable.find_many({'$or': [{'name': customer_name.strip()}, {'username': customer_name.strip()}]})
            if _cdata:
                _cdss = []
                for _cdd in _cdata:
                    _cdss.append(_cdd.get('uuid'))
                if _cdss:
                    filter_dict.update({'customer_id': {'$in': _cdss}})
        context_res.update({'customer_name': customer_name})

        service_account = request.args.get('service_account') or ''
        if service_account and service_account.strip():
            service_aa = CmsUserModel.find_one({'account': service_account.strip()})
            if service_aa:
                filter_dict['service_id'] = service_aa.get('uuid')
            else:
                filter_dict['service_id'] = service_account.strip()
        context_res.update({'service_account': service_account})

        category_filter = request.args.get('category') or ''
       
        start_time = request.args.get('start_time')
        if start_time:
            _start_time, _end_time = PagingCLS.by_silce(start_time)
            filter_dict.update({'start_time': {'$gte': _start_time, '$lte': _end_time}})
        context_res.update({'start_time': start_time})
        chat_text = request.args.get('chat_text')
        if chat_text and chat_text.strip():
            if start_time:
                _start_time, _end_time = PagingCLS.by_silce(start_time)
                filter_dict.update({'create_time': {'$gte': _start_time, '$lte': _end_time}})
                filter_dict.pop('start_time')
            if filter_dict.get('customer_id'):
                _cnid = []
                for dd in ChatConversationTable.find_many({'customer_id': filter_dict.get('customer_id')}):
                    _cnid.append(dd.get('uuid'))
                filter_dict['conversation_id'] = {'$in': _cnid}
                filter_dict.pop('customer_id')
            filter_dict['text'] = {'$regex': chat_text.strip()}
            total = ChatContentTable.count(filter_dict)
            _cdatas = ChatContentTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['create_time', -1]])
            pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)
            table_html = '''
                <tr style="background-color: #fafafa;">
                    <td>联系人</td>
                    <td>类别</td>
                    <td>接待客服</td>
                    <td>聊天内容</td>
                    <td>是否撤回</td>
                    <td>通讯时间</td>
                </tr>
            '''
            for data in _cdatas:
                _cdata = CustomerTable.find_one({'uuid': data.get('customer_id')}) or {}
                if category_filter != '' and _cdata.get('category') != category_filter:
                    continue
                _udata = CmsUserModel.find_one({'uuid': data.get('service_id')}) or {}
                table_html += f'''
                    <tr>
                        <td>{_cdata.get('username') or _cdata.get('name') or ''}</td>
                        <td>{ _cdata.get('category') or '' }</td>
                        <td><a >{ _udata.get('account') or '' }</a></td>                        
                '''
                text = data.get('text')
                if len(text) > 50:
                    table_html += f'''
                    <td onclick="xtalert.alertContent('{text}')">{text[:50] + '...'}</td>
                    '''
                else:
                    table_html += f'''
                    <td>{text}</td>
                    '''
                table_html += f'''
                    <td>{ '是' if data.get('is_retract') else '否' }</td>
                    <td>{ data.get('create_time').strftime('%Y-%m-%d %H:%M:%S') }</td>
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
                            </li>56
                        </ul>
                    '''
            option_html = f'<option value="" selected>选择类别</option>'
            for x in categoryTable.find_many({}):
                selected = ''
                if x.get("category") == category_filter:
                    selected = 'selected'
                option_html += f'''
                <option value='{x.get("category")}' {selected}>{x.get("category")}</option>
                '''
            return table_html, dataTableBottom_html, option_html,  context_res

        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
            site_dis = []
            for _cd in _cdas:
                site_dis.append(_cd.get('responsible_site'))
            filter_dict['site_code'] = {'$in': site_dis}
        if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
            filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')

        total = ChatConversationTable.count(filter_dict)
        all_datas = ChatConversationTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)

        table_html = f'''
            <tr style="background-color: #fafafa;">
                <td>对话渠道</td>
                <td>联系人</td>
                <td>类别</td>
                <td>设备</td>
                <td>ip</td>
                <td>对话时间</td>
                <td>接待客服</td>
                <td>满意评价</td>
                { '' if self.current_admin_dict.get('role_code') == PermissionCls.CustomerService else '<td>操作</td>'}
            </tr>
        '''
        for data in all_datas:
            _cdata = CustomerTable.find_one({'uuid': data.get('customer_id')}) or {}
            _udata = CmsUserModel.find_one({'uuid': data.get('service_id')}) or {}
            if category_filter != '' and _cdata.get('category') != category_filter:
                continue
            table_html += f'''
                <tr onclick="request_history('{data.get('uuid')}')" style="cursor: pointer;">
                    <td>{ SITE_DICT_CACHE.get(data.get('site_code')).get('site_name') if SITE_DICT_CACHE.get(data.get('site_code')) else '' }</td>
                    <td>{ _cdata.get('username') or _cdata.get('name') or '' }</td>
                    <td>{ _cdata.get('category') or '' }</td>
                    <td>
                '''
            if data.get('os_type') == 'windows':
                table_html += f'''
                <i class="iconfont icon-windows" style="color: #0babfe;font-size: 23px;top: 5px;position: relative;margin-right: 5px;"></i>
                '''
            elif data.get('os_type') == 'linux':
                table_html += f'''
                <i class="iconfont icon-linux" style="color: #0babfe;font-size: 20px;top: 5px;position: relative;margin-right: 5px;"></i>
                '''
            elif data.get('os_type') == 'macos':
                table_html += f'''
                <i class="iconfont icon-macos" style="color: #0babfe;font-size: 23px;top: 5px;position: relative;margin-right: 5px;"></i>
                '''

            if data.get('browser_type') == 'chrome':
                table_html += f'''
                    <img src="/assets/chat/images/guge.png" alt="" style="width: 18px; display: inline-block;">
                    '''
            elif data.get('browser_type') == 'firefox':
                table_html += f'''
                    <img src="/assets/images/firefox.png" alt="" style="width: 16px; display: inline-block;">
                    '''

            table_html += f'''
            </td>
            <td>{ data.get('ip') or '' }</td>
            '''
            table_html += f'''                    
                    <td><p>开始时间：{ self.format_time_func(data.get('start_time')) }</p></td>
                    <td><a >{ _udata.get('account') or '' }</a></td>
                    <td style="color: #FFB800;">                                    
                    '''
            if data.get('score_level'):
                for m in range(data.get('score_level')):
                    table_html +='''
                    <i class="iconfont icon-pingfen"></i>
                    '''
                for k in range(5 - data.get('score_level')):
                    table_html += '''
                    <i class="iconfont icon-pingfen1"></i>
                    '''
            table_html += '''
                    </td>
            '''
            if self.current_admin_dict.get('role_code') != PermissionCls.CustomerService:
                table_html += f'''
                    <td>                
                        <i class="iconfont icon-delete" onclick="data_del_func('delHistory','{data.get('uuid')}','确认删除该会话数据？')"></i>
                    </td>                    
                '''

            table_html += f'''
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
        option_html = f'<option value="" selected>选择类别</option>'
        for x in categoryTable.find_many({}):
            selected = ''
            if x.get("category") == category_filter:
                selected = 'selected'
            option_html += f'''
            <option value='{x.get("category")}' {selected}>{x.get("category")}</option>
            '''

        return table_html, dataTableBottom_html, option_html, context_res

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_history_html()
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_historyTable_html':
            table_html, dataTableBottom_html, option_html, context_res = self.get_historyTable_html()
            table_html = update_language(self.language, table_html)
            dataTableBottom_html = update_language(self.language, dataTableBottom_html)
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html, "option_html": option_html})
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'delHistory':
            if not self.data_uuid:
                return self.xtjson.json_params_error('缺少数据id！')
            ChatConversationTable.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()

        if self.action == 'get_history_list':
            conversation_id = self.request_data.get('conversation_id')
            if not conversation_id:
                return self.xtjson.json_params_error()

            _ces = ChatConversationTable.find_one({'uuid': conversation_id}, sort=[['create_time', -1]])

            _c = CustomerTable.find_one({'uuid': _ces.get('customer_id')})
            _s = CmsUserModel.find_one({'uuid': _ces.get('service_id')})

            _datas = ChatContentTable.find_many({'conversation_id': conversation_id}) or []
            _ce_dcit = {}
            _u_dict = {}
            _result = []
            for da in _datas:
                _dd = {
                    'customer_name': _c.get('username') or _c.get('name') or '',
                    'service_name': _s.get('nickname') or _s.get('account') or '',
                    'text': da.get('text') or '',
                    'file_path': da.get('file_path') or '',
                    'filename': da.get('filename') or '',
                    'file_size': da.get('file_size') or '',
                    'service_id': da.get('service_id') or '',
                    'customer_id': da.get('customer_id') or '',
                    'content_type': da.get('content_type') or '',
                    'create_time': da.get('create_time').strftime('%Y-%m-%d %H:%M:%S') or '',
                }
                _result.append(_dd)
            start_time = ''
            if _ces.get('start_time'):
                start_time = _ces.get('start_time').strftime('%Y-%m-%d %H:%M:%S')
            return self.xtjson.json_result(data={'datas': _result, 'sname': _s.get('nickname') or _s.get('account') or '', 'start_time': start_time})
