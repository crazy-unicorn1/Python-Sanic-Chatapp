import os, time, shortuuid, datetime
from .cms_base import CmsFormViewBase
from sanic.request import Request
from sanic import Sanic
from sanic.exceptions import NotFound
from modules.view_helpres.view_func import update_language, add_link_a
from models.cms_user import CmsUserModel
from models.kefu_table import CustomerTable, ChatConversationTable, ChatContentTable, QuickReplyTable, BlacklistTable
from models.site_table import SiteTable
from constants import SITE_DICT_CACHE, PermissionCls, SITE_CONFIG_CACHE, DEFAULT_FILE_SIZE, LANGUAGE, SERVICE_CONNECTION
from modules.goole_translate import translate_text_func
from constants import duration_dcit
from common_utils.utils_funcs import render_template

import aiofiles
# 会话页面
class ChatServiceView(CmsFormViewBase):
    add_url_rules = [['/chatService', 'ChatServiceView']]

    # 获取页面HTML
    async def get_chat_html_func(self):
        kj_list_html = ''
        QuickReplydata = QuickReplyTable.find_many({'service_id': self.current_admin_dict.get('uuid')}, sort=[['_create_time', -1]]) or []
        for _dq in QuickReplydata:
            kj_list_html += f'''<li data-dataid="{_dq.get('uuid')}" data-datatext="{ _dq.get('text') }"><span>{ _dq.get('title') or '' }</span></li>'''

        is_gly = 'false'
        if self.current_admin_dict.get('role_code') in [PermissionCls.AgentAdmin, PermissionCls.SUPERADMIN, PermissionCls.Administrator]:
            is_gly = 'true'

        translate_state = 'false'
        site_data = SITE_DICT_CACHE.get(self.current_admin_dict.get('responsible_site'))
        if site_data and site_data.get('fast_state'):
            translate_state = 'true'

        control_file_size = 10485760
        if hasattr(SITE_CONFIG_CACHE, 'control_file_size'):
            control_file_size = SITE_CONFIG_CACHE.control_file_size
        reception_count = self.current_admin_dict.get('reception_count') or 0

        automati_creply = site_data.get('automati_creply') or ''
        automati_creply_time = site_data.get('automati_creply_time') or -1
        automati_close_time = site_data.get('automati_close_time') or -1

        _context = {
            'is_gly': is_gly,
            'translate_state': translate_state,
            'kj_list_html': kj_list_html,
            'control_file_size': control_file_size,
            'reception_count': reception_count,
            'automati_close_time': automati_close_time,
            'automati_creply_time': automati_creply_time,
            'automati_creply': automati_creply,
        }
        html = await render_template('easychat/chat.html', _context)
        html = update_language(self.language, html)
        return html

    # 检测文件名称
    def chack_Fileformat_func(self):
        fileName = self.request_data.get('fileName')
        if not fileName:
            return self.xtjson.json_params_error()
        return self.xtjson.json_result()

    # 获取上一个会话内容
    def getPrevConversation(self):
        request = Request.get_current()
        site_code = request.args.get('site_code')
        msg_id = request.args.get('msg_id')
        if not site_code or not msg_id:
            return self.xtjson.json_params_error()

        content_data = ChatContentTable.find_one({'uuid': msg_id})
        if not content_data:
            return self.xtjson.json_params_error()

        conversationId = content_data.get('conversation_id')
        crr_conversation_data = ChatConversationTable.find_one({'uuid': conversationId})
        if not crr_conversation_data:
            return self.xtjson.json_params_error()

        prev_conversation_data = ChatConversationTable.find_one({'customer_id': crr_conversation_data.get('customer_id'), 'create_time': {'$lt': crr_conversation_data.get('create_time')}}, sort=[['create_time', -1]])
        if not prev_conversation_data:
            return self.xtjson.json_params_error()

        customer_data = CustomerTable.find_one({'uuid': prev_conversation_data.get('customer_id')})
        if not customer_data:
            return

        _re_customer_data = {}
        for k in ['username', 'site_code', 'track', 'address', 'telephone', 'telegram', 'note', 'gender', 'email', 'uuid', 'category']:
            _v = customer_data.get(k) or ''
            _re_customer_data.update({k: _v})

        crr_service = CmsUserModel.find_one({'uuid': prev_conversation_data.get('service_id')})
        _result = {
            'conversation_id': conversationId,
            'conversation_statu': prev_conversation_data.get('statu'),
            'customer_id': customer_data.get('uuid'),
            'customer_name': customer_data.get('name'),
            'customer_data': _re_customer_data,
            'service_data': {
                'service_name': crr_service.get('nickname') or crr_service.get('account') or '客服',
                'portrait': crr_service.get('portrait') or '/assets/chat/images/keFuLogo.png',
            }
        }
        prevconv_end_time = prev_conversation_data.get('end_time')
        if prevconv_end_time:
            _result['end_time'] = prevconv_end_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            _result['end_time'] = ''

        for k in ['os_type', 'browser_type', 'client_type', 'ip', 'track']:
            _result[k] = prev_conversation_data.get(k) or ''

        info_data = ChatContentTable.find_many({'conversation_id': prev_conversation_data.get('uuid'), 'is_retract': False}, sort=[['create_time', 1]]) or []
        _results = []
        _udsss = {}
        for data in info_data:
            new_red = {}
            c_serid = data.get('service_id')
            if c_serid:
                c_ser_data = _udsss.get(c_serid)
                if not c_ser_data:
                    c_ser_data = CmsUserModel.find_one({'uuid': c_serid}) or {}
                    if not c_ser_data:
                        continue
                    _udsss[c_serid] = c_ser_data
                new_red['service_data'] = {
                    'service_name': c_ser_data.get('nickname') or '客服',
                    'portrait': c_ser_data.get('portrait') or '/assets/chat/images/keFuLogo.png',
                }
            new_red.update({
                'uuid': data.get('uuid'),
                'text': add_link_a(data.get('text') or ''),
                'is_service': True if data.get('service_id') else False,
                'is_customer': True if data.get('customer_id') else False,
                'create_time': data.get('create_time').strftime('%m-%d %H:%M:%S'),
                'file_path': data.get('file_path'),
                'file_size': data.get('file_size'),
                'filename': data.get('filename'),
                'content_type': data.get('content_type'),
                'timeStamp': int(time.mktime(data.get('create_time').timetuple())),
                'customer_reading_state': data.get('customer_reading_state') or False,
            })
            _results.append(new_red)

        _result['info_data'] = _results
        return self.xtjson.json_result(data=_result)

    # 添加黑名单
    def add_heimingdan_data_func(self):
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
                'site_code': customer_data.get('site_code'),
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
                'site_code': _condata.get('site_code'),
            }
            BlacklistTable.insert_one(_dd)
        return self.xtjson.json_result()

    # 消息翻译
    def translateText_func(self):
        if not self.data_uuid:
            return self.xtjson.json_params_error()
        cont_data = ChatContentTable.find_one({'uuid': self.data_uuid}) or {}
        if not cont_data:
            return self.xtjson.json_params_error()

        site_Data = SITE_DICT_CACHE.get(cont_data.get('site_code'))
        if not site_Data:
            return self.xtjson.json_params_error()
        translate_state = site_Data.get('translate_state')
        target_language = site_Data.get('target_language')
        source_language = site_Data.get('source_language')
        if not translate_state or not target_language or not source_language:
            return self.xtjson.json_params_error()
        datakey = target_language + '_text'
        text = cont_data.get('text')
        if not text:
            return self.xtjson.json_params_error()
        _new_mag_text = cont_data.get(datakey)
        if _new_mag_text:
            return self.xtjson.json_result(message=_new_mag_text)

        source_language_code = LANGUAGE.lang_code.get(source_language) or 'en'
        target_language_code = LANGUAGE.lang_code.get(target_language) or 'en'
        try:
            _new_mag_text = translate_text_func(text, source_language=source_language_code, target_language=target_language_code)
            return self.xtjson.json_result(message=_new_mag_text)
        except:
            return self.xtjson.json_params_error()

    # 获取会话客户信息
    def get_sideInfo_html(self):
        ''' 信息弹窗 '''
        data = ChatConversationTable.find_one({'uuid': self.data_uuid})
        if not data:
            return self.xtjson.json_params_error()

        html = f'''
            <div class="itemInfoBox">
                <div class="infoBack sheBei">
                    <div class="shebeiOvh clientType" style="width: 30%; padding-left: 20px; text-align: left;">
                        <img src="/assets/images/computer.png" alt="" style="display: inline-block;width: 20px;height: 20px;">
            '''
        if data.get('client_type') == 'pc':
            html += '<span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">电脑端</span>'
        else:
            html += '<span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">手机端</span>'
        html += '''
                    </div>
                    <div class="shebeiOvh systemType" style="width: 30%; padding-left: 20px; text-align: left;">
        '''

        if data.get('os_type') == 'windows':
            html += '''
                            <img src="/assets/images/Windows.png" alt="" style="display: inline-block;width: 20px;height: 20px;">
                        <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">windows</span>
                    </div>
                    <div class="shebeiOvh browserType" style="width: 30%; padding-left: 20px; text-align: left;">            
            '''
        elif data.get('os_type') == 'linux':
            html += '''
                            <img src="/assets/images/linux.png" alt="" style="display: inline-block;width: 20px;height: 20px;">
                        <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">linux</span>
                    </div>
                    <div class="shebeiOvh browserType" style="width: 30%; padding-left: 20px; text-align: left;">                   
            '''
        elif data.get('os_type') == 'mac os x':
            html += '''
                            <img src="/assets/images/ios.png" alt="" style="display: inline-block;width: 20px;height: 20px;">
                        <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">mac os x</span>
                    </div>
                    <div class="shebeiOvh browserType" style="width: 30%; padding-left: 20px; text-align: left;">                   
            '''
        else:
            html += '''
                            <img src="/assets/images/Windows.png" alt="" style="display: inline-block;width: 20px;height: 20px;">
                        <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">windows</span>
                    </div>
                    <div class="shebeiOvh browserType" style="width: 30%; padding-left: 20px; text-align: left;">                     
            '''

        if data.get('browser_type') == 'chrome':
            html += '''
                <img src="/assets/images/guge.png" alt="" style="display: inline-block;width: 18px;height: 18px; top: -2px; position: relative;">
                <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">谷歌</span>            
            '''
        elif data.get('browser_type') == 'firefox':
            html += '''
                <img src="/assets/images/firefox.png" alt="" style="display: inline-block;width: 18px;height: 18px; top: -2px; position: relative;">
                <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">火狐</span>
            '''
        elif data.get('browser_type') == 'safari':
            html += '''
                <img src="/assets/images/Safari.png" alt="" style="display: inline-block;width: 18px;height: 18px; top: -2px; position: relative;">
                <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">Safari</span>
            '''
        else:
            html += '''
                <i class="iconfont icon-browser" style="font-size: 18px; position: relative; top: 2px; color: #0babfe; display: none;"></i>
                <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;">未知浏览器</span>
            '''

        html += f'''
                    </div>
                    <div class="shebeiOvh" style="width: 30%; padding-left: 20px; text-align: left;">
                        <img src="/assets/images/weizhi.png" alt="" style="display: inline-block;width: 18px;height: 18px; top: -2px; position: relative;">                            
                        <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px;"></span>
                    </div>
                    <div class="shebeiOvh ip" style="width: 30%; padding-left: 20px; text-align: left;">
                        <img src="/assets/images/IP.png" alt="" style="display: inline-block;width: 18px;height: 18px; top: -2px; position: relative;">
                        <span style="position: relative; margin-left: 5px; color: #00c9d1; font-size: 14px; line-height: 39px; vertical-align: -1px;">{data.get('ip')}</span>
                    </div>
                </div>

                <div class="infoBack mingPian" style="padding-left: 10px; padding-right: 10px;">
                    <h2>
                        <span>名片</span>
                        <span class="kfConfirmBtn" onclick="saveCustomerBtn2('{self.data_uuid}')">保存</span>
                    </h2>
                    <div class="form-inline" style="color: #999;">
                        <div class="form-item">
                            <span class="text-danger" style="position: absolute; top: 10px; left: 0px;">*</span>
                            <lable>姓名：</lable>
                            <input type="text" class="form-control mb-2 mr-sm-2" name="telephone" id="info_username" value="" placeholder="" aria-label="" style="margin-right: 15px !important;">
                            <lable>性别：</lable>
                            <div style="width: 165px; position: relative; overflow: hidden; box-sizing: border-box; display: flex; justify-content: left; align-items: center;">
                                <input class="form-check-input" type="radio" name="info_genderRadios" id="info_male" value="male" style="width: 30px;">
                                <label class="form-check-label" style="display: inline-block; width: auto; margin-right: 20px;">男</label>
                                <input class="form-check-input" type="radio" name="info_genderRadios" id="info_female" value="female" style="width: 30px;">
                                <label class="form-check-label" style="display: inline-block; width: auto;">女</label>
                            </div>
                        </div>
                        <div class="form-item">
                            <lable>邮箱：</lable>
                            <input type="text" class="form-control mb-2 mr-sm-2" name="email" id="info_email" value="" placeholder="" aria-label="" style="margin-right: 15px !important;">
                            <lable>电话：</lable>
                            <input type="text" class="form-control mb-2 mr-sm-2" name="telephone" id="info_telephone" value="" placeholder="" aria-label="">
                        </div>
                        <div class="form-item">
                            <lable>telegram：</lable>
                            <input type="text" class="form-control mb-2 mr-sm-2" name="telegram" id="info_telegram" value="" placeholder="" aria-label="" style="margin-right: 15px !important;">
                        </div>
                        <div class="form-item">
                            <lable>地址：</lable>
                            <input type="text" class="form-control mb-2 mr-sm-2" name="address" id="info_address" value="" placeholder="" aria-label="" style="margin-right: 0px !important; width: 330px !important;">
                        </div>
                        <div class="form-item">
                            <lable>说明：</lable>
                            <textarea class="form-control" placeholder="" rows="3" id="info_note" style="margin-right: 0px !important; width: 330px !important;"></textarea>
                        </div>

                    </div>
                </div>

            </div>        
'''

        html = update_language(self.language, html)
        return self.xtjson.json_result(message=html)

    # 上传文件
    async def uploadFile_func(self):
        request = Request.get_current()
        conversation_id = request.form.get('conversation_id')
        if not conversation_id:
            return self.xtjson.json_params_error()
        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
        if not conversation_data:
            return self.xtjson.json_params_error()
        site_code = conversation_data.get('site_code') or 'other_site'

        fileobj = request.files["upload"][0]
        if not fileobj:
            return self.xtjson.json_params_error()
        cont = fileobj.body
        lod_filename = fileobj.name
        size = len(cont)

        responsible_site = self.current_admin_dict.get('responsible_site')
        _crr_site_data = SiteTable.find_one({'site_code': responsible_site}) or {}
        site_code = _crr_site_data.get("site_code")
        site_data = SITE_DICT_CACHE.get(site_code)
        
        #control_file_size = site_data.get('control_file_size')
        control_file_size = DEFAULT_FILE_SIZE
        if 'control_file_size' in  site_data:
            control_file_size = site_data.get('control_file_size')

        if size > control_file_size:
            return self.xtjson.json_params_error('文件过大！')
        _size = round(size / 1024, 2)

        fname, fext = os.path.splitext(fileobj.name)
        relatively_path = f'/assets/upload/{site_code}/chatFile/files/' + datetime.datetime.now().strftime(
            '%Y%m%d') + '/'
        import_folder = self.project_static_folder + relatively_path
        if not os.path.exists(import_folder):
            os.makedirs(import_folder)

        new_filename = shortuuid.uuid()
        async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
            await f.write(request.files["upload"][0].body)

        filePath = relatively_path + new_filename + fext
        return self.xtjson.json_result(data={'filePath': filePath, 'lod_filename': lod_filename, 'size': _size})

    # 转接客户HTML
    def transferConversation_html(self):
        if not self.data_uuid:
            return self.xtjson.json_params_error('转接失败！')

        chatCon_data = ChatConversationTable.find_one({'uuid': self.data_uuid})
        if not chatCon_data:
            return self.xtjson.json_params_error('会话不存在！')

        suids = []
        udatas = CmsUserModel.find_many({'responsible_site': chatCon_data.get('site_code')})
        for u in udatas:
            suids.append(u.get('uuid'))

        tr_html = ''
        udatas = CmsUserModel.find_many({'uuid': {'$ne': self.current_admin_dict.get('uuid')}}) or []
        if not udatas:
            return self.xtjson.json_params_error('暂无可接收的客服！')

        for ud in udatas:
            if ud.get('uuid') not in SERVICE_CONNECTION:
                continue
            if ud.get('uuid') == self.current_admin_dict.get('uuid'):
                continue
            if ud.get('uuid') not in suids:
                continue
            tr_html += f'''
            <tr onclick="checkSelectService($(this))" style="cursor: pointer;">
                <td width="50">
                    <div class="form-check" style="display: flex; align-items: center; justify-content: center;">
                        <input class="form-check-input" type="radio" name="select_service_id" value="{ud.get('uuid')}" alt="" aria-label="">
                    </div>
                </td>
                <td style="text-align: left; padding-left: 35px;">
                    <img src="{ud.get('portrait') or '/assets/chat/images/keFuLogo.png'}" alt="" style="width: 35px;height: 35px; display: inline-block; border-radius: 100%; overflow: hidden; margin-right: 8px;">                        
                    <span>{ud.get('nickname') or ud.get('account') or ''}</span>
                </td>
            </tr>
            '''
        if not tr_html:
            return self.xtjson.json_params_error('暂无可接收的客服！')
        html = f'''
        <div style="height: 23rem; position: relative; box-sizing: border-box; overflow-y: auto; padding:20px 35px;">

            <table class="table table-bordered">
                {tr_html}
            </table>

        </div>      
        <div class="blank" style="background: #eeeeee; height: 1px; margin: 15px 0;"></div>

        <div style="position: relative; text-align: center; margin: 15px 0;">
            <span class="kfConfirmBtn" onclick="transferConversation('{self.data_uuid}')">确定</span>
            <span class="kfCancelBtn" onclick="xtalert.close()">取消</span>
        </div>            
        '''
        return self.xtjson.json_result(message=html)

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

    async def view_get(self, request):
        if not self.is_xhr():
            raise NotFound("404")
        action = request.args.get('action')
        if not action:
            return self.xtjson.json_params_error()
        if action == 'get_template_html':
            html = await self.get_chat_html_func()
            return self.xtjson.json_result(data={'html': html})
        return self.xtjson.json_params_error()

    async def post_other_way(self, request):
        if self.action == 'chack_Fileformat':
            return self.chack_Fileformat_func()
        if self.action == 'check_file_format':
            filename = self.request_data.get('filename')
            file_size = self.request_data.get('file_size')
            if not filename or not file_size:
                return self.xtjson.json_params_error()

            responsible_site = self.current_admin_dict.get('responsible_site')
            _crr_site_data = SiteTable.find_one({'site_code': responsible_site}) or {}
            site_code = _crr_site_data.get("site_code")
            site_data = SITE_DICT_CACHE.get(site_code)
            
            #control_file_size = site_data.get('control_file_size')
            control_file_size = DEFAULT_FILE_SIZE
            if 'control_file_size' in  site_data:
                control_file_size = site_data.get('control_file_size')
                #control_file_size = getattr(SITE_CONFIG_CACHE, 'control_file_size')
            

            if float(file_size) > control_file_size:
                return self.xtjson.json_params_error('文件过大！')

            return self.xtjson.json_result()
        if self.action == 'getPrevConversation':
            return self.getPrevConversation()
        if self.action == 'chatUploadImage':
            request = Request.get_current()
            fileobj = request.files.get('upload')
            conversation_id = request.form.get('conversation_id')
            if not conversation_id or not fileobj:
                return self.xtjson.json_params_error()
            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            if not conversation_data:
                return self.xtjson.json_params_error()
            site_code = conversation_data.get('site_code') or 'other_site'

            
            import_folder = os.path.join("static", Sanic.get_app().config.get('PROJECT_NAME')) + '/public/c_upload/images/'
            if not os.path.exists(import_folder):
                os.makedirs(import_folder)

            fname, fext = os.path.splitext(request.files["upload"][0].name)
            relatively_path = f'/assets/upload/{site_code}/chatFile/images/' + datetime.datetime.now().strftime('%Y%m%d') + '/'
            import_folder = 'static/'+ Sanic.get_app().config.get('PROJECT_NAME') + relatively_path
            if not os.path.exists(import_folder):
                os.makedirs(import_folder)

            new_filename = shortuuid.uuid()
            async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                await f.write(request.files["upload"][0].body)

            filePath = relatively_path + new_filename + fext
            return self.xtjson.json_result(message=filePath)
        

        if self.action == 'uploadFile':
            return await self.uploadFile_func()
        if self.action == 'add_heimingdan_data':
            return self.add_heimingdan_data_func()
        if self.action == 'translateText':
            return self.translateText_func()
        if self.action == 'get_sideInfo_html':
            return self.get_sideInfo_html()
        if self.action == 'transferConversation_html':
            return self.transferConversation_html()
        if self.action == 'get_heimingdan_html':
            return self.get_heimingdan_html()

