# -*- coding: utf-8 -*-

from KBEDebug import *
import random


ACTION_ROOM_READY = 10                   #房间准备状态
ACTION_ROOM_PLAYERS = 11                 #下发玩家信息
ACTION_ROOM_DISPATCH = 20                #发牌
ACTION_ROOM_JIAOPAI_NEXT = 29            #轮到下一位叫牌
ACTION_ROOM_JIAOPAI     = 30             #叫牌
ACTION_ROOM_STARTGAME   = 31             #确定地主，开始游戏
ACTION_ROOM_CHUPAI     = 32              #chu牌
ACTION_ROOM_NEXT      = 40               #轮到下一位
ACTION_ROOM_COMPUTE_DELAY   = 49         #胜利结算
ACTION_ROOM_COMPUTE   = 50               #胜利结算
ACTION_ROOM_KEEPON    = 60               #继续游戏
ACTION_ROOM_UPDATE    = 70               #更新房间信息
ACTION_ROOM_JIABEI    = 71               #玩家加倍
ACTION_ROOM_TUOGUAN   = 80               #托管消息
ACTION_ROOM_RELOGIN   = 81               #重连

#action 字符串形式，拥有debug
DEBUG_ACTION_STRING = {ACTION_ROOM_READY:"ACTION_ROOM_READY",
                       ACTION_ROOM_PLAYERS:"ACTION_ROOM_PLAYERS",
                       ACTION_ROOM_DISPATCH:"ACTION_ROOM_DISPATCH",
                       ACTION_ROOM_JIAOPAI_NEXT: "ACTION_ROOM_JIAOPAI_NEXT",
                       ACTION_ROOM_JIAOPAI:"ACTION_ROOM_JIAOPAI",
                       ACTION_ROOM_STARTGAME:"ACTION_ROOM_STARTGAME",
                       ACTION_ROOM_CHUPAI:"ACTION_ROOM_CHUPAI",
                       ACTION_ROOM_NEXT:"ACTION_ROOM_NEXT",
                       ACTION_ROOM_COMPUTE_DELAY:"ACTION_ROOM_COMPUTE_DELAY",
                       ACTION_ROOM_COMPUTE:"ACTION_ROOM_COMPUTE",
                       ACTION_ROOM_KEEPON:"ACTION_ROOM_KEEPON",
                       ACTION_ROOM_UPDATE:"ACTION_ROOM_UPDATE",
                       ACTION_ROOM_TUOGUAN:"ACTION_ROOM_TUOGUAN",
                       ACTION_ROOM_JIABEI:"ACTION_ROOM_JIABEI",
                       ACTION_ROOM_RELOGIN:"ACTION_ROOM_RELOGIN"}

# 获取牌组并洗牌
def reqRandomCards54():
    cards = []
    for i in range(1,55):
        cards.append(i)
        i+=1

    DEBUG_MSG("DDZRule.reqRandomCards54.Size = %i endNum = %i" % (len(cards),cards[53]))

    for i in range(0,54):
        index = random.randint(0,53)
        # DEBUG_MSG("range i =%i,index = %i " %(i,index))
        tmp = cards[i]
        cards[i] = cards[index]
        cards[index] = tmp
    return cards

def copyList(cards):
    copy = []
    for card in cards:
        copy.append(card)
    return copy

def getCardsby(array, length):
    """获取数组的前n位数，并删掉"""
    list = []
    for i in range(length):
        list.append(array.pop(0))
    list = sortCards(list)
    INFO_MSG("Room.getCardsby CardsSize:%i,remainSize:%i" % (len(list), len(array)))
    return list

def sortCards(cards):

    for i in range(0,len(cards)):
        for j in range(i+1,len(cards)):
            if cards[i] <cards[j]:
                tmp = cards[i]
                cards[i] = cards[j]
                cards[j] = tmp
    return cards

def getMinCards(cards):
    result = []
    last = 0
    for i in range(len(cards)-1, -1,-1):
        if last == 0:
            result.append(cards[i])
            last = cards[i]
        elif int((last-1)/4) == int((cards[i]-1)/4):
            result.insert(0,cards[i])
            last = cards[i]
        else:
            return result
    return result

CARDS_TYPE_ERROR   = 0  #卡牌类型error
CARDS_TYPE_A       = 1  #单张
CARDS_TYPE_AA      = 2  #对子
CARDS_TYPE_AAA     = 3  #三张
CARDS_TYPE_3AND1    = 8  #3带1
CARDS_TYPE_3AND2    = 9  #3带2
CARDS_TYPE_4AND2    = 10 #4带2
CARDS_TYPE_4ANDAA   = 11 #4带1对
CARDS_TYPE_1LIST    = 20  #单顺
CARDS_TYPE_2LIST    = 21  #双顺
CARDS_TYPE_3LIST    = 22  #三顺
CARDS_TYPE_FEIJIAND1    = 23 #飞机带1
CARDS_TYPE_FEIJIANDAA   = 24 #飞机带对

CARDS_TYPE_AAAA    = 99   #炸弹
CARDS_TYPE_KING    = 100  #王炸

CARDS_TYPE_STRING = {
    CARDS_TYPE_ERROR:"CARDS_TYPE_ERROR",
    CARDS_TYPE_A:"CARDS_TYPE_A",
    CARDS_TYPE_AA:"CARDS_TYPE_AA",
    CARDS_TYPE_AAA:"CARDS_TYPE_AAA",
    CARDS_TYPE_1LIST: "CARDS_TYPE_1LIST",
    CARDS_TYPE_2LIST: "CARDS_TYPE_2LIST",
    CARDS_TYPE_3LIST: "CARDS_TYPE_3LIST",
    CARDS_TYPE_3AND1:"CARDS_TYPE_3AND1",
    CARDS_TYPE_3AND2:"CARDS_TYPE_3AND2",
    CARDS_TYPE_4AND2:"CARDS_TYPE_4AND2",
    CARDS_TYPE_4ANDAA:"CARDS_TYPE_4ANDAA",
    CARDS_TYPE_AAAA:"CARDS_TYPE_AAAA",
    CARDS_TYPE_KING:"CARDS_TYPE_KING",
    CARDS_TYPE_FEIJIAND1:"CARDS_TYPE_FEIJIAND1",
    CARDS_TYPE_FEIJIANDAA:"CARDS_TYPE_FEIJIANDAA"}


def _analysisCards(cards):
    """cards 0~53 分析卡牌的type，并统计数量"""
    table = {}
    for c in cards:
        l = int(c / 4)
        if l in table:
            table[l] += 1
        else:
            table[l] = 1
    return table
def _analysisSequence(cards, offset):
    #先检测是否是顺子，然后再判断lev的数量
    for i in range(0,len(cards)-offset,offset):
        if int(cards[i]/4) != int(cards[i+offset]/4)+1:
            return False

    if offset > 1:
        table = _analysisCards(cards)
        for tt in table.values():
            if tt != offset:
                return False
    return True

def _assortCards(cards):
    """将手牌按lev分类"""
    result = {}
    for cc in cards:
        lev = int((cc-1)/4)
        if lev in result.keys():
            result[lev].append(cc)
        else:
            result[lev] = [cc]
    return result

def _assortType(cards):
    """分类_assortCards的结果"""
    result = {}
    for k in cards.keys():
        if len(cards[k]) == 1:
            if CARDS_TYPE_A in result:
                result[CARDS_TYPE_A].append(k)
            else:
                result[CARDS_TYPE_A] = [k]

        elif len(cards[k]) == 2 and k < 13:
            if CARDS_TYPE_AA in result:
                result[CARDS_TYPE_AA].append(k)
            else:
                result[CARDS_TYPE_AA] = [k]
        elif len(cards[k]) == 3:
            key = CARDS_TYPE_AAA
            if key in result:
                result[key].append(k)
            else:
                result[key] = [k]
        elif len(cards[k]) == 4:
            key = CARDS_TYPE_AAAA
            if key in result:
                result[key].append(k)
            else:
                result[key] = [k]
        elif len(cards[k]) == 2 and k == 13:
            key = CARDS_TYPE_KING
            if key in result:
                result[key].append(k)
            else:
                result[key] = [k]
    return result

def returnMaxLev(cards):
    array = _assortCards(cards)

    maxLev = 0
    lastLen = 0
    #to do 顺子maxLev
    for k in array.keys():
        if len(array.keys()) == 1:
            maxLev = k
        elif lastLen == 0 or len(array[k]) > lastLen:
            lastLen = len(array[k])
            maxLev = k
    return maxLev
def checkCardType(targetCards):
    # 整体降1位
    # DEBUG_MSG("checkCardType targetCards %r" %(json.dumps(targetCards)))
    cards = []
    for i in range(len(targetCards)):
        cards.append(targetCards[i]-1)

    if len(cards) == 1:        #单牌
        return CARDS_TYPE_A

    if len(cards) == 2:        #对子，皇炸
        if cards[0] >= 52 and cards[1] >= 52:
            return CARDS_TYPE_KING

        table = _analysisCards(cards)
        if len(table.values()) == 1:
            return CARDS_TYPE_AA

    if len(cards) == 3:      #三张
        table = _analysisCards(cards)
        if len(table.values()) == 1:
            return CARDS_TYPE_AAA

    if len(cards) == 4:      #3带1，炸弹
        table = _analysisCards(cards)
        if len(table.values()) == 1:
            return CARDS_TYPE_AAAA
        size = len(table.values())
        value = table.popitem()
        if size == 2 and (value[1] == 3 or value[1] == 1):
            return CARDS_TYPE_3AND1

    if len(cards) == 5:      #三带2
        table = _analysisCards(cards)
        size = len(table.values())
        value = table.popitem()
        if  size == 2 and (value[1] == 2 or value[1] == 3):
            return CARDS_TYPE_3AND2

    if len(cards) == 6:      #4带2，4带1对
        table = _analysisCards(cards)
        for tt in table.values():
            if tt == 4 and len(table.values()) == 3:
                return CARDS_TYPE_4AND2
            elif tt ==4 and len(table.values()) == 2:
                return CARDS_TYPE_4ANDAA

    if len(cards) >= 5:
        if _analysisSequence(cards, 1):
            return CARDS_TYPE_1LIST

    if len(cards) >= 4:
        if _analysisSequence(cards, 2):
            return CARDS_TYPE_2LIST

    if len(cards) >= 6:
        if _analysisSequence(cards, 3):
            return CARDS_TYPE_3LIST

    #飞机带翅膀
    if len(cards) >= 8 and (int(len(cards)%4) == 0 or int(len(cards)%5) == 0):
        table = _analysisCards(cards)
        array = []
        mark = 0
        for tt in table.values():
            if tt == 3:
                array.append(tt)
            elif tt != mark and mark == 0:
                mark = tt
        array.sort(reverse = True)
        isFeiji = True
        for i in range(len(array)-1):
            if array[i] != array[i+1]:
                isFeiji = False

        if isFeiji and mark == 1:
            return CARDS_TYPE_FEIJIAND1
        elif isFeiji and mark == 2:
            return CARDS_TYPE_FEIJIANDAA

    return CARDS_TYPE_ERROR

# print("type = %r" %(json.dumps(_assortType(_assortCards([14,13,11,10,9,6,5,3,2,1])))))

def getAICards(cards, lastCards):
    """根据上轮牌，选择当前出牌"""

    type = checkCardType(lastCards)
    maxLev = returnMaxLev(lastCards)

    if type < CARDS_TYPE_1LIST:
        result = returnCards(cards,type,maxLev)
        if len(result) > 0:
            return  result

    # 炸出炸
    if type != CARDS_TYPE_KING:
        result = returnCards(cards, CARDS_TYPE_AAAA, maxLev)
        if len(result) > 0:
            return result

        result = returnCards(cards, CARDS_TYPE_KING, 0)
        if len(result) > 0:
            return result
    return []

def returnCards(cards,type,maxLev):
    array = _assortCards(cards)
    table = _assortType(array)

    result = []
    #单牌，对子，三张，炸弹，王炸
    if len(table) > 0 and type in table:
        child = table[type]
        for k in child:
            if k > maxLev:
                result.extend(array[k])
                return result
            # 判断上家小王，下家大王
            elif type == CARDS_TYPE_A and array[k][0] == 54:
                return array[k]

    #三带1
    if len(table) >0 and type == CARDS_TYPE_3AND1:
        if CARDS_TYPE_AAA in table and CARDS_TYPE_A in table:
            child = table[CARDS_TYPE_AAA]
            for k in child:
                if k > maxLev:
                    result.extend(array[k])
                    break
            if len(result) > 0:
                child = table[CARDS_TYPE_A]
                k = child[len(child) - 1]
                result.extend(array[k])

    #三带2
    if len(table) > 0 and type == CARDS_TYPE_3AND2:
        if CARDS_TYPE_AAA in table and CARDS_TYPE_AA in table:
            child = table[CARDS_TYPE_AAA]
            for k in child:
                if k > maxLev:
                    result.extend(array[k])
                    break
            if len(result)>0:
                child = table[CARDS_TYPE_AA]
                k = child[len(child) - 1]
                result.extend(array[k])
    result.sort(reverse=True)
    return result

def getNextCid(cid):

    nextCid = cid % 3 + 1

    return nextCid

def getLastCid(cid):

    lastCid = cid - 1
    if lastCid == 0:
        lastCid = 3

    return lastCid


print(getLastCid(1))


