import KBEngine
from KBEDebug import *
from Rules_DDZ import *
import random
import json

class Player(KBEngine.Entity):

	def __init__(self):
		KBEngine.Entity.__init__(self)
		self.gameID = 0
		self.hallID = 0
		self.roomID = 0
		self.chairID = 0

		self.base.reqEnterGame(1)

		DEBUG_MSG("Bots Player __init__")

	def onGameInfo(self,data):
		pass
	def onGamesConfig(self,data):
		pass
	def onCash(self,retcode,alipay,phone):
		pass
	def onCharge(self, gold, amount):
		pass
	def onRefresh(self,data):
		pass
	def onCashInfo(self, retcode, glod, amount):
		pass
	def onStartGame(self):
		pass

	def onEnterGame(self,gameID,result):
		self.gameID = gameID
		self.base.reqEnterHall(1)

	def onLeaveGame(self,gameID):
		pass
	def onEnterHall(self,hallID):
		self.hallID = hallID
		self.base.reqEnterRoom("广东省深圳市")
		pass
	def onLeaveHall(self,hallID):
		pass
	def onEnterRoom(self,data):
		pass
	def onEnterDDZRoom(self,chairID):
		self.chairID = chairID
		pass
	def onLeaveRoom(self,retcode,chairID):
		if self.chairID == chairID:
			self.base.reqLeaveHall()

	def onContinue(self):
		pass
	def onRoomState(self,data):
		pass
	def onMessage(self,retcode,action,data):
		data_json = json.loads(data)
		if action == ACTION_ROOM_COMPUTE :
			self.base.reqContinue()

	def onRegisterProperties(self,retcode):
		pass
	def onAccessBank(self,retcode,access,offsetGold):
		pass
	def onReviseProperties(self,retcode,name,sex,head):
		pass
	def onRanksInfo(self,data):
		pass
	def onMyRankInfo(self,data):
		pass
	def onNoticeInfos(self,data):
		pass
	def onSay(self,str):
		pass
	def onUpdateHalls(self,data):
		pass