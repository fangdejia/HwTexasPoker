#! /usr/bin/env python
# -*-coding:utf-8 -*-

'''
向Server发送：
1、注册信息：
	reg: pid pname eol #(eol为换行符)

2、行动消息：
	check|call|raise num|all_in|fold
	# 让牌|跟注|加注 num|全押|弃牌

	# 若需要跟注时check，强制跟注
	# 若加注金额小于当前最低注限，server强制补齐
	# 若内容非法，默认弃牌

从Server获取：

1、坐次消息：（与发牌和喊注次序息息相关）
	seat/
	button: pid jetton money #(庄家：用户id 筹码 持有金币)
	small blind: pid jetton money #(小盲注：......)
	(big blind: pid jetton money) #(大盲注：......) <0-1>
	(pid jetton monry) #(其他玩家信息)
	/seat

	# 剩下两个玩家时没有大盲注和后续座位信息

2、盲注消息：
	blind/
	(pid: bet)   #(用户id：赌注)<1-2> 
	/blind
	# 下盲注过程由服务器自动完成，用户不必考虑
	# 大盲注金额为小盲注的两倍，只有2个玩家时，没有大盲注信息

3、手牌消息：
	hold/
	color point #(花色 大小)
	color point #(花色 大小)
	/hold
	# 服务器下发两张手牌

4、询问消息：
	inquire/
	(pid jetton money bet blind|check|call|raise|all_in|fold)
	total pot: num
	/inquire
	# server向player询问行动决策
	# player在收到此询问消息后，发出action消息
	# 询问包含如下：
	a. 本手牌已行动过的所有玩家（包括被询问者和盲注）的手中筹码、剩余金币数、
	本手牌累计投注额、及最近一次有效action，按逆时针座次由近及远排列，上家排
	第一个
	b. 当前底池总金额

5、公牌消息：
	flop/
	color point
	color point
	color point
	/flop
	# 发出三张公牌

6、转牌消息：
	turn/
	color point
	/turn
	# 发出一张转牌

7、河牌消息：
	river/
	color point
	/river

8、摊牌消息：
	showdown/
		common/
		(color point) <5>
		/common

		(rank: pid color point color point nut_hand) <2-8>
		# rank为数字，表明次序
	/showdown
	# 
9、彩池分配消息：
	pot-win/
	(pid: num) <0-8>
	/pot-win
	# num为分配的数目

10、游戏结束消息：
	game-over \n
'''

import socket
import sys
import re
import thread
import decision
from gameinfo import Card, Player, GameInfo, Action, PlayerHistory
from util import writeLog

def buildConnection(myip = None, myport = 0, uip = None, uport = 0):
	skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	myaddr = (myip, myport)
	try:
		skt.bind(myaddr)
	except socket.error, msg:
		err = 'Binding Failure. Error Message: ' + msg[1]
		print err
		writeLog(err)

	uaddr = (uip, uport)
	try:
		skt.connect(uaddr)
	except socket.error, msg:
		err = 'Connection Failure. Error Message: ' + msg[1]
		print err
		writeLog(err)

	return skt

# 监听处理服务器发送的信息
def listenServerInfo(sock = None, gameinfo = None):
	print 'Client is waiting message from remote gameserver...'
	while True:
		msg = sock.recv(2048)
		if msg:
			writeLog('\nReceived Message: ')
			writeLog(msg)
			print '\nReceived message: '
			print msg
			# thread.start_new_thread(handleMsg, (sock, msg, gameinfo))
			handleMsg(sock, msg, gameinfo)
			msg = ''
		else:
			continue
# 发送信息到服务器gameserver
def sendMsgToServer(sock = None, msg = None):
	if msg:
		writeLog('\nSend My Operation: ')
		writeLog(msg)
		print '\nSend My Operation: '
		print msg
		try:
			sock.send(msg)
		except socket.error, msg:
			print 'Message Send Failure. Error Message: ' + msg[1]
	else:
		print 'None message to send!'

# 处理接收到的信息
def handleMsg(skt, msg, gameinfo):
	lines = msg.split('\n')
	for line in lines:
		if line == 'seat/ ':
			handleSeatMsg(gameinfo, msg)
		elif line == 'blind/ ':
			handleBlindMsg(gameinfo, msg)
		elif line == 'hold/ ':
			handleHoldMsg(gameinfo, msg)
		elif line == 'flop/ ':
			handleFlopMsg(gameinfo, msg)
		elif line == 'turn/ ':
			handleTurnMsg(gameinfo, msg)
		elif line == 'river/ ':
			handleRiverMsg(gameinfo,msg)
		elif line == 'pot-win/ ':
			handlePotMsg(gameinfo, msg)
		elif line == 'inquire/ ':
			handleInquireMsg(skt, gameinfo, msg)
		elif line == 'showdown/ ':
			handleShowdownMsg(gameinfo, msg)
		elif line == 'game-over ':
			handleGameOverMsg(skt)
		else:
			continue

def handleSeatMsg(gameinfo, msg):
	# 匹配收到的信息中是否有座次信息，有则处理，否则进行其他检查
	# 座次信息正则表达式
	seatMsgRe = r'seat/\s\s*\n([\s\S]*)\s\s*\n/seat'
	# 庄家信息：用户id 筹码 持有金币
	buttonMsgRe = r'button:\s+(\d+)\s+(\d+)\s+(\d+)'
	# 小盲注信息：用户id 筹码 持有金币
	smallBlindMsgRe = r'small\s+blind:\s+(\d+)\s+(\d+)\s+(\d+)'
	# 大盲注信息：用户id  筹码 持有金币
	bigBlindMsgRe = r'big\s+blind:\s+(\d+)\s+(\d+)\s+(\d+)'
	# 其他用户信息：用户id 筹码 持有金币
	norlmalMsgRe = r'(\d+)\s+(\d+)\s+(\d+)'
	seatItems = re.findall(seatMsgRe, msg)
	if seatItems:
		gameinfo.someDataClean()
		gameinfo.gameNum += 1
		writeLog('\nGet seat message: ')
		print 'Get seat message: '
		seatInfo = seatItems[0]
		seats = seatInfo.split('\n')
		normalSeats = 3
		# seats对应所有玩家，seat对应每一个玩家
		for seat in seats:
			buttonMatch = re.search(buttonMsgRe, seat)
			if buttonMatch:
				# role: button (BTN)
				seatRole = 1 
				id = buttonMatch.group(1)
				jetton = buttonMatch.group(2)
				money = buttonMatch.group(3)
				gameinfo.addNewPlayer(id, jetton, money, seatRole)
				print 'Add new player: '
				print 'role: button'
				print 'id: ', id
				print 'jetton: ', jetton
				print 'money: ', money
				continue
			smallBlindMatch = re.search(smallBlindMsgRe, seat)
			if smallBlindMatch:
				# role: small blind (SB)
				seatRole = 2
				id = smallBlindMatch.group(1)
				jetton = smallBlindMatch.group(2)
				money = smallBlindMatch.group(3)
				gameinfo.addNewPlayer(id, jetton, money, seatRole)
				print 'Add new player: '
				print 'role: small blind'
				print 'id: ', id
				print 'jetton: ', jetton
				print 'money: ', money
				continue
			bigBlindMatch = re.search(bigBlindMsgRe, seat)
			if bigBlindMatch:
				# role: big blind (BB)
				seatRole = 3
				id = bigBlindMatch.group(1)
				jetton = bigBlindMatch.group(2)
				money = bigBlindMatch.group(3)
				gameinfo.addNewPlayer(id, jetton, money, seatRole)
				print 'Add new player: '
				print 'role: big blind'
				print 'id: ', id
				print 'jetton: ', jetton
				print 'money: ', money
				continue
			normalMatch = re.search(norlmalMsgRe, seat)
			if normalMatch:
				# role: normal (EP EP MP MP LP)
				normalSeats += 1
				id = normalMatch.group(1)
				jetton = normalMatch.group(2)
				money = normalMatch.group(3)
				gameinfo.addNewPlayer(id, jetton, money, normalSeats)
				print 'Add new player: '
				print 'role: normal'
				print 'id: ', id
				print 'jetton: ', jetton
				print 'money: ', money
				continue

def handleBlindMsg(gameinfo, msg):
	# 处理盲注消息：
	blindMsgRe = r'blind/\s*\n([\s\S]*)\s*\n/blind'
	# 盲注值：用户id；赌注（盲注）
	blindBetRe = r'(\d+):\s+(\d+)'
	blindItems = re.findall(blindMsgRe, msg)
	if blindItems:
		writeLog('\nGet blind bet message: ')
		print '\nGet blind bet message: '
		blindInfo = blindItems[0]
		blinds = blindInfo.split('\n')
		bet = []
		for blind in blinds:
			blindMatch = re.search(blindBetRe, blind)
			if blindMatch:
				betValue = blindMatch.group(2)
				bet.append(betValue)
		gameinfo.smallBlindBet = bet[0]
		smallbet = 'small bet: %s' % bet[0]
		writeLog(smallbet)
		if len(bet) == 2:
			gameinfo.bigBlindBet = bet[1]
			bigbet = 'big bet: %s' % bet[1]
			writeLog(bigbet)

def handleHoldMsg(gameinfo, msg):
	# 处理手牌消息：
	# 持有手牌：花色 大小 花色 大小（共两张牌）
	holdMsgRe = r'hold/\s*\n(\w+)\s+(\w+)\s*\n(\w+)\s+(\w+)\s*\n/hold'
	holdMatch = re.search(holdMsgRe, msg)
	if holdMatch:
		writeLog('\nGet hold cards message: ')
		print 'Get hold cards message: '
		color1 = holdMatch.group(1)
		point1 = holdMatch.group(2)
		card1 = Card()
		card1.setCardInfo(color1, point1)
		card1.saveCardLog()
		card1.printCardInfo()
		color2 = holdMatch.group(3)
		point2 = holdMatch.group(4)
		card2 = Card()
		card2.setCardInfo(color2, point2)
		card2.saveCardLog()
		card2.printCardInfo()
		gameinfo.addHoldCards(card1)
		gameinfo.addHoldCards(card2)

def handleInquireMsg(skt, gameinfo, msg):
	# 处理询问消息：
	# 询问消息：分为两部分----前面的player操作 + 彩池信息
	inquireMsgRe = r'inquire/\s*\n([\s\S]*)\s*\ntotal\s+pot:\s+(\d+)\s*\n/inquire'
	# Player操作：用户id 筹码 持有金币 下注 操作
	playerOpsRe = r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)\s+'
	inquireMatch = re.search(inquireMsgRe, msg)
	if inquireMatch:
		writeLog('\nGet inquire message')
		print 'Get inquire message: '
		opsMsg = inquireMatch.group(1)
		potMsg = inquireMatch.group(2)
		opsSet = opsMsg.split('\n')
		actionSet = []
		for ops in opsSet:
			opsMatch = re.search(playerOpsRe, ops)
			if opsMatch:
				player = opsMatch.group(1)
				jetton = opsMatch.group(2)
				money = opsMatch.group(3)
				bet = opsMatch.group(4)
				op = opsMatch.group(5)
				action = Action()
				action.setAction(player, jetton, money, bet, op)
				#action.saveActionLog()
				actionSet.append(action)
		gameinfo.actions = actionSet
		gameinfo.updatePlayerInfo()
		gameinfo.potNum = int(potMsg)
		decisionProcess(skt, gameinfo)

def handleFlopMsg(gameinfo, msg):
	# 公牌信息处理
	# 翻牌消息：
	flopMsgRe = r'flop/\s*\n(\w+)\s+(\w+)\s*\n(\w+)\s+(\w+)\s*\n(\w+)\s+(\w+)\s*\n/flop'
	flopMatch = re.search(flopMsgRe, msg)
	if flopMatch:
		writeLog('\nGet flop cards:')
		print 'Get flop cards: '
		color1 = flopMatch.group(1)
		point1 = flopMatch.group(2)
		card1 = Card()
		card1.setCardInfo(color1, point1)
		card1.printCardInfo()
		card1.saveCardLog()
		color2 = flopMatch.group(3)
		point2 = flopMatch.group(4)
		card2 = Card()
		card2.setCardInfo(color2, point2)
		card2.printCardInfo()
		card2.saveCardLog()
		color3 = flopMatch.group(5)
		point3 = flopMatch.group(6)
		card3 = Card()
		card3.setCardInfo(color3, point3)
		card3.printCardInfo()
		card3.saveCardLog()
		gameinfo.addPublicCards(card1)
		gameinfo.addPublicCards(card2)
		gameinfo.addPublicCards(card3)

def handleTurnMsg(gameinfo, msg):
	# 转牌消息处理：
	# 转牌消息：
	turnMsgRe = r'turn/\s*\n(\w+)\s+(\w+)\s*\n/turn'
	turnMatch = re.search(turnMsgRe, msg)
	if turnMatch:
		writeLog('\nGet turn card:')
		print 'Get turn card:'
		color = turnMatch.group(1)
		point = turnMatch.group(2)
		card = Card()
		card.setCardInfo(color, point)
		card.printCardInfo()
		card.saveCardLog()
		gameinfo.addPublicCards(card)

def handleRiverMsg(gameinfo, msg):
	# 河牌消息处理：
	# 河牌消息
	riverMsgRe = r'river/\s*\n(\w+)\s+(\w+)\s*\n/river'
	riverMatch = re.search(riverMsgRe, msg)
	if riverMatch:
		writeLog('\nGet river card:')
		print 'Get river card: '
		color = riverMatch.group(1)
		point = riverMatch.group(2)
		card = Card()
		card.setCardInfo(color, point)
		card.printCardInfo()
		card.saveCardLog()
		gameinfo.addPublicCards(card)

def handleShowdownMsg(gameinfo, msg):
	# 摊牌消息处理：
	# 摊牌消息： 牌池信息 + 排名信息
	showdownMsgRe = r'showdown/\s*\ncommon/\s*\n([\s\S]*)\s*\n/common\s*\n([\s\S]*)\s*\n/showdown'
	# 牌池信息：
	cardMsgRe = r'(\w+)\s+(\w+)'
	# 排名信息：
	rankMsgRe = r'(\d+):\s+(\d+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)'
	showdownMatch = re.search(showdownMsgRe, msg)
	if showdownMatch:
		writeLog('\nGet showdown message:')
		print 'Get showdown message: '
		cardMsg = showdownMatch.group(1)
		rankMsg = showdownMatch.group(2)
		cards = cardMsg.split('\n')
		ranks = rankMsg.split('\n')
		print 'Handling common cards information...'
		writeLog('Common cards information:')
		for card in cards:
			cardMatch = re.search(cardMsgRe, card)
			if cardMatch:
				color = cardMatch.group(1)
				point = cardMatch.group(2)
				print color, point
				clrinfo = 'Card color: %s' % color
				pitinfo = 'Card point: %s' % point
				writeLog(clrinfo)
				writeLog(pitinfo)
		writeLog('\nPlayer rank information')
		print 'Handling rank information...'
		for rank in ranks:
			rankMatch = re.search(rankMsgRe, rank)
			if rankMatch:
				rank = rankMatch.group(1)
				player = rankMatch.group(2)
				color1 = rankMatch.group(3)
				point1 = rankMatch.group(4)
				color2 = rankMatch.group(5)
				point2 = rankMatch.group(6)
				nut_hand = rankMatch.group(7)
				card1 = Card()
				card1.setCardInfo(color1, point1)
				card1.printCardInfo()
				card1.saveCardLog()
				card2 = Card()
				card2.setCardInfo(color1, point1)
				card2.printCardInfo()
				card2.saveCardLog()
				gameinfo.updateRankInfo(player, card1, card2, rank, nut_hand)

def handlePotMsg(gameinfo, msg):
	# 彩池分配消息处理：
	# 彩池分配消息：
	potwinMsgRe = r'pot-win/\s*\n([\s\S]*)\s*\n/pot-win'
	# 彩池单分配：
	potMsgRe = r'(\d+):\s+(\d+)'
	potwinItems = re.findall(potwinMsgRe, msg)
	if potwinItems:
		writeLog('\nGet pot num message')
		print 'Get pot num message'
		potwinMsg = potwinItems[0]
		potwins = potwinMsg.split('\n')
		for potwin in potwins:
			potwinMatch = re.search(potMsgRe, potwin)
			if potwinMatch:
				player = potwinMatch.group(1)
				pot = potwinMatch.group(2)
				playerInfo = gameinfo.getPlayerById(player)
				playerHistory = gameinfo.getPHById(player)
				if not playerHistory:
					playerHistory = PlayerHistory(player)
				playerHistory.addPlayerHistory(playerInfo.holdcards, int(pot))
				writeLog('Pot-win info: ')
				print 'Pot-win info: '
				writeLog('Player ID: %s' % player)
				print 'Player ID: ', player
				writeLog('Player Pot: %s' % pot)
				print 'PlayerPot: ', pot

def handleGameOverMsg(skt):
	skt.close()
	sys.exit()

def decisionProcess(skt, gameinfo):
	writeLog('\nDecision Process...')
	writeLog('Game Number: ' + str(gameinfo.gameNum))
	writeLog('Hold Cards Count: ' + str(len(gameinfo.holdCards)))
	writeLog('Public Cards Count: ' + str(len(gameinfo.publicCards)))
	'''
	我们通过gameinfo中的公牌数量来判断当前局应该执行什么操作
	'''
	if len(gameinfo.publicCards) == 0:
		writeLog('Hold Cards Round: ')
		gameinfo.holdNum += 1
		msg = decision.handRoundDecision(gameinfo)
	elif len(gameinfo.publicCards) == 3:
		writeLog('Flop Cards Round: ')
		gameinfo.flopNum += 1
		msg = decision.flopRoundDecision(gameinfo)
	elif len(gameinfo.publicCards) == 4:
		writeLog('Turn Cards Round: ')
		gameinfo.turnNum += 1
		msg = decision.turnRoundDecision(gameinfo)
	elif len(gameinfo.publicCards) == 5:
		writeLog('River Cards Round: ')
		gameinfo.riverNum += 1
		msg = decision.riverRoundDecision(gameinfo)
	else:
		msg = 'fold \n'
	sendMsgToServer(skt, msg)