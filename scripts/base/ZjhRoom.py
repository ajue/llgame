# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
from Rules_ZJH import *

class ZjhRoom(KBEngine.Base):
    """
	这是一个游戏房间
	该房间中记录了房间里所有玩家的mailbox，通过mailbox我们可以将信息推送到他们的客户端。
	"""
    def __init__(self):
        KBEngine.Base.__init__(self)

        self.players = {}

        self.cellData["dizhuC"]         = self.dizhu
        self.cellData["taxRateC"]       = self.taxRate
        self.cellData["jzListC"]        = self.jzList
        self.cellData["stateC"]         = ROOM_STATE_READY

        self.createInNewSpace(None)

    def set_state(self,state):

        pass

    def onLoseCell(self):
        """
        KBEngine method.
        entity的cell部分实体丢失
        """
        self.destroy()

    def onGetCell(self):
        """
        KBEngine method.
        entity的cell部分实体被创建成功
        """
        DEBUG_MSG("ZjhRoom::onGetCell: %r" % self.roomID)

        self.parent.onRoomGetCell(self,self.roomID)

    def onEnterRoom(self, player):

        #去重
        if player.id in self.players:
            return

        if self.state == 1:
            #断线重连，重新进入游戏
            player.cell.set_AoiRadius(80.0)

            player.roomID = self.roomID
            self.players[player.id] = player

        else:
            for i in range(1, 6):
                has = False
                for pp in self.players.values():
                    if i == pp.cid:
                        has = True
                        break
                if has == False:
                    player.cid = i
                    break

            player.createCell(self.cell, player.cid)

            player.roomID = self.roomID
            self.players[player.id] = player


    def onLeaveRoom(self, player):
        # 防止多次离开

        DEBUG_MSG("ZjhRoom::onLeaveRoom Player[%r] PlayerCount[%r]" % (player.id,len(self.players)))

        if player.id not in self.players:
            return

        if self.state == ROOM_STATE_INGAME:
            #游戏进行中断线，离开游戏
            player.cell.set_AoiRadius(0.0)

        elif player.cell:
            player.destroyCellEntity()

        if player.id in self.players:

            del self.players[player.id]

            if player.client:
                player.client.onLeaveRoom(self.state, player.cid)

            player.roomID = 0

    def reqPlayerCount(self):

        return len(self.players)

    def hasNull(self):

        if len(self.players) < 5:
            return True

        return False
