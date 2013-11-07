#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import xmlrpclib
from Queue import Queue
from threading import Thread
from pymongo import Connection
from bson.objectid import ObjectId
from socket import error as SocketError

from db import documents, set_server, set_server_status, set_web, set_web_status
temperatures, server, location, server_status = documents()

con = Connection()
db = con.ServerMonitor

web = db.web
#server = mon.server
#location = mon.location
#temperatures = mon.temperature
#server_status = mon.server_status
web_status = db.web_status

def get_server():
    servers = server.find()
    return servers

def connect(ip):
    try:
        RemoteServer = xmlrpclib.ServerProxy("http://%s" % ip)
    except SocketError:
        return 0
    return RemoteServer

#def set_server_values(id, remote):
#    """
#    set server values in mongodb
#    """


def init_server(oid):
    '''
    after do_create_server() in sery.py
    init the server1
    '''
    a = server.find_one({'_id':ObjectId(oid)})
    remote = connect(a['ip'])
    server.update({'_id':ObjectId(oid)},
                  {'$set':
                       dict(
                            node = remote.get_node(),
                            uname = remote.get_uname(),
                            cpu_info = remote.cpu_info(),
                            system = remote.get_system(),
                        )
                  })

def init_web(oid):
    """
    set web values in mongodb
    """
    target = web.find_one({"_id":ObjectId(oid)})
    monitor = WebMonitor(target['url'])
    db.web.update({'_id':ObjectId(oid)},
                  {'$set':
                       dict(
                            title = monitor.get_title(),
                            encoding = monitor.get_encoding(),
                            content_type=monitor.content_type(),
                        )
                  })

def create_server_status(oid):
    """
    create server status function
    in the daemon thread
    """
    try:
        oip = server.find_one({'_id':ObjectId(oid)})['ip']
        remote = connect(oip)
        dic = {
            'server_ID': oid,
            'load_avg': remote.load_avg(),
            'mem_info': remote.mem_info(),
            'net_stat': remote.net_stat(),
            'cpu_usage': remote.cpu_usage(),
            'disk_stat': remote.disk_stat(),
            'up_time': remote.uptime_stat(),
            'datetime': datetime.datetime.now(),
            }
        set_server(oid, {'status_now': 0,}) # update "server
        set_server_status(dic)
        print('update server %s' % oid)
    except SocketError:
        dic = {'status_now': 1,} #无法连接
        set_server(oid, dic)

from web_monitor import WebMonitor

def create_web_status(oid):
    try:
        target = web.find_one({"_id":ObjectId(oid)})
        monitor = WebMonitor(target['url'])
        dic = {
            'web_ID': oid,
            'title': monitor.get_title(),
            'encoding': monitor.get_encoding(),
            'total_name': monitor.total_time(),
            'content_type': monitor.content_type(),
            'name_look_up': monitor.name_look_up(),
            'connect_time': monitor.connect_time(),
            'status_code': monitor.get_status_code(),
            'per_transfer_time': monitor.per_transfer_time(),
            'content_encoding': monitor.get_content_encoding(),
            'start_transfer_time': monitor.start_transfer_time(),
            'keywords': monitor.contain_keyword(target['keywords']),
        }
        set_web(oid, {'status_now': 0,})
        set_web_status(dic)
    except SocketError:
        set_web(oid, {'status_now': 1,})
