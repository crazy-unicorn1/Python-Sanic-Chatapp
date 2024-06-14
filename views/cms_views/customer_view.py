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
class CustomerView(CmsFormViewBase):
    add_url_rules = [['/customer', 'CustomerView']]

    # 获取访客页面html
    async def get_customer_html(self):
        request = Request.get_current()
        ip = request.args.get('ip') or ''
        name = request.args.get('name') or ''
        username = request.args.get('username') or ''
        site_name = request.args.get('site_name') or ''
        _context = {
            'ip': ip,
            'name': name,
            'username': username,
            'site_name': site_name,
        }
        html = await render_template('easychat/customer.html', _context)
        html = update_language(self.language, html)
        return html

    # 获取访客表格数据
    def get_customer_datas(self):
        request = Request.get_current()
        try:
            page = int(request.args.get('page') or 1)
        except:
            page = 1
        per_page = 20
        skip = (page - 1) * per_page
        filter_dict, context_res = {}, {}
        fields = CustomerTable.fields()
        statu, res = self.search_from_func(CustomerTable, fields)
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
            filter_dict['site_code'] =self.current_admin_dict.get('responsible_site')

        total = CustomerTable.count(filter_dict)
        all_datas = CustomerTable.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)

        table_html = ''
        for _dd in all_datas:
            site_name = ''
            if _dd.get('site_code') and SITE_DICT_CACHE.get(_dd.get('site_code')):
                site_name = SITE_DICT_CACHE.get(_dd.get('site_code')).get('site_name') or ''

            ip_data= IpTable.find_one({'ip':_dd.get('ip') }) or {}
            table_html += f'''
                <tr>
                    <td>{ site_name }</td>
                    <td>{ _dd.get('name') }</td>
                    <td>{ _dd.get('username') or '' }</td>
                    <td>{ _dd.get('telephone') or '' }</td>
                    <td>{ _dd.get('telegram') or '' }</td>
                    <td>{ self.format_time_func(_dd.get('_create_time')) }</td>
                    <td></td>
                    <td>{ _dd.get('ip') }</td>
                    <td>{ip_data.get('country_name') or ''}-{ip_data.get('region_name')or''}-{ip_data.get('city_name')or''}</td>                    
            '''
            if BlacklistTable.count({'customer_id': _dd.get('uuid')}):
                table_html += f'''
                <td>已拉黑</td>
                <td>
                                        <i class="iconfont icon-heimingdan mr-1" style="color: #d96464; font-size: 14px;"></i>
                '''
            else:
                table_html += f'''
                <td>未拉黑</td> 
                <td>
                                        <i class="iconfont icon-heimingdan mr-1" style="font-size: 14px;" onclick="post_from_html('get_heimingdan_html','{_dd.get('uuid')}','加入黑名单', '', '/site_admin/')"></i>
                '''
            table_html += f'''
                        <i class="iconfont icon-wenbenshuru mr-2" style="font-size: 14px;" onclick="post_from_html('editCustomerHtml','{_dd.get('uuid')}', '编辑客户信息', '', '/site_admin/customer')"></i>
                        <i class="iconfont icon-delete" style="font-size: 14px;" onclick="data_del_func('delCustomer','{_dd.get('uuid')}','确认删除该用户？')"></i>
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

    # 编辑访客html代码
    def editCustomerHtml_func(self):
        if not self.data_uuid:
            return self.xtjson.json_params_error()
        crr_data = CustomerTable.find_one({'uuid': self.data_uuid})
        if not crr_data:
            return self.xtjson.json_params_error()
        html = f'''
            <div style="position: relative; width: 100%; overflow: hidden; padding: 20px 50px 0;">

                <div class="input-group mb-3"> 
                    <div class="input-group-prepend"> 
                        <span class="input-group-text"><span style="color: red;">*</span>姓名</span>
                    </div>
                    <input type="text" class="form-control" id="username" value="{crr_data.get('username') or ''}" placeholder="姓名" aria-label="" aria-describedby="basic-addon1"> 
                </div>
                <div class="input-group mb-3"> 
                    <div class="input-group-prepend">
                        <span class="input-group-text">telegram</span>
                    </div>
                    <input type="text" class="form-control" id="telegram" value="{crr_data.get('telegram') or ''}" placeholder="telegram" aria-label="" aria-describedby="basic-addon1"> 
                </div>
                <div class="input-group mb-3"> 
                    <div class="input-group-prepend">
                        <span class="input-group-text">电话</span>
                    </div>
                    <input type="text" class="form-control" id="telephone" value="{crr_data.get('telephone') or ''}" placeholder="电话" aria-label="" aria-describedby="basic-addon1"> 
                </div>
                <div class="input-group mb-3"> 
                    <div class="input-group-prepend">
                        <span class="input-group-text">邮箱</span>
                    </div>
                    <input type="text" class="form-control" id="email" value="{crr_data.get('email') or ''}" placeholder="邮箱" aria-label="" aria-describedby="basic-addon1"> 
                </div>
                <div class="input-group mb-3"> 
                    <div class="input-group-prepend">
                        <span class="input-group-text">地址</span>
                    </div>
                    <input type="text" class="form-control" id="address" value="{crr_data.get('address') or ''}" placeholder="地址" aria-label="" aria-describedby="basic-addon1"> 
                </div>
                <div class="input-group mb-3"> 
                    <div class="input-group-prepend">
                        <span class="input-group-text">说明</span>
                    </div>
                    <input type="text" class="form-control" id="note" value="{crr_data.get('note') or ''}" placeholder="说明" aria-label="" aria-describedby="basic-addon1"> 
                </div>

                <div style="display: block; margin: 35px auto 0; text-align: center">
                    <span class="btn btn-success subBtn" onclick="edit_Customer_data('{crr_data.get('uuid')}')">提交</span>
                    <span class="btn btn-default cancelBnt" onclick="xtalert.close()">取消</span>
                </div>
            </div>
        '''
        html = update_language(self.language, html)
        return self.xtjson.json_result(message=html)

    # 提交修改访客信息
    def editCustomer_func(self):
        if not self.data_uuid:
            return self.xtjson.json_params_error('缺少数据id！')
        _data = CustomerTable.find_one({'uuid': self.data_uuid}) or {}
        if not _data:
            return self.xtjson.json_params_error()

        data_from = {}
        for k in ['username', 'telegram', 'telephone', 'email', 'address', 'note']:
            data_from[k] = self.request_data.get(k) or ''

        _data.update(data_from)
        CustomerTable.save(_data)
        return self.xtjson.json_result()

    # 添加黑名单
    def add_heimingdan_data_func(self):
        request = Request.get_current()
        if not self.data_uuid:
            return self.xtjson.json_params_error()
        duration = self.request_data.get('duration')
        if not duration:
            return self.xtjson.json_params_error()

        is_cistomer = self.request_data.get('is_cistomer')
        if is_cistomer:
            customer_data = CustomerTable.find_one({'uuid': self.data_uuid})
            if not customer_data:
                return self.xtjson.json_params_error()
            if BlacklistTable.count({'customer_id': self.data_uuid}):
                return self.xtjson.json_result()
            d = datetime.datetime.now() + datetime.timedelta(days=int(duration))
            _dd = {
                'duration': duration,
                'ip': customer_data.get('ip'),
                'operation_uuid': self.current_admin_dict.get('uuid'),
                'expire_time': d,
                'customer_id': self.data_uuid,
            }
            BlacklistTable.insert_one(_dd)
        else:
            _condata = ChatConversationTable.find_one({'uuid': self.data_uuid}) or {}
            d = datetime.datetime.now() + datetime.timedelta(days=int(duration))
            if BlacklistTable.count({'customer_id': _condata.get('customer_id')}):
                return self.xtjson.json_result()
            _dd = {
                'duration': duration,
                'ip': _condata.get('ip'),
                'operation_uuid': self.current_admin_dict.get('uuid'),
                'expire_time': d,
                'customer_id': _condata.get('customer_id'),
            }
            BlacklistTable.insert_one(_dd)
        return self.xtjson.json_result()

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_customer_html()
            return self.xtjson.json_result(data={'html': html})
        elif action == 'get_customer_datas':
            table_html, dataTableBottom_html, context_res = self.get_customer_datas()
            table_html = update_language(self.language, table_html)
            dataTableBottom_html = update_language(self.language, dataTableBottom_html)
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html})
        else:
            return self.xtjson.json_params_error()

    def post_other_way(self, request):
        if self.action == 'editCustomerHtml':
            return self.editCustomerHtml_func()
        if self.action == 'editCustomer':
            return self.editCustomer_func()
        if self.action == 'delCustomer':
            for ch in ChatConversationTable.find_many({'customer_id': self.data_uuid}):
                ChatContentTable.delete_many({'conversation_id': ch.get('uuid') or ''})
                ChatConversationTable.delete_one({'uuid':  ch.get('uuid') or ''})
            LeavingMessageTable.delete_many({'customer_id': self.data_uuid or ''})
            CustomerTable.delete_one({'uuid': self.data_uuid})
            return self.xtjson.json_result()
        if self.action == 'add_heimingdan_data':
            return self.add_heimingdan_data_func()

