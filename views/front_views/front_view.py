# -*- coding: utf-8 -*-
import datetime, os, shortuuid
import aiofiles
from sanic import request, Sanic, views
from sanic.response import html, redirect
from sanic.exceptions import NotFound
from sanic_session import Session, InMemorySessionInterface
from . import bp
from modules.view_helpres.tool_func import front_risk_control
from constants import IMAGES_TYPES, ASSETS_FOLDER, SITE_DICT_CACHE, LANGUAGE_JSON, LANGUAGE, VIDEO_TYPES
from common_utils import xtjson
from models.site_table import SiteTable
from modules.api_module.chat_tools import ChatFuncTools
from models.kefu_table import CustomerTable, ChatConversationTable
from common_utils.tools.cls_pictures import PicturesCLS
from common_utils.utils_funcs import graph_captcha, stream_template_string
from common_utils import xtjson



# @bp.before_request
# def site_before_request():
#     statu, res = front_risk_control()
#     if not statu:
#         return res



class FrontIndex(views.HTTPMethodView):
    add_url_rules = [['/', 'front_index']]

    def get(self, request):
        if 'sodochat.xyz' in request.url or 'easychat.one' in request.url:
            return redirect('https://www.easychat24.com')
        return redirect('https://www.easychat24.com')



class FrontChatView(views.HTTPMethodView):
    add_url_rules = [["/chat/<site_code_str>", 'chat_text']]

    def format_list(self, data):
        try:
            if isinstance(data, list):
                return ','.join(data)
            return data
        except:
            return data

    def get_conrl_types(self, site_code):

        fileSize = 10 * 1024 * 1024
        site_data = SITE_DICT_CACHE.get(site_code)
        if not site_data:
            return '', [], fileSize

        control_file_type_state = site_data.get('control_file_type_state')
        if not control_file_type_state:
            return '', [], fileSize

        control_file_size = site_data.get('control_file_size')
        if control_file_size:
            try:
                fileSize = int(control_file_size)
            except:
                pass

        control_file_types = site_data.get('control_file_types')
        if not control_file_types:
            return '', [], fileSize

        image_types = []
        for t in control_file_types:
            if t in IMAGES_TYPES:
                image_types.append(t)

        video_types = []
        for v in control_file_types:
            if v in VIDEO_TYPES:
                video_types.append(v)

        return image_types, video_types, fileSize

    def chack_domain(self, site_code_dd):
        site_data = SITE_DICT_CACHE.get(site_code_dd)
        if not site_data:
            raise NotFound("404")
        use_domain = site_data.get('use_domain') or Sanic.get_app().config.get('MAIN_DOMAIN')
        if use_domain not in request.host:
            raise NotFound("404")

    async def get(self, request, site_code_str):
        # if site_code == 'chat_S4NQBW':
        #     raise NotFound("404")
        # if site_code == 'chat_S4000W':
        #     site_code = 'chat_S4NQBW'
        # res = self.chack_domain(site_code)
        # if res:
        #     return res
        site_code, extension = site_code_str.split('.')
        if extension == 'html':
            context = {}
            context['site_code'] = site_code
    #        context['img_cap'] = graph_captcha()
            context['format_list'] = self.format_list

            image_types, video_types, fileSize = self.get_conrl_types(site_code)
            typeStr = ''
            if image_types:
                typeStr += ',' + ','.join(image_types)
            if video_types:
                typeStr += ',' + ','.join(video_types)
            typeStr = typeStr.strip(',')
            context['typeStr'] = typeStr

            site_data = SITE_DICT_CACHE.get(site_code)
            if not site_data:
                raise NotFound("404")

            context['default_comment'] = site_data.get('default_comment') or ''
            base_template_path = 'templates' + '/front/chat.html'
            base_template_str = open(base_template_path, 'r', encoding='utf8').read()

            base_template_str = base_template_str.replace('{#image_types#}', str(image_types or IMAGES_TYPES))
            base_template_str = base_template_str.replace('{#file_size#}', str(fileSize))
            base_template_str = base_template_str.replace('{#video_types#}', str(video_types or VIDEO_TYPES))
            if site_data.get('fast_state'):
                fastState_text = 'true'
            else:
                fastState_text = 'false'
            base_template_str = base_template_str.replace('{#fastState#}', fastState_text)

            if site_data.get('site_language') == LANGUAGE.en_US:
                for la in LANGUAGE_JSON:
                    base_template_str = base_template_str.replace(la.get('zh'), la.get('en'))
                base_template_str = base_template_str.replace('/public/chat/js/app.js', '/public/chat/js/app.js?language=en_US')
                base_template_str = base_template_str.replace('/public/chat/js/pickerDate.js', '/public/chat/js/pickerDate.js?language=en_US')
            elif site_data.get('site_language') == LANGUAGE.vi_VN:
                for la in LANGUAGE_JSON:
                    base_template_str = base_template_str.replace(la.get('zh'), la.get('vi'))
                base_template_str = base_template_str.replace('/public/chat/js/app.js', '/public/chat/js/app.js?language=vi_VN')
                base_template_str = base_template_str.replace('/public/chat/js/pickerDate.js', '/public/chat/js/pickerDate.js?language=vi_VN')
            elif site_data.get('site_language') == LANGUAGE.ba_IDN:
                for la in LANGUAGE_JSON:
                    base_template_str = base_template_str.replace(la.get('zh'), la.get('idn'))
                base_template_str = base_template_str.replace('/public/chat/js/app.js', '/public/chat/js/app.js?language=ba_IDN')
                base_template_str = base_template_str.replace('/public/chat/js/pickerDate.js', '/public/chat/js/pickerDate.js?language=ba_IDN')
            elif site_data.get('site_language') == LANGUAGE.bx_Pr:
                for la in LANGUAGE_JSON:
                    base_template_str = base_template_str.replace(la.get('zh'), la.get('Pt'))
                base_template_str = base_template_str.replace('/public/chat/js/app.js', '/public/chat/js/app.js?language=bx_Pr')
                base_template_str = base_template_str.replace('/public/chat/js/pickerDate.js', '/public/chat/js/pickerDate.js?language=bx_Pr')
            elif site_data.get('site_language') == LANGUAGE.ja:
                for la in LANGUAGE_JSON:
                    base_template_str = base_template_str.replace(la.get('zh'), la.get('ja'))
                base_template_str = base_template_str.replace('/public/chat/js/app.js', '/public/chat/js/app.js?language=ja')
                base_template_str = base_template_str.replace('/public/chat/js/pickerDate.js', '/public/chat/js/pickerDate.js?language=ja')
            elif site_data.get('site_language') == LANGUAGE.ko:
                for la in LANGUAGE_JSON:
                    base_template_str = base_template_str.replace(la.get('zh'), la.get('ko'))
                base_template_str = base_template_str.replace('/public/chat/js/app.js', '/public/chat/js/app.js?language=ko')
                base_template_str = base_template_str.replace('/public/chat/js/pickerDate.js', '/public/chat/js/pickerDate.js?language=ko')
            
            html_str = await stream_template_string(base_template_str, context)
            return html(html_str)
        
        elif extension == 'js':
            res = self.chack_domain(site_code)
            if res:
                return res
            site_data = SITE_DICT_CACHE.get(site_code)

            project_static_file = os.path.join(Sanic.get_app().static_folder, 'easychat', ASSETS_FOLDER, 'js/chatJs.js')
            if os.path.exists(project_static_file):
                df = open(project_static_file, 'r').read()
                df = df.replace('{#site_code#}', site_code)
                df = df.replace('{#domain#}', site_data.get('use_domain'))
                res = make_response(df)
                res.headers['Content-Type'] = 'text/plain; charset=utf-8'
                return res

            return abort(403)
        else:
            raise NotFound("404")

    async def post(self, request, site_code_str):
        site_code, extension = site_code_str.split('.')

        if extension == 'html':
            action = request.form.get('action')
            chatUsid = request.form.get('chatUsid')
            chatSession = request.form.get('chatSession')
            filename = request.form.get('filename')
            filesize = request.form.get('filesize')
            if action == 'chatUploadImage':
                if not chatUsid or not chatSession or not filename or not filesize:
                    return xtjson.json_params_error('上传失败！')

                fts = filename.rsplit('.', 1)
                if not fts:
                    return xtjson.json_params_error('上传失败！')

                ft = str('.' + fts[-1]).lower()
                if ft not in IMAGES_TYPES:
                    return xtjson.json_params_error('上传失败！')

                crr_site_data = SiteTable.find_one({'site_code': site_code}) or {}
                if not crr_site_data:
                    return xtjson.json_params_error('上传失败！')

                control_file_type_state = crr_site_data.get('control_file_type_state')
                control_file_size = crr_site_data.get('control_file_size') or 10
                control_file_types = crr_site_data.get('control_file_types') or []

                try:
                    if int(filesize) > control_file_size * 1024 * 1024:
                        return xtjson.json_params_error('文件过大，上传失败！')
                except:
                    pass

                if control_file_types and control_file_type_state:
                    if ft not in control_file_types:
                        return xtjson.json_params_error('文件格式不支持，上传失败！')

                customer_id = ChatFuncTools.analysis_chatCache(chatUsid)
                conversation_id = ChatFuncTools.analysis_chatCache(chatSession)
                if not CustomerTable.find_one({'uuid': customer_id}):
                    return xtjson.json_params_error()
                if not ChatConversationTable.find_one({'uuid': conversation_id}):
                    return xtjson.json_params_error()

                fname, fext = os.path.splitext(request.files["upload"][0].name)
                import_folder = os.path.join("static", Sanic.get_app().config.get('PROJECT_NAME')) + '/public/c_upload/images/'
                if not os.path.exists(import_folder):
                    os.makedirs(import_folder)

                new_filename = shortuuid.uuid()
                async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                    await f.write(request.files["upload"][0].body)

                PicturesCLS.compress_image(import_folder + new_filename + fext)
                filePath = '/public/c_upload/images/' + new_filename + fext
                return xtjson.json_result(message=filePath)
            if action == 'chatUploadVideo':
                if not chatUsid or not chatSession or not filename or not filesize:
                    return xtjson.json_params_error('上传失败1！')

                fts = filename.rsplit('.', 1)
                if not fts:
                    return xtjson.json_params_error('上传失败2！')

                ft = str('.' + fts[-1]).lower()
                if ft not in VIDEO_TYPES:
                    return xtjson.json_params_error('上传失败3！')

                crr_site_data = SiteTable.find_one({'site_code': site_code}) or {}
                if not crr_site_data:
                    return xtjson.json_params_error('上传失败4！')

                control_file_type_state = crr_site_data.get('control_file_type_state')
                control_file_size = crr_site_data.get('control_file_size') or 10
                control_file_types = crr_site_data.get('control_file_types') or []

                try:
                    if int(filesize) > control_file_size * 1024 * 1024:
                        return xtjson.json_params_error('文件过大，上传失败！')
                except:
                    pass

                if control_file_types and control_file_type_state:
                    if ft not in control_file_types:
                        return xtjson.json_params_error('文件格式不支持，上传失败！')

                customer_id = ChatFuncTools.analysis_chatCache(chatUsid)
                conversation_id = ChatFuncTools.analysis_chatCache(chatSession)
                if not CustomerTable.find_one({'uuid': customer_id}):
                    return xtjson.json_params_error()
                if not ChatConversationTable.find_one({'uuid': conversation_id}):
                    return xtjson.json_params_error()
                
                fname, fext = os.path.splitext(request.files["upload"][0].name)
                import_folder = os.path.join("static", Sanic.get_app().config.get('PROJECT_NAME')) + '/public/c_upload/video/'
                if not os.path.exists(import_folder):
                    os.makedirs(import_folder)

                new_filename = shortuuid.uuid()
                async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                    await f.write(request.files["upload"][0].body)

                filePath = '/public/c_upload/video/' + new_filename + fext


                return xtjson.json_result(message=filePath)

            if action == 'uploadImage':
                fts = filename.rsplit('.', 1)
                if not fts:
                    return xtjson.json_params_error('上传失败！')

                ft = str('.' + fts[-1]).lower()
                if ft not in IMAGES_TYPES:
                    return xtjson.json_params_error('上传失败！')

                crr_site_data = SiteTable.find_one({'site_code': site_code}) or {}
                if not crr_site_data:
                    return xtjson.json_params_error('上传失败！')

                try:
                    if int(filesize) > 10 * 1024 * 1024:
                        return xtjson.json_params_error('文件过大，上传失败！')
                except:
                    pass

                if ft not in IMAGES_TYPES:
                    return xtjson.json_params_error('文件格式不支持，上传失败！')

                fname, fext = os.path.splitext(request.files["upload"][0].name)
                import_folder = os.path.join("static", Sanic.get_app().config.get('PROJECT_NAME')) + '/public/c_upload/images/'
                if not os.path.exists(import_folder):
                    os.makedirs(import_folder)

                new_filename = shortuuid.uuid()
                async with aiofiles.open(import_folder + new_filename + fext, 'wb') as f:
                    await f.write(request.files["upload"][0].body)

                PicturesCLS.compress_image(import_folder + new_filename + fext)
                filePath = '/public/c_upload/images/' + new_filename + fext

                return xtjson.json_result(message=filePath)
        else:
            return xtjson.json_params_error("Error")


# class ChatJsView(views.HTTPMethodView):
#     add_url_rules = [[r"/chat/(?P<site_code>.+)\.js", 'chat_js']]

#     def chack_domain(self, site_code):
#         site_data = SITE_DICT_CACHE.get(site_code)
#         if not site_data:
#             raise NotFound("404")
#         use_domain = site_data.get('use_domain') or Sanic.get_app().config.get('MAIN_DOMAIN')
#         if use_domain not in request.host:
#             raise NotFound("404")

#     def get(self, site_code):
#         res = self.chack_domain(site_code)
#         if res:
#             return res
#         site_data = SITE_DICT_CACHE.get(site_code)

#         project_static_file = os.path.join(Sanic.get_app().static_folder, 'easychat', ASSETS_FOLDER, 'js/chatJs.js')
#         if os.path.exists(project_static_file):
#             df = open(project_static_file, 'r').read()
#             df = df.replace('{#site_code#}', site_code)
#             df = df.replace('{#domain#}', site_data.get('use_domain'))
#             res = make_response(df)
#             res.headers['Content-Type'] = 'text/plain; charset=utf-8'
#             return res

#         return abort(403)



class winChatView(views.HTTPMethodView):
    add_url_rules = [['/chat/<site_code>/winChat.html', 'winChat']]

    def chack_domain(self, site_code):
        site_data = SITE_DICT_CACHE.get(site_code)
        if not site_data:
            raise NotFound("404")
        use_domain = site_data.get('use_domain') or Sanic.get_app().config.get('MAIN_DOMAIN')
        if use_domain not in request.host:
            raise NotFound("404")

    def get_conrl_imges_types(self, site_code):
        data = []
        site_data = SITE_DICT_CACHE.get(site_code)
        if not site_data:
            return ''

        control_file_type_state = site_data.get('control_file_type_state')
        if not control_file_type_state:
            return ''
        control_file_types = site_data.get('control_file_types')
        if not control_file_types:
            return ''
        for t in control_file_types:
            if t in IMAGES_TYPES:
                data.append(t)
        if data:
            return ','.join(data)
        return ''

    def get(self, site_code):
        res = self.chack_domain(site_code)
        if res:
            return res
        context = {
            'site_code': site_code,
        }
        context['kz_image_types'] = self.get_conrl_imges_types(site_code)
        context['crrtime'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')
        return render_template('front/winChat.html', context)

    def post(self, site_code):
        action = request.form.get('action')
        if action == 'chatUploadImage':
            fileobj = request.files['upload']
            fname, fext = os.path.splitext(fileobj.filename)
            import_folder = '/' + 'static/'+ Sanic.get_app().config.get('PROJECT_NAME') + '/assets/upload/images/'
            if not os.path.exists(import_folder):
                os.makedirs(import_folder)

            new_filename = shortuuid.uuid()
            fileobj.save(import_folder + new_filename + fext)
            filePath = '/assets/upload/images/' + new_filename + fext
            return xtjson.json_result(message=filePath)



class acquireBackupView(views.HTTPMethodView):
    add_url_rules = [['/acquireBackup', 'acquireBackupView']]
    
    def get(self, request):
        action = request.args.get('action')
        token = request.args.get('token')
        datel = request.args.get('datel')
        if action == 'acquireBackup':
            if token != 'ASDzxcqwe~!@#123456789' or not datel or not datel.strip():
                raise NotFound("404")
            project_static_file = Sanic.get_app().static_folder + '/' + Sanic.get_app().config.get('PROJECT_NAME') + '/assets/backup/' + datel + '.zip'
            if not os.path.exists(project_static_file):
                raise NotFound("404")
            return make_response(send_file(project_static_file))

