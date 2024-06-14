# -*- coding: utf-8 -*-
from sanic import Blueprint
from constants import UrlPrefix

bp = Blueprint('common', url_prefix=UrlPrefix.COMMON_PREFIX)
