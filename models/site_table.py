from . import dbModel
from constants import SITE_DICT_CACHE, ExportStatu



class SiteTable(dbModel):
    ''' 网站 '''
    __tablename__ = 'sitetable'
    uuid = dbModel.UUIDField()
    site_name = dbModel.StringField('网站名称')
    link = dbModel.StringField('网站链接')
    _create_time = dbModel.DateTimeField('接入时间', nullable=False)
    site_code = dbModel.StringField('网站Code', is_index=True)
    site_language = dbModel.StringField('聊天界面语言')
    site_title = dbModel.StringField('网站标题')
    site_main_color = dbModel.StringField('网站主题颜色')
    site_right_info_back_color = dbModel.StringField('右侧信息栏背景颜色')
    site_right_info_img = dbModel.StringField('右侧信息栏图片')
    site_announcement = dbModel.StringField('网站公告')
    use_domain = dbModel.StringField('访问域名')
    clew_text = dbModel.StringField('网站提示语')
    site_icon = dbModel.StringField('网站Icon')
    beep_switch =dbModel.BooleanField('提示音开关')

    control_file_type_state = dbModel.BooleanField('控制上传文件类型', nullable=False)
    control_file_types = []

    automati_creply = dbModel.StringField('自动回复')
    automati_creply_time = dbModel.StringField('自动回复时间')
    automati_close_time = dbModel.StringField('自动结束对话时间')
    
    control_file_size = dbModel.FloatField('文件大小/KB', default=10485760)

    default_comment = dbModel.StringField('默认评论')
    finish_time = dbModel.DateTimeField('结束时间')
    ip_whitelist = dbModel.StringField('ip白名单')
    site_google_verify_statu = dbModel.BooleanField('谷歌登录验证开关')
    create_cust_service_count = dbModel.IntegerField('创建客服数量')

    fast_state = dbModel.BooleanField('快捷模式开启状态')
    translate_statu = dbModel.StringField('翻译开启状态')
    client_language = dbModel.StringField('客户语言')
    service_language = dbModel.StringField('客服语言')
    client_service_language = dbModel.StringField('客户端客服信息展示语言')
    service_client_language = dbModel.StringField('客服端客户信息展示语言')

    @classmethod
    def update_site_config(cls):
        while SITE_DICT_CACHE:
            for k in list(SITE_DICT_CACHE):
                SITE_DICT_CACHE.pop(k)
        _sds = cls.find_many({}) or []
        for sd in _sds:
            SITE_DICT_CACHE[sd.get('site_code')] = sd



class ExportDataModel(dbModel):
    """导出数据"""
    __tablename__ = 'export_data_table'
    uuid = dbModel.UUIDField()
    filename = dbModel.StringField('文件名', nullable=False, is_index=True)
    path = dbModel.StringField('文件路径', nullable=False)
    file_size = dbModel.IntegerField('文件大小(KB)', nullable=False)
    total = dbModel.IntegerField('数据量', nullable=False)
    out_count = dbModel.IntegerField('已导出')
    statu = dbModel.DictField('导出状态', dict_cls=ExportStatu, nullable=False, btn_show=True, is_index=True)
    note = dbModel.StringField('备注')
    site_code = dbModel.StringField('网站', is_index=True)
    operator_id = dbModel.StringField('操作人')
    create_time = dbModel.DateTimeField('通讯时间', nullable=False)

    @classmethod
    def field_search(cls):
        return ['statu', 'filename', 'create_time', 'note']

