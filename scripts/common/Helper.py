
import socket
import re

def Round(num):
    #去掉小数点后两位
    return float('%.2f' % num)

def cutHttp(str,start,end):
    index1 = str.find(start)
    index2 = str.rfind(end) + 1

    result = str[index1: index2]

    return result

def cutInHttp(str,start,end):
    slen = len(start)
    index1 = str.find(start)
    index2 = str.rfind(end)

    result = str[index1+slen: index2]
    print(result)

    return result

def convertDict(httpStr,str1,str2):
    if httpStr == '':
        return {}

    datas = re.split(str1,httpStr)
    # print(datas)

    result = {}
    for data in datas:
        list = re.split(str2,data)
        result[list[0]] = list[1]
    print(result)

    return result

def start(_host,_page, _param_data, _get_post):
    """
    @param _commitName, _realAccountName, _datas: 这三个参数来自于requestAccountLogin,记在这个LoginPoller中,
    数据请求完毕之后可以从外部重新拿到这些数据
    @param _param_data: http请求参数
    @param _tid: 可视为这个LoginPoller的Id, 回调时会返回这个id, 便于外部管理
    """
    _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _socket.connect((_host, 80))

    if _get_post == "GET":
        _rstr = "GET " + _page + "?" + _param_data + " HTTP/1.1\r\n"
        _rstr += "Host: " + _host + "\r\n"
        _rstr += "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:43.0) Gecko/20100101 Firefox/43.0\r\n"
        _rstr += "Connection: close\r\n"
        _rstr += "\r\n"

    elif _get_post == "POST":

        _rstr = "POST " + _page + " HTTP/1.1\r\n"
        _rstr += "Host: " + _host + "\r\n"
        _rstr += "Content-Type: application/x-www-form-urlencoded\r\n"
        _rstr += "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:43.0) Gecko/20100101 Firefox/43.0\r\n"
        _rstr += "Content-Length: " + str(len(_param_data)) + "\r\n"
        _rstr += "Connection: close\r\n"
        _rstr += "\r\n" + _param_data + "\r\n"
        _rstr += "\r\n"

    _request_str = _rstr.encode()
    _socket.send(_request_str)

    buf = _socket.recv(1024)
    while len(buf):
        print(buf)
        buf = _socket.recv(1024)




