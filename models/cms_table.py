# -*- coding: utf-8 -*-
from . import dbModel
from constants import SITE_CONFIG_CACHE, FRONT_CONFIG_CACHE


class SiteConfigModel(dbModel):
    """网站配置"""
    __tablename__ = 'site_config_table'
    uuid = dbModel()
    project_name = dbModel.StringField('项目名', nullable=False)
    secret_key = dbModel.StringField('项目秘钥', nullable=False)
    cms_prefix = dbModel.StringField('CMS登录目录', nullable=False)
    max_filesize = dbModel.IntegerField('项目最大文件限制/KB')
    cms_text = dbModel.StringField('后台名称')
    cms_icon = dbModel.StringField('后台ICON图标')
    front_domain = dbModel.StringField('网站前端域名', nullable=False)
    cms_domain = dbModel.StringField('网站后台域名', nullable=False)

    # 网站功能
    site_statu = dbModel.BooleanField('网站状态', default=0, true_text='已开启', false_text='已关闭')
    cms_captcha = dbModel.BooleanField('CMS登录图片验证码', default=0, true_text='已开启', false_text='已关闭')
    cms_log_save_time = dbModel.IntegerField('CMS操作日志保存时间/天')
    front_log_save_time = dbModel.IntegerField('前端日志保存时间/天')

    cms_ip_whitelist = dbModel.StringField('后台ip白名单')

    control_file_type_state = dbModel.BooleanField('控制上传文件类型', nullable=False)
    control_file_types = []

    automati_creply = dbModel.StringField('自动回复')
    automati_creply_time = dbModel.StringField('自动回复时间')
    automati_close_time = dbModel.StringField('自动结束对话时间')
    
    control_file_size = dbModel.FloatField('文件大小/KB', default=10485760)
    site_domain = dbModel.StringField('网站域名')
    google_verify_statu = dbModel.BooleanField('谷歌登录验证开关')

    @classmethod
    def update_site_config(cls, config={}):
        if not config:
            config = cls.find_one({}) or {}
        SITE_CONFIG_CACHE.__dict__.update(config)



class FrontConfigModel(dbModel):
    """前端网站配置"""
    __tablename__ = 'front_config_table'
    uuid = dbModel.UUIDField()
    site_name = dbModel.StringField('网站名称')
    site_icon = dbModel.ImagesField('网站icon图标')
    site_logo = dbModel.ImagesField('网站LOGO')

    @classmethod
    def update_site_config(cls, config={}):
        if not config:
            config = cls.find_one({}) or {}
        FRONT_CONFIG_CACHE.__dict__.update(config)

