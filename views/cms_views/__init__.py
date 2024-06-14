# -*- coding: utf-8 -*-
from sanic import Blueprint
from functools import wraps
from constants import SITE_CONFIG_CACHE, UrlPrefix

url_prefix = ''
if SITE_CONFIG_CACHE.cms_prefix:
    url_prefix = '/%s' % SITE_CONFIG_CACHE.cms_prefix
else:
    url_prefix = UrlPrefix.CMS_PREFIX
bp = Blueprint('admin',  url_prefix=url_prefix)


def front_login_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
            return func(*args,**kwargs)
    return wrapper
