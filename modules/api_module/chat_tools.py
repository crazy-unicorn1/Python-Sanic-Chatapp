# -*- coding: utf8 -*-
import random, string, user_agents, datetime, requests, re, json
from models.cms_user import CmsUserModel
from models.kefu_table import CustomerTable, ChatConversationTable
from constants import ClientTypes, BrowserTypes, OnlineStatu, SERVICE_CONNECTION, CLIENT_CONNECTION, ConversationStatu, SITE_CONFIG_CACHE, IMAGES_TYPES, PermissionCls, SITE_DICT_CACHE, LANGUAGE, SERVICECHAT_NAMESPACE_CONNECTIONS, CHAT_NAMESPACE_CONNECTIONS
import ipaddress

class xtjsonCls():

    @classmethod
    def json_result(cls, message='', data={}, **kwargs):
        json_dict = {'code': 200, 'message': message, 'data': data}

        if kwargs.keys():
            for k, v in kwargs.items():
                json_dict[k] = v

        return json_dict

    @classmethod
    def json_params_error(cls, message='', data={}, **kwargs):
        """
            请求参数错误
        """
        json_dict = {'code': 400, 'message': message, 'data': data}
        if kwargs.keys():
            for k, v in kwargs.items():
                json_dict[k] = v

        return json_dict



class ChatFuncTools():

    @classmethod
    def add_link_a(cls, text):
        if not text:
            return text
        if '<' in text and '>' in text:
            return text
        try:
            pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(pattern, text) or []
            for u in urls:
                html = '<a href="%s" target="_blank">%s</a>' % (u, u)
                text = text.replace(u, html, 1)
            return text
        except:
            return text

    @classmethod
    def getCustomerCode(cls):
        ''' 获取网站Code '''
        while True:
            _code = 'chat_'
            for i in range(6):
                _code += random.choice(string.ascii_letters + string.digits)
            if CustomerTable.find_one({'name': _code}):
                continue
            return _code

    @classmethod
    def check_client(cls, ua):
        ''' 判断客户端 '''
        ua_par = user_agents.parse(ua)
        _data = {}
        if 'mobile' in ua_par.browser.family.lower():
            _data['clientType'] = ClientTypes.Mobile
        elif ua_par.os.family.lower() in ['windows', 'linux', 'mac os x']:
            _data['clientType'] = ClientTypes.PC
        else:
            _data['clientType'] = ''

        if 'chrome' in ua_par.browser.family.lower():
            _data['browser_type'] = BrowserTypes.Chrome
        elif 'firefox' in ua_par.browser.family.lower():
            _data['browser_type'] = BrowserTypes.Firefox
        elif 'edge' in ua_par.browser.family.lower():
            _data['browser_type'] = BrowserTypes.Edge
        elif 'safari' in ua_par.browser.family.lower():
            _data['browser_type'] = BrowserTypes.Safari
        else:
            _data['browser_type'] = ''

        if 'linux' in ua_par.os.family.lower():
            _data['os_type'] = 'linux'
        elif 'windows' in ua.lower():
            _data['os_type'] = 'windows'
        elif 'mac os x' in ua.lower():
            _data['os_type'] = 'mac os x'
        else:
            _data['os_type'] = ''
        return _data

    @classmethod
    def planning_service(cls, site_code):
        ''' 分配客服 '''
        if not SERVICE_CONNECTION:
            return {}

        service_datas = CmsUserModel.find_many({'online_statu': OnlineStatu.online, 'responsible_site': site_code, 'dialogue_statu': True})
        uuids = []
        service_data_dicts = {}
        for service_data in service_datas:
            if service_data.get('role_code') in [PermissionCls.SUPERADMIN, PermissionCls.AgentAdmin]:
                continue
            _suuid = service_data.get('uuid')
            service_data_dicts[_suuid] = service_data
            uuids.append(_suuid)

        planning_total = {}
        for service_id in SERVICE_CONNECTION:
            if service_id not in uuids:
                continue
            _tal = ChatConversationTable.count({'service_id': service_id, '$or': [{'statu': ConversationStatu.normal}, {'statu': ConversationStatu.waiting}]}) or 0
            _ud = service_data_dicts.get(service_id) or {}
            if not _ud:
                continue
            reception_count = int(_ud.get('reception_count') or 0)
            if _tal >= reception_count:
                continue
            planning_total[service_id] = _tal

        if not planning_total:
            return {}

        student_tuplelist_sorted = sorted(planning_total.items(), key=lambda x: x[1], reverse=False)
        crr_service_id = student_tuplelist_sorted[0][0]
        service_data = service_data_dicts.get(crr_service_id)
        return service_data

    @classmethod
    def generate_chatCache(cls, text):
        ''' 生成前端缓存id '''
        return 'chat' + text

    @classmethod
    def analysis_chatCache(cls, text):
        ''' 解析前端缓存id '''
        if text and len(text) == 26:
            return text[4:]

    @classmethod
    def get_sid_service_id(cls, sid):
        ''' 根据sid, 从在线客服中获取客服的uuid '''
        for service_id, _ddd in SERVICE_CONNECTION.items():
            if _ddd.get('sid') == sid:
                return service_id
        return ''

    @classmethod
    def get_service_sid_present_count(cls, service_sid):
        ''' 获取客服的客户当前在线数量 '''
        c = 0
        for k, v in CLIENT_CONNECTION.items():
            if v.get('service_sid') == service_sid:
                c += 1
        return c

    @classmethod
    def get_service_id_present_count(cls, service_sid):
        ''' 获取客服的客户当前在线数量 '''
        c = 0
        for k, v in CLIENT_CONNECTION.items():
            if v.get('service_id') == service_sid:
                c += 1
        return c

    @classmethod
    def get_conversation_id_to_CLIENT_DATA(cls, conversation_id):
        ''' 根据会话id, 获取客户连接信息 '''
        for k, v in CLIENT_CONNECTION.items():
            if v.get('conversation_id') == conversation_id:
                v.update({'sid': k})
                return v
        return {}

    @classmethod
    def update_cilent_data(cls, service_id, service_sid):
        crr_data = {}
        crr_sid = ''
        for k, v in CLIENT_CONNECTION.items():
            if v.get('service_id') == service_id:
                crr_data = v
                crr_sid = k
                break
        if crr_data and crr_sid:
            crr_data.update({'service_sid': service_sid})
            CLIENT_CONNECTION.update({crr_sid: crr_data})

    @classmethod
    def get_conrl_imges_types(cls):
        data = []
        if hasattr(SITE_CONFIG_CACHE, 'control_file_types'):
            control_file_types = getattr(SITE_CONFIG_CACHE, 'control_file_types')
            if not control_file_types:
                return ''
            for t in control_file_types:
                if t in IMAGES_TYPES:
                    data.append(t)
        if data:
            return ','.join(data)
        return ''

    @classmethod
    def getIpAddr(cls, ip):
        try:
            ipobj = ipaddress.ip_address(ip)
            if ipobj.version == 4:
                url = 'https://api.ip2location.io/?key=AD11EBCA2F00FC54072C90D695451981&ip=' + ip
                try:
                    res = requests.get(url, timeout=15)
                    data_json = res.json()
                    if data_json.get('error'):
                        return
                    if not data_json.get('ip'):
                        return
                    return data_json
                except:
                    return
            elif ipobj.version == 6:
                return cls.get_location(ip)
            else:
                return "Unknown"
        except ValueError:
            return "Invalid IP address"
    @classmethod
    def get_country_name(cls,country_code):
        try:
            response = requests.get(f"https://restcountries.com/v3.1/alpha/{country_code}")
            if response.status_code == 200:
                data = response.json()
                return data[0]['name']['common']
            else:
                print("Failed to get country name. Status code:", response.status_code)
                return None
        except Exception as e:
            print("Error:", e)
            return None

    @classmethod
    def get_location(cls, ip_address):
        try:
            # Send HTTP request to ipinfo.io API
            response = requests.get(f"https://ipinfo.io/{ip_address}/json")
            
            # Check if request was successful
            if response.status_code == 200:
                # Parse JSON response
                data = response.json()
                
                # Extract location information
                country_code = data.get('country')
                country_name = cls.get_country_name(country_code)
                region_name = data.get('region')
                city_name = data.get('city')
                latitude, longitude = data.get('loc', '').split(',')
                time_zone = data.get('timezone')
                
                return {
                    'country_name': country_name,
                    'region_name': region_name,
                    'city_name': city_name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'time_zone': time_zone
                }
            else:
                print("Failed to get location. Status code:", response.status_code)
                return None
        except Exception as e:
            print("Error:", e)
            return None

    @classmethod
    def getUtcTime(cls, crrdate, strftimeStr='%Y-%m-%d %H:%M:%S'):
        crrtime = datetime.datetime.utcnow()
        return crrtime.strftime(strftimeStr)

    # @classmethod
    # def translateText_func(cls, msgtext, site_Data={}, site_code=''):
    #     result = {}
    #     result['msgtext'] = msgtext
    #     if not site_Data:
    #         site_Data = SITE_DICT_CACHE.get(site_code)
    #         if not site_Data:
    #             return result
    #     translate_state = site_Data.get('translate_state')
    #     site_language = site_Data.get('site_language')
    #     if not translate_state or not site_language:
    #         return result
    #
    #     target_language_code = LANGUAGE.lang_code.get(site_language) or 'en'
    #     try:
    #         _new_mag_text = translate_text(msgtext, target_language=target_language_code)
    #         result['msgtext'] = msgtext
    #         result['target_language'] = _new_mag_text
    #     except:
    #         pass
    #     return result

    @classmethod
    def timeZone_transform(cls, crr_time, timeZone='UTC+08:00'):
        if not isinstance(crr_time, datetime.datetime):
            return crr_time
        if not timeZone or timeZone == 'UTC+08:00':
            return crr_time
        if '-' in timeZone:
            zz = timeZone.split('-')[-1]
            h, t = zz.split(':')
            return crr_time - datetime.timedelta(hours=8) - datetime.timedelta(hours=int(h)) - datetime.timedelta(minutes=int(t))

        zz = timeZone.split('+')[-1]
        h, t = zz.split(':')
        return crr_time - datetime.timedelta(hours=8) + datetime.timedelta(hours=int(h)) + datetime.timedelta(minutes=int(t))

async def disconnect(sid, namespace=''):
    if namespace == '/chat': 
        ws = CHAT_NAMESPACE_CONNECTIONS.get(sid)
        if ws:
            await ws.close()
            CHAT_NAMESPACE_CONNECTIONS.pop(sid)
            return
    
    if namespace == '/serviceChat':
        ws = SERVICECHAT_NAMESPACE_CONNECTIONS.get(sid)
        if ws:
            await ws.close()
            SERVICECHAT_NAMESPACE_CONNECTIONS.pop(sid)
            return   
     
async def emit(event_id, data, namespace='', broadcast=False, room = ''):
    senddata = json.dumps({
        "event_id": event_id,
        "msg": data
    })

    if namespace == '/serviceChat':
        if broadcast:
            for ws in SERVICECHAT_NAMESPACE_CONNECTIONS.values():
                try:
                    await ws.send(senddata)
                except:
                    pass
        else:
            if room:
                ws = SERVICECHAT_NAMESPACE_CONNECTIONS.get(room)
                if ws:
                    try:
                        await ws.send(senddata)
                    except:
                        pass
        return
    elif namespace == '/chat':
        if broadcast:
            for ws in CHAT_NAMESPACE_CONNECTIONS.values():
                try:
                    await ws.send(senddata)
                except:
                    pass
            return
        else:
            if room:
                ws = CHAT_NAMESPACE_CONNECTIONS.get(room)
                if ws:
                    try:
                        await ws.send(senddata)
                    except:
                        pass
        return
    
  