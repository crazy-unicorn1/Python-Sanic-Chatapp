# -*- coding:utf-8 -*-
from views.cms_views import bp as cms_bp
from views.front_views import bp as front_bp
from views.common_views import bp as common_bp
from views.common_views.common_view import img_cap

from views.cms_views.cms_view import CmsIndexView
from views.cms_views.customer_view import CustomerView
from views.cms_views.chat_view import ChatServiceView
from views.cms_views.history_view import ChatHistoryView
from views.cms_views.leavingMsg import LeavingMsgView
from views.cms_views.user_view import userManageView
from views.cms_views.setting_view import SettingView, SiteManageView, BlacklistView, problemListView, categoryCustomersView, systemLogView, OtherSetupView, quickReplyView, SiteDomainManageView, downloadFileListView
from views.cms_views.cms_login import CmsLogin, CmsLoginOut


from views.front_views.front_view import FrontIndex, FrontChatView, winChatView, acquireBackupView

from views.api_views import api_view


CMS_VIEWS = [
    CmsIndexView,
    CmsLogin, CmsLoginOut, CustomerView, ChatServiceView, ChatHistoryView, LeavingMsgView, SettingView, SiteManageView, userManageView, BlacklistView, problemListView, categoryCustomersView, systemLogView, OtherSetupView, quickReplyView, SiteDomainManageView, downloadFileListView
]

API_VIEWS = [
]

FRONT_VIEWS = [
    FrontIndex, FrontChatView, winChatView, acquireBackupView
]



for view_cls in CMS_VIEWS:
    if not hasattr(view_cls, 'add_url_rules'):
        continue
    if not getattr(view_cls, 'add_url_rules'):
        continue
    for rule in view_cls.add_url_rules:
        try:
            #cms_bp.add_url_rule(rule[0], view_func=view_cls.as_view(rule[1]))
            cms_bp.add_route(view_cls.as_view(), rule[0])
        except Exception as e:
            print(f'{view_cls.__name__}  error:', e)
            exit()

for view_cls in FRONT_VIEWS:
    if not hasattr(view_cls, 'add_url_rules'):
        continue
    if not getattr(view_cls, 'add_url_rules'):
        continue
    for rule in view_cls.add_url_rules:
        try:
            #front_bp.add_url_rule(rule[0], view_func=view_cls.as_view(rule[1]))
            front_bp.add_route(view_cls.as_view(), rule[0])
        except Exception as e:
            print(f'{view_cls.__name__}  error:', e)
            exit()

