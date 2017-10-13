import KBEngine
import json
from Rules_DDZ import *
from interfaces.EntityCommon import EntityCommon

class Player(KBEngine.Entity,EntityCommon):

    def __init__(self):

        DEBUG_MSG("Player.Cell __init__")

        KBEngine.Entity.__init__(self)
        EntityCommon.__init__(self)

        self.position = (self.cid, 0.0, 0.0)

        self.getCurrRoom().onEnter(self)

    def onDestroy(self):
        """
        KBEngine method
        """
        DEBUG_MSG("Player::onDestroy: %i" % self.id)

        room = self.getCurrRoom()
        if room:
            room.onLeave(self)

    def set_gold(self,gold):

        self.base.set_gold(gold)

    def set_AoiRadius(self,radius):

        self.setAoiRadius(radius,5.0)

        DEBUG_MSG("Player::set_AoiRadius aoi[%r] " % (self.getAoiRadius()))

    def reqMessageC(self,exposed,action,buf):
        if exposed != self.id:
            return

        DEBUG_MSG("Player::reqMessageC player[%r] buf = %r" % (self.cid,buf))

        if action == ACTION_ROOM_TUOGUAN:
            data_json = json.loads(buf)
            self.tuoguan = data_json["tuoguan"]
            self.allClients.onMessage(0,action,buf)
        else:
            self.getCurrRoom().reqMessage(self,action,buf)