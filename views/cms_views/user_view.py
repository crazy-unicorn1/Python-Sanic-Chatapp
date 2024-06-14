import os, shortuuid
from .cms_base import CmsFormViewBase
from sanic.request import Request
from sanic.exceptions import NotFound

from modules.view_helpres.view_func import update_language
from models.cms_user import CmsUserModel
from constants import SITE_DICT_CACHE, PermissionCls, DEFAULT_PORTRAIT, CMS_USER_SESSION_KEY, LANGUAGE
from common_utils.utils_funcs import PagingCLS, get_ip, render_template
from models.site_table import SiteTable
from modules.view_helpres.view_func import add_user_html, add_user_data, edit_user_html, edit_user_data, site_form_html, del_site_data, del_userManage, add_link_a
from models.kefu_table import systemLogTable
import aiofiles


# 用户管理
class userManageView(CmsFormViewBase):
    add_url_rules = [['/userManage', 'userManage']]

    # 用户管理页面HTML
    async def userManage_html(self):

        select_user_html = ''
        if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
            select_role_code_html = ''
            for perm in PermissionCls.kfshare_arr:
                select_role_code_html += f'''
                <option value="{ perm }">{ PermissionCls.name_dict.get(perm) }</option>
                '''
            select_user_html += f'''
                <select class="form-control custom-select mr-sm-2 mb-2" name="role_code" aria-label="" style="color: #666666; font-size: 13px;">
                    <option value="">全部角色</option>
                    { select_role_code_html }
                </select>
            '''
            select_user_html += f'''
                <select class="form-control custom-select mr-sm-2 mb-2" name="role_code" aria-label="" style="color: #666666; font-size: 13px;">
                    <option value="">查询方式</option>
                    { select_role_code_html }
                </select>
            '''

        elif self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            select_user_html += f'''
                <select class="form-control custom-select mr-sm-2 mb-2" name="role_code" aria-label="" style="color: #666666; font-size: 13px;">
                    <option value="">全部角色</option>
                    <option value="administrator">管理员</option>
                    <option value="customerservice">客服</option>
                </select>
            '''
        else:
            pass

        if self.current_admin_dict.get('role_code') == PermissionCls.SUPERADMIN:
            select_user_html += f'''
            <input type="text" class="form-control mb-2 mr-sm-2" name="agentadmin_account" value="" placeholder="输入代理账户" style="color: #666666; font-size: 13px;" aria-label="">
            <input type="text" class="form-control mb-2 mr-sm-2" name="site_name" value="" placeholder="输入网站名称" style="color: #666666; font-size: 13px;" aria-label="">
            '''
        elif self.current_admin_dict.get('role_code') == PermissionCls.AgentAdmin:
            select_user_html += f'''
            <input type="text" class="form-control mb-2 mr-sm-2" name="site_name" value="" placeholder="输入网站名称" style="color: #666666; font-size: 13px;" aria-label="">
            '''
        select_user_html += f'''
        <input type="text" class="form-control mb-2 mr-sm-2" name="account" value="" placeholder="账户" style="color: #666666; font-size: 13px;" aria-label="">        
        <input type="text" class="form-control mb-2 mr-sm-2" name="username" value="" placeholder="用户名" style="color: #666666; font-size: 13px;" aria-label="">        
        '''
        self.context['select_user_html'] = select_user_html
        createText = '创建用户'
        if self.current_admin_dict.get('role_code') == PermissionCls.Administrator:
            createText = '创建客服'
        self.context['createText'] = createText
        html = await render_template('easychat/userManage.html', self.context)
        html = update_language(self.language, html)
        return html

    # 用户管理列表html
    def userManageTable_html(self):
        request = Request.get_current()
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
        if crr_role_code == PermissionCls.CustomerService:
            filter_dict['responsible_site'] = self.current_admin_dict.get('responsible_site')
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

        total = CmsUserModel.count(filter_dict)
        all_datas = CmsUserModel.find_many(filter_dict, limit=per_page, skip=skip, sort=[['_create_time', -1]])
        pages, total_page = PagingCLS.ustom_pagination(page, total, per_page)

        table_html = ''
        for _dd in all_datas:
            table_html += f'''
                <tr>
                    <td>
                        <img src="{ _dd.get('portrait') or DEFAULT_PORTRAIT }" alt="" style="width: 30px; height: 30px; display: inline-block; position: relative; margin-right: 8px; overflow: hidden; border-radius: 50%;">
                        { _dd.get('account') or '' }
                    </td>
                    <td>{ _dd.get('username') or '' }</td>
                    <td>{ _dd.get('nickname') or '' }</td>
            '''
            table_html += f'''
                    <td>{ PermissionCls.name_dict.get(_dd.get('role_code') or '') or '' }</td>
                    <td>{ _dd.get('telephone') or '' }</td>
            '''

            crr_ddd = SITE_DICT_CACHE.get(_dd.get('responsible_site')) or {}
            table_html += f'''
                <td>{ crr_ddd.get('site_name') or '' }</td>                
            '''

            table_html += f'''
            <td>{ _dd.get('reception_count') or 0 }</td>
            '''
            if _dd.get('role_code') in [PermissionCls.SUPERADMIN, PermissionCls.AgentAdmin]:
                table_html +='''
                <td></td>
                '''
            else:
                table_html += '<td>'
                if _dd.get('dialogue_statu'):
                    table_html += f'''
                    <i class="iconfont icon-kaiguan4" style="color: #409eff; font-size: 35px; top: 5px; position: relative;" onclick="post_update_statu_um('userManage_dialogue_statu', '{ _dd.get('uuid') }', '确定切换对话权限状态？')"></i>
                    '''
                else:
                    table_html += f'''
                    <i class="iconfont icon-kaiguanguan" style="color: rgb(220, 223, 230); font-size: 35px; top: 5px; position: relative;" onclick="post_update_statu_um('userManage_dialogue_statu', '{ _dd.get('uuid') }', '确定切换对话权限状态？')"></i>
                    '''
                table_html += f'''
                    </td>
                '''
            table_html += f'''
                    <td>
                        <i class="iconfont icon-wenbenshuru mr-2" onclick="post_from_html('edit_user_html','{ _dd.get('uuid') }','编辑用户信息', '', '/site_admin/userManage')"></i>
                        <i class="iconfont icon-delete" onclick="post_update_statu_um('del_userManage','{ _dd.get('uuid') }','确认删除该用户？')"></i>
                        <i class="iconfont icon-yanzhengma" onclick="getGoogleQrcode('{ _dd.get('uuid') }')"></i>
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

    # 账户信息弹窗
    def info_user_html(self):
        html = f'''
        <div class="addUserBox">
            <div style="height: 23rem; position: relative; box-sizing: border-box; overflow-y: auto;">
                <div class="portrait">
                    <span style="float: left; width: 100px; text-align: right; line-height: 60px; font-size: 12px;">头像</span>
                    <div class="img">
                        <img class="portrait_img" src="{self.current_admin_dict.get('portrait') or '/assets/chat/images/defhead.png'}" alt="">
                    </div>

                    <div class="file-button" style="width: 80px;border-radius: 3px;border: solid 1px #eeeeee; padding: 6px 12px; font-size: 12px; display: inline-block; float: left; position: relative; top: 13px; cursor: pointer;">
                        <span>点击上传</span>
                        <input type="hidden" id="portrait" value="{self.current_admin_dict.get('portrait') or ''}" aria-label="">
                        <input type="file" id="upload1" onchange="upload_file_func($(\'#upload1\'),$(\'#portrait\'),\'updatePortrait\', '/site_admin/userManage', $(\'.portrait_img\'), \'\', \'progress\')">
                    </div>

                    <div style="clear: both;width: 100%;overflow: hidden;height: 10px;"></div>                    
                    <p style="margin-bottom: 0;font-size: 12px;text-align: left;padding-left: 120px;">仅限png格式；尺寸：144px X 144px；大小：不超过1M</p>
                </div>
        '''
        html += f'''
        <div class="list-group-item">
            <span style="width: 100px; text-align: right; display: inline-block; position: relative;"><span class="text-danger">*</span>账户：</span>
            <input type="text" class="form-control" id="winaccount" placeholder="账户" value="{self.current_admin_dict.get('account') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 120px)" disabled>
        </div>
        '''
        html += f'''
        <div class="list-group-item">
            <span style="width: 100px; text-align: right; display: inline-block; position: relative;">手机号：</span>
            <input type="text" class="form-control" id="wintelephone" placeholder="手机号" value="{self.current_admin_dict.get('telephone') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 120px)">
        </div>
        '''
        html += f'''
        <div class="list-group-item">
            <span style="width: 100px; text-align: right; display: inline-block; position: relative;"><span class="text-danger">*</span>姓名：</span>
            <input type="text" class="form-control" id="winusername" placeholder="姓名" value="{self.current_admin_dict.get('username') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 120px)">
        </div>
        '''
        html += f'''
        <div class="list-group-item">
            <span style="width: 100px; text-align: right; display: inline-block; position: relative;">昵称：</span>
            <input type="text" class="form-control" id="winnickname" placeholder="昵称" value="{self.current_admin_dict.get('nickname') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 120px)">
        </div>
        '''
        html += f'''
        <div class="list-group-item">
            <span style="width: 100px; text-align: right; display: inline-block; position: relative;">邮箱：</span>
            <input type="text" class="form-control" id="winemail" placeholder="邮箱" value="{self.current_admin_dict.get('email') or ''}" aria-label="" style="display: inline-block; width: calc(100% - 120px)">
        </div>
        <div class="list-group-item" style="display: flex; align-items: center; justify-content:left; margin-top: 0;margin-bottom: 0; padding-top: 0;padding-bottom: 0;">
            <span style="width: 110px; text-align: right; display: inline-block; position: relative;">新消息提示音：</span>
            <input type="hidden" alt="" aria-label="" value="{ '1' if self.current_admin_dict.get('beep_switch') else '0' }" id="beep_switch">
            <div style="display: inline-block; width: calc(100% - 180px); text-align: left;">
                <i class="iconfont { 'icon-kaiguan4' if self.current_admin_dict.get('beep_switch') else 'icon-kaiguanguan' } pointer" style="font-size: 40px;" onclick="switch_icon_func($(this))"></i>                        
            </div>
        </div>           
        </div>
        '''
        html += f'''
                <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>

                <div style="position: relative; text-align: center">
                    <span class="kfConfirmBtn" onclick="info_user_data()">确定</span>
                    <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
                </div>
        </div>
        '''
        html = update_language(self.language, html)
        return self.xtjson.json_result(message=html)

    # 修改密码HTML
    def get_edit_pwd_html(self):
        html = '''
        <div class="addUserBox">
            <div style="height: 20rem; position: relative; box-sizing: border-box; overflow-y: auto;">
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;"><span class="text-danger">*</span>新密码：</span>
                    <input type="text" class="form-control" id="password" placeholder="密码" aria-label="" style="display: inline-block; width: calc(100% - 100px)">
                </div>
                <div class="list-group-item">
                    <span style="width: 80px; text-align: right; display: inline-block; position: relative;"><span class="text-danger">*</span>确认密码：</span>
                    <input type="text" class="form-control" id="confirmPassword" placeholder="确认密码" aria-label="" style="display: inline-block; width: calc(100% - 100px)">
                </div>
            </div>

            <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>

            <div style="position: relative; text-align: center">
                <span class="kfConfirmBtn" onclick="user_pwd_func()">确定</span>
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
            html = await self.userManage_html()
            return self.xtjson.json_result(data={'html': html})
        if action == 'get_userManage_datas':
            table_html, dataTableBottom_html, context_res = self.userManageTable_html()
            return self.xtjson.json_result(data={'dataTableBottom_html':dataTableBottom_html, 'table_html': table_html})
        return self.xtjson.json_params_error()

    async def post_other_way(self, request):
        if self.action == 'add_user_data':
            res = add_user_data(self.request_data, self.current_admin_dict, self.MAIN_DOMAIN)
            if res:
                return res
            return self.xtjson.json_result()
        if self.action == 'edit_user_html':
            html = edit_user_html(self.data_uuid, self.language)
            return self.xtjson.json_result(message=html)
        if self.action == 'edit_user_data':
            res = edit_user_data(self.data_uuid, self.request_data)
            if res:
                return res
            return self.xtjson.json_result()
        if self.action == 'del_userManage':
            _u = CmsUserModel.delete_one({'uuid': self.data_uuid})
            if not _u:
                return self.xtjson.json_params_error('该用户不存在！')
            _log = {
                'user_id': self.current_admin_dict.get('uuid'),
                'note': '删除用户！用户账户',
                'ip': get_ip(),
            }
            systemLogTable.insert_one(_log)
            # return del_userManage(self.data_uuid)
            return self.xtjson.json_result()
        if self.action == 'userManage_dialogue_statu':
            if not self.data_uuid:
                return self.xtjson.json_params_error('缺少数据id！')
            _data = CmsUserModel.find_one({'uuid': self.data_uuid})
            if not _data:
                return self.xtjson.json_params_error('数据不存在！')

            if _data.get('dialogue_statu'):
                _data['dialogue_statu'] = False
            else:
                _data['dialogue_statu'] = True
            CmsUserModel.save(_data)
            return self.xtjson.json_result(message='对话权限修改成功！')
        if self.action == 'add_user_html':
            html = add_user_html(self.current_admin_dict, self.language, self.MAIN_DOMAIN)
            return self.xtjson.json_result(message=html)
        if self.action == 'updatePortrait':
            fname, fext = os.path.splitext(request.files["upload"][0].name)
            if 'png' not in fext:
                return self.xtjson.json_params_error('头像图片格式仅限png格式！')
            
            relatively_path = f'/assets/upload/userPortrait/images/'
            import_folder = self.project_static_folder + relatively_path
            if not os.path.exists(import_folder):
                os.makedirs(import_folder)

            new_filename = shortuuid.uuid()
            async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                await f.write(request.files["upload"][0].body)

            filePath = relatively_path + new_filename + fext
            return self.xtjson.json_result(message=filePath)
        if self.action == 'info_user_html':
            return self.info_user_html()
        if self.action == 'info_user_data':
            if not self.data_uuid or self.data_uuid != self.current_admin_dict.get('uuid'):
                return self.xtjson.json_params_error()
            portrait = self.request_data.get('portrait')
            telephone = self.request_data.get('telephone')
            username = self.request_data.get('username')
            nickname = self.request_data.get('nickname')
            email = self.request_data.get('email')
            beep_switch = self.request_data.get('beep_switch')
            _beep_switch = False
            if beep_switch == '1':
                _beep_switch = True

            self.data_from['portrait'] = portrait
            self.data_from['telephone'] = telephone
            self.data_from['username'] = username
            self.data_from['nickname'] = nickname
            self.data_from['email'] = email
            self.data_from['beep_switch'] = _beep_switch
            crr_data = CmsUserModel.find_one({'uuid': self.current_admin_dict.get('uuid')}) or {}
            crr_data.update(self.data_from)
            CmsUserModel.save(crr_data)
            return self.xtjson.json_result()
        if self.action == 'get_edit_pwd_html':
            return self.get_edit_pwd_html()
        if self.action == 'user_pwd_data':
            if not self.data_uuid or self.data_uuid != self.current_admin_dict.get('uuid'):
                return self.xtjson.json_params_error()
            crr_data = self.MCLS.find_one({'uuid': self.current_admin_dict.get('uuid')}) or {}
            password = self.request_data.get('password')
            if not password:
                return self.xtjson.json_params_error('请输入密码！')
            if len(password) < 5 or len(password) > 18:
                return self.xtjson.json_params_error('密码要在5~18位数之间！')

            self.data_from['password'] = self.MCLS.encry_password(password)
            crr_data.update(self.data_from)
            self.MCLS.save(crr_data)
            request.ctx.session.pop(CMS_USER_SESSION_KEY)
            return self.xtjson.json_result()
        if self.action == 'update_language':
            if not self.data_uuid or self.data_uuid != self.current_admin_dict.get('uuid'):
                return self.xtjson.json_params_error()
            language = self.request_data.get('language')
            if not language:
                return self.xtjson.json_params_error()
            if language not in LANGUAGE.name_arr:
                return self.xtjson.json_params_error()
            CmsUserModel.update_one({'uuid': self.current_admin_dict.get('uuid')},{'$set': {'language': language}})
            self.user_uuid = request.ctx.session.get(CMS_USER_SESSION_KEY)
            self.current_admin_user = CmsUserModel.query_one({'uuid': self.user_uuid})
            self.current_admin_dict = CmsUserModel.find_one({'uuid': self.user_uuid}) or {}
            self.language = self.current_admin_dict.get('language') or LANGUAGE.zh_CN
            return self.xtjson.json_result()







