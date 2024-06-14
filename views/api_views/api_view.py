# -*- coding: utf-8 -*-
import datetime, time

import shortuuid
from sanic.request import Request

from site_exts import socketio
from models.cms_user import CmsUserModel
from models.site_table import SiteTable
from models.kefu_table import CustomerTable, ChatConversationTable, ChatContentTable, LeavingMessageTable, BlacklistTable, FinishListTable, IpTable, problemTable, categoryTable, systemLogTable, CacheDataTable
from constants import ConversationStatu, CLIENT_CONNECTION, SERVICE_CONNECTION, SITE_DICT_CACHE, SITE_CONFIG_CACHE, ContentTypes, OnlineStatu, IMAGES_TYPES, FIEL_TYPES, AUDIO_TYPES, VIDEO_TYPES, PermissionCls, OPERATION_TYPES, CMS_USER_SESSION_KEY, LANGUAGE, translateStatu, CHAT_NAMESPACE_CONNECTIONS, SERVICECHAT_NAMESPACE_CONNECTIONS
from modules.api_module.chat_tools import ChatFuncTools, xtjsonCls, emit, disconnect
from common_utils.utils_funcs import get_ip, get_all_ip, convertTextFunc
from modules.view_helpres.view_func import disconnect_func
from modules.goole_translate import translate_text_func
from common_utils.lqredis import SiteRedis
from site_exts import mc


class RedisLock:
    def __init__(self, lock_key, lock_timeout=20):
        self.redis = mc
        self.lock_key = lock_key
        self.lock_timeout = lock_timeout

    def acquire_lock(self):
        if self.redis.setnx(self.lock_key, 1):
            self.redis.expire(self.lock_key, self.lock_timeout)
            return True
        return False

    def release_lock(self):
        # 锁仍然存在，执行删除操作
        self.redis.delete(self.lock_key)
        return True


def send_text_limit():
    return
    REMOTE_ADDR = get_ip()
    ip = str(REMOTE_ADDR or '').split(',')[0]
    if not ip:
        return
    key = 'KF_S_SEND_TEXT_%s' % ip
    _crr_num = SiteRedis.get(key)
    if not _crr_num:
        SiteRedis.set(key, 1, expire=60)
    else:
        if int(_crr_num.decode()) >= 40:
            return True
        SiteRedis.incrby(key, 1)
        SiteRedis.expire(key, 60)
    return

def send_liuyan_limit():
    return
    REMOTE_ADDR = get_ip()
    ip = str(REMOTE_ADDR or '').split(',')[0]
    if not ip:
        return
    key = 'KF_S_SEND_LIUYAN_%s' % ip
    _crr_num = SiteRedis.get(key)
    if not _crr_num:
        SiteRedis.set(key, 1, expire=600)
    else:
        if int(_crr_num.decode()) >= 2:
            return True
        SiteRedis.incrby(key, 1)
        SiteRedis.expire(key, 600)
    return

def send_IMG_limit():
    return
    REMOTE_ADDR = get_ip()
    ip = str(REMOTE_ADDR or '').split(',')[0]
    if not ip:
        return
    key = 'KF_S_SEND_IMG_%s' % ip
    _crr_num = SiteRedis.get(key)
    if not _crr_num:
        SiteRedis.set(key, 1, expire=600)
    else:
        if int(_crr_num.decode()) >= 15:
            return True
        SiteRedis.incrby(key, 1)
        SiteRedis.expire(key, 600)
    return

def send_fileS_limit():
    return
    REMOTE_ADDR = get_ip()
    ip = str(REMOTE_ADDR or '').split(',')[0]
    if not ip:
        return
    key = 'KF_S_SEND_FILE_%s' % ip
    _crr_num = SiteRedis.get(key)
    if not _crr_num:
        SiteRedis.set(key, 1, expire=600)
    else:
        if int(_crr_num.decode()) >= 4:
            return True
        SiteRedis.incrby(key, 1)
        SiteRedis.expire(key, 600)
    return


class ChatSocketIOCls():

    # 开启连接
    def on_connect(self, request):
        print('Client server is connected:', request.ctx.session.sid)

    # 断开连接
    async def on_disconnect(self, request):
        crr_sid = str(request.ctx.session.sid)
        if str(crr_sid) in CLIENT_CONNECTION:
            customer_data = CLIENT_CONNECTION.get(crr_sid)
            CLIENT_CONNECTION.pop(crr_sid)

            disconnect_tiem = datetime.datetime.now()
            conversation_data = ChatConversationTable.find_one({'uuid': customer_data.get('conversation_id')})
            if conversation_data.get('statu') == ConversationStatu.normal:
                conversation_data.update({
                    'statu': ConversationStatu.waiting,
                    'disconnect_tiem': disconnect_tiem,
                })
                ChatConversationTable.save(conversation_data)

            service_dd = SERVICE_CONNECTION.get(customer_data.get('service_id'))
            if service_dd:
                present_count = ChatFuncTools.get_service_sid_present_count(service_dd.get('sid'))
                _d = {
                    'onlineTotal': len(CLIENT_CONNECTION), 'onlinePresent': present_count,
                    'connectionState': '0', 'conversation_id': customer_data.get('conversation_id'),
                    'disconnect_tiem':disconnect_tiem.strftime('%m-%d %H:%M'),
                    'crr_service_id': conversation_data.get('service_id'),
                }
                await emit('chatCtnOnlineCount', _d, namespace='/serviceChat', broadcast=True)

        print('Client disconnected:', request.ctx.session.sid)

    # 访客信息初始化
    async def on_initVisitor(self, request, data):
        '''
        chatUid 访客id
        chatSession 会话id
        '''
        sid = ''
        if request.ctx.session.sid:
            sid = request.ctx.session.sid

        if not isinstance(data, dict):
            return
        site_code = data.get('site_code')
        chatSession = data.get('chatSession')
        chatUsid = data.get('chatUsid')

        if site_code == 'chat_S4NQBW':
            return
        if site_code == 'chat_S4000W':
            site_code = 'chat_S4NQBW'

        problem = data.get('problem')
        account = data.get('account')
        txTme = data.get('txTme')
        czTime = data.get('czTime')
        cjhdText = data.get('cjhdText')
        problemImage = data.get('problemImage')

        user_agent = request.headers.get('User-Agent')
        if user_agent:
            config_data = ChatFuncTools.check_client(user_agent)
        else:
            config_data = {}

        customer_id = ''
        if chatUsid and len(chatUsid) == 26:
            _d = CustomerTable.find_one({'uuid': chatUsid[4:]}) or {}
            if _d:
                customer_id = chatUsid[4:]

        site_data = SiteTable.find_one({'site_code': site_code}) or {}
        if not site_data:
            return

        _site_data = {}
        _site_data['site_icon'] = site_data.get('site_icon') or ''
        _site_data['site_title'] = site_data.get('site_title') or ''
        _site_data['site_main_color'] = site_data.get('site_main_color') or ''
        _site_data['site_announcement'] = site_data.get('site_announcement') or ''
        _site_data['site_right_info_img'] = site_data.get('site_right_info_img') or ''
        _site_data['site_right_info_back_color'] = site_data.get('site_right_info_back_color') or ''

        track = ''
        REMOTE_ADDR = get_ip()
        crrip = str(REMOTE_ADDR or '').split(',')[0]
        ip_data = IpTable.find_one({'ip': crrip})
        if not ip_data:
            ip_info_json = ChatFuncTools.getIpAddr(crrip) or {}
            if ip_info_json:
                country_name = ip_info_json.get('country_name') or ''
                region_name = ip_info_json.get('region_name') or ''
                city_name = ip_info_json.get('city_name') or ''
                track = f'{country_name}-{region_name}-{city_name}'
                _ipdata = {
                    'ip': ip_info_json.get('ip'),
                    'country_name': ip_info_json.get('country_name'),
                    'region_name': ip_info_json.get('region_name') or '',
                    'city_name': ip_info_json.get('city_name') or '',
                    'latitude': ip_info_json.get('latitude') or '',
                    'longitude': ip_info_json.get('longitude') or '',
                    'time_zone': ip_info_json.get('time_zone') or '',
                }
                IpTable.insert_one(_ipdata)
        else:
            country_name = ip_data.get('country_name') or ''
            region_name = ip_data.get('region_name') or ''
            city_name = ip_data.get('city_name') or ''
            track = f'{country_name}-{region_name}-{city_name}'

        if not customer_id:
            customer_data = {
                "name": ChatFuncTools.getCustomerCode(),
                "site_code": site_code,
                'ip': crrip or '',
                'track': track,
            }
            customer_id = CustomerTable.insert_one(customer_data)

        Blacklist_data = BlacklistTable.find_one({'customer_id': customer_id})
        if Blacklist_data:
            if Blacklist_data.get('expire_time') > datetime.datetime.now():
                return await emit('initResponse', xtjsonCls.json_params_error(), room=sid, namespace='/chat')

        conversation_id, crr_service = '', ''
        if chatSession and len(chatSession) == 26:
            _cd = ChatConversationTable.find_one({'uuid': chatSession[4:]}) or {}
            if _cd and _cd.get('statu') in [ConversationStatu.normal, ConversationStatu.waiting]:
                crr_service = CmsUserModel.find_one({'uuid': _cd.get('service_id')})
                if crr_service:
                    conversation_id = chatSession[4:]
                    ChatConversationTable.update_one({'uuid': conversation_id}, {'$set': {'disconnect_tiem': '', 'statu': ConversationStatu.normal, 'start_time': datetime.datetime.now()}})

        if not conversation_id:
            crr_service = ChatFuncTools.planning_service(site_code)
            if not crr_service:
                back_data = {
                    'chatUsid': 'chat' + customer_id,
                    'service_state': False,
                    '_site_data': _site_data,
                    'problems': []
                }
                return await emit('initResponse', xtjsonCls.json_result(data=back_data), room=sid, namespace='/chat')

            _DATA = {
                'browser_type': config_data.get('browser_type') or '',
                'client_type': config_data.get('clientType') or '',
                'os_type': config_data.get('os_type') or '',
                'start_time': datetime.datetime.utcnow(),
                'service_id': crr_service.get('uuid'),
                'site_code': site_code,
                'ip': crrip,
                'track': track,
                'customer_id': customer_id,
                'sid': sid,
                'statu': ConversationStatu.normal,
                'score_level': 5,
                'score_text': '',
            }
            try:
                _DATA['zs_ip'] = get_all_ip()
            except:
                pass
            conversation_id = ChatConversationTable.insert_one(_DATA)

        _fd = {
            'service_id': crr_service.get('uuid'),
            'customer_id': customer_id,
        }
        FinishListTable.delete_one(_fd)

        back_data = {
            'chatUsid': 'chat' + customer_id,
            'chatSession': 'chat'+conversation_id,
            'service_state': True,
            'service_data': {
                'service_name': crr_service.get('nickname') or '',
                'portrait': crr_service.get('portrait') or '',
            },
            'is_score': False
        }

        CLIENT_CONNECTION.update({
            sid: {
                'service_sid': (SERVICE_CONNECTION.get(crr_service.get('uuid')) or {}).get('sid'),
                'service_id': crr_service.get('uuid'),
                'conversation_id': conversation_id,
                'customer_id': customer_id,
            },
        })


        if not ChatContentTable.count({'conversation_id': conversation_id, 'is_retract': False}):
            ChatContentTable.insert_one({
                'text': site_data.get('clew_text') or '请输入，您的问题？',
                'service_id': crr_service.get('uuid'),
                'conversation_id': conversation_id,
                'customer_reading_state': False,
                'content_type': ContentTypes.TEXT,
                'is_retract': False,
                'site_code': site_code,
                'is_clew_text': True,
            })
            if site_data.get('fast_state'):
                if problem == 'czwt' and account and czTime and problemImage:
                    ChatContentTable.insert_one({
                        'text': f'【充值问题】，账户：{account}，充值时间：{czTime}',
                        'customer_id': customer_id,
                        'conversation_id': conversation_id,
                        'service_reading_state': False,
                        'content_type': ContentTypes.TEXT,
                        'is_retract': False,
                        'site_code': site_code,
                    })
                    ChatContentTable.insert_one({
                        'text': '',
                        'customer_id': customer_id,
                        'conversation_id': conversation_id,
                        'service_reading_state': False,
                        'content_type': ContentTypes.PICTURE,
                        'file_path': problemImage,
                        'is_retract': False,
                        'site_code': site_code,
                    })
                if problem == 'txwt' and account and txTme and problemImage:
                    ChatContentTable.insert_one({
                        'text': f'【提现问题】，账户：{account}，提现时间：{txTme}',
                        'customer_id': customer_id,
                        'conversation_id': conversation_id,
                        'service_reading_state': False,
                        'content_type': ContentTypes.TEXT,
                        'is_retract': False,
                        'site_code': site_code,
                    })
                    ChatContentTable.insert_one({
                        'text': '',
                        'customer_id': customer_id,
                        'conversation_id': conversation_id,
                        'service_reading_state': False,
                        'content_type': ContentTypes.PICTURE,
                        'file_path': problemImage,
                        'is_retract': False,
                        'site_code': site_code,
                    })
                if problem == 'cjsq' and account and cjhdText:
                    ChatContentTable.insert_one({
                        'text': f'【彩金申请】，账户：{account}',
                        'customer_id': customer_id,
                        'conversation_id': conversation_id,
                        'service_reading_state': False,
                        'content_type': ContentTypes.TEXT,
                        'is_retract': False,
                        'site_code': site_code,
                    })
                    ChatContentTable.insert_one({
                        'text': f'参数活动内容：{cjhdText}',
                        'customer_id': customer_id,
                        'conversation_id': conversation_id,
                        'service_reading_state': False,
                        'content_type': ContentTypes.TEXT,
                        'is_retract': False,
                        'site_code': site_code,
                    })


        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id}) or {}
        if conversation_data:
            score_text = conversation_data.get('score_text')
            score_level = conversation_data.get('score_level')
            if score_level is not None and score_text is not None and score_text and score_level:
                back_data['is_score'] = True

        site_language = site_data.get('site_language') or 'en'
        translate_statu = site_data.get('translate_statu')
        client_language = site_data.get('client_language') or site_language
        service_language = site_data.get('service_language')
        client_service_language = site_data.get('client_service_language') or ''
        client_language_code = LANGUAGE.lang_code.get(client_language) or 'en'
        service_language_code = LANGUAGE.lang_code.get(service_language) or 'en'
        client_service_language_code = LANGUAGE.lang_code.get(client_service_language) or 'en'
        target_key = client_service_language + '_text'
        
        datas = ChatContentTable.find_many({'conversation_id': conversation_id, 'is_retract': False, 'is_transfer_text':{'$exists': False}}, sort=[['create_time', 1]])
        _results = []
        for data in datas:
            text = data.get('text') or ''
            target_text = data.get(target_key) or ''
            _ddd = {
                'text': ChatFuncTools.add_link_a(text),
                'is_service': True if data.get('service_id') else False,
                'is_customer': True if data.get('customer_id') else False,
                'create_time': data.get('create_time').strftime('%m-%d %H:%M'),
                'file_path': data.get('file_path'),
                'content_type': data.get('content_type'),
                'filename': data.get('filename'),
                'file_size': data.get('file_size'),
                'dataId': data.get('uuid'),
            }
            if translate_statu and _ddd.get('is_service') and translate_statu in [translateStatu.TFBS, translateStatu.TSCS] and service_language and client_service_language:
                if not target_text:
                    try:
                        _new_mag_text = translate_text_func(text, source_language=service_language_code, target_language=client_service_language_code)
                    except:
                        _new_mag_text = ''
                    if _new_mag_text:
                        ChatContentTable.update_one({'uuid': data.get('uuid')}, {'$set': {target_key: _new_mag_text}})
                        _ddd['text'] = ChatFuncTools.add_link_a(_new_mag_text)
                else:
                    _ddd['text'] = ChatFuncTools.add_link_a(target_text)

            _results.append(_ddd)
        back_data['messageList'] = _results

        CLIENT_DATA = CLIENT_CONNECTION.get(request.ctx.session.sid) or {}
        service_id = CLIENT_DATA.get('service_id')
        service_sid = CLIENT_DATA.get('service_sid')
        if service_sid and service_id:
            new_data = {
                'uuid': conversation_id,
                'service_id': service_id,
            }

            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            start_time = conversation_data.get('start_time')
            new_data['start_time'] = start_time.strftime('%m-%d %H:%M')
            for k in ['end_time', 'waiting_time', 'create_time', '_id', '_create_time', 'start_time']:
                try:
                    conversation_data.pop(k)
                except:
                    pass
            new_data.update(conversation_data)

            _customer_data = CustomerTable.find_one({'uuid': new_data.get('customer_id')}) or {}
            if _customer_data:
                new_data['customer_name'] = _customer_data.get('username') or _customer_data.get('name') or ''
                new_data['site_name'] = SITE_DICT_CACHE.get(new_data.get('site_code')).get('site_name') or ''

                wdCount = ChatContentTable.count({'conversation_id': conversation_id, 'service_reading_state': False, 'is_retract': False}) or 0
                new_data['wdCount'] = wdCount
                await emit('chatNewConversation', new_data, namespace='/serviceChat', broadcast=True)

            # 实时更新在线人数
            present_count = ChatFuncTools.get_service_sid_present_count(service_sid)
            _rdd = {
                'onlineTotal': len(CLIENT_CONNECTION), 'onlinePresent': present_count, 'connectionState': '1',
                'start_time': start_time.strftime('%m-%d %H:%M'), 'conversation_id': conversation_id,
                'crr_service_id': service_id,
            }
            await emit('chatCtnOnlineCount', _rdd, namespace='/serviceChat', broadcast=True)

        back_data['site_data'] = _site_data

        pdatas = problemTable.find_many({'site_code': site_code}) or []
        autoProblems = []

        for problem in pdatas:
            autoProblems.append({
                'uuid': problem.get("uuid"),
                'title': problem.get("title")
            })

        back_data['problems'] = autoProblems


        return await emit('initResponse', xtjsonCls.json_result(data=back_data), room=sid, namespace='/chat')

    # 留言处理
    async def on_leaveMessage(self, request, msg):
        if not isinstance(msg, dict):
            return
        if send_liuyan_limit():
            return
        REMOTE_ADDR = get_ip()
        crrip = str(REMOTE_ADDR or '').split(',')[0]
        action = msg.get('action')
        if action == 'subLeaveMessage':
            username = msg.get('username')
            telephone = msg.get('telephone')
            email = msg.get('email')
            note = msg.get('note')
            customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
            site_code = msg.get('site_code')
            _data = {
                'text': convertTextFunc(note or ''),
                'customer_id': customer_id or '',
                'telephone': convertTextFunc(telephone or ''),
                'email': convertTextFunc(email) or '',
                'username': convertTextFunc(username) or '',
                'site_code': site_code or '',
                'ip': crrip,
                'statu': False,
            }
            LeavingMessageTable.insert_one(_data)
            leavingCount = LeavingMessageTable.count({'statu': False, 'site_code': site_code}) or 0
            return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'update_leavingCount', 'leavingCount': leavingCount, 'site_code': site_code}), namespace='/serviceChat', broadcast=True)

    # 接收信息
    async def on_chatReceiveMessage(self, request, msg):
        if not isinstance(msg, dict):
            return
        if send_text_limit():
            return
        type = msg.get('type')
        if not type or type not in  ContentTypes.name_arr:
            return

        customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
        conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
        if not customer_id or not conversation_id:
            return

        _uuid = msg.get('uuid') or ''
        if _uuid:
            if SiteRedis.incrby(_uuid) > 1:
                return
            else:
                SiteRedis.incrby(_uuid)
                SiteRedis.expire(_uuid, 10)

        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
        if not conversation_data:
            return
        _sitedata = SITE_DICT_CACHE.get(conversation_data.get('site_code'))

        text = msg.get('text')
        _data = {
            'text': convertTextFunc(text),
            'customer_id': customer_id,
            'conversation_id': conversation_id,
            'service_reading_state': False,
            'content_type': ContentTypes.TEXT,
            'is_retract': False,
            'site_code': conversation_data.get('site_code') or '',
        }
        content_id = ChatContentTable.insert_one(_data)
        customer_data = CustomerTable.find_one({'uuid': customer_id})

        service_language = _sitedata.get('service_language') or ''
        client_language = _sitedata.get('client_language') or ''
        translate_statu = _sitedata.get('translate_statu') or False
        service_client_language = _sitedata.get('service_client_language') or ''
        _result_data = {
            'content_id': content_id,
            'translate_state': _sitedata.get('translate_state') or False,
        }
        if service_client_language and client_language and translate_statu in [translateStatu.TFBS, translateStatu.WTCSS]:
            client_language_code = LANGUAGE.lang_code.get(client_language) or 'en'
            service_client_language_code = LANGUAGE.lang_code.get(service_client_language) or 'en'
            try:
                _new_mag_text = translate_text_func(msg.get('text'), source_language=client_language_code, target_language=service_client_language_code)
                ChatContentTable.update_one({'uuid': content_id}, {'$set': {service_client_language+'_text': _new_mag_text}})
                _result_data['translate_text'] = _new_mag_text
            except:
                pass

        if customer_data:
            _result_data['customer_name'] = customer_data.get('name')
        else:
            _result_data['customer_name'] = ''
            
        create_time = datetime.datetime.utcnow()
        _result_data['create_time'] = create_time.strftime('%m-%d %H:%M')
        _result_data.update({
            'djs_h': 0,
            'djs_m': 0,
            'djs_s': 0,
        })

        customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
        if customer_data:
            service_id = customer_data.get('service_id')
            for k in ['text', 'customer_id', 'conversation_id', 'content_type', 'file_path']:
                _result_data.update({k: _data.get(k)})
            _result_data['crr_service_id'] = service_id

            autoproblem = problemTable.find_one({'title' : text}) or {}
            if autoproblem:
                _result_data['is_automatic'] = True
                _result_data['auto_reply'] = autoproblem.get('answer')
                _result_data['dataUid'] = shortuuid.uuid()

            await emit('chatNewConversationNewReceive', _result_data, namespace='/serviceChat', broadcast=True)

    # 前端输入框实时信息
    async def on_realTimeInputMessage(self, request, msg):
        if not isinstance(msg, dict):
            return
        text = msg.get('text')
        customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
        conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))

        _result_data = {
            'text': text or '',
            'conversation_id': conversation_id,
        }
        customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
        if customer_data:
            service_sid = customer_data.get('service_sid')
            await emit('ChatServerSideMessage', _result_data, namespace='/serviceChat', room=service_sid)

    # 图片上传
    async def on_chatUploadImage(self, request, msg):
        ''' 图片上传 '''
        if not isinstance(msg, dict):
            return
        if send_IMG_limit():
            return
        action = msg.get('action')
        if not action:
            return
        if action == 'check_image_format':
            filename = msg.get('filename')
            if not filename:
                return

            fts = filename.rsplit('.', 1)
            if not fts:
                return await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'state': False, 'action': 'check_image_format', 'message': f'文件格式错误！'}), room=request.ctx.session.sid, namespace='/chat')
            ft = '.' + fts[-1]
            if ft not in IMAGES_TYPES:
                return await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'state': False, 'action': 'check_image_format', 'message': f'文件格式错误！限制为：{ ",".join(IMAGES_TYPES) }!'}), room=request.ctx.session.sid, namespace='/chat')

            return await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'state': True, 'action': 'check_image_format'}), room=request.ctx.session.sid, namespace='/chat')
        if action == 'upload_image':
            image = msg.get('image')
            uoloadCode = msg.get('uoloadCode')
            customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
            conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
            if not customer_id or not conversation_id or not image:
                return
            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            if not conversation_data:
                return

            _data = {
                'text': '',
                'customer_id': customer_id,
                'conversation_id': conversation_id,
                'service_reading_state': False,
                'content_type': ContentTypes.PICTURE,
                'file_path': image,
                'is_retract': False,
                'site_code': conversation_data.get('site_code') or '',
            }
            content_id = ChatContentTable.insert_one(_data)
            customer_data = CustomerTable.find_one({'uuid': customer_id})
            _result_data = {
                'content_id': content_id
            }
            if customer_data:
                _result_data['customer_name'] = customer_data.get('name')
            else:
                _result_data['customer_name'] = ''

            create_time = datetime.datetime.utcnow()
            _result_data['create_time'] = create_time.strftime('%m-%d %H:%M')

            customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
            if customer_data:
                service_id = customer_data.get('service_id')
                for k in ['text', 'customer_id', 'conversation_id', 'content_type', 'file_path']:
                    _result_data.update({k: _data.get(k)})
                _result_data.update({
                    'djs_h': 0,
                    'djs_m': 0,
                    'djs_s': 0,
                })
                _result_data['crr_service_id'] = service_id
                await emit('chatNewConversationNewReceive', _result_data, namespace='/serviceChat', broadcast=True)
            await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'uoloadCode': uoloadCode, 'file_path': image, 'action': 'serverUploadFeedback'}), room=request.ctx.session.sid, namespace='/chat')

    # 上传文件
    async def on_chatUploadFile(self, request, msg):
        if not isinstance(msg, dict):
            return
        if send_fileS_limit():
            return
        action = msg.get('action')
        if not action:
            return
        if action == 'upload_image':
            image = msg.get('image')
            uoloadCode = msg.get('uoloadCode')
            customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
            conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
            if not customer_id or not conversation_id or not image:
                return
            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            if not conversation_data:
                return

            create_time = datetime.datetime.utcnow()
            _data = {
                'text': '',
                'customer_id': customer_id,
                'conversation_id': conversation_id,
                'service_reading_state': False,
                'content_type': ContentTypes.PICTURE,
                'file_path': image,
                'is_retract': False,
                'site_code': conversation_data.get('site_code') or '',
            }
            content_id = ChatContentTable.insert_one(_data)
            customer_data = CustomerTable.find_one({'uuid': customer_id})
            _result_data = {
                'content_id': content_id
            }
            if customer_data:
                _result_data['customer_name'] = customer_data.get('name')
            else:
                _result_data['customer_name'] = ''
            _result_data['create_time'] = create_time.strftime('%m-%d %H:%M')

            customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
            if customer_data:
                service_id = customer_data.get('service_id')
                for k in ['text', 'customer_id', 'conversation_id', 'content_type', 'file_path']:
                    _result_data.update({k: _data.get(k)})
                _result_data.update({
                    'djs_h': 0,
                    'djs_m': 0,
                    'djs_s': 0,
                    # 'create_time': datetime.datetime.utcnow()
                })
                _result_data['crr_service_id'] = service_id
                await emit('chatNewConversationNewReceive', _result_data, namespace='/serviceChat', broadcast=True)
            await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'uoloadCode': uoloadCode, 'file_path': image, 'action': 'serverUploadFeedback'}), room=request.ctx.session.sid, namespace='/chat')
        if action == 'upload_video':
            video = msg.get('video')
            filesize = msg.get('filesize')
            filename = msg.get('filename')
            uoloadCode = msg.get('uoloadCode')
            customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
            conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
            if not customer_id or not conversation_id or not video:
                return
            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            if not conversation_data:
                return

            create_time = datetime.datetime.utcnow()
            _data = {
                'text': '',
                'customer_id': customer_id,
                'conversation_id': conversation_id,
                'service_reading_state': False,
                'content_type': ContentTypes.VIDEO,
                'file_path': video,
                'is_retract': False,
                'file_size': filesize,
                'filename': filename,
                'site_code': conversation_data.get('site_code') or '',
            }
            content_id = ChatContentTable.insert_one(_data)
            customer_data = CustomerTable.find_one({'uuid': customer_id})
            _result_data = {
                'content_id': content_id
            }
            if customer_data:
                _result_data['customer_name'] = customer_data.get('name')
            else:
                _result_data['customer_name'] = ''
            _result_data['create_time'] = create_time.strftime('%m-%d %H:%M')

            customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
            if customer_data:
                service_id = customer_data.get('service_id')
                for k in ['text', 'customer_id', 'conversation_id', 'content_type', 'file_path', 'filename', 'file_size']:
                    _result_data.update({k: _data.get(k) or ''})
                _result_data.update({
                    'djs_h': 0,
                    'djs_m': 0,
                    'djs_s': 0,
                    # 'create_time': datetime.datetime.utcnow()
                })
                _result_data['crr_service_id'] = service_id
                await emit('chatNewConversationNewReceive', _result_data, namespace='/serviceChat', broadcast=True)
            # await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'uoloadCode': uoloadCode, 'file_path': image, 'action': 'serverUploadFeedback'}), room=request.ctx.session.sid)


    # 评分
    async def on_customerScore(self, request, msg):
        if not isinstance(msg, dict):
            return
        level = msg.get('level')
        cntText = msg.get('cntText')
        customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
        conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))

        _result = {
            'action': 'left_customer_score',
        }
        if not level or not cntText or not customer_id or not conversation_id or not isinstance(level, int):
            return await emit('chatReceiveServerFeedback', xtjsonCls.json_params_error(message='评分提交失败！', data=_result), room=request.ctx.session.sid, namespace='/chat')

        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
        if not conversation_data:
            return await emit('chatReceiveServerFeedback', xtjsonCls.json_params_error(message='评分提交失败！', data=_result), room=request.ctx.session.sid, namespace='/chat')

        conversation_data.update({
            'score_level': int(level),
            'score_text': cntText,
        })
        ChatConversationTable.save(conversation_data)
        return await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data=_result), room=request.ctx.session.sid, namespace='/chat')

    # 结束会话
    async def on_ping(self, request, msg):
        return await emit('pong', xtjsonCls.json_result(data=""), room=request.ctx.session.sid, namespace='/chat')

    async def on_finishConversation(self, request, msg):
        if not isinstance(msg, dict):
            return
        level = msg.get('level')
        cntText = msg.get('cntText')
        customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
        conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
        if not customer_id or not conversation_id:
            return
        _result = {
            'action': 'finish_conversation',
        }
        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
        if not conversation_data:
            return await emit('chatReceiveServerFeedback', xtjsonCls.json_params_error(message='评分提交失败！', data=_result), room=request.ctx.session.sid, namespace='/chat')
        if level and cntText:
            conversation_data.update({
                'score_level': int(level),
                'score_text': cntText,
            })

        if conversation_data.get('statu') != ConversationStatu.finished:
            conversation_data.update({
                'statu': ConversationStatu.finished,
                'end_time': datetime.datetime.now(),
            })

            _fd = {
                'service_id': conversation_data.get('service_id'),
                'customer_id': customer_id,
            }
            _fdata = FinishListTable.find_one(_fd)
            if not _fdata:
                _fd.update({'conversation_id': conversation_id})
                FinishListTable.insert_one(_fd)
            else:
                _fdata.update({'conversation_id': conversation_id})
                FinishListTable.save(_fdata)

            customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
            if customer_data:
                service_sid = customer_data.get('service_sid')
                _red = {
                    'crr_service_sid': conversation_data.get('service_id'),
                    'conversation_id': conversation_id,
                }
                await emit('chatFinishConversation', _red, namespace='/serviceChat', broadcast=True)

                CLIENT_CONNECTION.pop(request.ctx.session.sid)
                present_count = ChatFuncTools.get_service_sid_present_count(service_sid)
                await emit('chatCtnOnlineCount', {'onlineTotal': len(CLIENT_CONNECTION), 'onlinePresent': present_count}, namespace='/serviceChat', room=service_sid)

        ChatConversationTable.save(conversation_data)
        return await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data=_result), room=request.ctx.session.sid, namespace='/chat')

    # 获取问题列表
    async def on_chatProblem(self, request, msg):
        if not msg or not isinstance(msg, dict):
            return
        action = msg.get('action')
        data_uuid = msg.get('data_id')
        if action == 'getProblemList':
            datas = problemTable.find_many({}) or []
            _datas = []
            for da in datas:
                _datas.append({
                    'data_id': da.get('uuid'),
                    'title': da.get('title'),
                })
            return await emit('chatJsProblem', xtjsonCls.json_result(data={'action': 'problemList', 'datas': _datas}), room=request.ctx.session.sid, namespace='/chat')
        if action == 'getProblemData':
            if not data_uuid:
                return
            _data = problemTable.find_one({'uuid': data_uuid})
            if not _data:
                return
            return await emit('chatJsProblem', xtjsonCls.json_result(data={'action': 'problemData', 'text': _data.get('answer'), 'title': _data.get('title'), 'data_id': _data.get('uuid')}), room=request.ctx.session.sid, namespace='/chat')

    # 小窗口上传图片
    async def on_chatWinUploadImage(self, request, msg):
        if not isinstance(msg, dict):
            return
        action = msg.get('action')
        if not action:
            return

        if action == 'upload_image':
            type = msg.get('type')
            if not type or type not in ContentTypes.name_arr or type != 'picture':
                return
            imagePath = msg.get('imagePath')
            uoloadCode = msg.get('uoloadCode')
            customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
            conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
            if not customer_id or not conversation_id:
                return
            conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            if not conversation_data:
                return
            create_time = datetime.datetime.utcnow()
            _data = {
                'text': '',
                'customer_id': customer_id,
                'conversation_id': conversation_id,
                'service_reading_state': False,
                'content_type': ContentTypes.PICTURE,
                'file_path': imagePath,
                'is_retract': False,
                'site_code': conversation_data.get('site_code') or '',
            }
            content_id = ChatContentTable.insert_one(_data)
            customer_data = CustomerTable.find_one({'uuid': customer_id})
            _result_data = {
                'content_id': content_id
            }
            if customer_data:
                _result_data['customer_name'] = customer_data.get('name')
            else:
                _result_data['customer_name'] = ''
            _result_data['create_time'] = create_time.strftime('%m-%d %H:%M')

            customer_data = CLIENT_CONNECTION.get(request.ctx.session.sid)
            if customer_data:
                service_id = customer_data.get('service_id')
                for k in ['text', 'customer_id', 'conversation_id', 'content_type', 'file_path']:
                    _result_data.update({k: _data.get(k)})
                _result_data.update({
                    'djs_h': 0,
                    'djs_m': 0,
                    'djs_s': 0,
                })
                _result_data['crr_service_id'] = service_id
                await emit('chatNewConversationNewReceive', _result_data, namespace='/serviceChat', broadcast=True)
            await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'uoloadCode': uoloadCode, 'file_path': imagePath, 'action': 'serverUploadFeedback'}), room=request.ctx.session.sid, namespace='/chat')

    # 客户窗口激活
    async def on_customerWinFocus(self, request, msg):
        if not isinstance(msg, dict):
            return
        chatUsid = msg.get('chatUsid')
        site_code = msg.get('site_code')
        chatSession = msg.get('chatSession')
        if not site_code or not chatUsid or not chatSession:
            return
        customer_id = ChatFuncTools.analysis_chatCache(msg.get('chatUsid'))
        conversation_id = ChatFuncTools.analysis_chatCache(msg.get('chatSession'))
        if not customer_id or not conversation_id:
            return

        client_data = CLIENT_CONNECTION.get(request.ctx.session.sid) or {}
        if not client_data:
            return
        if ChatContentTable.count({'service_id': client_data.get('service_id'), 'conversation_id': conversation_id, 'customer_reading_state': False}):
            ChatContentTable.update_many({'service_id': client_data.get('service_id'), 'conversation_id': conversation_id, 'customer_reading_state': False}, {'$set': {'customer_reading_state': True}})
            _result = {
                'type': 'customerWinFocus',
                'conversation_id': conversation_id,
                'crr_service_id': client_data.get('service_id'),
            }
            await emit('serverFeedback', xtjsonCls.json_result(data=_result), namespace='/serviceChat', broadcast=True)

    async def on_process_message(self, request, event_id, msg):
        if event_id == "initVisitor":
            await self.on_initVisitor(request, msg)
        elif event_id == "leaveMessage":
            await self.on_leaveMessage(request, msg)
        elif event_id == "chatReceiveMessage":
            await self.on_chatReceiveMessage(request, msg)
        elif event_id == "realTimeInputMessage":
            await self.on_realTimeInputMessage(request, msg)
        elif event_id == "chatUploadImage":
            await self.on_chatUploadImage(request, msg)
        elif event_id == "chatUploadFile":
            await self.on_chatUploadFile(request, msg)
        elif event_id == "customerScore":
            await self.on_customerScore(request, msg)
        elif event_id == "finishConversation":
            await self.on_finishConversation(request, msg)
        elif event_id == "chatProblem":
            await self.on_chatProblem(request, msg)
        elif event_id == "chatWinUploadImage":
            await self.on_chatWinUploadImage(request, msg)
        elif event_id == "customerWinFocus":
            await self.on_customerWinFocus(request, msg)
        elif event_id == "ping":
            await self.on_ping(request, msg)

class ServiceSocketIoCls():
    async def reva_msg_chuli(self, request, msg):
        text = msg.get('text')
        dataType = msg.get('dataType')
        service_id = msg.get('service_id')
        conversation_id = msg.get('conversation_id')
        is_automatic = msg.get('is_automatic')
        temporary_data_id = msg.get('temporary_data_id')
        is_problem = msg.get('is_problem')
        action = msg.get('action')
        fileType = msg.get('filetype')
          
        filePath = msg.get('filePath')
        filename = msg.get('filename')
        file_size = msg.get('file_size')
        if not service_id or not conversation_id or not temporary_data_id or not action:
            return
        if not text and not filePath:
            return

        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
        if not conversation_data:
            return

        create_time = datetime.datetime.now()
        _data = {
            'text': convertTextFunc(text),
            'service_id': service_id,
            'conversation_id': conversation_id,
            'is_automatic': is_automatic or False,
            'file_path': filePath or '',
            'filename': filename or '',
            'file_size': file_size or '',
            'is_retract': False,
            'temporary_data_id': temporary_data_id, # 前端生成用的消息临时id
            'customer_reading_state': False,
            'site_code': conversation_data.get('site_code') or '',
        }

        _new_mag_text = ''
        if fileType == ContentTypes.VIDEO:
            content_type = ContentTypes.VIDEO
            _data.update({'content_type': ContentTypes.VIDEO})
        elif dataType == ContentTypes.FILE:
            content_type = ContentTypes.FILE
            _data.update({'content_type': ContentTypes.FILE})
        else:
            content_type = ContentTypes.TEXT
            _data.update({'content_type': ContentTypes.TEXT})

            site_Data = SITE_DICT_CACHE.get(_data.get('site_code'))
            if site_Data:
                translate_statu = site_Data.get('translate_statu') or ''
                client_language = site_Data.get('client_language') or ''
                service_language = site_Data.get('service_language') or ''
                client_service_language = site_Data.get('client_service_language')
                client_language_code = LANGUAGE.lang_code.get(client_language) or 'en'
                service_language_code = LANGUAGE.lang_code.get(service_language) or 'en'
                client_service_language_code = LANGUAGE.lang_code.get(client_service_language) or 'en'
                if translate_statu and service_language and client_service_language and translate_statu in [translateStatu.TFBS, translateStatu.TSCS]:
                    try:
                        _new_mag_text = translate_text_func(text, source_language=service_language_code, target_language=client_service_language_code)
                    except:
                        _new_mag_text = ''
                    _data['text'] = text
                    _data[client_service_language+'_text'] = _new_mag_text

        data_id = ChatContentTable.insert_one(_data)
        _text = ChatFuncTools.add_link_a(_new_mag_text or text)
        _result = {
            'text': _text,
            'file_path': filePath or '',
            'filename': filename or '',
            'file_size': file_size or '',
            'create_time': datetime.datetime.utcnow().strftime('%m-%d %H:%M'),
            'content_type': ContentTypes.TEXT,
            'dataId': data_id,
        }
        if fileType == ContentTypes.VIDEO:
            _result.update({'content_type': ContentTypes.VIDEO})
        elif dataType == ContentTypes.FILE:
            _result.update({'content_type': ContentTypes.FILE})
        else:
            _result.update({'content_type': ContentTypes.TEXT})

        CLIENT_DATA = ChatFuncTools.get_conversation_id_to_CLIENT_DATA(conversation_id)
        if CLIENT_DATA:
            await emit('chatReceiveServiceMessage', _result, namespace='/chat', room=CLIENT_DATA.get('sid'))

        to_data = {
            'data_id': data_id,
            'type': 'text_message_feedback',
            'temporary_data_id': temporary_data_id,
            'service_id': service_id,
            'conversation_id': conversation_id,
        }

        if dataType == ContentTypes.FILE:
            to_data.update({'type': 'upload_file_feedback'})
        else:
            _data.update({'type': 'text_message_feedback'})

        await emit('serverFeedback', xtjsonCls.json_result(data=to_data), room=request.ctx.session.sid, namespace='/serviceChat')

        udata = CmsUserModel.find_one({'uuid': service_id}) or {}
        if not udata:
            return
        service_data = {
            'service_name': udata.get('nickname') or '客服',
            'portrait': udata.get('portrait') or '/assets/chat/images/keFuLogo.png',
        }
        msg_data = {
            'content_type': content_type,
            'timeStamp': int(time.mktime(create_time.timetuple())),
            'uuid': data_id,
            'create_time': datetime.datetime.utcnow().strftime('%m-%d %H:%M'),
            'text': ChatFuncTools.add_link_a(text),
            'is_automatic': is_automatic or False,
            'file_path': filePath or '',
            'filename': filename or '',
            'file_size': file_size or '',
            'is_retract': False,
        }
        _dd_receiveTsConversationMsg = {
            'conversation_id': conversation_id,
            'service_data': service_data,
            'data': msg_data,
            'service_id': service_id,
        }
        await emit('receiveTsConversationMsg', xtjsonCls.json_result(data=_dd_receiveTsConversationMsg), namespace='/serviceChat', broadcast=True)

    # 获取会话列表
    def getConversationList(self, service_id):
        datas = ChatConversationTable.find_many({'service_id': service_id, '$or': [{'statu': ConversationStatu.normal}, {'statu': ConversationStatu.waiting}]}, sort=[['create_time', 1]])
        _datas = []
        totalWdNumber = 0
        for data in datas:
            start_time = data.get('start_time')
            disconnect_tiem = data.get('disconnect_tiem')

            wdCount = ChatContentTable.count({'conversation_id': data.get('uuid'), 'service_reading_state': False, 'is_retract': False}) or 0
            data['wdCount'] = wdCount

            _dddc = ChatContentTable.find_one({'conversation_id': data.get('uuid')}, sort=[['create_time', -1]])
            djs_h, djs_m, djs_s = 0, 0, 0
            djs_statu = False
            if _dddc and _dddc.get('customer_id') and not _dddc.get('service_id') and _dddc.get('is_automatic'):
                _dc = datetime.datetime.now() - _dddc.get('create_time')
                djs_h, djs_m, djs_s = str(_dc).split(':')
                djs_statu = True

            data.update({
                'djs_h': int(str(djs_h).split(',')[-1]),
                'djs_m': int(str(djs_m).split(',')[-1]),
                'djs_s': int(float(str(djs_s).split(',')[-1])),
                'djs_statu': djs_statu,
            })

            _ddd2 = ChatContentTable.find_one({'conversation_id': data.get('uuid'), 'service_id': service_id, 'is_retract': False}, sort=[['create_time', -1]])
            if _ddd2:
                is_automatic = _ddd2.get('is_automatic') or False
            else:
                is_automatic = False
            data['is_automatic'] = is_automatic

            crr_time = datetime.datetime.now()
            if isinstance(disconnect_tiem, datetime.datetime) and (crr_time - disconnect_tiem).seconds > 60 * 60 and data.get('statu') == ConversationStatu.waiting:
                ChatConversationTable.update_one({'uuid': data.get('uuid')}, {'$set': {'statu': ConversationStatu.finished}})
                continue

            if data.get('statu') == ConversationStatu.normal and not disconnect_tiem and not ChatFuncTools.get_conversation_id_to_CLIENT_DATA(data.get('uuid')):
                ChatConversationTable.update_one({'uuid': data.get('uuid')}, {'$set': {'statu': ConversationStatu.finished, 'end_time': disconnect_tiem or datetime.datetime.now()}})

                _fd = {
                    'service_id': service_id,
                    'customer_id': data.get('customer_id'),
                }
                _fdata = FinishListTable.find_one(_fd)
                if not _fdata:
                    _fd.update({'conversation_id': data.get('uuid')})
                    FinishListTable.insert_one(_fd)
                else:
                    _fdata.update({'conversation_id': data.get('uuid')})
                    FinishListTable.save(_fdata)
                continue

            data['start_time'] = start_time.strftime('%m-%d %H:%M')
            if isinstance(disconnect_tiem, datetime.datetime):
                data['disconnect_tiem'] = disconnect_tiem.strftime('%m-%d %H:%M')
            else:
                data['disconnect_tiem'] = ''

            for k in ['end_time', 'waiting_time', 'create_time', '_id', '_create_time']:
                try:
                    data.pop(k)
                except:
                    pass
            _customer_data = CustomerTable.find_one({'uuid': data.get('customer_id')}) or {}
            if not _customer_data:
                continue
            data['customer_name'] = _customer_data.get('username') or _customer_data.get('name') or ''
            data['site_name'] = SITE_DICT_CACHE.get(data.get('site_code')).get('site_name') or ''
            _datas.append(data)

            totalWdNumber += wdCount

        _datas = sorted(_datas, key=lambda person: person['wdCount'], reverse=True)
        _result = {
            'totalWdNumber': totalWdNumber,
            'datas': _datas
        }
        return _result

    # 获取风控图片类型
    def get_conrl_imges_types(self, site_code):
        img_data = []
        file_data = []
        site_data = SITE_DICT_CACHE.get(site_code)
        if not site_data:
            return '', ''

        control_file_type_state = site_data.get('control_file_type_state')
        if not control_file_type_state:
            return '', ''
        control_file_types = site_data.get('control_file_types')
        if not control_file_types:
            return '', ''
        for t in control_file_types:
            if t in IMAGES_TYPES:
                img_data.append(t)
            if t in FIEL_TYPES or t in AUDIO_TYPES or t in VIDEO_TYPES:
                file_data.append(t)

        return ','.join(img_data), ','.join(file_data)

    async def on_ping(self, request, msg):
        return await emit('pong', xtjsonCls.json_result(data=""), room=request.ctx.session.sid, namespace='/serviceChat')

    # 开启连接
    async def on_connect(self, request):
        session = request.ctx.session
        sid = session.sid
        siteCode = request.args.get('siteCode')
        crrServiceId = request.args.get('crrServiceId')

        if not crrServiceId:
            return False
        if not session.get(CMS_USER_SESSION_KEY):
            return False
        _udata = CmsUserModel.find_one({'uuid': crrServiceId}) or {}
        if not _udata:
            return False
        connec_data = SERVICE_CONNECTION.get(crrServiceId) or {}
        if connec_data:
            await emit('monitorCommand', xtjsonCls.json_result(data={'action': 'outLogin'}), room=connec_data.get('sid'), namespace='/serviceChat')

        REMOTE_ADDR = get_ip()
        crrip = str(REMOTE_ADDR or '').split(',')[0]

        if _udata:
            _log = {
                'user_id': crrServiceId,
                'operation_type': OPERATION_TYPES.ONLINE,
                'site_code': _udata.get('responsible_site') or '',
                'note': '',
                'ip': crrip,
            }
            systemLogTable.insert_one(_log)

        SERVICE_CONNECTION.update({
            crrServiceId: {
                'sid': sid,
                'online_time': datetime.datetime.now(),
                'ip': crrip,
            }
        })
        print("Admin chat server is connected:", sid)
    # 断开连接
    async def on_disconnect(self, request):
        session = request.ctx.session
        sid = session.sid
        await disconnect_func(sid)
        print("Admin chat server is disconnected....", sid)

    #客服连接初始化
    async def on_serviceInit(self, request, msg):
        service_id = msg.get('service_id')
        _udata = CmsUserModel.find_one({'uuid': service_id}) or {}
        for k in list(CLIENT_CONNECTION.keys()):
            v = CLIENT_CONNECTION.get(k)
            if v.get('service_id') == service_id:
                v['service_sid'] = request.ctx.session.sid
                CLIENT_CONNECTION.update({k: v})
                break

        # 更新连接信息
        ChatFuncTools.update_cilent_data(msg.get('service_id'), request.ctx.session.sid)

        # 实时更新在线人数
        present_count = ChatFuncTools.get_service_id_present_count(msg.get('service_id'))
        _result = {
            'onlineTotal': len(CLIENT_CONNECTION), 'onlinePresent': present_count,
        }
        wdToaslCount = 0
        for data in ChatConversationTable.find_many({'service_id': msg.get('service_id'),  '$or': [{'statu': ConversationStatu.normal}, {'statu': ConversationStatu.waiting}]}):
            _c = ChatContentTable.count({'conversation_id': data.get('uuid'), 'service_reading_state': False, 'is_retract': False}) or 0
            wdToaslCount += _c
        leavingCount = LeavingMessageTable.count({'statu': False, 'site_code': _udata.get('responsible_site')}) or 0
        _result['leavingCount'] = leavingCount
        _result['wdToaslCount'] = wdToaslCount
        await emit('serviceReceiveInit', xtjsonCls.json_result(data=_result), room=request.ctx.session.sid, namespace='/serviceChat')

    # 切换状态
    async def on_editOnlineStatu(self, request, data):
        if not isinstance(data, dict):
            return
        crr_data = CmsUserModel.find_one({'uuid': data.get('data_id')}) or {}
        if not crr_data:
            return
        crr_data['online_statu'] = data.get('state')
        CmsUserModel.save(crr_data)

        REMOTE_ADDR = get_ip()
        crrip = str(REMOTE_ADDR or '').split(',')[0]

        _log = {
            'user_id': crr_data.get('uuid'),
            'site_code': crr_data.get('responsible_site') or '',
            'note': '',
            'ip': crrip,
        }
        if data.get('state') == OnlineStatu.online:
            _log['operation_type'] = OPERATION_TYPES.ONLINE
        if data.get('state') == OnlineStatu.bebusy:
            _log['operation_type'] = OPERATION_TYPES.BEBUSY
        if data.get('state') == OnlineStatu.offline:
            _log['operation_type'] = OPERATION_TYPES.OFFLINE
        systemLogTable.insert_one(_log)

    # 接收信息
    async def on_customerServiceMsg(self, request, msg):
        if not isinstance(msg, dict):
            return
        action = msg.get('action')
        if not action or action == 'sendProblemMsg':
            return 
        await self.reva_msg_chuli(request, msg)

    async def on_problemServiceMsg(self, request, msg):
        if not isinstance(msg, dict):
            return
        text = msg.get('text')
        action = msg.get('action')
        is_problem = msg.get('is_problem')
        temporary_data_id = msg.get('temporary_data_id')
        print('problemServiceMsg:', text, action, temporary_data_id)
        if not action or action != 'sendProblemMsg':
            return
        if not is_problem or len(temporary_data_id) != 22:
            return
        try:
            CacheDataTable.insert_one({
                'mkey': temporary_data_id
            })
        except:
            return
        await self.reva_msg_chuli(request, msg)

    # 会话列表
    async def on_conversationList(self, request, msg):
        if not isinstance(msg, dict):
            return
        service_id = msg.get('service_id')
        _result = self.getConversationList(service_id) or {}
        await emit('chatConversationList', xtjsonCls.json_result(data=_result), room=request.ctx.session.sid, namespace='/serviceChat')

    # 获取客服会话列表
    async def on_serverConversationList(self, request, msg):
        if not isinstance(msg, dict):
            return
        action = msg.get('action')
        service_id = msg.get('service_id')
        if action == 'serverConversationList':
            service_datas = []
            service_data = CmsUserModel.find_one({'uuid': service_id}) or {}
            if not service_data:
                return
            filter_dict = {}
            if service_data.get('role_code') == PermissionCls.Administrator:
                filter_dict['responsible_site'] = service_data.get('responsible_site')
            if service_data.get('role_code') == PermissionCls.CustomerService:
                filter_dict['responsible_site'] = service_data.get('responsible_site')
            if service_data.get('role_code') == PermissionCls.AgentAdmin:
                _cds = CmsUserModel.find_many({'super_admin_id': service_data.get('uuid')})
                _sdis = []
                for cd in _cds:
                    _sitecode = cd.get('responsible_site')
                    if _sitecode not in _sdis:
                        _sdis.append(_sitecode)
                filter_dict['responsible_site'] = {'$in': _sdis}
            if service_data.get('role_code') == PermissionCls.SUPERADMIN:
                filter_dict['role_code'] = {'$in': [PermissionCls.CustomerService, PermissionCls.Administrator]}
            udatas = CmsUserModel.find_many(filter_dict) or []
            total = 0
            for udata in udatas:
                if udata.get('uuid') == service_data.get('uuid'):
                    continue

                u_id = udata.get('uuid')
                if udata.get('uuid') == service_id:
                    continue
                _result = self.getConversationList(u_id) or {}
                if _result:
                    total += len(_result.get('datas'))
                else:
                    _result['datas'] = []
                _sd = {
                    'u_id': u_id,
                    'portrait': udata.get('portrait') or '',
                    'uname': udata.get('nickname') or 'TK88-客服',
                }
                _sd.update(_result)
                service_datas.append(_sd)
            _ddd = {
                'total': total,
                'datas': service_datas,
            }
            await emit('serviceConversationList', xtjsonCls.json_result(data=_ddd), room=request.ctx.session.sid, namespace='/serviceChat')
        if action == 'ServerConversationTotal':
            service_datas = []

            service_data = CmsUserModel.find_one({'uuid': service_id}) or {}
            if not service_data:
                return
            filter_dict = {}
            if service_data.get('role_code') == PermissionCls.Administrator:
                filter_dict['responsible_site'] = service_data.get('responsible_site')
            if service_data.get('role_code') == PermissionCls.AgentAdmin:
                _cds = CmsUserModel.find_many({'super_admin_id': service_data.get('uuid'), 'role_code': PermissionCls.Administrator})
                _sdis = []
                for cd in _cds:
                    _sitecode = cd.get('responsible_site')
                    if _sitecode not in _sdis:
                        _sdis.append(_sitecode)
                filter_dict['responsible_site'] = {'$in': _sdis}
            if service_data.get('role_code') == PermissionCls.CustomerService:
                filter_dict['responsible_site'] = service_data.get('responsible_site')
            if service_data.get('role_code') == PermissionCls.SUPERADMIN:
                filter_dict['role_code'] = {'$in': [PermissionCls.CustomerService, PermissionCls.Administrator]}

            udatas = CmsUserModel.find_many(filter_dict) or []
            for udata in udatas:
                u_id = udata.get('uuid')
                if udata.get('uuid') == service_id:
                    continue
                _tl = 0
                for k, v in CLIENT_CONNECTION.items():
                    if v.get('service_id') == u_id:
                        _tl += 1
                _sd = {
                    'u_id': u_id,
                    'portrait': udata.get('portrait') or '/assets/chat/images/keFuLogo.png',
                    'uname': udata.get('nickname') or udata.get('account')+'-客服',
                    'total': _tl,
                }
                service_datas.append(_sd)
            await emit('ServerReceiveConversationTotal', xtjsonCls.json_result(data=service_datas), room=request.ctx.session.sid, namespace='/serviceChat')
        if action == 'getTargetServerConversationList':
            target_service_id = msg.get('target_service_id') or ''
            if not target_service_id:
                return
            udata = CmsUserModel.find_one({'uuid': target_service_id}) or {}
            if not udata:
                return
            _result = self.getConversationList(target_service_id) or {}
            total = 0
            if _result:
                total = len(_result.get('datas'))
            else:
                _result['datas'] = []
            _sd = {
                'u_id': target_service_id,
                'portrait': udata.get('portrait') or '',
                'uname': udata.get('nickname') or udata.get('account') or '客服',
            }
            _sd.update(_result)
            _ddd = {
                'total': total,
                'datas': [_sd],
            }
            await emit('serviceConversationList', xtjsonCls.json_result(data=_ddd), room=request.ctx.session.sid, namespace='/serviceChat')

    # 获取会话信息
    async def on_conversationInfo(self, request, msg):
        if not isinstance(msg, dict):
            return
        data_id = msg.get('data_id')
        if not data_id:
            return
        _data = ChatConversationTable.find_one({'uuid': data_id})
        if not _data:
            return
        _sitdata = SITE_DICT_CACHE.get(_data.get('site_code')) or {}
        translate_statu = _sitdata.get('translate_statu')
        client_language = _sitdata.get('client_language') or ''
        service_language = _sitdata.get('service_language') or ''
        service_client_language = _sitdata.get('service_client_language') or ''

        customer_data = CustomerTable.find_one({'uuid': _data.get('customer_id')})
        if not customer_data:
            return

        _re_customer_data = {}
        for k in ['username', 'site_code', 'track', 'address', 'telephone', 'telegram', 'note', 'gender', 'email', 'uuid']:
            _v = customer_data.get(k) or ''
            _re_customer_data.update({k: _v})

        crr_service = CmsUserModel.find_one({'uuid': _data.get('service_id')})
        _result = {
            'translate_state': _sitdata.get('translate_state') or False,
            'conversation_id': data_id,
            'conversation_statu': _data.get('statu'),
            'customer_id': customer_data.get('uuid'),
            'customer_name': customer_data.get('name'),
            'customer_data': _re_customer_data,
            'service_data': {
                'service_name': crr_service.get('nickname') or '客服',
                'portrait': crr_service.get('portrait') or '/assets/chat/images/keFuLogo.png',
            }
        }
        for k in ['os_type', 'browser_type', 'client_type', 'ip', 'track']:
            _result[k] = _data.get(k) or ''

        info_data = ChatContentTable.find_many({'conversation_id': data_id, 'is_retract': False}, sort=[['create_time', 1]]) or []
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
            _low_mag_text = data.get('text') or ''
            _new_mag_text = ''
            _translate_text = ''
            service_datas = {}
            if data.get('is_transfer_text'):
                _service_id = ChatFuncTools.get_sid_service_id(request.ctx.session.sid)
                if not _service_id:
                    continue
                _service_data = service_datas.get(_service_id)
                if not _service_data:
                    _service_data = CmsUserModel.find_one({'uuid': _service_id})
                    if not _service_data:
                        continue
                    service_datas[_service_id] = _service_data
                language = _service_data.get('language') or LANGUAGE.zh_CN
                _new_mag_text = data.get(language+'_text')
                if not _new_mag_text:
                    lang_code = LANGUAGE.lang_code.get(language) or 'en'
                    try:
                        _new_mag_text = translate_text_func(_low_mag_text, target_language=lang_code)
                        ChatContentTable.update_one({'uuid': data.get('uuid')}, {'$set': {language+'_text': _new_mag_text}})
                    except:
                        pass
            elif data.get('customer_id') and translate_statu and client_language and service_client_language and translate_statu in [translateStatu.TFBS, translateStatu.WTCSS]:
                datakey = service_client_language+'_text'
                _translate_text = data.get(datakey)
                if not _translate_text:
                    service_client_language_code = LANGUAGE.lang_code.get(service_client_language) or 'en'
                    client_language_code = LANGUAGE.lang_code.get(client_language) or 'en'
                    try:
                        _translate_text = translate_text_func(_low_mag_text, source_language=client_language_code, target_language=service_client_language_code)
                        ChatContentTable.update_one({'uuid': data.get('uuid')}, {'$set': {datakey: _translate_text}})
                    except:
                        pass

            new_red.update({
                'uuid': data.get('uuid'),
                'text': ChatFuncTools.add_link_a(_new_mag_text or _low_mag_text),
                'translate_text': _translate_text,
                'is_service': True if data.get('service_id') else False,
                'is_customer': True if data.get('customer_id') else False,
                'create_time': data.get('create_time').strftime('%m-%d %H:%M'),
                'file_path': data.get('file_path'),
                'file_size': data.get('file_size'),
                'filename': data.get('filename'),
                'content_type': data.get('content_type'),
                'timeStamp': int(time.mktime(data.get('create_time').timetuple())),
                'customer_reading_state': data.get('customer_reading_state') or False,
            })
            _results.append(new_red)

        _result['info_data'] = _results

        kz_image_types, kz_file_types = self.get_conrl_imges_types(_data.get('site_code'))
        _result['kz_image_types'] = kz_image_types
        _result['kz_file_types'] = kz_file_types

        category_datas = categoryTable.find_many({'site_code': _data.get('site_code')}) or []
        categories = []
        for category in category_datas:
            categories.append({
                'uuid': category.get('uuid'),
                'category': category.get('category')
            })
        
        _result['categories'] = categories

        ChatContentTable.update_many({'conversation_id': data_id}, {'$set': {'service_reading_state': True}})

        return await emit('chatConversationInfo', _result, room=request.ctx.session.sid, namespace='/serviceChat')

    # 结束会话
    async def on_closeConversation(self, request, msg):
        if not isinstance(msg, dict):
            return
        data_id = msg.get('data_id')
        is_admin_colse = msg.get('is_admin_colse')
        if not data_id:
            return

        ChatConversationTable.update_one({'uuid': data_id}, {'$set': {'statu': ConversationStatu.finished, 'end_time': datetime.datetime.now()}})
        CLIENT_DATA = ChatFuncTools.get_conversation_id_to_CLIENT_DATA(data_id)
        ChatConversation_data = ChatConversationTable.find_one({'uuid': data_id})

        _fd = {
            'service_id': ChatConversation_data.get('service_id'),
            'customer_id': ChatConversation_data.get('customer_id'),
        }
        _fdata = FinishListTable.find_one(_fd)
        if not _fdata:
            _fd.update({'conversation_id': data_id})
            FinishListTable.insert_one(_fd)
        else:
            _fdata.update({'conversation_id': data_id})
            FinishListTable.save(_fdata)

        _result = {
            'action': 'serviceColseChat',
        }
        score_state = False
        if ChatConversation_data.get('score_text'):
            score_state = True
        _result['score_state'] = score_state

        if CLIENT_DATA:
            await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data=_result), namespace='/chat', room=CLIENT_DATA.get('sid'))
            CLIENT_CONNECTION.pop(CLIENT_DATA.get('sid'))

        if is_admin_colse:
            ddd = SERVICE_CONNECTION.get(ChatConversation_data.get('service_id')) or {}
            if ddd:
                ssid = ddd.get('sid')
                _red = {
                    'crr_service_sid': ChatConversation_data.get('service_id'),
                    'conversation_id': data_id,
                }
                await emit('chatFinishConversation', _red, namespace='/serviceChat', broadcast=True)
                present_count = ChatFuncTools.get_service_sid_present_count(request.ctx.session.sid)
                await emit('chatCtnOnlineCount', {'onlineTotal': len(CLIENT_CONNECTION), 'onlinePresent': present_count, 'crr_service_id': ChatConversation_data.get('service_id')}, room=ssid, namespace='/serviceChat')
        else:
            present_count = ChatFuncTools.get_service_sid_present_count(request.ctx.session.sid)
            print("here8")
            await emit('chatCtnOnlineCount', {'onlineTotal': len(CLIENT_CONNECTION), 'onlinePresent': present_count, 'crr_service_id': ChatConversation_data.get('service_id')}, room=request.ctx.session.sid, namespace='/serviceChat')

    # 获取当前客服全部未读信息数量
    async def on_wdTotalCount(self, request, msg):
        if not isinstance(msg, dict):
            return
        service_id = msg.get('service_id')
        if not service_id:
            return

        wdToaslCount = ChatContentTable.count({'service_id': service_id, 'service_reading_state': False, 'is_retract': False})
        await emit('chatWdTotalCount', {'wdToaslCount': wdToaslCount}, room=request.ctx.session.sid, namespace='/serviceChat')

    # 设置已读
    async def on_chatMessageReadState(self, request, msg):
        if not isinstance(msg, dict):
            return
        content_id = msg.get('content_id')
        if not content_id:
            return
        ChatContentTable.update_many({'uuid': content_id}, {'$set': {'service_reading_state': True}})

    # 设置会话状态
    async def on_SetConversationState(self, request, msg):
        if not isinstance(msg, dict):
            return
        state = msg.get('state')
        service_id = msg.get('service_id')
        conversation_id = msg.get('conversation_id')
        if not state or not conversation_id or state not in ConversationStatu.name_arr:
            return

        _fd = {
            'service_id': service_id,
            'customer_id': conversation_id,
        }
        _fdata = FinishListTable.find_one(_fd)
        if not _fdata:
            _fd.update({'conversation_id': conversation_id})
            FinishListTable.insert_one(_fd)
        else:
            _fdata.update({'conversation_id': conversation_id})
            FinishListTable.update_one({'conversation_id': conversation_id}, {'$set': _fd})

        _d = {
            'statu': state,
        }
        if state == ConversationStatu.finished:
            _d['end_time'] = datetime.datetime.now()
        ChatConversationTable.update_one({'uuid': conversation_id}, {'$set': _d})

    # 图片上传
    async def on_serverPicUpload(self, request, msg):
        if not isinstance(msg, dict):
            return
        imagePath = msg.get('image')
        service_id = msg.get('service_id')
        conversation_id = msg.get('conversation_id')
        if not imagePath or not service_id or not conversation_id:
            return

        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
        if not conversation_data:
            return

        create_time = datetime.datetime.now()
        _data = {
            'file_path': imagePath,
            'service_id': service_id,
            'conversation_id': conversation_id,
            'content_type': ContentTypes.PICTURE,
            'is_retract': False,
            'customer_reading_state': False,
            'site_code': conversation_data.get('site_code') or '',
        }
        data_id = ChatContentTable.insert_one(_data)

        _result = {
            'file_path': imagePath,
            'content_type': ContentTypes.PICTURE,
            'create_time': datetime.datetime.utcnow().strftime('%m-%d %H:%M'),
            'data_uuid': data_id,
        }
        await emit('ServerSideUploadFeedback', _result, room=request.ctx.session.sid, namespace='/serviceChat')

        _result = {
            'file_path': imagePath,
            'content_type': ContentTypes.PICTURE,
            'create_time': datetime.datetime.utcnow().strftime('%m-%d %H:%M'),
            'dataId': data_id,
        }
        CLIENT_DATA = ChatFuncTools.get_conversation_id_to_CLIENT_DATA(conversation_id)
        if CLIENT_DATA:
            await emit('chatReceiveServiceMessage', _result, namespace='/chat', room=CLIENT_DATA.get('sid'))

        udata = CmsUserModel.find_one({'uuid': service_id}) or {}
        if not udata:
            return
        service_data = {
            'service_name': udata.get('nickname') or '客服',
            'portrait': udata.get('portrait') or '/assets/chat/images/keFuLogo.png',
        }
        msg_data = {
            'content_type': ContentTypes.PICTURE,
            'timeStamp': int(time.mktime(create_time.timetuple())),
            'uuid': data_id,
            'create_time': datetime.datetime.utcnow().strftime('%m-%d %H:%M'),
            'text': '',
            'file_path': imagePath or '',
            'is_retract': False,
        }
        _dd_receiveTsConversationMsg = {
            'conversation_id': conversation_id,
            'service_data': service_data,
            'data': msg_data,
            'service_id': service_id,
        }
        await emit('receiveTsConversationMsg', xtjsonCls.json_result(data=_dd_receiveTsConversationMsg), namespace='/serviceChat', broadcast=True)


    # 客户信息处理
    async def on_customerInfo(self, request, msg):
        if not isinstance(msg, dict):
            return
        action = msg.get('action')
        if action == 'saveCustomer':
            _data_form = {}
            for k in ['username', 'gender', 'email', 'telephone', 'telegram', 'address', 'note', 'category']:
                _data_form[k] = msg.get(k) or ''
            if not _data_form.get('username'):
                return
            conversation_id = msg.get('conversation_id')
            if not conversation_id:
                return
            Conversation_data = ChatConversationTable.find_one({'uuid': conversation_id})
            if not Conversation_data:
                return
            CustomerTable.update_one({'uuid': Conversation_data.get('customer_id')},{'$set': _data_form})
            print('saveCustomer success!')

    # 获取结束列表
    async def on_serverGetFinishList(self, request, msg):
        if not isinstance(msg, dict):
            return
        service_id = msg.get('service_id')
        commentType = msg.get('commentType')
        if not service_id:
            return
        _result = []
        for _data in FinishListTable.find_many({'service_id':service_id}):
            _dd = {}
            if commentType == 'commentOn':
                _ces = ChatConversationTable.find_one({'uuid': _data.get('conversation_id'), 'score_level':{'$gte': 1}, 'statu': ConversationStatu.finished}, sort=[['create_time', -1]])
            elif commentType == 'commentOff':
                _ces = ChatConversationTable.find_one({'uuid': _data.get('conversation_id'), 'score_level':{'$lte': 1}, 'statu': ConversationStatu.finished}, sort=[['create_time', -1]])
            else:
                _ces = ChatConversationTable.find_one({'uuid': _data.get('conversation_id'), 'statu': ConversationStatu.finished}, sort=[['create_time', -1]])

            _udata = CmsUserModel.find_one({'uuid': service_id})
            if not _ces or not _udata:
                continue
            _cdata = CustomerTable.find_one({'uuid': _ces.get('customer_id')})
            if not _cdata:
                continue
            _dd['customer_name'] = _cdata.get('username') or _cdata.get('name') or ''
            _dd['site_name'] = SITE_DICT_CACHE.get(_ces.get('site_code')).get('site_name') or ''
            _dd['start_time'] = _ces.get('start_time').strftime('%m-%d %H:%M')
            _dd['end_time'] = _ces.get('end_time').strftime('%m-%d %H:%M')
            _dd['os_type'] = _ces.get('os_type') or ''
            _dd['browser_type'] = _ces.get('browser_type') or ''
            _dd['client_type'] = _ces.get('client_type') or ''
            _dd['uuid'] = _ces.get('uuid') or ''
            _result.append(_dd)
        return await emit('serviceFinishList', xtjsonCls.json_result(data=_result), room=request.ctx.session.sid, namespace='/serviceChat')

    # 客服撤回消息撤回处理
    async def on_serviceRetractMessage(self, request, msg):
        if not isinstance(msg, dict):
            return
        data_uuid = msg.get('data_uuid')
        conversation_id = msg.get('conversation_id')
        ChatContentTable.update_one({'uuid': data_uuid}, {'$set': {'is_retract': True}})
        CLIENT_DATA = ChatFuncTools.get_conversation_id_to_CLIENT_DATA(conversation_id)
        if CLIENT_DATA:
            _result = {
                'action': 'serviceRetractMessage',
                'dataId': data_uuid,
            }
            await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data=_result), namespace='/chat', room=CLIENT_DATA.get('sid'))

        feedback_data = {
            'type': 'retractMessage',
            'data_uuid': data_uuid,
        }
        await emit('serverFeedback', xtjsonCls.json_result(data=feedback_data), namespace='/serviceChat', broadcast=True)

    # 客服回复输入状态
    async def on_severRelyStatu(self, request, msg):
        if not isinstance(msg, dict):
            return
        statu = 'success'
        text = msg.get('text') or ''
        conversation_id = msg.get('conversation_id')
        if text and text.strip():
            statu = 'ongoing'
        CLIENT_DATA = ChatFuncTools.get_conversation_id_to_CLIENT_DATA(conversation_id)
        if CLIENT_DATA:
            await emit('chatReceiveServerFeedback', xtjsonCls.json_result(data={'action': 'serverReply', 'statu': statu}), namespace='/chat', room=CLIENT_DATA.get('sid'))

    # 更新状态
    async def on_uploadOnlieState(self, request, msg):
        if not isinstance(msg, dict):
            return
        data_uuid = msg.get('data_uuid')
        state = msg.get('state')
        if state not in OnlineStatu.name_arr:
            return

        udata = CmsUserModel.find_one({'uuid': data_uuid}) or {}
        if not udata:
            return

        CmsUserModel.update_one({'uuid': data_uuid}, {'$set': {'online_statu': state}})
        sdata = SERVICE_CONNECTION.get(data_uuid)
        if sdata:
            _dd = {
                'newState': state,
            }
            await emit('receiveOnlieUpload', xtjsonCls.json_result(data=_dd), room=sdata.get('sid'), namespace='/serviceChat')

    # 发送指令
    async def on_serverMonitorCommand(self, request, msg):
        if not isinstance(msg, dict):
            return
        action = msg .get('action')
        if action == 'forceOutLogin':
            target_service_id = msg.get('target_service_id')
            if not target_service_id:
                return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'forceOutLogin', 'msg': '强制下线失败！', 'state': False}), room=request.ctx.session.sid, namespace='/serviceChat')
            sddd = SERVICE_CONNECTION.get(target_service_id)
            if not sddd:
                return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'forceOutLogin', 'msg': '强制下线失败！该用户已下线，请刷新列表数据后操作！', 'state': False}), room=request.ctx.session.sid, namespace='/serviceChat')
            try:
                await emit('monitorCommand', xtjsonCls.json_result(data={'action': 'outLogin'}), room=sddd.get('sid'), namespace='/serviceChat')
                await disconnect(sddd.get('sid'), namespace='/serviceChat')
                await disconnect_func(sddd.get('sid'))
            except Exception as e:
                print('disconnect error:', str(e))
            return await emit('serverFeedback', xtjsonCls.json_result( data={'type': 'forceOutLogin', 'msg': '强制下线成功！', 'state': True}), room=request.ctx.session.sid, namespace='/serviceChat')

    # 转接会话
    async def on_transferConversation(self, request, msg):
        if not isinstance(msg,dict):
            return
        conversation_id = msg.get('conversation_id')
        select_service_id = msg.get('select_service_id')
        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id}) or {}
        if not conversation_data:
            return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'transferConversation', 'statu': False}), room=request.ctx.session.sid, namespace='/serviceChat')
        if select_service_id not in SERVICE_CONNECTION:
            return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'transferConversation', 'statu': False}), room=request.ctx.session.sid, namespace='/serviceChat')

        low_udata = CmsUserModel.find_one({'uuid': conversation_data.get('service_id')}) or {}
        if not low_udata:
            return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'transferConversation', 'statu': False}), room=request.ctx.session.sid, namespace='/serviceChat')

        udata = CmsUserModel.find_one({'uuid': select_service_id}) or {}
        if not udata:
            return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'transferConversation', 'statu': False}), room=request.ctx.session.sid, namespace='/serviceChat')

        ChatConversationTable.update_one({'uuid': conversation_id}, {'$set': {'service_id': select_service_id, 'is_transfer': True}})

        new_data = {
            'uuid': conversation_id,
            'is_transfer': True,
        }
        start_time = conversation_data.get('start_time')
        new_data['start_time'] = start_time.strftime('%m-%d %H:%M')
        for k in ['end_time', 'waiting_time', 'create_time', '_id', '_create_time', 'start_time']:
            try:
                conversation_data.pop(k)
            except:
                pass
        new_data.update(conversation_data)

        _customer_data = CustomerTable.find_one({'uuid': new_data.get('customer_id')}) or {}
        new_data['customer_name'] = _customer_data.get('username') or _customer_data.get('name') or ''
        new_data['site_name'] = SITE_DICT_CACHE.get(new_data.get('site_code')).get('site_name') or ''
        wdCount = ChatContentTable.count({'conversation_id': conversation_id, 'service_reading_state': False, 'is_retract': False}) or 0
        new_data['wdCount'] = wdCount
        new_data['conversation_id'] = conversation_id
        new_data['service_id'] = select_service_id

        await emit('chatNewConversation', new_data, namespace='/serviceChat', broadcast=True)
        
        crr_cl_data = {}
        cc_sid = ''
        for k, v in CLIENT_CONNECTION.items():
            if v.get('conversation_id') == conversation_id:
                cc_sid = k
                crr_cl_data = v
                break
        if crr_cl_data and cc_sid:
            CLIENT_CONNECTION.update({
                cc_sid: {
                    'service_sid': SERVICE_CONNECTION.get(select_service_id).get('sid'),
                    'service_id': select_service_id,
                    'conversation_id': conversation_id,
                    'customer_id': new_data.get('customer_id'),
                },
            })

        ChatContentTable.insert_one({
            'text': f'收到客服: “{low_udata.get("nickname") or low_udata.get("account") or ""}”，转接的客户',
            'service_id': select_service_id,
            'conversation_id': conversation_id,
            'service_reading_state': True,
            'content_type': ContentTypes.TEXT,
            'is_retract': False,
            'site_code': conversation_data.get('site_code') or '',
            'is_transfer_text': True,
        })

        xx = await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'transferConversation', 'statu': True, 'conversation_id': conversation_id}), room=request.ctx.session.sid, namespace='/serviceChat')

        return xx

    # 获取会话名片信息
    async def on_serverInfoCard(self, request, msg):
        if not isinstance(msg, dict):
            return
        conversation_id = msg.get('conversation_id')
        if not conversation_id:
            return
        conversation_data = ChatConversationTable.find_one({'uuid': conversation_id}) or {}
        if not conversation_data:
            return
        customer_data = CustomerTable.find_one({'uuid': conversation_data.get('customer_id')}) or {}
        if not customer_data:
            return

        _re_customer_data = {}
        for k in ['username', 'site_code', 'track', 'address', 'telephone', 'telegram', 'note', 'gender', 'email', 'uuid']:
            _v = customer_data.get(k) or ''
            _re_customer_data.update({k: _v})

        _result = {
            'conversation_id': conversation_id,
            'customer_id': customer_data.get('uuid'),
            'customer_name': customer_data.get('name'),
            'customer_data': _re_customer_data,
        }
        for k in ['os_type', 'browser_type', 'client_type', 'ip', 'track']:
            _result[k] = conversation_data.get(k) or ''

        return await emit('receviceUploadCard', xtjsonCls.json_result(data=_result), room=request.ctx.session.sid, namespace='/serviceChat')

    # 留言处理(安全处理！)
    async def on_leavingMessage(self, request, msg):
        if not isinstance(msg, dict):
            return
        action = msg.get('action')
        site_code = msg.get('site_code')
        if action == 'update_leavingCount':
            if not site_code:
                return
            leavingCount = LeavingMessageTable.count({'statu': False, 'site_code': site_code}) or 0
            return await emit('serverFeedback', xtjsonCls.json_result(data={'type': 'update_leavingCount', 'leavingCount': leavingCount}), namespace='/serviceChat', broadcast=True)
    
    async def on_process_message(self, request, event_id, msg):
        if event_id == "serviceInit":
            await self.on_serviceInit(request, msg)
        elif event_id == "editOnlineStatu":
            await self.on_editOnlineStatu(request, msg)
        elif event_id == "customerServiceMsg":
            await self.on_customerServiceMsg(request, msg)
        elif event_id == "problemServiceMsg":
            await self.on_problemServiceMsg(request, msg)
        elif event_id == "conversationList":
            await self.on_conversationList(request, msg)
        elif event_id == "serverConversationList":
            await self.on_serverConversationList(request, msg)
        elif event_id == "conversationInfo":
            await self.on_conversationInfo(request, msg)
        elif event_id == "closeConversation":
            await self.on_closeConversation(request, msg)
        elif event_id == "wdTotalCount":
            await self.on_wdTotalCount(request, msg)
        elif event_id == "chatMessageReadState":
            await self.on_chatMessageReadState(request, msg)
        elif event_id == "SetConversationState":
            await self.on_SetConversationState(request, msg)
        elif event_id == "serverPicUpload":
            await self.on_serverPicUpload(request, msg)
        elif event_id == "customerInfo":
            await self.on_customerInfo(request, msg)
        elif event_id == "serverGetFinishList":
            await self.on_serverGetFinishList(request, msg)
        elif event_id == "serviceRetractMessage":
            await self.on_serviceRetractMessage(request, msg)
        elif event_id == "severRelyStatu":
            await self.on_severRelyStatu(request, msg)
        elif event_id == "uploadOnlieState":
            await self.on_uploadOnlieState(request, msg)
        elif event_id == "serverMonitorCommand":
            await self.on_serverMonitorCommand(request, msg)
        elif event_id == "transferConversation":
            await self.on_transferConversation(request, msg)
        elif event_id == "serverInfoCard":
            await self.on_serverInfoCard(request, msg)
        elif event_id == "leavingMessage":
            await self.on_leavingMessage(request, msg)
        elif event_id == "ping":
            await self.on_ping(request, msg)
    

chat_server = ChatSocketIOCls()
serviceChat_server = ServiceSocketIoCls()
