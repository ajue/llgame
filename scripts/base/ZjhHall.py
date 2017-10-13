# -*- coding: utf-8 -*-
import KBEngine
import time
from GlobalConst import *
from KBEDebug import *
from d_config import *

class ZjhHall(KBEngine.Base):
	"""
	大厅实体
	该实体管理该大厅中所有的房间/桌
	"""
	def __init__(self):
		KBEngine.Base.__init__(self)

		#空房队列
		self.roomsList = []

		# 管理所有房间实体
		self.rooms = {}

		# 进入该大厅的所有玩家mailbox
		self.players = {}

		#管理所有房间缓冲请求
		self.roomReqs = {}

		self.lastNewRoomID = 0

		INFO_MSG("ZjhHall[%i] __init__" % (self.hallID))

	def reqEnterHall(self, player):
		"""
		defined.
		客户端调用该接口请求进入大厅
		onEnterHall 返回-1 为金钱不足，0为已经开始一局游戏
		"""
		if player.gold < d_ZJH[self.hallID]["limit"]:
			player.client.onEnterHall(-1)

			INFO_MSG("ZjhHall::reqEnterHall Player[%r] gold < limit" % (player.id))
			return

		INFO_MSG("ZjhHall::reqEnterHall Player[%r]" % (player.id))

		self.players[player.id] = player

		player.hallID = self.hallID

		if player.client:
			player.client.onEnterHall(self.hallID)

	def reqLeaveHall(self, player):
		"""
		defined.
		客户端调用该接口请求离开大厅
		"""
		if player.id in self.players:

			del self.players[player.id]

			if player.client:
				player.client.onLeaveHall(player.hallID)

			player.hallID = 0
		
	def createRooms(self, player):
		"""
		根据玩家人数，动态创建房间
		"""

		roomData = self.roomReqs.get(self.lastNewRoomID)

		if roomData is None or len(roomData["Reqs"]) >= 5:
			self.lastNewRoomID = len(self.rooms) + 1
			KBEngine.createBaseAnywhere("ZjhRoom", {"parent": self,
													"roomID": self.lastNewRoomID,
													"state": 0,
													"dizhu": d_ZJH[self.hallID]["base"],
													"limit": d_ZJH[self.hallID]["limit"],
													"jzList":json.dumps(d_ZJH[self.hallID]["jzList"]),
													"taxRate": d_ZJH["taxRate"]}, None)

			self.roomReqs[self.lastNewRoomID] = {"Reqs":[player.id]}

		else:
			if player.id not in roomData["Reqs"]:
				roomData["Reqs"].append(player)


	def onRoomGetCell(self, roomMailbox, roomID):
		"""
        defined method.
        Room的cell创建好了
        """
		self.rooms[roomID] = roomMailbox
		self.roomsList.append(roomID)

		# space已经创建好了， 现在可以将之前请求进入的玩家全部丢到cell地图中
		for pid in self.roomReqs[roomID]["Reqs"]:

			roomMailbox.onEnterRoom(self.players[pid])

			if not roomMailbox.hasNull():
				self.roomsList.remove(roomID)

		del self.roomReqs[roomID]

	def reqEnterRoom(self, player):
		"""
		defined.
		客户端调用该接口请求进入房间/桌子
		遍历房间，为玩家匹配空房间
		"""
		INFO_MSG("ZjhHall::reqEnterRoom Hall[%r] Player[%r]" % (self.hallID,player.id))

		#to do gold < limit
		if len(self.roomsList) > 0:
			for value in self.roomsList:
				self.rooms[value].onEnterRoom(player)
				if not self.rooms[value].hasNull():
					self.roomsList.remove(value)
				break
		else:
			self.createRooms(player)


	def reqLeaveRoom(self, player, roomID):
		"""
		defined.
		先检测满人房间，如果有人离开，则重新归类
		"""
		INFO_MSG("ZjhHall::reqLeaveRoom Hall[%r] Room[%r] Player[%r]" % (self.hallID,roomID,player.id))

		if roomID in self.rooms.keys():

			self.rooms[roomID].onLeaveRoom(player)

			if self.rooms[roomID].hasNull():

				self._sorted(self.rooms[roomID])

	def _sorted(self,room):
		#将金花人数最多的房间推到顶部

		success = False

		for rid in self.roomsList:

			if self.rooms[rid].reqPlayerCount() <= room.reqPlayerCount():
				success = True

				self.roomsList.insert(self.roomsList.index(rid), room.roomID)

				DEBUG_MSG("_sorted index = %r roomslist = %r" % (self.roomsList.index(rid), self.roomsList))
				break

		if not success:
			self.roomsList.append(room.roomID)


	def reqPlayerCount(self):
		"""
        获取玩家数量
        """
		return len(self.players.values())

	def reqMessage(self, player, action, string):

		INFO_MSG("ZjhHall::reqMessage Hall[%r] Player[%r]" % (self.hallID, player.id))

		if player.roomID in self.rooms.keys():
			self.rooms[player.roomID].reqMessage(player, action, string)
