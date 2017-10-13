# -*- coding: utf-8 -*-
import KBEngine
import random
import time
import json
from KBEDebug import *
from Rules_ZJH import *
from d_config import *
import Helper

class Room(KBEngine.Base):
    """
	这是一个游戏房间
	该房间中记录了房间里所有玩家的mailbox，通过mailbox我们可以将信息推送到他们的客户端。
	"""

    def __init__(self):
        KBEngine.Base.__init__(self)

        # 跟进chairID ,存储该房间内的玩家MAILBOX
        self.chairPlayers = {}
        # 当前ID
        self.curChairID = 0
        # 庄家ID
        self.makerID = 0
        # 胜利ID
        self.victoryID = 0

        # 当房内玩家大于2人时，则计算开局时间
        self.roomTime = 8
        self.curRoomTime = 0

        # 玩家回合思考时间
        self.limitTime = 20
        self.curLimitTime = 0

        # 总注数
        self.dizhu   = d_ZJH[self.hallID]["base"]
        self.limit   = d_ZJH[self.hallID]["limit"]
        self.taxRate = d_ZJH["taxRate"]

        # 定时管理器
        self.timerMgr = {}
        self._initState_()

        INFO_MSG("Room.__init__")

    def _initState_(self):
        """重置房间状态"""

        # 状态 0：未开始游戏， 1：游戏中
        self.state = 0
        # 第几轮
        self.curTurn = 0
        #游戏中的人数
        self.playCount = 0

        self.curRoomTime = 0
        self.curLimitTime = 0
        self.curzhu = self.dizhu
        self.totalzhu = 0.0
        #筹码链表
        self.chipMgr = []

        for pp in self.chairPlayers.values():
            pp.isLookCard = False
            pp.status = PLAYER_STATE_READY
            pp.curCost = 0.0
            pp.cards = []
            pp.curTurn = 0

        self._removeUserArgTimer(0)

    def _addUserArgTimer(self, initialOffset, repeatOffset, userArg):

        tid = self.addTimer(initialOffset, repeatOffset, userArg)
        bMgr = False
        if userArg in self.timerMgr:
            self._removeUserArgTimer(userArg)
        if repeatOffset > 0:
            self.timerMgr[userArg] = tid
            bMgr = True
        INFO_MSG("addTimer = %i userArg = %r,isMgr =%r" % (tid, DEBUG_ACTION_STRING[userArg], bMgr))

    def _removeUserArgTimer(self, userArg):

        if userArg == 0:
            INFO_MSG("delTimer ALL")
            for tt in self.timerMgr.values():
                self.delTimer(tt)
            self.timerMgr.clear()

        elif userArg in self.timerMgr:
            tid = self.timerMgr.pop(userArg)
            self.delTimer(tid)
            INFO_MSG("delTimer = %i,userArg = %r" % (tid, DEBUG_ACTION_STRING[userArg]))

    def onTimer(self, id, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param id		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """
        INFO_MSG("ACTION_ROOM_NEXT curLimitTime = %r,size = %i" % (self.curLimitTime, len(self.timerMgr.keys())))

        if userArg == ACTION_ROOM_TIME and self.curRoomTime > 0:
            self.curRoomTime -= 1
            if self.curRoomTime == 0:
                self._removeUserArgTimer(0)
                self.state = 1
                self._dispatchCards()

            INFO_MSG("onTimer userArg = %i curRoomTimer = %i state = %i" % (userArg, self.curRoomTime, self.state))

        elif userArg == ACTION_ROOM_START:
            #完成发牌后，确定庄家
            self._startGame()
        elif userArg == ACTION_ROOM_NEXT and self.curLimitTime > 0:
            #计算超时
            self.curLimitTime -= 1
            if self.curLimitTime == 0:
                self._removeUserArgTimer(0)
                data = {}
                data["chairID"] = self.curChairID
                data_string = json.dumps(data)
                self.reqMessage(self.chairPlayers[self.curChairID],ACTION_ROOM_QIPAI,data_string)

            # INFO_MSG("ACTION_ROOM_NEXT curLimitTime = %r,size = %i"%(self.curLimitTime,len(self.timerMgr.keys())))

        elif userArg == ACTION_ROOM_SETTLE:
            # 游戏结算
            self._removeUserArgTimer(0)
            koushui = Helper.Round((self.totalzhu - self.chairPlayers[self.victoryID].curCost) * self.taxRate)
            KBEngine.globalData["Games"].addIncome(koushui)

            self.totalzhu = self.totalzhu - koushui
            self.chairPlayers[self.victoryID].gold += self.totalzhu
            INFO_MSG("ACTION_ROOM_SETTLE======== self.totalzhu = %i vitoryID = %i koushui = %i gold=%i" % (self.totalzhu,self.victoryID,koushui,self.chairPlayers[self.victoryID].gold))

            self._broadcastAllCards()

            data = {}
            self.curChairID = self.victoryID
            data["victoryID"] = self.victoryID
            data["addzhu"] = self.totalzhu
            data["gold"] = self.chairPlayers[self.victoryID].gold
            data_string = json.dumps(data)
            self._broadcastMessage(0, ACTION_ROOM_SETTLE, data_string)
            self._addUserArgTimer(3, 0, ACTION_ROOM_CLEARGAME)

        elif userArg == ACTION_ROOM_CLEARGAME:
            self._initState_()
            self._broadcastMessage(0, ACTION_ROOM_CLEARGAME, "")

            # 如果金钱不足，则踢出房间
            removePlayers = []
            for pp in self.chairPlayers.values():
                if pp.gold < self.limit:
                    removePlayers.append(pp)
            for pp in removePlayers:
                self.reqLeaveRoom(pp)

            # 如果人数大于2，则开始游戏
            if  len(self.chairPlayers.values()) >= 2:
                self.curRoomTime = self.roomTime
                data = {"room_time": self.curRoomTime}
                data_string = json.dumps(data)
                self._broadcastMessage(0, ACTION_ROOM_TIME, data_string)
                self._addUserArgTimer(2, 1, ACTION_ROOM_TIME)

        elif userArg == ACTION_ROOM_KAIPAI_BEGIN:
            self._removeUserArgTimer(0)
            self._autoKaipai()
            self._addUserArgTimer(2,0,ACTION_ROOM_PUBLICH)

        elif userArg == ACTION_ROOM_PUBLICH:
            self._broadcastAllCards()
            self._addUserArgTimer(0.0, 0, ACTION_ROOM_SETTLE)

    def reqEnterRoom(self, player):
        """
		defined.
		客户端调用该接口请求进入房间/桌子
		并进行房间内广播通知
		"""
        INFO_MSG("Room.reqEnterRoom: roomID[%s],playerSize = %i" % (self.roomID, len(self.chairPlayers.values())))
        if player.client is None:
            return
        # 玩家所在场次的座位id
        player.chairID = 0
        # 玩家状态，0为不在游戏中
        player.status = PLAYER_STATE_GARK
        # 卡牌
        player.cards = []
        # 当前下注
        player.curCost = 0
        # 是否看牌
        player.isLookCard = False
        #进行到第几轮
        player.curTurn = 0

        # 进入房间后，分配chairID,返回房间状态
        for i in range(1, 6):
            has = False
            for tmp in self.chairPlayers.values():
                if i == tmp.chairID:
                    has = True
                    break
            if has == False:
                player.chairID = i
                break
        INFO_MSG("%s,Room.reqEnterRoom:set chairID == %i" % (player.__ACCOUNT_NAME__, player.chairID))

        #如果游戏未开始，则设置为准备状态
        if self.state == 0:
            player.status = PLAYER_STATE_READY

        #先下自身以及房间信息
        data = {}
        data["chairID"] = player.chairID
        data["state"] = player.status
        data["makerID"] = self.makerID
        data["limitTime"] = self.limitTime
        data["dizhu"] = self.dizhu
        data["totalzhu"] = self.totalzhu
        data["jiazhuConfig"] = d_ZJH[self.hallID]["jzList"]
        data["chipMgr"] = self.chipMgr
        data["addr"] = player.addr

        data_string = json.dumps(data)
        player.client.onRoomState(data_string)

        # 再下发房间内玩家信息
        for tmp in self.chairPlayers.values():
            data = {}
            data["chairID"] = player.chairID
            data["state"] = player.status
            data["name"] = player.name
            data["curCost"] = player.curCost
            data["gold"] = player.gold
            data["sex"] = player.sex
            data["head"] = player.head
            data["addr"] = player.addr
            data_string = json.dumps(data)
            tmp.client.onEnterRoom(data_string)

            data = {}
            data["chairID"] = tmp.chairID
            data["name"] = tmp.name
            data["curCost"] = tmp.curCost
            data["gold"] = tmp.gold
            data["state"] = tmp.status
            data["sex"] = tmp.sex
            data["head"] = tmp.head
            data["addr"] = tmp.addr
            data_string = json.dumps(data)
            player.client.onEnterRoom(data_string)

        player.roomID = self.roomID
        self.chairPlayers[player.chairID] = player

        # 当玩家数2人以上，游戏未开始
        INFO_MSG("%s,players len: %i , status:%i , curRoomTime:%i" % (player.__ACCOUNT_NAME__, len(self.chairPlayers.values()), self.state, self.curRoomTime))
        if len(self.chairPlayers.values()) >= 2 and self.state == 0:
            if self.curRoomTime <=0:
                self.curRoomTime = self.roomTime

            data = {"room_time": self.curRoomTime}
            data_string = json.dumps(data)
            self._broadcastMessage(0,ACTION_ROOM_TIME,data_string)
            self._addUserArgTimer(1,1,ACTION_ROOM_TIME)

    def reqLeaveRoom(self, player):
        """
		defined.
		客户端调用该接口请求离开房间/桌子
		"""
        INFO_MSG("Hall.reqLeaveRoom: %s" % (player.roomID))
        #退出房间先弃牌
        if player.status > PLAYER_STATE_LINE:
        	self._reqQipai(player.chairID)

        for pp in self.chairPlayers.values():
            if pp and pp.client:
                pp.client.onLeaveRoom(0,player.chairID)

        del self.chairPlayers[player.chairID]

        if len(self.chairPlayers.values()) < 2:
            self.curRoomTime = 0
            self.curLimitTime = 0
            self._removeUserArgTimer(0)

        player.roomID = 0
        player.chairID = 0
        player.status = 0

        # 如果房间内少于2人，且游戏未开始则重置cur_room_time
        if len(self.chairPlayers.values()) < 2 and self.state == 0:
            self._initState_()

    def reqMessage(self, player, action, string):
        """处理玩家游戏行为"""
        INFO_MSG("Room.reqMessage action = %r str = %s playerSize = %i" % (DEBUG_ACTION_STRING[action], string, len(self.chairPlayers.values())))
        #self.state = 0 为未开始游戏，= 2为完成当局游戏
        if self.state != 1:
            return

        data = json.loads(string)
        if action == ACTION_ROOM_GENZHU:
            self._removeUserArgTimer(0)
            chairID = data["chairID"]
            recode = 0
            tmpzhu = 0
            if self.chairPlayers[chairID].isLookCard:
                tmpzhu = self.curzhu * 2
                if self.chairPlayers[chairID].gold >= tmpzhu:
                    self.chairPlayers[chairID].gold -= tmpzhu
                    self.totalzhu += tmpzhu
                else:
                    recode = 1  # 金币不足
            else:
                tmpzhu = self.curzhu
                if self.chairPlayers[chairID].gold >= self.curzhu:
                    self.chairPlayers[chairID].gold -= self.curzhu
                    self.totalzhu += self.curzhu
                else:
                    recode = 1  # 金币不足

            self.chairPlayers[chairID].curCost += tmpzhu
            self.chipMgr.append(tmpzhu)
            data["curzhu"] = tmpzhu
            data_string = json.dumps(data)
            self._broadcastMessage(recode, ACTION_ROOM_GENZHU, data_string)
            self._broadcastUpdateRoom(recode, chairID, self.chairPlayers[chairID].gold,self.chairPlayers[chairID].curCost)
            self._broadcastNext()

        elif action == ACTION_ROOM_KANPAI:
            INFO_MSG("ACTION_ROOM_KANPAI chairID:%i" % (data["chairID"]))
            chairID = data["chairID"]

            if chairID in self.chairPlayers:
                self.chairPlayers[chairID].isLookCard = True
                self.chairPlayers[chairID].status = PLAYER_STATE_KANPAI
                data["state"] = self.chairPlayers[chairID].status
                data["cards"] = self.chairPlayers[chairID].cards
                data_string = json.dumps(data)
                self._broadcastMessage(0,ACTION_ROOM_KANPAI,data_string)

        elif action == ACTION_ROOM_JIAZHU:
            self._removeUserArgTimer(0)
            chairID = data["chairID"]
            jiazhu = data["jiazhu"]

            self.curzhu = jiazhu  # 当前注
            recode = 0
            if chairID in self.chairPlayers:
                curzhu = 0
                if self.chairPlayers[chairID].isLookCard:
                    curzhu = self.curzhu * 2
                    if self.chairPlayers[chairID].gold >= curzhu:
                        self.chairPlayers[chairID].gold -= curzhu
                        self.totalzhu += curzhu
                    else:
                        recode = 1  # 金币不足
                else:
                    curzhu = self.curzhu
                    if self.chairPlayers[chairID].gold >= self.curzhu:
                        self.chairPlayers[chairID].gold -= self.curzhu
                        self.totalzhu += self.curzhu
                    else:
                        recode = 1  # 金币不足

                data["curzhu"] = curzhu
                self.chairPlayers[chairID].curCost += curzhu
                self.chipMgr.append(curzhu)
                data_string = json.dumps(data)
                self._broadcastMessage(recode, ACTION_ROOM_JIAZHU, data_string)
                self._broadcastUpdateRoom(recode, chairID, self.chairPlayers[chairID].gold,self.chairPlayers[chairID].curCost)
                self._broadcastNext()

        elif action == ACTION_ROOM_BIPAI_START:
            self._broadcastMessage(0, ACTION_ROOM_BIPAI_START, string)
        elif action == ACTION_ROOM_BIPAI_END:
            self._removeUserArgTimer(0)

            chair1 = data["chair1"]  # chairID
            chair2 = data["chair2"]  # chairID

            cards1 = self.chairPlayers[chair1].cards
            cards2 = self.chairPlayers[chair2].cards

            #先计算玩家比牌所花
            mult = 2
            if self.chairPlayers[chair1].isLookCard and not self.chairPlayers[chair2].isLookCard:
                mult = 4

            settleGold = self.curzhu*mult
            self.chairPlayers[chair1].gold -= settleGold
            self.chairPlayers[chair1].curCost += settleGold
            self.totalzhu += settleGold
            self.chipMgr.append(settleGold)

            self._broadcastUpdateRoom(0,chair1,self.chairPlayers[chair1].gold,self.chairPlayers[chair1].curCost)

            # 比牌
            data = {}
            if CompareCards(cards1, cards2):
                # cards 1胜利
                data["wid"] = chair1
                data["wCards"] = cards1
                data["lid"] = chair2
                data["lCards"] = cards2
                self.chairPlayers[chair1].status = PLAYER_STATE_WIN
                self.chairPlayers[chair2].status = PLAYER_STATE_LOSER
            else:
                data["wid"] = chair2
                data["wCards"] = cards2
                data["lid"] = chair1
                data["lCards"] = cards1
                self.chairPlayers[chair1].status = PLAYER_STATE_LOSER
                self.chairPlayers[chair2].status = PLAYER_STATE_WIN

            data["wState"] = self.chairPlayers[data["wid"]].status
            data["lState"] = self.chairPlayers[data["lid"]].status

            data_string = json.dumps(data)
            self._broadcastMessage(0, ACTION_ROOM_BIPAI_END, data_string)

            if self._checkResult():
                # 如果胜利，则先存储庄家ID
                self._addUserArgTimer(0.0,0,ACTION_ROOM_SETTLE)
            else:
                self._broadcastNext()

        elif action == ACTION_ROOM_QIPAI:
            self._removeUserArgTimer(0)
            INFO_MSG("ACTION_ROOM_QIPAI chairID:%i" % (data["chairID"]))
            chairID = data["chairID"]
            self._reqQipai(chairID)

    def _reqQipai(self, chairID):
        """弃牌"""

        if self.state != 1:
            return

        self.chairPlayers[chairID].status = PLAYER_STATE_QIPAI
        data = {}
        data["chairID"] = chairID
        data["state"] = PLAYER_STATE_QIPAI

        data_string = json.dumps(data)
        self._broadcastMessage(0, ACTION_ROOM_QIPAI, data_string)


        if self._checkResult():
            self._addUserArgTimer(0.0,0,ACTION_ROOM_SETTLE)
        else:
            if self.curChairID == chairID:
                self._broadcastNext()

    def _checkResult(self):
        """检测当局是否玩家胜利,并存储胜利玩家的ID"""

        count = 0
        tmpid = 0
        for pp in self.chairPlayers.values():
            if pp.status > PLAYER_STATE_LINE:
                tmpid = pp.chairID
                count += 1

        if count <= 1:
            #存储胜利ID
            self.victoryID = tmpid
            self.state = 2
            return True

        return False

    def _dispatchCards(self):
        """
		发牌
		"""
        cards = reqRandomCards52()
        for pp in self.chairPlayers.values():
            pp.cards = self._requireList(cards, 3)

            pp.status = PLAYER_STATE_START
            pp.gold -= self.dizhu
            pp.curCost += self.dizhu
            self.totalzhu += self.dizhu
            self.chipMgr.append(self.dizhu)

            data = {}
            data["curzhu"] = self.dizhu
            data_string = json.dumps(data)
            pp.client.onMessage(0, ACTION_ROOM_DISPATCH, data_string)
            INFO_MSG("Room._dispatchCards json %r" % (data_string))
            self._broadcastUpdateRoom(0, pp.chairID, pp.gold, pp.curCost)

        self._addUserArgTimer(1, 0, ACTION_ROOM_START)

    def _broadcastMessage(self, recode, action, str):
        """广播"""
        for pp in self.chairPlayers.values():
            if pp.client:
                pp.client.onMessage(recode, action, str)
        INFO_MSG("_broadcastMessage action = %r,str = %r" % (DEBUG_ACTION_STRING[action],str))

    def _broadcastTheirMessage(self,player,recode,action,str):
        for pp in self.chairPlayers.values():
            if pp.client and pp.chairID != player.chairID:
                pp.client.onMessage(recode, action, str)
        INFO_MSG("_broadcastTheirMessage action = %r,str = %r" % (DEBUG_ACTION_STRING[action], str))

    def _broadcastUpdateRoom(self, recode, chairID, gold,curCost):

        info = {}
        info["gold"] = gold
        info["chairID"] = chairID
        info["curCost"] = curCost
        info["totalzhu"] = self.totalzhu
        info["curzhu"] = self.curzhu
        info_string = json.dumps(info)
        self._broadcastMessage(recode, ACTION_INFO_UPDATE, info_string)
        INFO_MSG("Room._broadcastUpdateRoomData %i" % (chairID))

    def _startGame(self):
        """确定庄家"""
        # userArg 11 为完成发牌后，确定庄家
        self.curChairID = self._autoMakerID()
        self.curTurn = 1
        self.chairPlayers[self.curChairID].curTurn = 1

        for pp in self.chairPlayers.values():
            start = {}
            self.curLimitTime = self.limitTime

            start["curChairID"] = self.curChairID
            start["curTurn"] = self.curTurn
            start_string = json.dumps(start)
            if pp.client:
                pp.client.onMessage(0, ACTION_ROOM_START, start_string)
            self._addUserArgTimer(1,1,ACTION_ROOM_NEXT)

    def _broadcastAllCards(self):
        """公布所有玩家的牌"""
        for pp in self.chairPlayers.values():
            if pp.status > PLAYER_STATE_QIPAI:
                data = {}
                data["chairID"] = pp.chairID
                data["cards"] = pp.cards
                data_string = json.dumps(data)
                self._broadcastMessage(0, ACTION_ROOM_PUBLICH, data_string)

    def _broadcastNext(self):

        lastChairID = self.curChairID
        for i in range(0, 5):
            tmp = (self.curChairID + i) % 5 + 1
            if tmp in self.chairPlayers:
                if self.chairPlayers[tmp].status > PLAYER_STATE_LINE:
                    self.curChairID = tmp
                    break

        if self.curTurn > self.chairPlayers[self.curChairID].curTurn:
            self.chairPlayers[self.curChairID].curTurn = self.curTurn
        else:
            self.curTurn += 1

        #如果金币不足2倍，则开牌
        if self.chairPlayers[self.curChairID].gold < self.curzhu * 2:
            self._broadcastMessage(0, ACTION_ROOM_KAIPAI_BEGIN, "")
            self._addUserArgTimer(2,0,ACTION_ROOM_KAIPAI_BEGIN)
            pass
        else:
            self.curLimitTime = self.limitTime
            info = {}
            info["curLimitTime"] = self.curLimitTime
            info["lastChairID"] = lastChairID
            info["curChairID"] = self.curChairID
            info["curTurn"] = self.curTurn
            info_string = json.dumps(info)
            self._broadcastMessage(0, ACTION_ROOM_NEXT, info_string)
            self._addUserArgTimer(1, 1, ACTION_ROOM_NEXT)

            INFO_MSG("Room._broadcastNext lastChairID: %i  ,curChairID:%i" % (lastChairID, self.curChairID))

    def _autoKaipai(self):
        """自动开牌"""
        players = []
        winPlayer = self.chairPlayers[self.curChairID]
        players.append(winPlayer)
        for i in range(0, 5):
            tt = (self.curChairID + i) % 5 + 1
            if tt in self.chairPlayers:
                if self.chairPlayers[tt].status > PLAYER_STATE_LINE and tt != self.curChairID:
                    if CompareCards(winPlayer.cards,self.chairPlayers[tt].cards):
                        self.chairPlayers[tt].status = PLAYER_STATE_LOSER
                        winPlayer.status = PLAYER_STATE_WIN
                        players.append(self.chairPlayers[tt])
                        self.victoryID = winPlayer.chairID
                    else:
                        winPlayer.status = PLAYER_STATE_LOSER
                        self.chairPlayers[tt].status = PLAYER_STATE_WIN
                        winPlayer = self.chairPlayers[tt]
                        self.victoryID = winPlayer.chairID
                        players.append(winPlayer)
        datas = []
        for pp in players:
            data = {}
            data["chairID"] = pp.chairID
            data["state"] = pp.status
            data["cards"] = pp.cards
            datas.append(data)

        data_json = json.dumps(datas)
        self._broadcastMessage(0,ACTION_ROOM_KAIPAI_END,data_json)


    def _autoMakerID(self):
        #如果victoryID == 0时，随机分配一个makerID,否则makerID为victoryID下一位
        if self.victoryID == 0 and len(self.chairPlayers.keys()) >= 2:
            for kk in self.chairPlayers.keys():
                self.makerID = kk
                break
        elif self.victoryID != 0 and len(self.chairPlayers.keys()) >= 2:
            for i in range(0, 5):
                tmp = (self.victoryID + i) % 5 + 1
                if tmp in self.chairPlayers:
                    self.makerID = tmp
                    break

        INFO_MSG("---------------->>_autoMakerID makerID = %r" % (self.makerID))
        if self.makerID == 0:
            ERROR_MSG("error self.makerID == 0")
        return self.makerID
    def _requireList(self, array, length):
        """获取数组的前3位数，并删掉"""
        tmp = []
        while len(array) > 3:
            for i in range(length):
                tmp.append(array.pop(0))
            if not IsA23(tmp):
                break
            else:
                tmp.clear()
        tmp = SortCards(tmp)
        INFO_MSG("Room._requireList CardsSize:%i,remainSize:%i" % (len(tmp), len(array)))

        return tmp
    def say(self, player, str):
        """
		说话的内容
		"""
        INFO_MSG("Room.Player[%i].say: %s" % (self.roomID, str))
        for mb in self.chairPlayers.values():
            if mb.client:
                mb.client.onSay(str)

    def hasNull(self):
        """
		是否还有空位
		@return:
		"""
        if (len(self.chairPlayers.values()) < 5):
            return True
        return False

    def reqPlayerCount(self):

        return len(self.chairPlayers.values())
