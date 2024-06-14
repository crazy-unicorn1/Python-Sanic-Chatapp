# -*- coding: utf-8 -*-
from sanic  import Blueprint
from constants import SITE_CONFIG_CACHE, UrlPrefix

bp = Blueprint('front', UrlPrefix.FRONT_PREFIX)
