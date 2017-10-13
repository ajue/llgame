# -*- coding: utf-8 -*-
import KBEngine
import random
import time
import d_games
import d_config
import Helper
from GlobalConst import *
import json
from KBEDebug import *


class Games(KBEngine.Base):
	"""
	游戏管理器实体
	该实体管理该服务组上所有的游戏类型
	"""
	def __init__(self):
		KBEngine.Base.__init__(self)

		KBEngine.globalData["Games"] = self

		self.games = {}

		self.players = {}

		self.orders = {}

		# 通过添加一个定时器延时执行游戏大厅的创建，确保一些状态在此期间能够初始化完毕
		self.addTimer(1,0,1)

		DEBUG_MSG("Games::__init__ Games[%r]" % (self.id))

	def onTimer(self, id, userArg):
		"""
		KBEngine method.
		使用addTimer后， 当时间到达则该接口被调用
		@param id		: addTimer 的返回值ID
		@param userArg	: addTimer 最后一个参数所给入的数据
		"""
		if userArg == 1:
			self._createGames()

	def _createGames(self):
		"""
		callback
		根据配置创建出所有游戏
		"""
		for infos in d_games.datas.values():
			KBEngine.createBaseAnywhere("Halls",{"hallsID":infos["id"],"hallsName":infos["gameName"],"open":infos["open"]})

	def reqGamesConfig(self,player):
		"""
		获取游戏配置
		"""
		string_json = json.dumps(d_config.d_users)
		player.client.onGamesConfig(string_json)

	def reqEnterGames(self,player):
		self.players[player.id] = player

		delList = []
		for name in self.orders.keys():
			if player.__ACCOUNT_NAME__ == name:

				player.gold += self.orders[name]
				delList.append(name)

				DEBUG_MSG("player[%r] online and charge money[%r] success" % (name,self.orders[name]))

		for name in delList:
			del self.orders[name]

	def reqLeaveGames(self,player):

		if player in self.players.values():
			del self.players[player.id]

		INFO_MSG("Games::reqLeaveGames player[%r]" % player.id)

	def reqEnterGame(self,player,gameID):
		"""
		defined.
		进入指定游戏
		"""
		self.games[gameID].reqEnterHalls(player)

	def reqLeaveGame(self,player,gameID):
		"""
		defined.
		离开指定游戏
		"""
		if gameID in self.games:
			self.games[gameID].reqLeaveHalls(player)

	def addHalls(self,id,mailbox):
		"""
		defined.
		注册指定游戏大厅管理器
		"""
		self.games[id] = mailbox

	def reqGameInfo(self,player):
		"""
		define.
		请求游戏信息
		"""
		results = []
		for halls in self.games.values():
			count = halls.reqPlayerCount()
			result = {}
			result["id"] = halls.hallsID
			result["name"] = halls.hallsName
			result["status"] = getServerStatus(count)
			result["players_count"] = count
			result["open"] = halls.open
			results.append(result)

		json_results = json.dumps(results)
		if player.client:
			player.client.onGameInfo(json_results)

	def reqChargeToPlayer(self,accountName,amount):
		"""请求充值"""
		chargeStatus = False
		for player in self.players.values():
			if(player.__ACCOUNT_NAME__ == accountName):
				player.gold += amount

				chargeStatus = True
				player.reqRefresh()
				break

		if not chargeStatus:
			INFO_MSG("charge account[%r] not online. but order is saved" % (accountName))
			self.orders[accountName] = amount
		else:
			INFO_MSG("charge account[%r] for amount[%r] is success" % (accountName,amount))

	def addIncome(self,add):
		"""收益统计"""
		income = Helper.Round(add)

		self.income += income

		self.writeToDB()
		INFO_MSG("Games::addIncome income[%r] add[%r]" % (self.income,income))



