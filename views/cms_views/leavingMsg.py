import os, datetime
from .cms_base import CmsFormViewBase
from sanic.request import Request
from sanic.exceptions import NotFound
from modules.view_helpres.view_func import update_language
from models.cms_user import CmsUserModel
from models.kefu_table import CustomerTable, IpTable, BlacklistTable, ChatConversationTable, ChatContentTable, LeavingMessageTable
from constants import SITE_DICT_CACHE, PermissionCls
from common_utils.utils_funcs import PagingCLS, render_template


# 访客页面
class LeavingMsgView(CmsFormViewBase):
    add_url_rules = [['/leavingMsg', 'LeavingMsgView']]

    async def get_leavingMessage_html(self):
        request = Request.get_current()
        ip = request.args.get('ip')
        username = request.args.get('username')
        site_name = request.args.get('site_name')
        telephone = request.args.get('telephone')
        _data = {
            'ip': ip,
            'username': username,
            'site_name': site_name,
            'telephone': telephone,
        }
        html = await render_template('easychat/leavingMessage.html', _data)
        html = update_language(self.language, html)
        return html

    # 获取表格数据
    def get_leavingMessage_datas(self):
        request = Request.get_current()
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        fields = LeavingMessageTable.fields()
        statu, res = self.search_from_func(LeavingMessageTable, fields)
        if not statu:
            return res
        filter_dict.update(res[0])
        context_res.update(res[1])

        site_name = request.args.get('site_name') or ''
        if site_name:
            _ids = []
            for k, v in SITE_DICT_CACHE.items():
                if v.get('site_name') == site_name.strip():
                    _ids.append(v.get('site_code'))
            filter_dict.update({'site_code': {'$in': _ids}})
        context_res.update({'site_name': site_name})

        if self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            _cdas = CmsUserModel.find_many({'super_admin_id': self.current_admin_dict.get('uuid')})
            site_dis = []
            for _cd in _cdas:
                site_dis.append(_cd.get('responsible_site'))
            filter_dict['site_code'] = {'$in': site_dis}
        if self.current_admin_dict.get('role_code') in [PermissionCls.Administrator, PermissionCls.CustomerService]:
            filter_dict['site_code'] = self.current_admin_dict.get('responsible_site')

        total = LeavingMessageTable.count(filter_dict)
        all_datas = LeavingMessageTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)

        table_html = ''
        for _dd in all_datas:
            customer_data = CustomerTable.find_one({'uuid': _dd.get('customer_id')}) or {}
            _cdu_uid = _dd.get('operator_id')
            _cdu = {}
            if _cdu_uid:
                _cdu = CmsUserModel.find_one({'uuid': _cdu_uid}) or {}

            update_statu_text = '确定更新当前处理状态为`已处理`？'
            if _dd.get('statu'):
                update_statu_text = '确定更新当前处理状态为`未处理`？'

            _crr_site_data = SITE_DICT_CACHE.get(_dd.get('site_code')) or {}
            table_html += f'''
                <tr>
                    <td>{ _crr_site_data.get('site_name') or '' }</td>
                    <td><a>{ customer_data.get('name') or '' }</a></td>
                    <td>{ _dd.get('ip') or '' }</td>
                    <td>{ _dd.get('username') or '' }</td>
                    <td>{ _dd.get('telephone') or '' }</td>
                    <td>{ _dd.get('email') or '' }</td>
                    <td>{ _dd.get('text') or '' }</td>
                    <td>{ self.format_time_func(_dd.get('_create_time')) }</td>                        
                    <td>{ '已处理' if _dd.get('statu') else '未处理' }</td>
                    <td>{ _cdu.get('username') or _cdu.get('account') or ''  }</td>                        
                    <td>
                        <i class="iconfont icon-delete" onclick="data_del_func('delLeavingMessage','{_dd.get('uuid')}','确认删除该留言吗？')"></i>
                        <i class="iconfont icon-xitongzhuangtai-baozhangzhuangtai" onclick="post_leaving_statu('leaving_update_statu', '{ _dd.get('uuid') }', '{update_statu_text}')"></i>
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
        is_not_data = False
        if not all_datas:
            is_not_data = True
        return table_html, dataTableBottom_html, context_res, is_not_data

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_leavingMessage_html()
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_leavingMessage_datas':
            table_html, dataTableBottom_html, context_res, is_not_data = self.get_leavingMessage_datas()
            table_html = update_language(self.language, table_html)
            dataTableBottom_html = update_language(self.language, dataTableBottom_html)
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html, 'is_not_data': is_not_data})
        return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'delLeavingMessage':
            LeavingMessageTable.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()
        if self.action == 'leaving_update_statu':
            if not self.data_uuid:
                return self.xtjson.json_params_error()
            _d = LeavingMessageTable.find_one({'uuid': self.data_uuid})
            if not _d:
                return self.xtjson.json_params_error('数据不存在！')
            if _d.get('statu'):
                _d['statu'] = False
            else:
                _d['statu'] = True
            _d['operator_id'] = self.current_admin_dict.get('uuid')
            LeavingMessageTable.save(_d)
            return self.xtjson.json_result()

