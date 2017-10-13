import KBEngine
import json
from KBEDebug import *
from Rules_ZJH import *
import Helper


class ZjhRoom(KBEngine.Entity):

    def __init__(self):
        KBEngine.Entity.__init__(self)

        self.position = (9999.0, 0.0, 0.0)
        self.timerMgr = {}

        self.players = {}

        # 房间时间
        self.roomtime   = 10
        self.curRoomtime = 0

        #先手ID
        self.firstCid   = 0
        self.victoryID  = 0

        #重置房间数据
        self.reset()

        KBEngine.globalData["Room_%i" % self.spaceID] = self.base

        KBEngine.setSpaceData(self.spaceID, "dizhu",    str(self.dizhuC))
        KBEngine.setSpaceData(self.spaceID, "totalzhu", str(self.totalzhu))
        KBEngine.setSpaceData(self.spaceID, "roomtime", str(self.roomtime))
        KBEngine.setSpaceData(self.spaceID, "curRound", str(self.curRound))
        KBEngine.setSpaceData(self.spaceID, "state", str(self.stateC))

        KBEngine.setSpaceData(self.spaceID, "jzList", self.jzListC)

    def reset(self):
        #当前玩家
        self.curCid = 0

        #当前回合
        self.curRound = 0

        #当前低注
        self.curDizhu = self.dizhuC

        #总下注
        self.totalzhu = 0

        #下注记录，用于给观战玩家生成筹码界面
        self.chipsList = []


    def set_state(self,state):

        DEBUG_MSG("ZjhRoom::set_state space[%r] state[%r]" % (self.spaceID,state))

        self.stateC = state

        if state == ROOM_STATE_INGAME:
            for pp in self.players:
                pp.state = PLAYER_STATE_START

        KBEngine.setSpaceData(self.spaceID, "state", str(self.stateC))

    def onEnter(self, player):

        DEBUG_MSG('ZjhRoom::onEnter space[%d] cid = %i.' % (self.spaceID, player.cid))

        self.players[player.cid] = player

        if self.stateC != ROOM_STATE_INGAME:
            player.stateC = PLAYER_STATE_READY

        if self.stateC != ROOM_STATE_INGAME and len(self.players) >= 2:
            self._addUserArgTimer(1,0,ACTION_ROOM_TIME)

    def onLeave(self, player):

        DEBUG_MSG('ZjhRoom::onLeave space[%d] cid = %i.' % (self.spaceID, player.cid))

        if player.cid in self.players:
            del self.players[player.cid]

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

    def onDispatchCards(self):
        """
        发牌
        """
        cards = reqRandomCards52()
        for pp in self.players.values():
            pp.cards        = getCardsby(cards, 3)
            pp.cardCount    = len(pp.cards)

            pp.goldC     -= self.curDizhu
            pp.cost      += self.curDizhu
            pp.chip       = self.curDizhu

            self.totalzhu += self.curDizhu
            self.chipsList.append(self.curDizhu)

            KBEngine.setSpaceData(self.spaceID, "totalzhu", str(self.totalzhu))

            INFO_MSG("ZjhRoom::onDispatchCards Player[%r]" % (pp.cid))

    def _nextPlayer(self):

        if self.curCid == 0:

            self.curCid = random.randint(1, len(self.players))
            self.firstCid = self.curCid
            self.players[self.curCid].first = 1

            KBEngine.setSpaceData(self.spaceID, "firstCid", str(self.firstCid))
        else:
            for i in range(0, 5):
                tCid = (self.curCid + i) % 5 + 1
                if tCid in self.players:
                    if self.players[tCid].stateC == ROOM_STATE_INGAME:
                        self.curCid = tCid
                        break

        #计算回合数
        if self.firstCid == self.curCid:
            self.curRound += 1
            KBEngine.setSpaceData(self.spaceID, "curRound", str(self.curRound))

        # 重置房间时间
        self.curRoomtime = self.roomtime
        self._removeUserArgTimer(0)
        self._addUserArgTimer(1, 1, ACTION_ROOM_NEXT)

        data = {}
        data["curCid"] = self.curCid
        data["curDizhu"] = self.curDizhu
        data["curRoomtime"] = self.curRoomtime

        data_json = json.dumps(data)
        KBEngine.setSpaceData(self.spaceID, "ACTION_ROOM_NEXT", data_json)



    def reqMessage(self, player, action, buf):

        DEBUG_MSG("ZjhRoom::reqMessage %r space[%d] player[%r] buf[%r]"
                  % (DEBUG_ACTION_STRING.get(action), self.spaceID, player.cid, buf))

        if action == ACTION_ROOM_GENZHU:
            self._removeUserArgTimer(0)
            self.onGenzhu(player,action,buf)

        elif action == ACTION_ROOM_KANPAI:
            player.lookcard = 1

        elif action == ACTION_ROOM_JIAZHU:
            pass
        elif action == ACTION_ROOM_BIPAI_START:
            pass
        elif action == ACTION_ROOM_QIPAI:
            self._removeUserArgTimer(0)
            self.onQipai(player,action,buf)


    def onGenzhu(self,player,action,buf):
        #跟注
        curChip = self.curDizhu
        if player.lookcard == 1:
            curChip = self.curDizhu * 2

        player.goldC -= curChip
        player.cost  += curChip
        player.chip  = curChip

        self.totalzhu += curChip
        KBEngine.setSpaceData(self.spaceID, "totalzhu", str(self.totalzhu))

        self._nextPlayer()

    def onQipai(self,player,action,buf):

        player.stateC = PLAYER_STATE_QIPAI

        if self.onCheckResult():
            self.onSettle()
        else:
            self._nextPlayer()

    def onCheckResult(self):
        """检测当局是否玩家胜利,并存储胜利玩家的ID"""
        count = 0
        tmpid = 0
        for pp in self.chairPlayers.values():
            if pp.state > PLAYER_STATE_LINE:
                tmpid = pp.chairID
                count += 1

        if count <= 1:
            # 存储胜利ID
            self.victoryID = tmpid
            self.state = 2
            return True

        return False

    def onSettle(self):
        #结算
        taxGold = Helper.Round((self.totalzhu - self.players[self.victoryID].cost) * self.taxRateC)

        KBEngine.globalData["Games"].addIncome(taxGold)

        self.totalzhu -= taxGold
        self.chairPlayers[self.victoryID].gold += self.totalzhu
        self.chairPlayers[self.victoryID].chip  = -self.totalzhu

        

    def onTimer(self, id, userArg):
        """
        KBEngine method.
        使用addTimer后， 当时间到达则该接口被调用
        @param id		: addTimer 的返回值ID
        @param userArg	: addTimer 最后一个参数所给入的数据
        """

        if userArg == ACTION_ROOM_TIME:

            self.curRoomtime = self.roomtime
            self.set_state(ROOM_STATE_READY)

            self._addUserArgTimer(1,1,ACTION_ROOM_READY)
            KBEngine.setSpaceData(self.spaceID, "ACTION_ROOM_READY",str(self.curRoomtime))

        elif userArg == ACTION_ROOM_READY:
            self.curRoomtime -= 1

            if self.curRoomtime <= 0:
                self._removeUserArgTimer(0)

                self.set_state(ROOM_STATE_INGAME)

                self.onDispatchCards()

                self._nextPlayer()

        elif userArg == ACTION_ROOM_NEXT:

            self.curRoomtime -= 1

            if self.curRoomtime <= 0:
                self.onOuttime(userArg,self.players[self.curCid])

    def onOuttime(self, userArg, player):
        """超时处理"""

        if userArg == ACTION_ROOM_NEXT:
            #弃牌
            self._nextPlayer()







