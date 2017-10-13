# -*- coding: utf-8 -*-
import KBEngine
import random
import time
import json
import Functor
from KBEDebug import *
class Ranks(KBEngine.Base):
	"""
	排行榜管理器实体
	该实体管理该服务组上所有的游戏类型
	"""
	def __init__(self):
		KBEngine.Base.__init__(self)

		KBEngine.globalData["Ranks"] = self

		INFO_MSG("Ranks[%i].__init__" % (self.id))

	def onTimer(self, id, userArg):
		"""
		KBEngine method.
		使用addTimer后， 当时间到达则该接口被调用
		@param id		: addTimer 的返回值ID
		@param userArg	: addTimer 最后一个参数所给入的数据
		"""

	def reqRanksInfo(self,player):
		"""
		Exposed
		获取排行榜信息
		"""
		#获取排行榜前 n 名的数据
		# sql = "SELECT @rownum := @rownum + 1 AS rank,sm_name,sm_gold+sm_bankGold AS totalGold FROM tbl_Player,(SELECT @rownum :=0) b ORDER BY totalGold DESC LIMIT 10"
		sql = "SELECT CASE WHEN @rowtotal = sm_gold+sm_bankGold THEN @rownum " \
			  "WHEN @rowtotal := sm_gold+sm_bankGold THEN @rownum :=@rownum + 1 " \
			  "WHEN @rowtotal = 0 THEN @rownum :=@rownum + 1 END AS rank," \
			  "sm_name,sm_gold+sm_bankGold AS totalGold FROM tbl_Player," \
			  "(SELECT @rownum :=0,@rowtotal := NULL) b ORDER BY totalGold DESC LIMIT 10"

		KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(self.onRanksInfo, player))

	def reqMyRankInfo(self,player):
		"""
		Exposed
		获取自己的排名信息
		"""

		sql = "SELECT (SELECT count(1)+1 as rank  from tbl_Player WHERE " \
			  "(sm_gold+sm_bankGold) > (SELECT sm_gold+sm_bankGold FROM" \
			  " tbl_Player WHERE id = %i))AS rank ,sm_name,(sm_gold+sm_bankGold) " \
			  "AS totalGold FROM tbl_Player WHERE id=%i " % (player.databaseID,player.databaseID)

		INFO_MSG("Ranks.reqMyRankInfo player[%i]" % (player.databaseID))

		KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(self.onMyRankInfo, player))

	def onRanksInfo(self, player, result, line, error):
		"""
		返回的数据库回掉
		"""
		# str = "huangyechuan"
		# str_utf8 = str.encode(encoding="utf-8")

		str_result = []
		for i in result:
			str_i = []
			for j in i:
				str_j = j.decode()
				str_i.append(str_j)
			str_result.append(str_i)

		json_result = json.dumps(str_result)
		player.client.onRanksInfo(json_result)

		INFO_MSG("Ranks._onRanksInfo result = %r, line = %r,error = %r" % (str_result,line,error))

	def onMyRankInfo(self, player, result, line, error):
		"""
        返回的数据库回掉
        """
		# str = "huangyechuan"
		# str_utf8 = str.encode(encoding="utf-8")

		str_result = []
		for i in result:
			for j in i:
				str_j = j.decode()
				str_result.append(str_j)

		json_result = json.dumps(str_result)
		player.client.onMyRankInfo(json_result)
		INFO_MSG("Ranks.onMyRankInfo result = %r, line = %r,error = %r" % (str_result, line, error))


