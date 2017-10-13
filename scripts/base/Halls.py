# -*- coding: utf-8 -*-
import KBEngine
import random
import time
import d_games
import json
from GlobalConst import *
from d_config import  *
from KBEDebug import *
from Functor import Functor

class Halls(KBEngine.Base):
	"""
	大厅管理器实体
	该实体管理该服务组上所有的大厅
	"""
	def __init__(self):
		KBEngine.Base.__init__(self)
		# 将自己注册到共享数据中， 在当前进程KBEngine.globalData["Halls"]返回的是Halls实体，其他进程中
		# 由于实体不在那个进程所以KBEngine.globalData["Halls"]返回的是mailbox
		# 因此调用KBEngine.globalData["Halls"].xxx方法必须在def定义，允许远程访问
		
		# 将大厅管理器注册到游戏当中
		KBEngine.globalData["Games"].addHalls(self.hallsID,self)
		# 将大厅管理器设置为全局
		KBEngine.globalData["Halls" + str(self.hallsID)] = self

		# 存放所有大厅信息与mailbox
		self.halls = {}

		# 进入该游戏的所有玩家mailbox
		self.players = {}

		# 创建游戏大厅
		self.addTimer(1,0,1)

		INFO_MSG("Halls[%i].__init__" % (self.hallsID))

	def onTimer(self, id, userArg):
		"""
		KBEngine method.
		使用addTimer后， 当时间到达则该接口被调用
		@param id		: addTimer 的返回值ID
		@param userArg	: addTimer 最后一个参数所给入的数据
		"""
		self._createHalls()
		
	def _createHalls(self):
		"""
		根据配置创建出所有的大厅
		"""
		for i in range(d_games.datas[self.hallsID]["hallCount"]):
			hallID = i + 1
			if self.hallsID == GAME_TYPE_DDZ:
				KBEngine.createBaseAnywhere("DdzHall", { "hallID": hallID},Functor(self.onCreateBaseCallback,hallID))
			elif self.hallsID == GAME_TYPE_ZJH:
				KBEngine.createBaseAnywhere("Hall", {"hallID" : hallID},Functor(self.onCreateBaseCallback,hallID))

	def onCreateBaseCallback(self,id,mailbox):
		"""
		defined.
		向大厅管理器添加大厅
		"""
		self.halls[id] = mailbox

		
	def removeHall(self, id):
		"""
		defined.
		向大厅管理器移除大厅
		"""
		del self.halls[id]
		
	def reqEnterHall(self, player, hallID):
		"""
		defined.
		客户端调用该接口请求进入大厅
		"""
		INFO_MSG("Halls[%i].reqEnterHall" % (self.hallsID))

		self.halls[hallID].reqEnterHall(player)
		
	def reqLeaveHall(self, player, hallID):
		"""
		defined.
		客户端调用该接口请求离开大厅
		"""
		INFO_MSG("Halls[%i].reqLeaveHall: %s" % (self.hallsID, hallID))
		if self.halls[hallID]:
			self.halls[hallID].reqLeaveHall(player)
		

	def reqEnterRoom(self, player, hallID):
		"""
		defined.
		客户端调用该接口请求进入房间/桌子
		"""
		INFO_MSG("Halls::reqEnterRoom Player[%r] Halls[%r] " % (player.id,self.hallsID))

		if len(self.halls.values()) >= hallID:
			self.halls[hallID].reqEnterRoom(player)
		
	def reqLeaveRoom(self, player, hallID, roomID):
		"""
		defined.
		客户端调用该接口请求离开房间/桌子
		"""
		INFO_MSG("Halls::reqLeaveRoom Player[%r] Halls[%r] " % (player.id, self.hallsID))

		if hallID in self.halls:
			self.halls[hallID].reqLeaveRoom(player, roomID)

	def say(self, player, hallID, roomID, str):
		"""
		defined.
		说话的内容
		"""
		INFO_MSG("Halls[%i].say: %s" % (self.hallsID, str))
		self.halls[hallID].say(player, roomID, str)

	def reqPlayerCount(self):
		"""
		defined.
		获取玩家数量
		"""
		return len(self.players.values())

	def reqEnterHalls(self,player):
		"""
		define
		"""
		player.gameID = self.hallsID
		self.players[player.id] = player

		results = []
		if self.hallsID == GAME_TYPE_ZJH:
			for hall in self.halls.values():
				count = hall.reqPlayerCount()
				result = {}
				result["id"] = hall.hallID
				result["status"] = getServerStatus(count)
				result["players_count"] = count
				result["limit"] = d_ZJH[hall.hallID]["limit"]
				result["base"] = d_ZJH[hall.hallID]["base"]
				results.append(result)
		elif self.hallsID == GAME_TYPE_DDZ:
			for hall in self.halls.values():
				count = hall.reqPlayerCount()
				result = {}
				result["id"] = hall.hallID
				result["status"] = getServerStatus(count)
				result["players_count"] = count
				result["limit"] = d_DDZ[hall.hallID]["limit"]
				result["base"] = d_DDZ[hall.hallID]["base"]
				results.append(result)
		json_results = json.dumps(results)

		if player.client:
			player.client.onEnterGame(self.hallsID, json_results)

	def reqLeaveHalls(self,player):

		if self.players[player.id]:
			del self.players[player.id]
			if player.client:
				player.client.onLeaveGame(player.gameID)

		player.gameID = 0

	def reqContinue(self,player,hallID,roomID):
		"""继续游戏"""
		INFO_MSG("Halls::reqContinue Player[%r] Halls[%r]" % (player.id, self.hallsID))

		if hallID in self.halls:
			self.halls[hallID].reqContinue(player,roomID)

	def reqMessage(self,player,action,string):
		"""
		define
		@return:
		"""
		INFO_MSG("Halls::reqMessage Player[%r] Halls[%r]" % (player.id,self.hallsID))

		if player.hallID in self.halls:
			self.halls[player.hallID].reqMessage(player,action,string)


