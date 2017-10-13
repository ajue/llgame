import json
import codecs
import os
import d_games
from KBEDebug import *

#诈金花数据配置
d_ZJH = {
    "taxRate": 0.05,                        #税点
    1:
        {
            "base": 1.0,                                      #底
            "limit": 50.0,                                    #入场底线
            "jzList": [3.0,5.0,8.0,10.0],              #加注数等于配置值
        },

    2:
        {
            "base": 2.0,                                        #底
            "limit": 120.0,                                     #入场底线
            "jzList": [6.0,10.0,16.0,20.0],             #加注数等于配置值
        },
    3:
        {
            "base": 5.0,                                       # 底
            "limit": 300.0,                                    #入场底线
            "jzList": [15.0,25.0,40.0,50.0],                 # 加注数等于配置值
        },
    4:
        {
            "base": 10.0,                                       # 底
            "limit": 600.0,                                     #入场底线
            "jzList": [30.0, 50.0, 80.0, 100.0],          # 加注数等于配置值
        }
}
#斗地主数据配置
d_DDZ = {
    "taxRate": 0.05,                        #税点
    1:
        {
            "base":0.1,
            "limit":2.00,
        },
    2:
        {
            "base": 1.0,
            "limit": 18.00,
        },
    3:
        {
            "base": 3.0,
            "limit": 72.00,
        },
    4:
        {
            "base": 6.0,
            "limit": 150.00,
        },
}
#游戏公告
d_notice ={
    "moving":"系统正在升级，近期将公告开服时间！",
    "static":"系统正在升级，近期将公告开服时间! QQ客服：1151351916"
}
d_ranks = {
    "rank": {
        1:"1~3",
        2:"4~10",
        3:"11~20"
    },
    "rankValue":{
        1:"奖励50.00元",
        2:"奖励20.00元",
        3:"奖励10.00元"
    },
    "notice":"排行榜凌晨0点刷新榜单。"

}

d_users = {
    "base_money":10.0,              #底钱
    "duixian_base":150.0,           #兑现在duixian_base以内，收取 duixian_base_fee 手续费
    "duixian_base_fee":3.0,
    "duixian_add":50.0,             #兑现大于duixian_base，每增加duixian_add，收取duixian_add_fee手续费
    "duixian_add_fee":1.0,
    "use_ui_duixian":True,         #是否打开充值界面
    "use_pay_weixin":True,          #是否打开微信支付
    "use_pay_alipay":False           #是否打开支付宝支付
}
