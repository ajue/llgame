import KBEngine
import json
from Rules_DDZ import *
from KBEDebug import *
from GlobalConst import *
import Helper

class DdzRoom(KBEngine.Entity):

    def __init__(self):
        KBEngine.Entity.__init__(self)

        self.position = (9999.0, 0.0, 0.0)
        self.timerMgr = {}

        self.players    = {}
        self.cards      = []
        self.curfen     = Helper.Round(self.difenC)
        self.multiple   = 1

        #房间时间
        self.roomtime   = 15
        self.curRoomtime = 0

        #当前玩家ID
        self.curCid     = 0
        self.beginCid   = 0
        self.dzCid      = 0
        self.curScore   = 0

        #叫牌不成次数
        self.giveupCount = 2

        #霸权ID
        self.powerCid   = 0
        self.powerCards = []

        KBEngine.globalData["Room_%i" % self.spaceID] = self.base

        KBEngine.setSpaceData(self.spaceID, "curfen", "%.2f" % self.curfen)
        KBEngine.setSpaceData(self.spaceID, "multiple", str(self.multiple))
        KBEngine.setSpaceData(self.spaceID, "roomtime", str(self.roomtime))
        KBEngine.setSpaceData(self.spaceID, "state", str(self.stateC))

    def set_state(self,state):

        DEBUG_MSG("DdzRoom::set_state space[%r] state[%r]" % (self.spaceID,state))

        self.stateC = state
        KBEngine.setSpaceData(self.spaceID, "state", str(self.stateC))

    def _sendAllClients(self, action, json):
        for pp in self.players.values():
            if pp.client:
                pp.client.onMessage(0,action,json)

    def _addUserArgTimer(self,initialOffset,repeatOffset,userArg):
            tid = self.addTimer(initialOffset,repeatOffset,userArg)
            bMgr = False
            if userArg in self.timerMgr:
                self._removeUserArgTimer(userArg)
            if repeatOffset > 0:
                self.timerMgr[userArg] = tid
                bMgr = True

    def _removeUserArgTimer(self,userArg):
        if userArg == 0:

            INFO_MSG("DdzRoom::_removeUserArgTimer(0)")

            for tt in self.timerMgr.values():
                self.delTimer(tt)
            self.timerMgr.clear()

        elif userArg in self.timerMgr:
            tid = self.timerMgr.pop(userArg)
            self.delTimer(tid)

    def onEnter(self, player):

        DEBUG_MSG('DdzRoom::onEnter space[%d] cid = %i.' % (self.spaceID, player.cid))

        self.players[player.cid] = player

        #满足开局人数
        if len(self.players.values()) == 3:
            self._addUserArgTimer(1,0,ACTION_ROOM_DISPATCH)

    def onLeave(self, player):

        DEBUG_MSG('DdzRoom::onLeave space[%d] cid = %i.' % (self.spaceID, player.cid))

        if player.cid in self.players:
            del self.players[player.cid]

    def onDestroy(self):
        """
        KBEngine method
        """

        del KBEngine.globalData["Room_%i" % self.spaceID]

    def _dispatchCards(self):
        """发牌"""
        INFO_MSG("DdzRoom::_dispatchCards space[%d]" % (self.spaceID))

        self.cards = reqRandomCards54()

        for pp in self.players.values():

            pp.cards        = getCardsby(self.cards, 17)
            pp.cardCount    = len(pp.cards)

    def _nextPlayer(self,userArg):

        if self.curCid == 0:
            # 随机一位玩家先手
            self.curCid     = random.randint(1, len(self.players))
        else:
            self.curCid     = self.curCid % 3 + 1

        #重置房间时间
        self.curRoomtime = self.roomtime
        self._removeUserArgTimer(0)
        self._addUserArgTimer(1, 1, userArg)

        if userArg == ACTION_ROOM_JIAOPAI_NEXT:

            data = {}
            data["curCid"]      = self.curCid
            data["curScore"]    = self.curScore
            data["type"]        = self.players[self.curCid].type

            data_json = json.dumps(data)
            KBEngine.setSpaceData(self.spaceID, "ACTION_ROOM_JIAOPAI_NEXT", data_json)

        elif userArg == ACTION_ROOM_NEXT:

            data = {}
            data["curCid"]      = self.curCid
            data["powerCid"]    = self.powerCid
            data["powerCards"]  = self.powerCards

            data_json = json.dumps(data)
            KBEngine.setSpaceData(self.spaceID, "ACTION_ROOM_NEXT", data_json)

    def reqMessage(self,player,action,buf):

        DEBUG_MSG("DdzRoom::reqMessage %r space[%d] player[%r] buf[%r]"
                  % (DEBUG_ACTION_STRING.get(action),self.spaceID,player.cid,buf))

        #不是当前玩家，则默认为超时操作，不予处理
        if self.curCid != player.cid:
            return

        if action == ACTION_ROOM_JIAOPAI:

            self.onMessage_ACTION_ROOM_JIAOPAI(player,action,json.loads(buf))

        elif action == ACTION_ROOM_CHUPAI:

            self.onMessage_ACTION_ROOM_CHUPAI(player,action,json.loads(buf))

    def onMessage_ACTION_ROOM_JIAOPAI(self,player,action,data_json):

        score = data_json["curScore"]
        player.curScore = score

        if score <= 3:

            if self.curScore < score:

                self.dzCid      = player.cid
                self.curScore   = score
                self.curfen     = self.difenC * score

                KBEngine.setSpaceData(self.spaceID, "curfen", "%.2f" % self.curfen)

            #分值最大的玩家成为地主
            if score == 3 or (getLastCid(self.beginCid) == player.cid and (self.curScore != 0 or self.giveupCount == 0)):

                #如果叫牌流程为0，且未确定dzCid，则beginCid为地主
                if self.giveupCount == 0 and self.dzCid == 0:
                    self.dzCid = self.beginCid

                DEBUG_MSG("DdzRoom::onMessage_ACTION_ROOM_JIAOPAI dzCid[%d] beginCid[%d]" % (self.dzCid,self.beginCid))

                self.curCid     = self.dzCid
                self.powerCid   = self.dzCid

                for pp in self.players.values():

                    if pp.cid != self.dzCid:
                        pp.type = 2
                    else:
                        threeCards  = getCardsby(self.cards,3)
                        pp.type     = 1

                        pp.cards.extend(threeCards)
                        pp.cards     = sortCards(pp.cards)
                        pp.cardCount = len(pp.cards)

                        data = {}
                        data["cards"] = threeCards
                        KBEngine.setSpaceData(self.spaceID, "threeCards", json.dumps(threeCards))

            elif getLastCid(self.beginCid) == player.cid and self.curScore == 0:
                #如果没人叫分，则重新发牌
                self.beginCid = 0
                self.giveupCount -= 1
                self._addUserArgTimer(1, 0, ACTION_ROOM_DISPATCH)
                return

            elif self.beginCid == 0:
                #记录开始叫牌的玩家cid,用于判定是否结束叫分流程
                self.beginCid = player.cid

        elif score > 10 and score <= 12:

            player.multiple = (score - 10)

            if getLastCid(self.dzCid) == player.cid:

                self._nextPlayer(ACTION_ROOM_NEXT)
                return

        self._nextPlayer(ACTION_ROOM_JIAOPAI_NEXT)

    def onMessage_ACTION_ROOM_CHUPAI(self,player,action,data_json):

        cards   = data_json["cards"]
        player.showCards = cards

        if len(cards) > 0:

            self.powerCid   = player.cid
            self.powerCards = cards

            if checkCardType(cards) == CARDS_TYPE_AAAA or checkCardType(cards) == CARDS_TYPE_KING:

                self.multiple *= 2
                KBEngine.setSpaceData(self.spaceID, "multiple", str(self.multiple))

            #to do error
            handCards = player.cards

            for card in cards:
                handCards.remove(card)

            player.cards        = handCards
            player.cardCount    = len(player.cards)

            if player.cardCount == 0:
                self._addUserArgTimer(1.5,0,ACTION_ROOM_COMPUTE)
            else:
                self._nextPlayer(ACTION_ROOM_NEXT)
        else:
            self._nextPlayer(ACTION_ROOM_NEXT)

    def onTimer(self, id, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param id		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """

        if userArg == ACTION_ROOM_DISPATCH:
            self._sendAllClients(ACTION_ROOM_DISPATCH, "")
            self._dispatchCards()
            self._addUserArgTimer(1, 0, ACTION_ROOM_STARTGAME)

        if userArg == ACTION_ROOM_STARTGAME:

            self._nextPlayer(ACTION_ROOM_JIAOPAI_NEXT)

        elif userArg == ACTION_ROOM_JIAOPAI_NEXT or userArg == ACTION_ROOM_NEXT:

            self.curRoomtime -= 1
            player = self.players[self.curCid]

            if self.curRoomtime <= 0:

                self._removeUserArgTimer(0)
                self.onOuttime(userArg,player)

            elif player.tuoguan == 1:

                self._removeUserArgTimer(0)
                self.onAi(userArg, player)

        elif userArg == ACTION_ROOM_COMPUTE:
            self.onCompute()

    def onOuttime(self,userArg,player):
        """超时处理"""

        if userArg == ACTION_ROOM_JIAOPAI_NEXT:

            if player.tuoguan == 0:
                player.tuoguan = 1

            data = {}
            data["curCid"] = self.curCid

            if self.curScore < 3 and player.type == 0:
                data["curScore"] = 0
            else:
                data["curScore"] = 11

            data_json = json.dumps(data)
            self.reqMessage(player, ACTION_ROOM_JIAOPAI, data_json)

        elif userArg == ACTION_ROOM_NEXT:

            if player.tuoguan == 0:
                player.tuoguan = 1

                if player.cid == self.powerCid:
                    self.onAi(ACTION_ROOM_NEXT,player)
                else:
                    data = {}
                    data["curCid"] = self.curCid
                    data["cards"] = []

                    data_json = json.dumps(data)
                    self.reqMessage(player, ACTION_ROOM_CHUPAI, data_json)

    def onAi(self,userArg,player):
        """托管"""

        if userArg == ACTION_ROOM_JIAOPAI_NEXT:

            self.onOuttime(userArg,player)

        elif userArg == ACTION_ROOM_NEXT:

            data = {}
            data["curCid"] = self.curCid

            if self.curCid == self.powerCid:

                data["cards"] = getMinCards(player.cards)
            else:
                data["cards"] = getAICards(player.cards, self.powerCards)

            data_json = json.dumps(data)
            self.reqMessage(player, ACTION_ROOM_CHUPAI, data_json)

    def onCompute(self):

        winPlayer   = self.players[self.curCid]
        dzPlayer    = self.players[self.dzCid]

        baseGold    = round(self.curfen * self.multiple,2)
        allMult     = 0

        for pp in self.players.values():
            if pp.type == 2:
                allMult += pp.multiple

        datas = {}
        datas["multiple"]   = self.multiple
        datas["curfen"]     = self.curfen

        #地主赢
        if winPlayer.type == 1:

            canWinGold = baseGold * allMult
            realWinGold = 0.0

            if dzPlayer.goldC < canWinGold:
                canWinGold = dzPlayer.goldC

            newBaseGold = Helper.Round(canWinGold/allMult)

            for pp in self.players.values():

                settleGold = newBaseGold * pp.multiple

                if pp.type == 2 and pp.goldC < settleGold:
                    settleGold  = Helper.Round(pp.goldC)
                    realWinGold += settleGold
                    pp.goldC    = 0.0

                elif pp.type == 2:
                    realWinGold += settleGold
                    pp.goldC    -= settleGold

                pp.goldC    = Helper.Round(pp.goldC)

                data = {}
                data["settleGold"]    = -settleGold
                data["gold"]           = pp.goldC
                data["cards"]          = copyList(pp.cards)

                datas[pp.cid]           = data
                pp.set_gold(-settleGold)

            taxGold = round(realWinGold * self.taxRateC,2)
            KBEngine.globalData["Games"].addIncome(taxGold)

            realWinGold     -= taxGold
            dzPlayer.goldC  += realWinGold

            dzPlayer.goldC = Helper.Round(dzPlayer.goldC)

            data = {}
            data["settleGold"]   = realWinGold
            data["gold"]         = dzPlayer.goldC
            data["cards"]        = copyList(dzPlayer.cards)

            datas[dzPlayer.cid]   = data
            dzPlayer.set_gold(realWinGold)

        else:
            newBaseGold = Helper.Round(dzPlayer.goldC/allMult)
            realLoseGold = 0.0

            for pp in self.players.values():
                if pp.type == 2:

                    canWinGold = Helper.Round(baseGold * pp.multiple)

                    if pp.goldC < canWinGold:
                        canWinGold = Helper.Round(pp.goldC)

                    if canWinGold > (newBaseGold*pp.multiple):
                        canWinGold = (newBaseGold*pp.multiple)

                    realLoseGold += canWinGold
                    taxGold      =  round(canWinGold * self.taxRateC,2)
                    canWinGold   -= taxGold
                    pp.goldC     += canWinGold
                    KBEngine.globalData["Games"].addIncome(taxGold)

                    pp.goldC = Helper.Round(pp.goldC)

                    data = {}
                    data["settleGold"]  = canWinGold
                    data["gold"]        = pp.goldC
                    data["cards"]       = copyList(pp.cards)

                    datas[pp.cid] = data
                    pp.set_gold(canWinGold)

            dzPlayer.goldC -= realLoseGold

            #抹掉计算误差
            if self.players[self.dzCid].goldC <= 0.01:
                self.players[self.dzCid].goldC = 0.0

            dzPlayer.goldC = Helper.Round(dzPlayer.goldC)

            data = {}
            data["settleGold"]       = -realLoseGold
            data["gold"]             = dzPlayer.goldC
            data["cards"]            = copyList(dzPlayer.cards)

            datas[self.dzCid]        = data
            dzPlayer.set_gold(-realLoseGold)

        # 退出游戏状态
        self.base.set_state(ROOM_STATE_READY)

        data_json   = json.dumps(datas)
        self._sendAllClients(ACTION_ROOM_COMPUTE,data_json)

        INFO_MSG("DdzRoom::onCompute space[%d] data_json = [%r]" % (self.spaceID,data_json))

