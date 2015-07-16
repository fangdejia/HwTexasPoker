#! /usr/bin/env python
# -*- coding:utf-8 -*-

import itertools
import re

# 玩家位置分为以下几种：
# 庄家、小盲注、大盲注、EP、MP、LP等
PlayerRole = {
	1 : 'BTN',
	2 : 'SB',
	3 : 'BB',
	4 : 'EP',
	5 : 'EP',
	6 : 'MP', 
	7 : 'MP',
	8 : 'LP'
}

# 扑克花色共分为四种：HEARTS/CLUBS/DIAMONDS/SPADES(设置未知花色UNKNOWN)
CardColor = {
	'UNKNOWN':0,
	'SPADES': 1,
	'HEARTS': 2,
	'CLUBS': 3,
	'DIAMONDS': 4
}

# 牌值分为13张牌： 2-A（2-14）
CardPoint = {
	'unknown': 0,
	'2': 2,
	'3': 3,
	'4': 4,
	'5': 5,
	'6': 6,
	'7': 7,
	'8': 8,
	'9': 9,
	'10': 10,
	'J': 11,
	'Q': 12,
	'K': 13,
	'A': 14
}

# 牌型分九品：
# 高牌
# 一对
# 两对
# 三条
# 顺子
# 同花
# 葫芦
# 四条
# 同花顺（皇家同花顺）
CardLevel = {
	'UNKNOWN': 0,
	'HIGH_CARD': 1,
	'ONE_PAIR': 2,
	'TWO_PAIR': 3,
	'THREE_OF_A_KIND': 4,
	'STRAIGHT': 5,
	'FLUSH': 6,
	'FULL_HOUSE': 7,
	'FOUR_OF_A_KIND': 8,
	'STRAIGHT_FLUSH': 9,
}

# 玩家操作分为下面几种：
# blind: 盲注
# check：让牌
# call：跟注
# raise：加注
# all_in：全押
# fold：弃牌
ActionSet = {
	'blind': 1,
	'check': 2,
	'call': 3,
	'raise': 4,
	'all_in': 5,
	'fold': 6
}

def getColorByIndex(index):
	if index == 1:
		return 'SPADES'
	elif index == 2:
		return 'HEARTS'
	elif index == 3:
		return 'CLUBS'
	elif index == 4:
		return 'DIAMONDS'
	return None

def getPointByIndex(index):
	if index>=2 and index<=10:
		return str(index)
	elif index == 11:
		return 'J'
	elif index == 12:
		return 'Q'
	elif index == 13:
		return 'K'
	elif index == 14:
		return 'A'
	return None

def getLevelByIndex(index):
	if index == 0:
		return 'UNKNOWN'
	elif index == 1:
		return 'HIGH_CARD'
	elif index == 2:
		return 'ONE_PAIR'
	elif index == 3:
		return 'TWO_PAIR'
	elif index == 4:
		return 'THREE_OF_A_KIND'
	elif index == 5:
		return 'STRAIGHT'
	elif index == 6:
		return 'FLUSH'
	elif index == 7:
		return 'FULL_HOUSE'
	elif index == 8:
		return 'FOUR_OF_A_KIND'
	elif index == 9:
		return 'STRAIGHT_FLUSH'
	return None

class holdCardSet(object):
	def __init__(self):
		self.pointMax = 0
		self.pointMin = 0
		self.plus = False
		self.isuit = False

	def setInfo(self, pointMax, pointMin, plus, isuit):
		self.pointMax = pointMax
		self.pointMin = pointMin
		self.plus = plus
		self.isuit = isuit

#我们在这里统计定义一些起手牌牌型集合，通过列表存放
# 这四个集合代表对应松紧度下的入手牌
tight3Cards = []
tight2EpCards = []
tight2MpCards = []
tight2LpCards = []
tight2BtnCards = []
tight2BlindCards = []
tight1Cards = []

# 下面三个代表当前所抓手牌的价值（或称为等级）
beautyCards = []
goodCards = []
fairCards = []

def initializeCardSet():
	# tight=3:
	h3s1 = holdCardSet()
	h3s2 = holdCardSet()
	h3s3 = holdCardSet()
	h3s1.setInfo(9, 9, True, False)
	h3s2.setInfo(14, 13, False, False)
	h3s3.setInfo(14, 12, True, True)
	tight3Cards.append(h3s1)
	tight3Cards.append(h3s2)
	tight3Cards.append(h3s3)

	# tight=2 and role=EP:
	h2s1 = holdCardSet()
	h2s2 = holdCardSet()
	h2s3 = holdCardSet()
	h2s4 = holdCardSet()
	h2s1.setInfo(4, 4, True, False)
	h2s2.setInfo(14, 13, False, False)
	h2s3.setInfo(14, 10, True, True)
	h2s4.setInfo(14, 12, True, False)
	tight2EpCards.append(h2s1)
	tight2EpCards.append(h2s2)
	tight2EpCards.append(h2s3)
	tight2EpCards.append(h2s4)

	# tight=2 and role=MP
	h2s5 = holdCardSet()
	h2s6 = holdCardSet()
	h2s7 = holdCardSet()
	h2s8 = holdCardSet()
	h2s8 = holdCardSet()
	h2s5.setInfo(4, 4, True, False)
	h2s6.setInfo(14, 9, True, True)
	h2s7.setInfo(14, 12, True, False)
	h2s8.setInfo(13, 11, True, False)
	h2s9.setInfo(13, 12, True, False)
	tight2MpCards.append(h2s5)
	tight2MpCards.append(h2s6)
	tight2MpCards.append(h2s7)
	tight2MpCards.append(h2s8)
	tight2MpCards.append(h2s9)

	# tight=2 and role=LP
	h2s12 = holdCardSet()
	h2s13 = holdCardSet()
	h2s14 = holdCardSet()
	h2s15 = holdCardSet()
	h2s16 = holdCardSet()
	h2s12.setInfo(4, 4, True, False)
	h2s13.setInfo(10, 9, True, True)
	h2s14.setInfo(14, 9, True, True)
	h2s15.setInfo(14, 11, True, False)
	h2s15.setInfo(13, 12, True, False)
	tight2LpCards.append(h2s12)
	tight2LpCards.append(h2s13)
	tight2LpCards.append(h2s14)
	tight2LpCards.append(h2s15)
	tight2LpCards.append(h2s16)

	# tight=2 and role=BTN
	h2s22 = holdCardSet()
	h2s23 = holdCardSet()
	h2s24 = holdCardSet()
	h2s25 = holdCardSet()
	h2s22.setInfo(4, 4, True, False)
	h2s23.setInfo(14, 9, True, True)
	h2s24.setInfo(10, 9, True, True)
	h2s25.setInfo(14, 11, True, False)
	tight2BtnCards.append(h2s22)
	tight2BtnCards.append(h2s23)
	tight2BtnCards.append(h2s24)
	tight2BtnCards.append(h2s25)

	# tight=2 and role=Blind
	h2s32 = holdCardSet()
	h2s33 = holdCardSet()
	h2s34 = holdCardSet()
	h2s35 = holdCardSet()
	h2s32.setInfo(6, 6, True, False)
	h2s33.setInfo(14, 13, False, False)
	h2s34.setInfo(14, 11, True, True)
	h2s35.setInfo(6, 6, True, False)
	tight2BlindCards.append(h2s32)
	tight2BlindCards.append(h2s33)
	tight2BlindCards.append(h2s34)
	tight2BlindCards.append(h2s35)

	# tight=1
	h3s1 = holdCardSet()
	h3s2 = holdCardSet()
	h3s3 = holdCardSet()
	h3s4 = holdCardSet()
	h3s5 = holdCardSet()
	h3s6 = holdCardSet()
	h3s7 = holdCardSet()
	h3s1.setInfo(2, 2, True, False)
	h3s2.setInfo(14, 11, True, False)
	h3s3.setInfo(14, 6, True, True)
	h3s4.setInfo(9, 8, True, True)
	h3s5.setInfo(11, 9, True, True)
	h3s6.setInfo(13, 12, False, False)
	h3s7.setInfo(13, 11, False, True)
	tight1Cards.append(h3s1)
	tight1Cards.append(h3s2)
	tight1Cards.append(h3s3)
	tight1Cards.append(h3s4)
	tight1Cards.append(h3s5)
	tight1Cards.append(h3s6)
	tight1Cards.append(h3s7)

	# perfect
	c1 = holdCardSet()
	c2 = holdCardSet()
	#c3 = holdCardSet()
	c1.setInfo(13, 13, True, False)
	c2.setInfo(14, 13, False, True)
	#c3.setInfo(13, 12, False, True)
	beautyCards.append(c1)
	beautyCards.append(c2)
	#beautyCards.append(c3)

	# good
	s1 = holdCardSet()
	s2 = holdCardSet()
	s3 = holdCardSet()
	s4 = holdCardSet()
	s1.setInfo(9, 9, True, False)
	s2.setInfo(14, 11, True, True)
	s3.setInfo(12, 11, True, True)
	s4.setInfo(13, 12, True, False)
	goodCards.append(s1)
	goodCards.append(s2)
	goodCards.append(s3)
	goodCrads.append(s4)

	# fair
	h1 = holdCardSet()
	h2 = holdCardSet()
	h3 = holdCardSet()
	h4 = holdCardSet()
	h5 = holdCardSet()
	h6 = holdCardSet()
	h1.setInfo(2, 2, True, False)
	h2.setInfo(8, 7, True, True)
	h3.setInfo(12, 11, True, False)
	h4.setInfo(14, 8, True, True)
	h5.setInfo(14, 10, True, False)
	h6.setInfo(11, 9, True, True)
	fairCards.append(h1)
	fairCards.append(h2)
	fairCards.append(h3)
	fairCards.append(h4)
	fairCards.append(h5)
	fairCards.append(h6)

def setFileName(myid):
	global filename
	filename = myid + '.log'

def writeLog(msg):
	record = msg + '\n'
	with open(filename, 'a') as file:
		file.write(record)

def fileClean():
	with open(filename, 'w') as file:
		file.truncate(0)

def group(points):
	"Return a list of [(count, x)...], highest count first, the highest x first"
	groups = [(points.count(p), p) for p in set(points)]
	return sorted(groups, reverse = True)

def unzip(pairs):
	return list(zip(*pairs))
