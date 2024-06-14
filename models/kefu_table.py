from . import dbModel
import shortuuid



class BlacklistTable(dbModel):
    ''' 黑名单 '''
    uuid = dbModel.UUIDField()
    site_code = dbModel.StringField('网站', is_index=True)
    customer_id = dbModel.StringField('客户ID', is_index=True)
    ip = dbModel.StringField('IP', is_index=True)
    _create_time = dbModel.DateTimeField('操作时间',  nullable=False)
    expire_time = dbModel.DateTimeField('截止时间')
    duration = dbModel.StringField('时长')
    operation_uuid = dbModel.StringField('操作人', is_index=True)
    note = dbModel.StringField('备注')

    @classmethod
    def field_search(cls):
        return ['ip']



class CustomerTable(dbModel):
    ''' 访客 '''
    uuid = dbModel.UUIDField()
    name = dbModel.StringField('名称', is_index=True)
    username = dbModel.StringField('姓名', is_index=True)
    _create_time = dbModel.DateTimeField('创建时间', nullable=False)
    site_code = dbModel.StringField('网站', is_index=True)
    ip = dbModel.StringField('IP地址')
    track = dbModel.StringField('轨迹') # IP归属地
    address = dbModel.StringField('地址')
    telephone = dbModel.StringField('电话')
    telegram = dbModel.StringField('telegram')
    note = dbModel.StringField('说明')
    gender = dbModel.StringField('性别')
    email = dbModel.StringField('邮箱')
    ip_info_json = {} #ip信息
    is_transfer = dbModel.BooleanField('是否转接', is_index=True)
    category = dbModel.StringField('category') # customer category

    @classmethod
    def field_search(cls):
        return ['ip', 'site_code','name', 'username', 'telephone', 'telegram']



class ChatConversationTable(dbModel):
    ''' 聊天会话 '''
    uuid = dbModel.UUIDField()
    usid = dbModel.StringField('会话id')
    start_time = dbModel.DateTimeField('进入时间')
    end_time = dbModel.DateTimeField('结束时间')
    waiting_time = dbModel.DateTimeField('等待时间')
    service_id = dbModel.StringField('接待客服', is_index=True)
    os_type = dbModel.StringField('系统类型', is_index=True)
    browser_type = dbModel.StringField('浏览器', is_index=True)
    client_type = dbModel.StringField('客户端类型', is_index=True)
    create_time = dbModel.DateTimeField('创建时间', nullable=False)
    site_code = dbModel.StringField('网站', is_index=True)
    ip =  dbModel.StringField('IP地址', is_index=True)
    customer_id = dbModel.StringField('客户id', is_index=True)
    statu = dbModel.StringField('会话状态', is_index=True)
    disconnect_tiem = dbModel.DateTimeField('连接断开时间')
    score_level = dbModel.IntegerField('评分等级')
    score_text = dbModel.StringField('评分描述')
    track = dbModel.StringField('轨迹') # IP归属地

    @classmethod
    def field_search(cls):
        return ['site_code', 'service_id', 'ip', 'start_time', 'customer_id']



class ChatContentTable(dbModel):
    ''' 聊天内容 '''
    uuid = dbModel.UUIDField()
    text = dbModel.StringField('内容')
    file_path = dbModel.StringField('文件路径')
    content_type = dbModel.StringField('类型', is_index=True)
    filename = dbModel.StringField('文件名', is_index=True)
    file_size = dbModel.FloatField('文件大小/kb', is_index=True)
    create_time = dbModel.DateTimeField('通讯时间', nullable=False)
    customer_id = dbModel.StringField('访客id', is_index=True)
    service_id = dbModel.StringField('客服id', is_index=True)
    conversation_id = dbModel.StringField('会话id', is_index=True)
    service_reading_state = dbModel.BooleanField('阅读状态')
    is_automatic = dbModel.BooleanField('自动回复')
    is_retract = dbModel.BooleanField('撤回消息')
    temporary_data_id = dbModel.StringField('前端临时消息id')
    site_code = dbModel.StringField('网站', is_index=True)
    customer_reading_state = dbModel.BooleanField('客户信息阅读状态') # 客户是否阅读
    is_clew_text = dbModel.BooleanField('网站提示语')
    is_transfer_text = dbModel.BooleanField('是否转接提示语')



class StatisticTable(dbModel):
    __tablename__ = 'statistic_table'
    ''' 聊天内容 '''
    uuid = dbModel.UUIDField()
    user_uuid = dbModel.StringField('文件路径', is_index = True)
    first_reply_delay_time = dbModel.FloatField("time")
    total_delay_duration = dbModel.FloatField("time"),
    total_delay_count = dbModel.IntegerField("time")
    positive_score_count = dbModel.IntegerField("time")
    score_count = dbModel.IntegerField("time")
    login_time = dbModel.FloatField("time")
    online_time = dbModel.FloatField("time")
    offline_time = dbModel.FloatField("time")
    busy_time = dbModel.FloatField("time")
    no_reply_count = dbModel.IntegerField("time")


class LeavingMessageTable(dbModel):
    ''' 留言 '''
    uuid = dbModel.UUIDField()
    text = dbModel.StringField('留言内容')
    _create_time = dbModel.DateTimeField('时间', nullable=False)
    customer_id = dbModel.StringField('访客id', is_index=True)
    telephone = dbModel.StringField('电话', is_index=True)
    email = dbModel.StringField('邮箱', is_index=True)
    qq = dbModel.StringField('QQ', is_index=True)
    username = dbModel.StringField('姓名', is_index=True)
    site_code = dbModel.StringField('网站', is_index=True)
    ip = dbModel.StringField('IP地址', nullable=False)
    statu = dbModel.BooleanField('处理状态')
    operator_id = dbModel.StringField('操作人')

    @classmethod
    def field_search(cls):
        return [
            'telephone', 'username', 'site_code', 'ip', 'name', 'operator_id', 'statu'
        ]



class QuickReplyTable(dbModel):
    ''' 快捷回复 '''
    __tablename__ = 'quick_reply_table'
    uuid = dbModel.UUIDField()
    index = dbModel.IntegerField('索引序号')
    title = dbModel.StringField('标题')
    text = dbModel.StringField('内容')
    _create_time = dbModel.DateTimeField('时间', nullable=False)
    service_id = dbModel.StringField('客服id', is_index=True)
    site_code = dbModel.StringField('网站', is_index=True)



class FinishListTable(dbModel):
    ''' 会话结束列表 '''
    uuid = dbModel.UUIDField()
    service_id = dbModel.StringField('客服id', is_index=True)
    conversation_id = dbModel.StringField('会话id', is_index=True)
    customer_id = dbModel.StringField('访客id', is_index=True)



class IpTable(dbModel):
    ''' IP库 '''
    __tablename__ = 'ip_table'
    uuid = dbModel.UUIDField()
    ip = dbModel.StringField('IP')
    country_name = dbModel.StringField('国家')
    region_name = dbModel.StringField('省份')
    city_name = dbModel.StringField('城市')
    latitude = dbModel.StringField('经度')
    longitude = dbModel.StringField('维度')
    time_zone = dbModel.StringField('时区')
    create_time = dbModel.DateTimeField('时间', nullable=False)



class problemTable(dbModel):
    '问题'
    __tablename__ = 'problem_table'
    uuid = dbModel.UUIDField()
    title = dbModel.StringField('标题')
    answer = dbModel.StringField('答案')
    create_time = dbModel.DateTimeField('时间', nullable=False)
    site_code = dbModel.StringField('网站', is_index=True)

class categoryTable(dbModel):
    'category'
    __tablename__ = 'category_table'
    uuid = dbModel.UUIDField()
    category = dbModel.StringField('标题')
    create_time = dbModel.DateTimeField('时间', nullable=False)
    site_code = dbModel.StringField('网站', is_index=True)
    @classmethod
    def count(cls,filter=None, session=None, **kwargs):
        return cls.collection().count_documents(filter=filter, session=session, **kwargs)
    @classmethod
    def save(cls, data_dict):
        uuid = data_dict.get('uuid')
        if not uuid:
            uuid = shortuuid.uuid()
            data_dict['uuid'] = uuid
        if data_dict.get('_id'):
            cls.collection().update_one({"uuid": data_dict['uuid']}, {"$set": data_dict})
        else:
            cls.insert_one(data_dict)
        return uuid
    

# 系统操作日志
class systemLogTable(dbModel):
    __tablename__ = 'system_log'
    uuid = dbModel.UUIDField()
    user_id = dbModel.StringField('操作人ID')
    operation_type = dbModel.StringField('操作类型')
    note = dbModel.StringField('备注')
    ip = dbModel.StringField('IP')
    create_time = dbModel.DateTimeField('时间', nullable=False)
    site_code = dbModel.StringField('网站Code')

    @classmethod
    def field_search(cls):
        return [
            'site_code',
            'operation_type',
            'create_time',
            'note',
        ]

class signLogTable(dbModel):
    __tablename__ = 'sign_log'
    uuid = dbModel.UUIDField()
    user_id = dbModel.StringField('操作人ID')
    operation_type = dbModel.StringField('操作类型')
    ip = dbModel.StringField('IP')
    create_time = dbModel.DateTimeField('时间', nullable=False)
    site_code = dbModel.StringField('网站Code')

    @classmethod
    def field_search(cls):
        return [
            'site_code',
            'operation_type',
            'create_time',
            'note',
        ]



#
class CacheDataTable(dbModel):
    __tablename__ = 'cache_data_table'
    mkey = dbModel.StringField('mkey', is_index=True, unique=True)


