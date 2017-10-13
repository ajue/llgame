# -*- coding: utf-8 -*-
import KBEngine
import random
import Halls
import Games
import json
from datetime import datetime,time
from d_config import *
from Rules_DDZ import *
from Rules_ZJH import *
import Helper

class Player(KBEngine.Proxy):
	"""
	玩家实体
	客户端登陆到服务端后，服务端将自动创建这个实体，通过这个实体与客户端进行交互
	"""
	def __init__(self):
		KBEngine.Proxy.__init__(self)

		#玩家当前所在游戏
		self.gameID = 0

		# 玩家当前所在大厅
		self.hallID = 0

		# 玩家当前所在房间
		self.roomID = 0

		self.bContinue = False

	def createCell(self, space,cid):
		"""
        defined method.
        """

		if self.cell:
			pass
		else:

			self.cellData["dbid"]  = self.databaseID
			self.cellData["nameC"] = self.name
			self.cellData["goldC"] = Helper.Round(self.gold)
			self.cellData["sexC"]  = self.sex
			self.cellData["headC"] = self.head
			self.cellData["addrC"] = self.addr
			self.cellData["cards"] = []
			self.cellData["cardCount"] 	= 0
			self.cellData["curScore"] 		= -1
			self.cellData["showCards"] 	= []
			self.cellData["multiple"] 		= 1
			self.cellData["type"] 			= 0  # 0无身份 1地主 2农民
			self.cellData["tuoguan"] 		= 0  # 0正常 1托管
			self.cellData["cid"] 			= cid

			#zjh
			self.cellData["cost"]		= 0.0
			self.cellData["chip"] 		= 0.0
			self.cellData["lookcard"] 	= 0
			self.cellData["stateC"]	= 0
			self.cellData["first"]		= 0


			self.createCellEntity(space)
			self.bContinue = False
		
	def onEntitiesEnabled(self):
		"""
		KBEngine method.
		该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
		cell部分。
		"""
		INFO_MSG("Account[%i]::onEntitiesEnabled:entities enable. mailbox:%s, clientType(%i), clientDatas=(%s), accountName=%s" % \
			(self.id, self.client, self.getClientType(), self.getClientDatas(), self.__ACCOUNT_NAME__))

		# 并处于Games中
		KBEngine.globalData["Games"].reqEnterGames(self)

		#如果是机器人，则直接初始化属性
		if self.getClientType() == 6:
			self.name = "bots%r" % self.id
			self.gold = 1000.0
			self.sex  = 1
			self.head = 1

	def onLogOnAttempt(self, ip, port, password):
		"""
		KBEngine method.
		客户端登陆失败时会回调到这里
		"""
		return KBEngine.LOG_ON_ACCEPT

	def onClientDeath(self):
		"""
		KBEngine method.
		客户端对应实体已经销毁
		"""
		if self.state == 0:
			if self.cell:
				self.destroyCellEntity()
			else:
				self.destroy()

		INFO_MSG("------------Account[%r].state[%r]onClientDeath()------------" % (self.id,self.state))

	def onGetCell(self):
		"""
        KBEngine method.
        entity的cell部分实体被创建成功
        """
		DEBUG_MSG('Player::onGetCell: %s' % self.cell)

	def onLoseCell(self):
		"""
        KBEngine method.
        entity的cell部分实体丢失
        """
		DEBUG_MSG("%s::onLoseCell: %r" % (self.className, self.id))
		if self.bContinue:
			self.reqEnterRoom(self.addr)

		elif not self.client:
			self.destroy()

	def onDestroy(self):

		DEBUG_MSG("Player::onDestroy player[%r] gameID[%r] hallID[%r] roomID[%r]" %
				  (self.id,self.gameID,self.hallID,self.roomID))

		# 先退出大厅，退出大厅功能中应该能确保后续所有的事情
		if self.state == 0:
			if self.roomID != 0:
				self.reqLeaveRoom()
			if self.hallID != 0:
				self.reqLeaveHall()
			if self.gameID != 0:
				self.reqLeaveGame()

			KBEngine.globalData["Games"].reqLeaveGames(self)

	def reqReviseProperties(self,name,sex,head):
		"""
		Exposed
		设置玩家属性
		"""
		retcode = 0
		if self.name == "" or self.name is None:
			# 注册
			self.name = name
			self.sex  = sex
			self.head = head
			self.gold = 6.0
			self.writeToDB()

		elif name == "":
			#改名时值为""
			retcode = -1

		else:
			#修改属性成功
			self.name = name
			if sex > 0 and sex <= 2:
				self.sex = sex
			if head > 0:
				self.head = head

			self.writeToDB()

		self.client.onReviseProperties(retcode,self.name,self.sex,self.head)

	def reqAccessBank(self,access,offsetGold):
		"""
		Exposed
		银行存取
		access == 1 为存钱，== 2为取钱
		offsetGold 为金额
		"""
		retcode = -1
		if access == 1 and self.gold >= offsetGold:
			self.gold -= offsetGold
			self.bankGold += offsetGold
			retcode = 0
		elif access == 2 and self.bankGold>=offsetGold:
			self.gold += offsetGold
			self.bankGold -= offsetGold
			retcode = 0

		#retcode 0为存取成功，-1为存取失败，防止作弊
		self.client.onAccessBank(retcode,self.gold,self.bankGold)

	def reqNoticeInfos(self):
		"""
		Exposed
		获取静态公告以及滑动公告信息
		"""
		notice_string = json.dumps(d_notice)
		self.client.onNoticeInfos(notice_string)

	def reqGameInfo(self):
		"""
		请求游戏类型，游戏信息，游戏在线人数
		"""
		KBEngine.globalData["Games"].reqGameInfo(self)

	def reqGamesConfig(self):
		KBEngine.globalData["Games"].reqGamesConfig(self)

	def reqRanksInfo(self):
		"""
		Exposed
		"""
		KBEngine.globalData["Ranks"].reqRanksInfo(self)

	def reqMyRankInfo(self):
		"""
		Exposed
		"""
		KBEngine.globalData["Ranks"].reqMyRankInfo(self)

	def reqEnterGame(self,gameID):
		"""
		exposed
		"""
		# assert self.gameID == 0
		INFO_MSG("Player[%i].reqEnterGame: %s" % (self.id, gameID))

		KBEngine.globalData["Games"].reqEnterGame(self,gameID)

	def reqLeaveGame(self):
		"""
		exposed
		"""
		if self.gameID == 0:
			return

		INFO_MSG("Player[%i].reqLeaveGame: %s" % (self.id, self.gameID))

		KBEngine.globalData["Games"].reqLeaveGame(self, self.gameID)

	def reqEnterHall(self, hallID):
		"""
		exposed.
		客户端调用该接口请求进入大厅
		"""
		assert self.gameID != 0
		INFO_MSG("Player[%i].reqEnterHall: %s" % (self.id, "Halls"+ str(self.gameID)))
		
		KBEngine.globalData["Halls"+ str(self.gameID)].reqEnterHall(self, hallID)
		
	def reqLeaveHall(self):
		"""
		exposed.
		客户端调用该接口请求离开大厅
		"""
		INFO_MSG("Player[%i].reqLeaveHall: %s" % (self.id, self.hallID))

		KBEngine.globalData["Halls"+ str(self.gameID)].reqLeaveHall(self, self.hallID)

	def reqEnterRoom(self,addr):
		"""
		exposed.
		客户端调用该接口请求进入房间开局
		"""
		INFO_MSG("Player[%r]::reqEnterRoom" % (self.id))

		self.addr = addr
		KBEngine.globalData["Halls"+str(self.gameID)].reqEnterRoom(self, self.hallID)

	def reqLeaveRoom(self):
		"""
		exposed.
		"""
		INFO_MSG("Player[%r]::reqLeaveRoom" % (self.id))
		KBEngine.globalData["Halls"+str(self.gameID)].reqLeaveRoom(self, self.hallID, self.roomID)

	def reqContinue(self):
		"""
		exposed
		继续游戏
		"""
		INFO_MSG("Player[%r]::reqContinue" % (self.id))

		KBEngine.globalData["Halls" + str(self.gameID)].reqContinue(self, self.hallID, self.roomID)

	def reqCashInfo(self,amount):

		retcode = 0
		income  = 0

		if amount < 50:
			retcode = -2
		elif (self.gold - amount) >= d_users["base_money"]:
			if amount <= d_users["duixian_base"]:
				income = d_users["duixian_base_fee"]
			else:
				income += d_users["duixian_base_fee"]
				rate = (int)((amount - d_users["duixian_base"])/d_users["duixian_add"])
				remain = (int)((amount - d_users["duixian_base"]) % (int)(d_users["duixian_add"]))
				income += rate*d_users["duixian_add_fee"]
				if remain > 0 :
					income += d_users["duixian_add_fee"]
		else:
			retcode = -1
		INFO_MSG("amount:%r  income:%r" % (amount,income))

		self.client.onCashInfo(retcode,amount,int(income))

	def reqCash(self,amount,alipay):
		#请求兑现
		INFO_MSG("Player::reqCash")
		retcode = 0
		income  = 0
		if self.alipay != alipay:
			self.alipay = alipay

		#进行写入兑现数据表操作,并扣去玩家对应金额
		if(self.gold - amount) >= d_users["base_money"]:
			self.gold -= amount
			if amount <= d_users["duixian_base"]:
				income = d_users["duixian_base_fee"]
			else:
				income += d_users["duixian_base_fee"]
				rate = (int)((amount - d_users["duixian_base"]) / d_users["duixian_add"])
				remain = (int)((amount - d_users["duixian_base"]) % (int)(d_users["duixian_add"]))
				income += rate * d_users["duixian_add_fee"]
				if remain > 0:
					income += d_users["duixian_add_fee"]

			curAmount = amount - income
			KBEngine.globalData["Games"].addIncome(income)
			sql = "insert into TBL_WITHDDRAW(USER,ZHIFUBAO_NUMBER,ADDTIME,AMOUNT) values('%s','%s','%s','%s')" \
				  % (self.__ACCOUNT_NAME__,self.alipay,datetime.now(),str(curAmount))
			KBEngine.executeRawDatabaseCommand(sql, None)
		else:
			retcode = -1

		if self.client:
			self.client.onCash(retcode,self.gold,self.alipay)

	def reqRefresh(self):
		INFO_MSG(" Player::reqRefresh ")

		data = {}
		data["gold"] = self.gold
		json_string = json.dumps(data)

		if self.client:
			self.client.onRefresh(json_string)

	def reqMessage(self,action,string):
		"""
		exposed
		"""
		KBEngine.globalData["Halls"+str(self.gameID)].reqMessage(self,action,string)


	def set_gold(self,settleGold):

		gold = Helper.Round(settleGold)
		self.gold += gold

		DEBUG_MSG("Player::set_gold player[%r] self.gold[%r] settleGold[%r]" % (self.id,self.gold, gold))

