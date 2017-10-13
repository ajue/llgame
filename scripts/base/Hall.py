# -*- coding: utf-8 -*-
import KBEngine
import time
from KBEDebug import *
from d_config import *

class Hall(KBEngine.Base):
	"""
	大厅实体
	该实体管理该大厅中所有的房间/桌
	"""
	def __init__(self):
		KBEngine.Base.__init__(self)

		#空房队列
		self.roomIDList = []

		# 所有空房间
		self.rooms = {}

		# 进入该大厅的所有玩家mailbox
		self.players = {}

		INFO_MSG("Hall[%i] __init__" % (self.hallID))
		
	def _createRooms(self):
		"""
		根据玩家人数，动态创建房间
		根据游戏类型进行不同房间的使用创建
		"""
		roomID = len(self.rooms.values()) + 1

		self.rooms[roomID] = KBEngine.createBaseLocally("Room", {"hallID":self.hallID, "roomID" : roomID})

		self.roomIDList.append(roomID)
		return self.rooms[roomID]

	def reqEnterHall(self, player):
		"""
		defined.
		客户端调用该接口请求进入大厅
		onEnterHall 返回-1 为金钱不足，0为已经开始一局游戏
		"""
		if player.gold < d_ZJH[self.hallID]["limit"]:
			player.client.onEnterHall(-1)
			INFO_MSG("Player[%r] Hall.reqEnterHall gold < limit" % (player.__ACCOUNT_NAME__))

			return

		INFO_MSG("Hall.reqEnterHall success: %r" % (player.__ACCOUNT_NAME__))
		self.players[player.id] = player
		player.hallID = self.hallID

		if player.client:
			player.client.onEnterHall(self.hallID)

	def reqLeaveHall(self, player):
		"""
		defined.
		客户端调用该接口请求离开大厅
		应该在这里做一些条件，允许进入后返回给角色离开成功
		"""
		if player.id in self.players:
			del self.players[player.id]
			player.hallID = 0
			if player.client:
				player.client.onLeaveHall(player.hallID)

	def reqEnterRoom(self, player):
		"""
		defined.
		客户端调用该接口请求进入房间/桌子
		遍历房间，为玩家匹配空房间
		"""
		INFO_MSG("Player[%r].Hall[%r].reqEnterRoom" % (player.__ACCOUNT_NAME__, self.hallID))
		INFO_MSG("self.rooms = %r" % (self.rooms.keys()))

		if len(self.roomIDList) > 0:
			for value in self.roomIDList:
				self.rooms[value].reqEnterRoom(player)
				INFO_MSG(" test input value = %r hasNull = %r" % (value,self.rooms[value].hasNull()))
				if not self.rooms[value].hasNull():
					self.roomIDList.remove(value)
					INFO_MSG("test remains rooms = %r " % (self.roomIDList))
				break
		else:
			room = self._createRooms()
			room.reqEnterRoom(player)

	def reqPlayerCount(self):
		"""
        defined.
        获取玩家数量
        """
		return len(self.players.values())

	def reqMessage(self,player,action,string):
		"""
		define
		"""
		INFO_MSG("Player[%s].Hall[%r].reqMessage(roomID = %r) and self.rooms = %r" % (
			player.__ACCOUNT_NAME__,
			self.hallID,
			player.roomID,
			self.rooms.keys()))

		if player.roomID in self.rooms.keys():
			self.rooms[player.roomID].reqMessage(player, action, string)

	def reqLeaveRoom(self, player, roomID):
		"""
		defined.
		先检测满人房间，如果有人离开，则重新归类
		"""
		INFO_MSG("Player[%r].Hall[%r].reqLeaveRoom roomID = %r" % (player.__ACCOUNT_NAME__, self.hallID,roomID))

		if roomID in self.rooms.keys():
			#此时客户端可能已经断了
			self.rooms[roomID].reqLeaveRoom(player)
			if self.rooms[roomID].hasNull():
				self._sorted(self.rooms[roomID])
				# self.roomIDList.append(roomID)

	def _sorted(self,room):
		#将金花人数最多的房间推到顶部
		success = False
		for rid in self.roomIDList:
			if self.rooms[rid].reqPlayerCount() <= room.reqPlayerCount():
				success = True
				self.roomIDList.insert(self.roomIDList.index(rid), room.roomID)
				DEBUG_MSG("_sorted index = %r roomIDlist = %r" % (self.roomIDList.index(rid),self.roomIDList))
				break
		if not success:
			self.roomIDList.append(room.roomID)
