# -*- coding: utf-8 -*-
from redis import StrictRedis
from common_utils.mongodb import MongoCLS
from flask_socketio import SocketIO


mc = StrictRedis(host='127.0.0.1', port=6379)
db = MongoCLS()
socketio = SocketIO()

