#! /usr/bin/env python
# -*- coding:utf-8 -*-

import itertools
import math
from util import *

# 单张牌的类声明：
# color 和 point都是纯数字
class Card:
	def __init__(self):
		self.color = 0
		self.point = 0

	def setCardInfo(self, color = None, point = None):
		print 'Add new card %s-%s' %(color, point)
		clr = CardColor[color]
		pit = CardPoint[point]
		self.color = clr
		self.point = pit

	def printCardInfo(self):
		print '\nCard Information:'
		print 'Card Color: ', getColorByIndex(self.color)
		print 'Card Point: ', getPointByIndex(self.point)

	def saveCardLog(self):
		writeLog('\nCard Information:')
		color = 'Card Color: %s' % getColorByIndex(self.color)
		writeLog(color)
		point = 'Card Point: %s' % getPointByIndex(self.point)
		writeLog(point)

# 玩家操作类：
# 主要包括下面一些内容：
# 操作玩家ID、玩家现持筹码、玩家现持金币、玩家当前下注金币、玩家最近一次的操作
class Action:
	def __init__(self):
		self.player = 0
		self.jetton = 0
		self.money = 0
		self.bet = 0
		self.opid = 0
		self.oparg = None
		self.ops = None
		self.playerStatus = None

	def setAction(self, player, jetton, money, bet, ops):
		self.player = player
		self.jetton = jetton
		self.money = money
		self.bet = bet
		self.ops = ops
		self.parseActionOps()

	def parseActionOps(self):
		# 表示操作为raise
		if 'raise' in self.ops:
			op = self.ops.split(' ')
			self.opid = ActionSet[op[0]]
			if len(op) == 2:
				self.oparg = op[1]
			else:
				self.oparg = None
			self.playerStatus = 'active'
		# 其他情况如check|all_in||call|fold|blind
		else:
			self.opid = ActionSet[self.ops]
			if 'fold' in self.ops:
				self.playerStatus = 'down'
			else:
				self.playerStatus = 'active'

	def saveActionLog(self):
		writeLog('\nNew Player Action Information:')
		player = 'Operation player id: %s' % self.player
		writeLog(player)
		jetton = 'Player jetton: %s' % self.jetton
		writeLog(jetton)
		money = 'Player money: %s' % self.money
		writeLog(money)
		bet  = 'Player bet: %s' % self.bet
		writeLog(bet)
		ops = 'Player operation: %s' % self.ops
		writeLog(ops)

class Player:
	# 字段说明：
	# rank 为最终排名
	# money 为玩家剩余总金额
	# jetton 为玩家筹码
	def __init__(self):
		self.id = 0
		self.rank = 0
		self.nut_hand = 0
		self.jetton = 0
		self.money = 0
		self.role = 0
		# default is active
		self.status = 1
		self.holdcards = []
		self.lastbet = 0
		self.bet = 0

	def setInfo(self, id = 0, jetton = 0, money = 0, role = 0):
		self.id = id
		self.jetton = jetton
		self.money = money
		self.role = role

	def updateInfo(self, jetton, money):
		self.jetton = jetton
		self.money = money

	def setRank(self, rank):
		self.rank = rank

	def setNutHand(self, nut_hand):
		nh = CardLevel[nut_hand]
		self.nut_hand = nh

	def addCard(self, card):
		self.holdcards.append(card)

	def setStatus(self, status):
		if status == 'active':
			self.status = 1
		else:
			self.status = 0

	def savePlayerLog(self):
		writeLog('\nPlayer Information:')
		id = 'id: %s' % self.id
		writeLog(id)
		role = 'role: %s' % PlayerRole[self.role]
		writeLog(role)
		jetton = 'jetton: %s' % self.jetton
		writeLog(jetton)
		money = 'money: %s' % self.money
		writeLog(money)

class CardToPot:
	def __init__(self, holdcards=None, pot=0):
		self.holdcards = holdcards
		self.pot = pot

class PlayerHistory:
	def __init__(self, id=0):
		self.id = id
		self.cardtopot = []
		# 这里的tightlevel可以为小数，主要维护一个平均值
		self.tightlevel = 0

	def addPlayerHistory(self, holdcards=None, pot=0):
		ctop = CardToPot(holdcards, pot)
		self.cardtopot.append(ctop)

	def setTightLevel(self, tightLevel=0):
		self.tightlevel = tightlevel

class GameInfo:
	def __init__(self):
		# 玩家集合
		self.players = []
		# 本玩家，这个成员很重要，主要保存本玩家的一些信息，包括下注、金钱以及排名等
		self.myplayer = None
		# 本玩家id
		self.myid = 0
		# 本玩家根据自己的排名进行的松紧策略调整
		self.mytight = 0
		# 游戏局信息（大小盲注）
		self.smallBlindBet = 0
		self.bigBlindBet = 0
		# 本玩家持有的牌
		self.holdCards = []
		# 公共牌（3-5张不等）
		self.publicCards = []
		# 本回合玩家操作集合
		self.actions = []
		# 彩池金额数目
		self.potNum = 0
		# 保存当前的最小加注信息
		self.minRaiseCount = 0
		# 在无限下注德州扑克中，我们要记录目前已经是第几轮喊注了
		self.holdNum = 0 
		self.flopNum = 0
		self.turnNum = 0
		self.riverNum = 0
		# 维护一个值，这个值表示这是第几轮（每轮从发布seat信息开始到pot-win信息结束）
		self.gameNum = 0
		# 我们这里维护这样一个数据集合，这个集合有着特殊的意义，用于分析用户的松紧策略（仅限于最基本的手牌分析）
		self.phSet = []
		# 保存当前的player-tight信息
		self.playertights = []

	def someDataClean(self):
		self.players = []
		self.numSet = 0
		self.potNum = 0
		self.smallBlindBet = 0
		self.bigBlindBet = 0
		self.holdCards = []
		self.publicCards = []
		self.actions = []
		# self.myplayer = None
		self.holdNum = 0 
		self.flopNum = 0
		self.turnNum = 0
		self.riverNum = 0
		self.minRaiseCount = 0

	def getPlayerById(self, id):
		for p in self.players:
			if p.id == id:
				return p
		return None

	def getPHById(self, id):
		for ph in self.phSet:
			if ph.id == id:
				return ph
		return None

	def setPlayerTights(self, pts):
		self.playertights = pts

	def addNewPlayer(self, id, jetton, money, role):
		player = Player()
		player.setInfo(id, jetton, money, role)
		self.players.append(player)
		player.savePlayerLog()
		if id == self.myid:
			writeLog('This is me player!')
			myplayer = Player()
			myplayer.setInfo(id, jetton, money, role)
			myplayer.savePlayerLog()
			self.myplayer = myplayer

	def addHoldCards(self, hc):
		self.holdCards.append(hc)

	def addPublicCards(self, pc):
		self.publicCards.append(pc)

	def updatePlayerInfo(self):
		for action in self.actions:
			action.parseActionOps()
			player = self.getPlayerById(action.player)
			if player:
				player.jetton = action.jetton
				player.money = action.money
				player.lastbet = player.bet
				player.bet = action.bet
				player.setStatus(action.playerStatus)
			if action.player == self.myid:
				self.myplayer.jetton = action.jetton
				self.myplayer.money = action.money
				self.myplayer.lastbet = player.bet
				self.myplayer.bet = action.bet
				self.myplayer.setStatus(action.playerStatus)

	def updateRankInfo(self, playerid, card1, card2, rank, nut_hand):
		player = self.getPlayerById(playerid)
		player.addCard(card1)
		player.addCard(card2)
		player.rank = rank
		player.nut_hand = CardLevel[nut_hand]
		if playerid == self.myid:
			self.myplayer.rank = rank
			self.myplayer.nut_hand = CardLevel[nut_hand]

