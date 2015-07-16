#! /usr/bin/env python
# -*-coding:utf-8 -*-

import sys
from gameinfo import GameInfo
from connhandle import buildConnection, sendMsgToServer, listenServerInfo
from util import writeLog, fileClean, setFileName

if __name__ == '__main__':
	uip = sys.argv[1]
	uport = int(sys.argv[2])
	myip = sys.argv[3]
	myport = int(sys.argv[4])
	myid = sys.argv[5]
	myname = 'kobe'
	
	print '\ngameserver ip: ', uip
	print 'gameserver port: ', uport
	print 'my ip: ', myip
	print 'my port: ', myport  
	print 'my id:', myid
	print 'my name: ', myname
	setFileName(myid)
	fileClean()

	gameinfo = GameInfo()
	gameinfo.myid = myid
	skt = buildConnection(myip, myport, uip, uport)
	# 发送注册信息
	regmsg = 'reg: %s %s\n' % (myid, myname)
	regSend = 'Send message: %s' %regmsg
	writeLog(regSend)
	sendMsgToServer(skt, regmsg)
	listenServerInfo(skt, gameinfo)