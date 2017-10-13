# -*- coding: utf-8 -*-

"""
"""

GAME_TYPE_DDZ                      = 1 #斗地主
GAME_TYPE_ZJH                      = 2 #诈金花

ROOM_STATE_READY    =   0   #房间准备状态
ROOM_STATE_INGAME   =   1   #正在游戏
ROOM_STATE_FINISH   =   2   #游戏结束


def getServerStatus(playerCount):
    #获取服务器状态描述
    if playerCount < 20:
        return 1
    elif playerCount < 50:
        return 2
    elif playerCount > 100:
        return 3

