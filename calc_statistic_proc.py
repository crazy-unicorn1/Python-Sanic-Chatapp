# -*- coding: utf-8 -*-
import os, datetime, click, time, requests
from app_kfShare import app, ProjectConfig, PUBLIC_FOLDER
# from app_kfDemo import app, ProjectConfig, PUBLIC_FOLDER
from common_utils.lqredis import SiteRedis
from constants import PermissionCls, OnlineStatu, OPERATION_TYPES
from models.cms_user import CmsUserModel
from models.cms_table import SiteConfigModel
from models.site_table import SiteTable
from models.kefu_table import CustomerTable, ChatConversationTable, ChatContentTable, BlacklistTable, LeavingMessageTable, QuickReplyTable, FinishListTable, IpTable, StatisticTable, signLogTable, systemLogTable
from modules.site_module.ftpCls import FtpCls
from bson import ObjectId

def proc_statistic(_dd, _start_time, _end_time):
    data_from = {}
    data_from["user_uuid"] = _dd.get("uuid")
    conversation_data = ChatConversationTable.find_one({
        'service_id': _dd.get('uuid'),
        'create_time': {'$gte': _start_time, '$lte': _end_time},
    }) or {}

    distinct_conversation_ids = ChatContentTable.distinct("conversation_id", {
        "service_id": _dd.get('uuid'),
        'create_time': {'$gte': _start_time, '$lte': _end_time},
        })

    total_delay_duration = datetime.timedelta(days=0, hours=0, minutes=0)
    total_delay_count = 0
    first_reply_delay_time = 0

    for known_conversation_id in distinct_conversation_ids:
        matching_documents = ChatContentTable.find_many({
            "conversation_id": known_conversation_id
        })

        lastFlag = 0
        lastTime = datetime.datetime(1, 1, 1, 0, 0, 0, 0)

        first_reply = 0
        for document in matching_documents:
            newFlag = 1 if document.get('service_id') is not None else -1

            if newFlag == 1 and lastFlag == -1:
                if first_reply == 0:
                    first_reply_delay_time = document.get('create_time') - lastTime
                    first_reply = 1

                total_delay_duration += document.get('create_time') - lastTime
                total_delay_count += 1
            
            lastTime = document.get('create_time')
            lastFlag = newFlag

    data_from['first_reply_delay_time'] = first_reply_delay_time
    if first_reply_delay_time == 0:
        data_from['first_reply_delay_time'] = 0
    else:
        data_from['first_reply_delay_time'] = first_reply_delay_time.total_seconds()
        
    data_from['total_delay_duration'] =  total_delay_duration.total_seconds()
    data_from['total_delay_count'] =  total_delay_count

    conversation_datas = ChatConversationTable.find_many({
        'service_id': _dd.get('uuid'),
        'create_time': {'$gte': _start_time, '$lte': _end_time}, 
    }) or []

    negative_score_count = 0
    positive_score_count = 0

    negative_score_points = 0
    positive_score_points = 0
    score_count = len(conversation_datas)

    for conv_data in conversation_datas:
        if conv_data.get('score_level') >= 3:
            positive_score_count += 1
            positive_score_points += conv_data.get('score_level')
        else:
            negative_score_count += 1
            negative_score_points += conv_data.get('score_level')

    data_from['positive_score_count'] =  positive_score_count
    data_from['score_count'] =  score_count


    sign_logs = signLogTable.find_many({
        'user_id': _dd.get('uuid'),
            'create_time': {'$gte': _start_time, '$lte': _end_time}, 
        }) or []

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

    data_from['login_time'] =  login_time

    ################################################################
    system_logs = systemLogTable.find_many({
        'user_id': _dd.get('uuid'),
            'create_time': {'$gte': _start_time, '$lte': _end_time}, 
        }) or []

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

    data_from['online_time'] =  online_time
    data_from['offline_time'] =  offline_time
    data_from['busy_time'] =  busy_time

    # Format the string in the desired format
    #  Start Online time, busy time, no reply time(offline time)    
    no_reply_count = 0
    for known_conversation_id in distinct_conversation_ids:
        matching_documents_counts = ChatContentTable.count({
            "conversation_id": known_conversation_id
        })

        if matching_documents_counts == 1:
            no_reply_count += 1

    data_from['no_reply_count'] =  no_reply_count
    data_from['create_time'] =  _start_time

    data_from["_id"] = ObjectId()
    StatisticTable.insert_one(data_from)

def calc_chat_statistic():
    users = CmsUserModel.find_many({"role_code": {"$ne": PermissionCls.SUPERADMIN}})
    for _dd in users:
        xx = StatisticTable.find_one({"user_uuid": _dd.get("uuid")}, sort = [['create_time', -1]])
        if not xx:
            s = ChatContentTable.find_one({"service_id": _dd.get("uuid")}, sort = [['create_time', 1]])
            if s:
                _start_time = s.get("create_time").replace(minute=0, second=0, microsecond=0)
            else: 
                continue
        else:
            last_time = xx.get("create_time")
            _start_time = last_time + datetime.timedelta(hours=1)

        while _start_time < datetime.datetime.now():
            _end_time = _start_time + datetime.timedelta(hours=1)
            proc_statistic(_dd, _start_time, _end_time)
            _start_time = _end_time


    while True:
        now = datetime.datetime.now()
        if now.minute == 0 and now.second == 0:
            _end_time = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
            _start_time = _end_time - datetime.timedelta(hours=1)
            users = CmsUserModel.find_many({"role_code": {"$ne": PermissionCls.SUPERADMIN}})

            for _dd in users:
                proc_statistic(_dd, _start_time, _end_time)
        
        time.sleep(1)
#     x = 0

if __name__ == '__main__':
    calc_chat_statistic()
