
# -*- coding: utf-8 -*-
import KBEngine
import random
import time
from d_config import *
from KBEDebug import *
from GlobalConst import *

FIND_ROOM_NOT_FOUND = 0
FIND_ROOM_CREATING = 1

class DdzHall(KBEngine.Base):
	"""
	大厅实体
	"""
	def __init__(self):

		KBEngine.Base.__init__(self)

		#房间管理
		self.rooms = {}

		#玩家管理
		self.players = {}

		self.lastNewRoomKey = 0

	def reqEnterHall(self, player):
		"""
        defined.
        客户端调用该接口请求进入大厅
        onEnterHall 返回-1 为金钱不足，0为已经开始一局游戏
        """
		if player.gold < d_DDZ[self.hallID]["limit"]:
			player.client.onEnterHall(-1)
			INFO_MSG("DdzHall::reqEnterHall Player[%r] gold < limit" % (player.id))
			return

		INFO_MSG("DdzHall::reqEnterHall Player[%r]" % (player.id))

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

			if player.client:
				player.client.onLeaveHall(player.hallID)

		player.hallID = 0


	def findRoom(self, roomID, notFoundCreate = False):
		"""
        查找一个指定房间，如果找不到允许创建一个新的
        """
		DEBUG_MSG("DdzHall::findRoom self.rooms[%r]" % (self.rooms.keys()))
		roomDatas = self.rooms.get(roomID)

		# 如果房间没有创建，则将其创建
		if not roomDatas:
			if not notFoundCreate:
				return FIND_ROOM_NOT_FOUND

			# 如果最后创建的房间没有满员，则使用最后创建的房间key，否则产生一个新的房间唯一Key
			roomDatas = self.rooms.get(self.lastNewRoomKey)
			if roomDatas is not None and len(roomDatas["players"]) < 3:
				if roomDatas["roomMailbox"] is not None and roomDatas["roomMailbox"].state != ROOM_STATE_READY:
					pass
				else:
					return roomDatas

			self.lastNewRoomKey = KBEngine.genUUID64()

			KBEngine.createBaseAnywhere("DdzRoom",
										{"parent": self,
										 "state": 0,
										 "roomID": self.lastNewRoomKey,
										 "difen": d_DDZ[self.hallID]["base"],
										 "taxRate": d_DDZ["taxRate"]}
										,None)

			roomDatas = {"roomMailbox": None, "players": {}, "roomID": self.lastNewRoomKey}
			self.rooms[self.lastNewRoomKey] = roomDatas

			return roomDatas

		return roomDatas

	def onRoomGetCell(self, roomMailbox, roomID):
		"""
        defined method.
        Room的cell创建好了
        """
		self.rooms[roomID]["roomMailbox"] = roomMailbox

		# space已经创建好了， 现在可以将之前请求进入的玩家全部丢到cell地图中
		for entity in self.rooms[roomID]["players"].values():
			roomMailbox.onEnterRoom(entity)


	def reqEnterRoom(self, player):
		"""
        defined method.
        请求进入某个Room中
        """
		roomDatas = self.findRoom(player.roomID, True)

		#去重
		if player.id in roomDatas["players"]:
			return

		roomMailbox = roomDatas["roomMailbox"]

		roomDatas["players"][player.id] = player

		if roomMailbox is not None:
			roomMailbox.onEnterRoom(player)

	def reqLeaveRoom(self, player, roomID):

		DEBUG_MSG("DdzHall::reqLeaveRoom Player[%r] Hall[%r] RoomID[%r]" % (player.id,self.hallID, roomID))

		roomDatas = self.findRoom(roomID, False)

		if type(roomDatas) is dict:
			roomMailbox = roomDatas["roomMailbox"]

			if roomMailbox:
				roomMailbox.onLeaveRoom(player)

				if player.id in roomDatas["players"]:
					del roomDatas["players"][player.id]
					if len(roomDatas["players"]) <= 0:
						del self.rooms[roomID]
		else:
			# 由于玩家即使是掉线都会缓存至少一局游戏， 因此应该不存在退出房间期间地图正常创建中
			if roomDatas == FIND_ROOM_CREATING:
				raise Exception("FIND_ROOM_CREATING")

	def reqContinue(self,player,roomID):

		DEBUG_MSG("DdzHall::reqContinue Player[%r] Hall[%r] RoomID[%r]" % (player.id, self.hallID, roomID))

		if player.gold < d_DDZ[self.hallID]["limit"]:

			DEBUG_MSG("DdzHall::reqContinue Player[%d] gold[%r] < limit[%r]" % (player.id,player.gold,d_DDZ[self.hallID]["limit"]))
			self.reqLeaveRoom(player,roomID)
			return

		roomDatas = self.findRoom(roomID, False)

		if type(roomDatas) is dict:
			roomMailbox = roomDatas["roomMailbox"]
			if roomMailbox.state != ROOM_STATE_INGAME:

				roomMailbox.onContinue(player)

				if player.id in roomDatas["players"]:
					del roomDatas["players"][player.id]
					if len(roomDatas["players"]) <= 0:
						del self.rooms[roomID]

	def reqPlayerCount(self):

		return len(self.players.values())

