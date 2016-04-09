import requests
import xml.etree.ElementTree as ET
import time
import json
import re
import ast
import sys

headers = {
    'Accept-Encoding': 'deflate, gzip',
    #'Cookie': 'mursid=%s' % mursid,
    'Accept': 'text/xml, application/xml, application/xhtml+xml, text/html;q=0.9, text/plain;q=0.8, text/css, image/png, image/jpeg, image/gif;q=0.8, application/x-shockwave-flash, video/mp4;q=0.9, flv-application/octet-stream;q=0.8, video/x-flv;q=0.7, audio/mp4, application/futuresplash, */*;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Android; U; ru-RU) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/15.0',
    'x-flash-version': '15,0,0,223',
    'Connection': 'Keep-Alive',
    'Referer': 'app:/Murc2048_release_iOS.swf',
    'Content-Type': 'application/x-www-form-urlencoded'
}

COOKIES = None
mursid = None
csrf = None
id_p2p = None


def tryeval(val):
    try:
        val = ast.literal_eval(val)
    except ValueError:
        pass
    return val

def parce_grid(data):
    if 'access denied' in data:
        print "[ERROR] - Can't parse grid"
        exit(255)
    data = re.findall(r'<player id=\"(.+?)\">{\"score\":(.+?),\"grid\":(.+?),\"mcnt\":(.+?),\"state\":\"(.+?)\",\"mmax\":(.+?),\"alone\":(.+?)}</player>', data)
    res = {}
    res['id'] = data[0][0]
    res['score'] = data[0][1]
    res['grid'] = data[0][2].replace("-1","0")
    res['mcnt'] = data[0][3]
    res['state'] = data[0][4]
    res['mmax'] = data[0][5]
    res['alone'] = data[0][6]
    return res


def parce_grid2048(data):
    root = ET.fromstring(data)
    res = {}
    for item in root[0][0][0]:
        res[item.tag] = item.text

    assert 'errorstatus' not in res.keys(), res['errorstatus']

    return check_bomb(json.loads(res['result'].replace("-1","0"))['grid'])


def check_bomb(data):
        i = 0
        j = 0
        grid = tryeval(data)
        for element in grid:
                j = 0
                for k in element:
                        if ((int(k)>3000)and(int(k)<4000)):
                                grid[i][j] = 0.5
                        j=j+1
                i=i+1
        return grid

def make_auth(email, pwd):
    global mursid
    global COOKIES
    global csrf
    global id_p2p
    base_url = 'http://murclub.ru'
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    xml_proxy_flashvars = requests.post('%s/xmls/xml_proxy.php' % base_url,
                                        headers=headers,
                                        data='query=FLASHVARS&loc=ru%5FRU&protocolVer=2048%3A1%2E2%2E2').json()
    base_url = 'http://login.murclub.ru'
    r = requests.get('%s/index.php?login=%s&g=1&password=%s' % (base_url, email, pwd),
                     headers=headers, allow_redirects=False)




def auth(email,pwd):
    global mursid
    global COOKIES
    global csrf
    global id_p2p
    base_url = 'http://murclub.ru'
    flashvars = requests.get('%s/flashvars.php' % base_url, headers=headers).json()
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    xml_proxy_flashvars = requests.post('%s/xmls/xml_proxy.php' % base_url,
                                        headers=headers,
                                        data='query=FLASHVARS&loc=ru%5FRU&protocolVer=2048%3A1%2E2%2E2').json()
    base_url = 'http://login.murclub.ru'
    r = requests.get('%s/index.php?login=%s&g=1&password=%s' % (base_url, email, pwd),
                     headers=headers,
                     
                     allow_redirects=False)
    if r.status_code == 200:
        return None
    elif r.status_code == 302:
        base_url = 'http://murclub.ru'
        cookies = r.cookies
        mursid = requests.get(url=r.headers['location'],
                              cookies=cookies,
                              
                              headers=headers).json()['mursid']
        headers['Cookie'] = 'mursid=%s' % mursid
        flashvars = requests.post('%s/xmls/xml_proxy.php' % base_url,
                                  headers=headers,
                                
                                  data='query=FLASHVARS&loc=ru%5FRU&protocolVer=2048%3A1%2E2%2E2')
        COOKIES = flashvars.cookies
        flashvars = flashvars.json()
        cred = requests.post('%s/xmls/xml_proxy.php?%s' % (base_url, flashvars['xmlsparams']),
                             cookies=COOKIES,
                            
                             headers=headers,
                             data='bid=1&loc=ru%5FRU&action=list&id%5Fgame=1&query=KB%20GETPAGE%20P2P%5FSEARCH%5FGAME%20%23BR%5FR%23USERINFO%23BR%5FR%23MOBILE%5FUPDATE%202048%3A1%2E2%2E2%20android%2015%2C0%2C0%2C223&authMode=false&protocolVer=2048%3A1%2E2%2E2')


        csrf=requests.post('http://murclub.ru/xmls/xml_proxy.php',
                            data='query=FLASHVARS&loc=ru%5FRU&protocolVer=2048%3A1%2E3%2E1',
                            cookies=COOKIES,
                            
                            headers=headers).json()['xmlsparams'][5:-6]
        id_p2p=requests.post('http://murclub.ru/xmls/xml_proxy.php?csrf=%s&ver=3' % csrf,
                             data='bid=0&query=KB%20GETPAGE%20P2P%5FSEARCH%5FGAME%20&id%5Fgame=1&loc=ru%5FRU&'
                                  'action=newalone&protocolVer=2048%3A1%2E3%2E1',
                             
                             headers=headers, cookies=cookies).text
        if '<id_request>' in id_p2p:
            id_p2p=id_p2p[id_p2p.find('<id_request>')+12:id_p2p.find('</id_request>')]
        else:
            id_p2p=requests.post('http://murclub.ru/xmls/xml_proxy.php?csrf=%s&ver=3' % csrf,
                             data='bid=1&query=KB%20GETPAGE%20P2P%5FSEARCH%5FGAME'
                                  '%20%23BR%5FR%23USERINFO%23BR%5FR%23MOBILE%5FUPDATE%202048%'
                                  '3A1%2E3%2E1%20android%2015%2C0%2C0%2C223&id%5F'
                                  'game=1&authMode=false&loc=ru%5FRU&action=list&protocolVer=2048%3A1%2E3%2E1',
                             headers=headers,
                             
                             cookies=cookies).text
            id_p2p=id_p2p[id_p2p.find('<id_p2p id="')+12:id_p2p.find('"><bid>')]

        return cred

def make_move(move):
    data = requests.post(url='http://murclub.ru/xmls/xml_proxy.php?csrf=%s&ver=3' % csrf,headers=headers,
                         cookies=COOKIES,
                         data='id_p2p=%s&protocolVer=2048:1.3.0&query=KB GETPAGE P2P_GAME2048 &loc=ru_RU&action=move&direction=%s' % (id_p2p,str(move))).text
    return parce_grid2048(data)

def get_info():
    return parce_grid(
        requests.post(
            url='http://murclub.ru/xmls/xml_proxy.php?csrf=%s&ver=3' % csrf,
            
            headers=headers,
            cookies=COOKIES,
            data='protocolVer=2048:1.3.0&id_p2p=%s&loc=ru_RU&query=KB GETPAGE P2P_GAME2048 &action=getinfo' %
                 id_p2p).text)

if __name__ == "__main__":

    print  "var vk={ads_rotate_interval:120000,al:parseInt('3')||4,id:125244677,intnat:''?true:false,host:'vk.com',lang:0,rtl:parseInt('')||0,version:19239,stDomains:0,zero:false,contlen:52260,loginscheme:'https',ip_h:'8a79fa031cc02f0ecc',vc_h:'2f128d77e2f40f5c63e352e11c78c539',navPrefix:'/',dt:parseInt('0')||0,fs:parseInt('11')||11,ts:1460228423,tz:10800,pd:0,pads:1,vcost:7,time:[2016,4,9,22,0,23],sampleUser:-1,spentLastSendTS:new Date().getTime()};window.locDomain=vk.host.match(/[a-zA-Z]+\.[a-zA-Z]+\.?$/)[0];var _ua=navigator.userAgent.toLowerCase();if(/opera/i.test(_ua)||!/msie 6/i.test(_ua)||document.domain!=locDomain)document.domain=locDomain;var ___htest=(location.toString().match(/#(.*)/)||{})[1]||'',___to;if(vk.al!=1&&___htest.length&&___htest.substr(0,1)==vk.navPrefix){if(vk.al!=3||vk.navPrefix!='!'){___to=___htest.replace(/^(\/|!)/,'');if(___to.match(/^([^\?]*\.php|login|mobile)([^a-z0-9\.]|$)/))___to='';location.replace(location.protocol+'//'+location.host+'/'+___to);}}
var StaticFiles={'common.js':{v:1131},'common.css':{v:513},'ie6.css':{v:26},'ie7.css':{v:18},'lang0_0.js':{v:6703},'profile.css':{v:226},'page.css':{v:790},'profile.js':{v:218},'page.js':{v:942},'notifier.js':{v:383},'notifier.css':{v:151}}
var abp;</script>"

    login = raw_input('Enter email: ')
    passwd = raw_input('Enter password: ')
    #login = sys.argv[1]
    #passwd = sys.argv[2]

    auth(login, passwd)

    print id_p2p
    print mursid
    print csrf

    if not id_p2p:
        print "[ERROR] - Can't get game ID"
        exit(255)

    if not mursid:
        print "[ERROR] - Invalid login/password [or can't get mursid]"
        exit(255)

    if not csrf:
        print "[ERROR] - Invalid login/password [or can't get csrf]"
        exit(255)

    grid = tryeval(get_info()['grid'])

    ### BEGIN CLIENT

    import math

    def movename(move):
        return ['up', 'down', 'left', 'right'][move]

    def prepare_board(board):
        return [[int(math.log(float(col), 2)) if col > 0 else 0 for col in row] for row in board]

    from solver import *
    counter = 0
    while True:
        try:
            if counter>10:
                break
            board = prepare_board(grid)
            move = ['1', '3', '4', '2'][find_best_move(board)]
            """for row in grid:
                for col in row:
                    sys.stdout.write('%4s' % col)
                sys.stdout.write('\r\n')
            sys.stdout.write('\r\n') """
            grid = tryeval(make_move(move))
        except KeyboardInterrupt:
            break
        except:
            grid = tryeval(get_info()['grid'])
            counter=counter+1
    ### END CLIENT

    print "-----------[GAME OVER]--------"
    print "------------------------------"
    print repr(grid)
    print "------------------------------"

    if '2048' in repr(grid):
        print "Congratulations! You earn 2048 points!"
        exit(0)
    elif '4096' in repr(grid):
        print "Congratulations! You earn 4096 points!"
        exit(0)
    elif '8192' in repr(grid):
        print "Congratulations! You earn 8192 points!"
        exit(0)
    elif '16384' in repr(grid):
        print "Congratulations! You earn 16384 points!"
        exit(0)
    else:
        print "You lose! Cant't collect 2048 points!"
        exit(255)
	raw_input()