# -*- coding: utf-8 -*-
from . import dbModel
from werkzeug.security import generate_password_hash, check_password_hash


class CmsUserModel(dbModel):
    """CMS-管理员表"""
    __tablename__ = 'cms_user_table'
    uuid = dbModel.UUIDField()
    id = dbModel.IDField()
    username = dbModel.StringField('姓名', nullable=False, is_index=True)
    account = dbModel.StringField('登录账户名', nullable=False)
    password = dbModel.PasswordField('密码',nullable=False)
    nickname = dbModel.StringField('昵称', nullable=False)
    zalo = dbModel.StringField('zalo')
    telephone = dbModel.StringField('电话')
    email = dbModel.StringField('邮箱')
    portrait = dbModel.StringField('头像')
    statu = dbModel.BooleanField('状态', default=True, nullable=False, true_text='正常', false_text='禁用', is_index=True)
    _create_time = dbModel.DateTimeField('创建时间', nullable=False)
    _current_login = dbModel.DateTimeField('最后登录时间')
    _last_login_time = dbModel.DateTimeField('上次登录时间')
    _last_login_ip = dbModel.StringField(u'上次登录IP')
    intro = dbModel.StringField('介绍')
    note = dbModel.StringField('备注')
    role_code = dbModel.StringField('角色')
    dialogue_statu = dbModel.BooleanField('对话状态', is_index=True, nullable=False)
    permissions = []
    online_statu = dbModel.StringField('在线状态', is_index=True)
    responsible_site = dbModel.StringField('负责的网站code', is_index=True)
    reception_count = dbModel.IntegerField('客服接待数量', default=5)
    language = dbModel.StringField('语言')
    super_admin_id = dbModel.StringField('上级ID', is_index=True)
    zy_finish_time = dbModel.DateTimeField('代理商租用到期时间')
    create_admin_count = dbModel.IntegerField('创建网站数量')
    create_cust_service_count = dbModel.IntegerField('创建客服数量')
    is_activate = dbModel.BooleanField('激活')
    beep_switch =dbModel.BooleanField('提示音开关')
    seee_end_time = dbModel.IntegerField('会话自动结束时间/秒')

    @classmethod
    def field_sort(cls):
        return ['id', 'telephone', 'account', 'email', 'statu', '_create_time', 'note']
    @classmethod
    def field_search(cls):
        return ['statu', 'username', 'account', 'note', '_create_time', 'role_code', 'responsible_site']
    @classmethod
    def add_field_sort(cls):
        return ['username', 'account', 'password', 'zalo', 'email', 'note']
    @classmethod
    def edit_field_sort(cls):
        return ['username', 'account', 'email', 'zalo', 'note']

    @property
    def is_superadmin(self):
        if self.permissions == ['superadmin']:
            return True
        return

    def has_permission(self, *args):
        if self.is_superadmin:
            return True
        for p in args:
            if p and p in self.permissions:
                return True
        return False

    @classmethod
    def encry_password(cls, raspwd):
        return generate_password_hash(raspwd)

    @classmethod
    def check_password(cls, pwd, rawpwd):
        """
        :param pwd: 密文
        :param rawpwd: 明文
        """
        return check_password_hash(pwd, rawpwd)
