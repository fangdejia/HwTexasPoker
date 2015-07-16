#! /usr/bin/env python
# -*- coding:utf-8 -*-
import itertools
from util import group, unzip
from util import ActionSet, CardLevel, CardPoint, PlayerRole
from util import getLevelByIndex, writeLog, getColorByIndex, getPointByIndex

# 起手牌分析过程，分析是否应该玩一手牌
def handCardsHandle(mycards, myseatrole, tightPolicy = 1):
	'''
	分析手牌，然后确定是否应该加入牌局
	对于tightPolicy，其表示我们在玩牌时的松紧策略
	'''
	# tightPolicy表示是否实行紧方式
	# inFlag 用于表示是否决定玩一手牌。
	# 位置划分：
	# ep（前位）：8--大盲注后两个，4/3---依次递减
	# mp（中位）：8--EP后两个，6/5---依次递减
	# lp（末位）：8--MP后一个，7删除
	# button（庄家）
	# blind（大小盲注）	
	# 这里，我们使用经验，选择执行20%策略
	# 基于概率事件，通过经验：
	# ep: 44+/AKo/ATs+/AQo+
	# mp: 33+/A8s+/ATo+/KJo+
	# lp: 22+/A2s+
	# button: 22+/A2s+/T9s+/AJo+
	# blind: 22+/AKo/AQs/AJs/KQs
	# 另外，对于松机制
	# 所有：22+/AJo+/A4s+/98s+/KQo/KJs
	inFlag = False
	# 使用最紧机制
	# 最紧机制通常适用于这样的情况：
	# 1、起手牌时，对手中存在all_in时，实行最紧策略，不要轻易all_in
	# 2、当自己的金钱远远大于第二名时，实行最紧策略。原因在于不要轻易加入牌局，除非自己有着极大的赢牌几率
	# 3、当牌局的紧策略玩家出现加注和all_in操作时，我们实行最紧机制
	if tightPolicy == 3:
		inFlag =(justifyMode(mycards, pointMax=6, pointMin=6, plus=True, isuit=False) or
				 justifyMode(mycards, pointMax=14, pointMin=13, plus=False, isuit=False) or
				 justifyMode(mycards, pointMax=14, pointMin=10, plus=True, isuit=True) or
				 justifyMode(mycards, pointMax=13, pointMin=12, plus=True, isuit=True)
				 )
	# 使用紧机制
	# 紧机制通常适用于这样一些情况：
	# 1、当自己的金钱为第一名且稍微领先第二名时，实行紧策略
	# 2、当牌局的紧策略玩家出现跟注时，我们实行紧机制
	elif tightPolicy == 2:
		if PlayerRole[myseatrole] == 'EP':
			inFlag =(justifyMode(mycards, pointMax=3, pointMin=3, plus=True, isuit=False) or
					 justifyMode(mycards, pointMax=14, pointMin=13, plus=False, isuit=False) or
					 justifyMode(mycards, pointMax=14, pointMin=10, plus=True, isuit=True) or
					 justifyMode(mycards, pointMax=14, pointMin=12, plus=False, isuit=False) or
					 justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=False)
					)
		elif PlayerRole[myseatrole] == 'MP':
			inFlag =(
					justifyMode(mycards, pointMax=3, pointMin=3, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=14, pointMin=9, plus=True, isuit=True) or
					justifyMode(mycards, pointMax=14, pointMin=12, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=13, pointMin=11, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=False)
					)
		elif PlayerRole[myseatrole] == 'LP':
			inFlag =( 
					justifyMode(mycards, pointMax=3, pointMin=3, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=9, pointMin=8, plus=True, isuit=True) or
					justifyMode(mycards, pointMax=14, pointMin=9, plus=True, isuit=True) or
					justifyMode(mycards, pointMax=14, pointMin=11, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=False)
					)
		elif PlayerRole[myseatrole] == 'BTN':
			inFlag =(
					justifyMode(mycards, pointMax=3, pointMin=3, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=14, pointMin=9, plus=True, isuit=True) or
					justifyMode(mycards, pointMax=10, pointMin=9, plus=True, isuit=True) or
					justifyMode(mycards, pointMax=14, pointMin=11, plus=True, isuit=False)
					)
		elif PlayerRole[myseatrole] == 'SB' or PlayerRole[myseatrole] == 'BB':
			inFlag =(
					justifyMode(mycards, pointMax=3, pointMin=3, plus=True, isuit=False) or
					justifyMode(mycards, pointMax=7, pointMin=6, plus=True, isuit=True) or
					justifyMode(mycards, pointMax=14, pointMin=13, plus=False, isuit=False) or
					justifyMode(mycards, pointMax=14, pointMin=11, plus=False, isuit=True) or
					justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=True)
					)
	# 使用最松机制
	elif tightPolicy == 1:
		inFlag =(
				justifyMode(mycards, pointMax=2, pointMin=2, plus=True, isuit=False) or
				justifyMode(mycards, pointMax=14, pointMin=5, plus=True, isuit=False) or
				justifyMode(mycards, pointMax=14, pointMin=2, plus=True, isuit=True) or
				justifyMode(mycards, pointMax=10,pointMin=9, plus=True, isuit=True) or
				justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=False) or
				justifyMode(mycards, pointMax=13, pointMin=11, plus=False, isuit=True) or
				justifyMode(mycards, pointMax=13, pointMin=10, plus=False, isuit=True) or
				justifyMode(mycards, pointMax=12, pointMin=9, plus=False, isuit=False)
				)
	# 最后这一种，实行的机制最松
	# 22+/A8+/A2s+/76s+/109+/97s+/KJ/K10/K9s/Q10/Q9s/Q8s
	# 那么，哪些情况下实行最松机制呢？
	# 1、对于当自己的经济状况处于5-6名次时，同样执行最松机制，但是执行的方法为all_in
	# 2、自暴自弃：当自己的经济状况处于7-8名·，执行全all_in机制————投机方法
	elif tightPolicy == 0:
		inFlag =(
				justifyMode(mycards, pointMax=2, pointMin=2, plus=True, isuit=False) or
				justifyMode(mycards, pointMax=14, pointMin=8, plus=True, isuit=False) or
				justifyMode(mycards, pointMax=14, pointMin=4, plus=True, isuit=True) or
				justifyMode(mycards, pointMax=9, pointMin=8, plus=True, isuit=True) or
				justifyMode(mycards, pointMax=13, pointMin=11, plus=False, isuit=False) or
				justifyMode(mycards, pointMax=13, pointMin=10, plus=False, isuit=False) or
				justifyMode(mycards, pointMax=13, pointMin=9, plus=False, isuit=False) or
				justifyMode(mycards, pointMax=13, pointMin=8, plus=False, isuit=True) or
				justifyMode(mycards, pointMax=12, pointMin=10, plus=False, isuit=False) or 
				justifyMode(mycards, pointMax=12, pointMin=9, plus=False, isuit=True) or 
				justifyMode(mycards, pointMax=12, pointMin=8, plus=False, isuit=True)
				)

	if inFlag:
		writeLog('\nHand Round: Join this set!!!')
		print '\nHand Round: Join this set!!!'
	else:
		writeLog('\nHand Round: Do not join this set!!!')
		print '\nHand Round: Do not join this set!!!'

	return inFlag

# 分析起手牌的是否在特定的牌型范围
def justifyMode(mycards, pointMax, pointMin, plus=False, isuit=False):
	# 对本函数进行一些说明：本函数仅对第一轮手牌进行策略判断
	# pointMax表示最大纸牌点数，pointMin表示最小纸牌点数， plus用于表示是否向上匹配， isuit表示是否同花匹配
	# 现进行举例详细说明：
	# 22+(大于等于22的口袋对: pointMax=2, pointMin=2, plus=True, isuit=False)
	# 45s+(大于等于45的同花连续牌对,如5c6c: pointMax=5, pointMin=4, plus=True, isuit=True)
	# 46o+(大于等于46的同花要求的间隔牌对,如5c7s: pointMax=6, pointMin=4, plus=True, isuit=True)
	# 另外,对于A2s+(大于等于A2的A*牌,如A3: pointMax=14, pointMin=2, plus+True, isuit=True)
	colors = [card.color for card in mycards]
	points = [card.point for card in mycards]
	maxp = max(points)
	minp = min(points)
	maxc = max(colors)
	minc = min(colors)
	# 记录牌值间隔
	delta = pointMax - pointMin
	# 是否上匹配
	if plus:
		if pointMax == maxp == 14 and minp >= pointMin:
			if isuit and maxc != minc:
				pass
			else:
				return True
		elif pointMax != 14 and maxp == minp + delta and minp >= pointMin:
			# 设置同花标志，同时判断只有一种花色
			if isuit and maxc != minc:
				pass
			else:
				return True
	# 要求精确匹配
	else:
		if maxp == pointMax and minp == pointMin:
			# 设置同花标志，同时判断只有一种花色
			if isuit and maxc != minc:
				pass
			else:
				return True
	return False

# 翻牌轮后分析牌型和价值
def parseFlopRoundLevel(flopcards):
	"Return a value indicating how high the hand ranks"
	# counts元组保存每种牌型值的个数
	# points元组保存不同牌型值，并且按照大小排序（count值越大越优先）
	# Eg. '7 T 7 9 7' => counts=(3,1,1) points=(7,10,9)
	groups = group( [card.point for card in flopcards] )
	(counts, points) = unzip(groups)

	# 对于顺子(A,2,3,4,5), 规定其值为(1,2,3,4,5)
	if points == (14,5,4,3,2):
		points = (5,4,3,2,1)

	# 判断是否为顺子:
	# 五张牌数值各不同，同时最大牌与最小牌相差4
	straight = (len(points)==5) and (max(points)-min(points) == 4)

	# 判断是否为同花：
	# 五张牌花色相同
	flush = len(set([card.color for card in flopcards])) == 1

	# 这里我们判断9种牌型：同花顺、四条、葫芦、同花、顺子、三条、两对、一对、高牌
	level =( 9 if straight and flush else
			 8 if (4, 1) == counts else
			 7 if (3, 2) == counts else
			 6 if flush else
			 5 if straight else
			 4 if (3, 1, 1) == counts else
			 3 if (2, 2, 1) == counts else
			 2 if (2, 1, 1, 1) == counts else
			 1)
	'''
	# 打印该五张牌的信息
	print 'All five cards information:'
	for card in flopcards:
		print getColorByIndex(card.color) + '-' + getPointByIndex(card.point)

	# 打印该五张牌的牌型有多少种大小
	print 'Points Count: ', len(points)

	# 计算牌型价值
	'''
	value = computeCardsValue(level, points)
	print 'Cards Value: ', value

	return value, level

# 计算当前牌型价值
def computeCardsValue(level, points):
	'''
	对于每手牌进行牌型价值计算
	------------------------------------------------------
	这里，对计算方法进行如下说明：
	---------------------
	| A | B | C | D | E |
	---------------------
	其中，我们其大小顺序为：A>B>C>D>E
	（基于总共13张, 牌值为2-14, 因此牌值减2作为系数）
	对于高牌，其值最小：
		value = A*13^4 + B*13^3 + C*13^2 + D*13 + E
		对于其最大值，假设五张可能为一样（虽然不可能，但不影响结果）
		base_1 = 13^5（五张全为14 plus 1）
	对于一对(A==B)，其值肯定大于高牌：
		value = base_1 + A*13^3 + C*13^2 + D*13 + E
		对于其最大值，同上：
		base_2 = base_2 + 13^4
	对于顺子和同花，有如下讨论：
	对于顺子，仅仅考虑最大值即可：
		value = base + A
	对于同花，同高牌一样：
		value = base + A*13^4 + B*13^3 + C*13^2 + D*13 + E
	其余，如下面程序所示
	------------------------------------------------------
	结果讨论：
	高牌：0-371293
	一对：371293-399854
	两对：399854-402051
	三条：402051-404248
	顺子：404248-404261
	同花：404261-775554
	葫芦：775554-775723
	四条：775723-775892
	同花顺：775892-775905
	'''
	print level
	print points
	base_1 = 13**5
	base_2 = base_1 + 13**4
	base_3 = base_2 + 13**3
	base_4 = base_3 + 13**3
	base_5 = base_4 + 13
	base_6 = base_5 + 13**5
	base_7 = base_6 + 13**2
	base_8 = base_7 + 13**2
	# 高牌
	if level == 1:
		value = 13**4*(points[0]-2) + 13**3*(points[1]-2) + 13**2*(points[2]-2) + 13*(points[3]-2) + (points[4]-2)
	# 一对
	elif level == 2:
		value = base_1 + 13**3*(points[0]-2) + 13**2*(points[1]-2) + 13*(points[2]-2) + (points[3]-2)
	# 两对
	elif level == 3:
		value = base_2 + 13**2*(points[0]-2) + 13*(points[1]-2) + (points[2]-2)
	# 三条
	elif level == 4:
		value = base_3 + 13**2*(points[0]-2) + 13*(points[1]-2) + (points[2]-2)
	# 顺子
	elif level == 5:
		value = base_4 + (points[0]-2)
	# 同花
	elif level == 6:
		value = base_5 + 13**4*(points[0]-2) + 13**3*(points[1]-2) + 13**2*(points[2]-2) + 13*(points[3]-2) + (points[4]-2)
	# 葫芦
	elif level == 7:
		value = base_6 + 13* (points[0]-2) + (points[1]-2)
	# 四条
	elif level == 8:
		value = base_7 + 13* (points[0]-2) + (points[1]-2)
	# 同花顺
	elif level == 9:
		value = base_8 + (points[0]-2)

	return value

# 转牌轮后分析最大牌型
def parseTurnRoundLevel(turncards):
	result = []
	maxRet = None
	# combinations方法将实现多选多的过程
	combs = itertools.combinations(turncards, 5)
	for cards in combs:
		(value, level) = parseFlopRoundLevel(cards)
		ret = (value, level, cards)
		result.append(ret)
	if result:
		sortedRet = sorted(result, reverse=True)
		maxRet = sortedRet[0]

	valueMsg = 'Turn Round Max Cards Value: ' + str(maxRet[0])
	writeLog(valueMsg)
	print valueMsg

	levelMsg = 'Turn Round Max Cards Level: ' + getLevelByIndex(maxRet[1])
	writeLog(levelMsg)
	print levelMsg

	return maxRet

# 河牌轮后分析最大牌型
def parseRiverRoundLevel(rivercards):
	result = []
	maxRet = None
	# combinations方法将实现多选多的过程
	combs = itertools.combinations(rivercards, 5)
	for cards in combs:
		(value, level) = parseFlopRoundLevel(cards)
		ret = (value, level, cards)
		result.append(ret)
	if result:
		sortedRet = sorted(result, reverse=True)
		maxRet = sortedRet[0]

	valueMsg = 'River Round Max Cards Value: ' + str(maxRet[0])
	writeLog(valueMsg)
	print valueMsg

	levelMsg = 'River Round Max Cards Level: ' + getLevelByIndex(maxRet[1])
	writeLog(levelMsg)
	print levelMsg

	return maxRet

# 获取当前没有弃牌的玩家
def getOnlinePlayers(gameinfo):
	activePlayers = []
	for player in gameinfo.players:
		if player.status == 1:
			activePlayers.append(player.id)
	return activePlayers

# 根据没有弃牌的玩家信息，进行初步的分析
def handleActive(gameinfo):
	activePlayers = getOnlinePlayers(gameinfo)
	print 'active Count: ', len(activePlayers)
	if len(activePlayers) == 1:
		msg = 'all_in'
	else:
		msg = None
	return msg, activePlayers

# 通过分析这轮用户的所有操作，得出本玩家能够执行那些操作
def parseOperationSet(gameinfo):
	"通过分析收到的用户操作，得出本玩家能够执行哪些操作"
	'''
	# 起手牌操作
	if gameinfo.numSet == 1:
		# 跟注|加注|全押|弃牌
		dpSet = [3, 4, 5, 6]

	# 有公共牌时的操作
	else:
		# 让牌|跟注|加注|全押|弃牌
		dpSet = [2, 3, 4, 5, 6]
	'''
	dpSet = [3, 4, 5, 6]

	for action in gameinfo.actions[::-1]:

		# 处理raise操作
		if action.opid == 4:
			# 在所有种类的德州扑克中，加注必须等于或高于该圈最后一个加注牌手的加注金额
			# 若该圈尚未有牌手加注，则加注金额必需大于或等于大盲注。
			# 在这里，如果有人加注了，那么记录最小加注金额
			if action.oparg == None:
				gameinfo.minRaiseCount = max(gameinfo.minRaiseCount, int(gameinfo.bigBlindBet))
			else:
				gameinfo.minRaiseCount = int(action.oparg)

		# 对于check，这里增加可check的判定
		elif action.opid == 2:
			dpSet = [2, 3, 4, 5, 6]

		# 对于all_in，这里增加对是否满足最小加注的判定
		elif action.opid == 5:
			player = gameinfo.getPlayerById(action.player)
			myRaise = int(action.bet) - int(player.lastbet)
			if myRaise >= gameinfo.minRaiseCount:
				dpSet = [5, 6]

		else:
			continue

	return dpSet

def parseRaisePolicy(gameinfo):
	'''
	判定玩这手牌的松紧策略
	对于经济差距较大的情况，
	'''
	if gameinfo.gameNum <= 10:
		tightPolicy = 0
		return tightPolicy

	money = []
	for player in gameinfo.players:
		money.append(int(player.money)+int(player.jetton))
	myid = gameinfo.myid
	me = gameinfo.myplayer
	myrank = me.rank
	# sumrank = len(gameinfo.players)

	# 这里，有必要解释一下应该选择怎样的策略：
	# 如果我不是第一名但是又在前4，那么我们就玩得稍微松一点，如果在后面，就玩最松的牌
	# 如果我是第一名，那么必然玩紧牌，我们这里定义了一个阈值，超过阈值，就最紧，否则，稍稍紧一点就行
	if myrank != 1:
		# 这个地方，首先看看自己是什么名次，如果在前4名，那么就选择较紧策略，否则就选择最松策略
		# 你都快要死了，还要紧有个屁用。所以，实行松机制，没钱不疯狂一下？？
		if myrank <= 6:
			tightPolicy = 1
		else:
			tightPolicy = 0
	else:
		mymoney = int(me.money)
		myjetton = int(me.jetton)
		allmoney = sum(money)
		secondMoney = sorted(money, reverse=True)[1]
		smallMoneyGap = 0.10 * (mymoney + myjetton)
		bigMoneyGap = 0.40 * (mymoney + myjetton)
		greatMoneyGap = 0.16 * allmoney
		gapMoney = mymoney - secondMoney

		# 当经济差距较大时，实行紧机制，越有钱就越不能任性
		if gapMoney >= smallMoneyGap :
			tightPolicy = 2
		elif gapMoney >= bigMoneyGap:
			tightPolicy = 3
		elif gapMoney >= greatMoneyGap:
			tightPolicy = 4

	return tightPolicy

def parsePlayersTights(gameinfo):
	# 通过分析各玩家的投注行为，获取各玩家的松紧策略
	# 说明：
	# 我们每过25局分析一次各玩家的投注行为，从而维护一个玩家松紧系数向量。
	# 那么，我们就可以根据这个向量实施相应的策略

	# pts表示对应player对应的tight系数
	# 如 pts[1111] = 2
	pts = []

	writeLog('\nParse Players Tights...')
	print 'Parse Players Tights....'

	# 这里，我们考虑到内存问题，选择了这样一种策略：
	# 每次计算后清空player的历史操作，仅仅将结果赋值到变量tightlevel中
	# 这样，后面计算时，前面的结果就自动保存为一个结果，然后再相加
	for ph in gameinfo.phSet:
		# ph表示一个玩家的操作历史
		phtights = ph.tightlevel
		for ctp in ph.cardtopot:
			cards = ctp.holdcards
			phtights += parseTightFromHoldCards(ctp.holdcards)
		aveTight = float(phtights)/(len(ph.cardtopot)+1)
		pt = {} 
		pt['id'] = ph.id
		pt['tight'] = aveTight
		pts.append(pt)
		ph.setTightLevel(aveTight)
		ph.cardtopot = []

	return pts

def parseTightFromHoldCards(mycards):
	# tight = 3
	flag =(
			justifyMode(mycards, pointMax=4, pointMin=4, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=13, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=10, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=12, plus=True, isuit=True)
			)
	if flag:
		return 3

	# tight = 2
	flag =(
			justifyMode(mycards, pointMax=2, pointMin=2, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=5, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=2, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=7, pointMin=6, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=9,pointMin=7, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=11, plus=False, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=10, plus=False, isuit=True) or
			justifyMode(mycards, pointMax=12, pointMin=9, plus=False, isuit=False)
			)
	if flag:
		return 2

	# tight = 1
	flag =(
			justifyMode(mycards, pointMax=2, pointMin=2, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=8, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=2, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=7, pointMin=6, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=10, pointMin=9, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=9,pointMin=7, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=11, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=10, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=9, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=8, plus=False, isuit=True) or
			justifyMode(mycards, pointMax=12, pointMin=10, plus=False, isuit=False) or 
			justifyMode(mycards, pointMax=12, pointMin=9, plus=False, isuit=True) or 
			justifyMode(mycards, pointMax=12, pointMin=8, plus=False, isuit=True)
			)
	if flag:
		return 1
	
	# 很松很松
	return 0

def getMyTightFromPalyerTights(gameinfo, activePlayers):
	pts = gameinfo.playertights
	# 记录紧玩家
	tightPlayers = []
	# 记录松玩家
	loosePlayers = []
	atpCount = 0  
	alpCount = 0 
	apCount = len(activePlayers)
	if gameinfo.gameNum%30 == 0:
		pts = parsePlayersTights(gameinfo)
		gameinfo.setPlayerTights(pts)
	for pt in pts:
		if pt['tight'] >= 1.2:
			tightPlayers.append(pt['id'])
		else:
			loosePlayers.append(pt['id'])
	for ap in activePlayers:
		if ap in tightPlayers:
			atpCount += 1
		if ap in activePlayers:
			alpCount += 1
	if atpCount == apCount:
		mytight = 3
	elif atpCount >= apCount/2:
		mytight = 2
	elif alpCount == apCount:
		mytight = 0
	elif alpCount >= apCount/2:
		mytight = 1

	return mytight

def parseHoldLevel(mycards):
	# 神级手牌，可以一直加注
	flag = justifyMode(mycards, pointMax=11, pointMin=11, plus=True, isuit=False)
	if flag:
		return 4

	# 神级手牌，跟注策略
	flag =(
			justifyMode(mycards, pointMax=4, pointMin=4, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=13, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=10, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=12, plus=True, isuit=True)
			)
	if flag:
		return 3

	# 手牌还不错，加注
	flag =(
			justifyMode(mycards, pointMax=2, pointMin=2, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=5, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=2, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=7, pointMin=6, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=9,pointMin=7, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=12, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=11, plus=False, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=10, plus=False, isuit=True) or
			justifyMode(mycards, pointMax=12, pointMin=9, plus=False, isuit=False)
			)
	if flag:
		return 2

	# 手牌还凑合，跟注吧
	flag =(
			justifyMode(mycards, pointMax=2, pointMin=2, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=8, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=14, pointMin=2, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=7, pointMin=6, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=10, pointMin=9, plus=True, isuit=False) or
			justifyMode(mycards, pointMax=9,pointMin=7, plus=True, isuit=True) or
			justifyMode(mycards, pointMax=13, pointMin=11, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=10, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=9, plus=False, isuit=False) or
			justifyMode(mycards, pointMax=13, pointMin=8, plus=False, isuit=True) or
			justifyMode(mycards, pointMax=12, pointMin=10, plus=False, isuit=False) or 
			justifyMode(mycards, pointMax=12, pointMin=9, plus=False, isuit=True) or 
			justifyMode(mycards, pointMax=12, pointMin=8, plus=False, isuit=True)
			)
	if flag:
		return 1
	
	# 对于其他较龊的牌也敢玩，你完蛋了。。。
	return 0

# 起手牌分析阶段，同时执行策略
def handRoundDecision(gameinfo):
	# 通过handleActive函数分析当前未弃牌的玩家数，并作出最简单只剩下自己时的操作
	(msg, aplayers) = handleActive(gameinfo)
	if msg:
		log = 'Hand Round Decision:' + msg 
		writeLog(log)
		return msg

	# 玩家排名策略分析
	mytight1 = parseRaisePolicy(gameinfo)
	gameinfo.mytight = mytight1
	if mytight1 == 4:
		msg = 'fold \n'
		log = 'Hand Round Decision: ' + msg 
		writeLog(log)
		return msg

	mytight2 = 0

	'''
	# 通过分析用户松紧策略决定自己的松紧策略
	mytight2 = getMyTightFromPalyerTights(gameinfo, aplayers)
	if mytight2 == 3:
		mytight2 = 1
	elif mytight2 == 0:
		mytight2 = 2
	'''

	# 策略分析取值
	if mytight1 == 0:
		tightPolicy = 0
	else:
		tightPolicy = max(mytight1, mytight2)

	tightInfo = 'Hand Round Tight Policy: ' + str(tightPolicy)
	writeLog(tightInfo)

	myrole = gameinfo.myplayer.role
	opSet = parseOperationSet(gameinfo)

	joinFlag = handCardsHandle(gameinfo.holdCards, myseatrole=myrole, tightPolicy=tightPolicy)

	if joinFlag:
		bigBet = int(gameinfo.bigBlindBet)/4 + gameinfo.minRaiseCount
		smallBet= max(int(gameinfo.minRaiseCount), int(gameinfo.bigBlindBet))
		holdLevel = parseHoldLevel(gameinfo.holdCards)
		writeLog('Hold Cards Level: ' + str(holdLevel))
		# 如果我的总筹码能够承受我希望加注的钱，那么就加注
		if bigBet < int(gameinfo.myplayer.jetton):
			if 4 in opSet:
				if gameinfo.holdNum <= 3:
					if holdLevel >= 3:
						msg = 'raise %s \n' % bigBet
					elif holdLevel == 2:
						msg = 'raise %s \n' % smallBet
					else:
						msg = 'call \n'
				elif gameinfo.holdNum <= 5:
					if holdLevel == 3:
						msg = 'raise %s \n' % bigBet
					elif holdLevel == 3:
						msg = 'raise %s \n' % smallBet
					else:
						msg = 'call \n'
				else:
					if holdLevel == 4:
						msg = 'raise %s \n' % smallBet
					else:
						msg = 'fold \n'
			else:
				# 前面的小伙伴们都是all_in了，我就只有两条路可选了：
				# 要么一起all_in一起嗨，要么fold等下轮了...
				# 这可是关系到身家性命，当然不能马虎对待了
				# 此处的想法是，不要轻易的all_in
				holdLevel = parseHoldLevel(gameinfo.holdCards)
				if holdLevel == 4:
					msg = 'all_in \n'
				else:
					msg = 'fold \n'
		# 完蛋，钱不够，那就all_in吧，死活一条命嘛
		else:
			if holdLevel == 4:
				msg = 'all_in \n'
			else:
				msg = 'fold \n'
	else:
		msg = 'fold \n'

	log = 'Hand Round Decision: ' + msg 
	writeLog(log)
	return msg

def flopRoundDecision(gameinfo):
	(msg, aplayers) = handleActive(gameinfo)
	if msg:
		log = 'Flop Round Decision: ' + msg 
		writeLog(log)
		return msg

	allcards = gameinfo.holdCards + gameinfo.publicCards
	(value, level) = parseFlopRoundLevel(allcards)

	mytight2 = 0
	# 玩家排名的策略分析
	mytight1 = gameinfo.mytight

	'''
	# 通过分析用户松紧策略决定自己的松紧策略
	mytight2 = getMyTightFromPalyerTights(gameinfo, aplayers)
	'''

	# 策略分析取值
	if mytight1 == 0:
		tightPolicy = 0
	else:
		tightPolicy = max(mytight1, mytight2)

	tightInfo = 'Flop Round Tight Policy: ' + str(tightPolicy)
	writeLog(tightInfo)

	cardsLevelMsg = 'Flop Round Cards Level: ' + getLevelByIndex(level)
	writeLog(cardsLevelMsg)

	msg = getFlopMsgBasedOnTightLevel(gameinfo, tightPolicy, level, value, gameinfo.flopNum)

	log = 'Flop Round Decision: ' + msg
	writeLog(log)

	return msg

def turnRoundDecision(gameinfo):
	(msg, aplayers) = handleActive(gameinfo)
	if msg:
		log = 'Turn Round Decision: ' + msg 
		writeLog(log)
		return msg

	allcards = gameinfo.holdCards + gameinfo.publicCards
	(value, level, cards) = parseTurnRoundLevel(allcards)

	mytight2 = 0
	# 玩家排名的策略分析
	mytight1 = gameinfo.mytight

	'''
	# 通过分析用户松紧策略决定自己的松紧策略
	mytight2 = getMyTightFromPalyerTights(gameinfo, aplayers)
	'''

	# 策略分析取值
	if mytight1 == 0:
		tightPolicy = 0
	else:
		tightPolicy = max(mytight1, mytight2)

	tightInfo = 'Turn Round Tight Policy: ' + str(tightPolicy)
	writeLog(tightInfo)

	cardsLevelMsg = 'Turn Round Cards Level: ' + getLevelByIndex(level)
	writeLog(cardsLevelMsg)

	msg = getTurnMsgBasedOnTightLevel(gameinfo, tightPolicy, level, value, gameinfo.turnNum)

	log = 'Turn Round Decision: ' + msg
	writeLog(log)

	return msg

def riverRoundDecision(gameinfo):
	(msg, aplayers) = handleActive(gameinfo)
	if msg:
		log = 'River Round Decision: ' + msg 
		writeLog(log)
		return msg

	allcards = gameinfo.holdCards + gameinfo.publicCards
	(value, level, cards) = parseRiverRoundLevel(allcards)

	mytight2 = 0
	# 玩家排名的策略分析
	mytight1 = gameinfo.mytight
	# 通过分析用户松紧策略决定自己的松紧策略
	mytight2 = getMyTightFromPalyerTights(gameinfo, aplayers)
	# 取两种策略分析的最大值
	tightPolicy = max(mytight1, mytight2)

	tightInfo = 'River Round Tight Policy: ' + str(tightPolicy)
	writeLog(tightInfo)

	cardsLevelMsg = 'River Round Cards Level: ' + getLevelByIndex(level)
	writeLog(cardsLevelMsg)
	
	msg = getRiverMsgBasedOnTightLevel(gameinfo, tightPolicy, level, value, gameinfo.riverNum)

	log = 'River Round Decision: ' + msg
	writeLog(log)

	return msg

# 在翻牌、转牌、河牌时进行决策处理
def getFlopMsgBasedOnTightLevel(gameinfo, tightPolicy, level, value, setNum=1):
	'''
	我们这里首先说明几种紧等级：
	0、最松等级
	1、较松等级
	2、较紧等级
	3、最紧等级
	'''
	# 分析接收到的操作集，得出可操作的行为
	opSet = parseOperationSet(gameinfo)
	canCheck = 2 in opSet
	allInCheck = (len(opSet)==2)
	bigBet = int(gameinfo.minRaiseCount) + int(gameinfo.bigBlindBet)/4
	smallBet = int(gameinfo.minRaiseCount)

	#发送信息
	allInMsg = 'all_in \n'
	bigRaiseMsg = 'raise ' + str(bigBet) + ' \n'
	smallRaiseMsg = 'raise ' + str(smallBet) + ' \n'
	callMsg = 'call \n'
	checkMsg = 'check \n'
	foldMsg = 'fold \n'

	if allInCheck:
		if level >= 6:
			return allInMsg
		else:
			return foldMsg

	myjetton = gameinfo.myplayer.jetton
	mymoney = gameinfo.myplayer.money
	if myjetton < smallBet:
		if mymoney > 0:
			if level >= 5:
				return allInMsg
			else:
				return foldMsg
		else:
			if level >= 3:
				return allInMsg
			else:
				return foldMsg
	#-----------------------------------##############################-------------------------------
	if tightPolicy == 0:

		if level >= 8:
			return allInMsg

		elif level == 7:
			if setNum <= 2:
				return bigRaiseMsg
			elif setNum == 3:
				return smallRaiseMsg
			elif setNum <= 5:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum <= 7:
				return checkMsg
			elif setNum == 8:
				return smallRaiseMsg
			else:
				return foldMsg

		elif level >= 5:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 5:
				return checkMsg
			else:
				return foldMsg

		elif level == 4:
			if setNum == 1:
				return smallRaiseMsg
			elif setNum <= 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 4:
				return checkMsg
			else:
				return foldMsg

		elif level == 3:
			if setNum <= 2:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 3:
				return checkMsg
			else:
				return foldMsg

		elif level == 2:
			if setNum == 1:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 2:
				return checkMsg
			else:
				return foldMsg

		elif level == 1:
			if value >= 338000:
				if setNum == 1:
					return checkMsg
				else:
					return foldMsg
			else:
				return foldMsg
		else:
			return foldMsg

	# ------------------------------------#########################-------------------------------- #
	elif tightPolicy == 1:

		if level >= 8:
			return allInMsg

		elif level == 7:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum == 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 4:
				return checkMsg
			else:
				return foldMsg

		elif level == 4:
			if setNum == 1:
				return smallRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 3:
			if setNum == 1:
				if value >= 400100:
					return smallRaiseMsg
				else:
					return callMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 2:
			if setNum <= 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 1:
			if value >= 345000 and setNum <= 2:
				return checkMsg
			else:
				return foldMsg
		else:
			return foldMsg

	# ------------------------------------#########################-------------------------------- #
	elif tightPolicy == 2:

		if level >= 8:
			return allInMsg

		if level == 7:
			if setNum <= 2:
				return bigRaiseMsg
			elif setNum == 3:
				return smallRaiseMsg
			elif setNum == 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 5:
				return checkMsg
			else:
				return foldMsg

		elif level >= 5:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 5:
				return checkMsg
			else:
				return foldMsg

		elif level == 4:
			if setNum == 1:
				return smallRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 3:
			if setNum == 1:
				if value >= 400000:
					return smallRaiseMsg
				else:
					return callMsg
			elif setNum <= 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 2:
			if setNum <= 2:
				return checkMsg
			else:
				return foldMsg

		elif level == 1:
			return foldMsg

	# ------------------------------------#########################-------------------------------- #
	elif tightPolicy == 3:

		if level >= 8:
			return allInMsg

		elif level == 7:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum == 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level >= 5:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 4:
			if setNum == 1:
				return smallRaiseMsg
			elif setNum <= 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 3:
			if setNum <= 2:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 2:
			if value <= 390000:
				return foldMsg
			else:
				if setNum == 1:
					return checkMsg
				else:
					return foldMsg

		elif level == 1:
			return foldMsg

# 在翻牌、转牌、河牌时进行决策处理
def getTurnMsgBasedOnTightLevel(gameinfo, tightPolicy, level, value, setNum=1):
	'''
	我们这里首先说明几种紧等级：
	0、最松等级
	1、较松等级
	2、较紧等级
	3、最紧等级
	'''
	# 分析接收到的操作集，得出可操作的行为
	opSet = parseOperationSet(gameinfo)
	canCheck = 2 in opSet
	allInCheck = (len(opSet)==2)
	bigBet = int(gameinfo.minRaiseCount) + int(gameinfo.bigBlindBet)/4
	smallBet = int(gameinfo.minRaiseCount)

	#发送信息
	allInMsg = 'all_in \n'
	bigRaiseMsg = 'raise ' + str(bigBet) + ' \n'
	smallRaiseMsg = 'raise ' + str(smallBet) + ' \n'
	callMsg = 'call \n'
	checkMsg = 'check \n'
	foldMsg = 'fold \n'

	if allInCheck:
		if level >= 6:
			return allInMsg
		else:
			return foldMsg

	myjetton = gameinfo.myplayer.jetton
	mymoney = gameinfo.myplayer.money
	if myjetton < smallBet:
		if mymoney > 0:
			if level >= 5:
				return allInMsg
			else:
				return foldMsg
		else:
			if level >= 3:
				return allInMsg
			else:
				return foldMsg

	# 对于所有的松紧度，绝不轻易使用all_in，因此都是在所有牌型为葫芦及葫芦以上才选择all_in
	# ------------------------------------#########################-------------------------------- #
	if tightPolicy == 0 or tightPolicy == 1:

		if level >= 8:
			return allInMsg

		elif level == 7:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum == 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 4:
				return checkMsg
			else:
				return foldMsg

		elif level == 6:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum == 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 4:
				return checkMsg
			else:
				return foldMsg

		elif level >= 5:
			if setNum == 1:
				return smallRaiseMsg
			elif setNum <= 3:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 4:
			if setNum <= 2:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 3:
				return checkMsg
			else:
				return foldMsg

		elif level == 3:
			if setNum <= 2:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 3:
				return checkMsg
			else:
				return foldMsg

		elif level == 2:
			if setNum == 1:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 2:
				return checkMsg
			else:
				return foldMsg

		elif level == 1:
			if value >= 338000 and setNum <= 2:
				return checkMsg
			else:
				return foldMsg
		else:
			return foldMsg

	# ------------------------------------#########################-------------------------------- #
	elif tightPolicy == 2 or tightPolicy == 3:
		if level >= 8:
			return allInMsg

		elif level == 7:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum <= 3:
				return smallRaiseMsg
			elif setNum <= 5:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum <= 7:
				return checkMsg
			else:
				return foldMsg

		elif level == 6:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum == 2:
				return smallRaiseMsg
			elif setNum <= 5:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum <= 7:
				return checkMsg
			else:
				return foldMsg

		elif level == 5:
			if setNum == 1:
				return bigRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum <= 6:
				return checkMsg
			else:
				return foldMsg

		elif level == 4:
			if setNum == 1:
				return smallRaiseMsg
			elif setNum <= 4:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			else:
				return foldMsg

		elif level == 3:
			if setNum == 1:
				if value >= 400100:
					return smallRaiseMsg
				else:
					return callMsg
			elif setNum == 2:
				if canCheck:
					return checkMsg
				else:
					return callMsg
			elif setNum == 3:
				return checkMsg
			else:
				return foldMsg

		elif level == 2:
			if setNum <= 2:
				return checkMsg
			else:
				return foldMsg

		elif level == 1:
			return foldMsg


# 在翻牌、转牌、河牌时进行决策处理
def getRiverMsgBasedOnTightLevel(gameinfo, tightPolicy, level, value, setNum=1):
	'''
	我们这里首先说明几种紧等级：
	0、最松等级
	1、较松等级
	2、较紧等级
	3、最紧等级
	'''
	# 分析接收到的操作集，得出可操作的行为
	opSet = parseOperationSet(gameinfo)
	canCheck = 2 in opSet
	allInCheck = (len(opSet)==2)
	bigBet = int(gameinfo.minRaiseCount) + int(gameinfo.bigBlindBet)/4
	smallBet = int(gameinfo.minRaiseCount)

	#发送信息
	allInMsg = 'all_in \n'
	bigRaiseMsg = 'raise ' + str(bigBet) + ' \n'
	smallRaiseMsg = 'raise ' + str(smallBet) + ' \n'
	callMsg = 'call \n'
	checkMsg = 'check \n'
	foldMsg = 'fold \n'

	if allInCheck:
		if level >= 6:
			return allInMsg
		else:
			return foldMsg

	myjetton = gameinfo.myplayer.jetton
	mymoney = gameinfo.myplayer.money
	if myjetton < smallBet:
		if mymoney > 0:
			if level >= 5:
				return allInMsg
			else:
				return foldMsg
		else:
			if level >= 3:
				return allInMsg
			else:
				return foldMsg
	if True:

		if level >= 8:
			return allInMsg
		elif level == 8:
			return callMsg
		elif level == 7:
			return callMsg
		elif level == 6:
			return checkMsg
		elif level == 5:
			return checkMsg
		elif level == 4:
			return checkMsg
		elif level == 3:
			return checkMsg
		elif level == 2:
			return checkMsg
		elif level == 1:
			return foldMsg