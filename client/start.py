import argparse
import socket,sys,os,commands,time
from selenium import webdriver
from selenium.webdriver.common.proxy import * 
from stem import Signal
from stem.control import Controller

## add arguments
parser = argparse.ArgumentParser(description='Browse a site')
parser.add_argument('DEST_IP', help='destination IP')
parser.add_argument('DEST_PORT', help='destination port')
parser.add_argument('MODE',  help='tor|vpn|proxy|normal')
parser.add_argument('number',  help='cycle ips')
parser.add_argument('-c', action='store_true', default=False, help='change identity for each cycle') 
parser.add_argument('-hide', action='store_true', default=False, help='hide webbrowser') 

## parse arguments
args = parser.parse_args()
argv = vars(args)

## check validity of arguments
try:
    socket.inet_aton(argv['DEST_IP'])
except:
    print "Invalid IP address!"
    sys.exit(-1)

if int(argv['DEST_PORT']) > 65535 or int(argv['DEST_PORT']) < 0 :
    print "Invalid Port!"
    sys.exit(-1)
mode = {'tor', 'vpn', 'proxy', 'normal'} 
if argv['MODE'] not in mode:
    print "Invalid Mode!"
    sys.exit(-1)
cycle = int(argv['number'])
if cycle > 10000:
    print "Too many times!"
    sys.exit(-1)

## helper to read csv
def readConfig(filename):
    try:
        fileHdl = open(filename, 'rb')
    except:
        print 'No ' + filename + ' in current directory'
        sys.exit(-1)
    header = fileHdl.readline().strip('\n').split(',')
    data = fileHdl.readlines()
    output = []
    for line in data:
        output.append(dict(zip(header, line.strip('\n').split(','))))
    fileHdl.close()
    return output

## read proxylists
proxylist = readConfig('proxy.csv')

## read vpnlist and secrets
vpnlist = readConfig('vpn.csv')

## helper to get a new proxy from list
proxyId = 0
def getProxy(flag):
    global proxyId
    if not flag:
        return proxylist[0]
    if(proxyId == len(proxylist)):
        proxyId = 1
    else:
        proxyId = proxyId + 1
    return proxylist[proxyId - 1]
vpnId = 0

## use PhantomJS to hide the browser
def PhantomJSBrowsing(proxySetting):
    print "You'll not see the webbrowser..."
    try:
        webdriver.PhantomJS()
    except:
        print "Error: No PhantomJS found"
        sys.exit(-1)
    if proxySetting == None:
        return webdriver.PhantomJS()
    else:
        service_args = [
                '--proxy=' + proxySetting.split(',')[0],
                '--proxy-type=' + proxySetting.split(',')[1],
            ]
        return webdriver.PhantomJS(service_args = service_args)

## function to get page and measure time
def getPage(browser, dst, port):
    ## set page load timeout in case bad proxy server 
    browser.set_page_load_timeout(10)
    startTime = int(round(time.time() * 1000))
    try:
        browser.get('http://' + dst + ':' + port)
    except:
        print "Page load timeout..."
        browser.close()
        return 
    endTime = int(round(time.time() * 1000))
    print "Time to load page: " + str(endTime - startTime) + 'ms'
    browser.close()
    return 

## function to connect to a vpn currently only works on Mac
def connectVPN(vpnsetting):
    print 'Connecting to a different vpn [' + vpnsetting['Name'] + ']...'
    retry = 0
    # retry 10 times in case connection fail
    while retry < 10: 
        cmd = 'scutil --nc start ' + vpnsetting['Name'] + ' --secret ' + vpnsetting['Secret']
        os.system(cmd)
        time.sleep(2)
        if commands.getstatusoutput('scutil --nc status ' + vpnsetting['Name'])[1].split('\n')[0] == 'Connected':
             break
        retry = retry + 1
    if commands.getstatusoutput('scutil --nc status ' + vpnsetting['Name'])[1].split('\n')[0] == 'Connected':
        return True
    else:
        return False


## function to handle connection and  send browse request
def browse(dst, port, mode, newIdentity):
    if mode == 'tor':
        try:
            with Controller.from_port(port = 9000) as controller:
                if newIdentity:
                    #send change identity signal to tor via control port
                    controller.authenticate()
                    controller.signal(Signal.NEWNYM)
                    ## tor will delay change identity request for several seconds, we have to wait
                    print 'Waiting for tor to change identity...'
                    time.sleep(5) 
                    print 'New identity get...'
        except:
            print "Tor is not running or control port is not set to 9000"
            sys.exit(-1)
        tor_browsing(dst, port, 9050)
    elif mode == 'vpn':
        # check vpn list
        if len(vpnlist) == 0:
            print "No vpn available, make sure to put your vpn configs to vpn.csv"
            sys.exit(-1)
        # check platform
        if 'darwin' in sys.platform:
            if newIdentity:
                global vpnId
                connected = connectVPN(vpnlist[vpnId])

                # update vpnlist
                if vpnId == len(vpnlist) -1:
                    vpnId = 0
                else:
                    vpnId = vpnId + 1

                # connected or not
                if not connected:
                    print "Error: not connected!"
                    return
                else:
                    print 'Connected'
            else:
                if commands.getstatusoutput('scutil --nc status ' + vpnlist[0]['Name'])[1].split('\n')[0] == 'Connected':
                    print 'Connected to vpn [' + vpnlist[0]['Name'] + ']' 
                else:
                    connected = connectVPN(vpnlist[0])
                    if not connected:
                        print "Error: not connected!"
                        return
                    else:
                        print 'Connected'
 
            vpn_browsing(dst, port)
        else:
            print "Your operating system is not supported!"
            return 
    elif mode == 'proxy':
        if newIdentity:
            #get new identity from proxylist
            proxySetting = getProxy(True) 
        else:
            proxySetting = getProxy(False)
        print('You are using this proxy:', proxySetting)
        proxy_browsing(dst, port, proxySetting['IP'], proxySetting['Port'], proxySetting['Type'])
    else:
        if newIdentity:
            print 'You are not anonymous, ignoring change identity...'
        normal_browsing(dst, port)


## browse with tor 
def tor_browsing(dst, port, torPort):
    if(argv['hide']):
        browser = PhantomJSBrowsing('127.0.0.1:9050,socks5')
    else:
        print "You'll see the webbrowser..."
        profile=webdriver.FirefoxProfile()
        profile.set_preference('network.proxy.type', 1)
        profile.set_preference('network.proxy.socks', '127.0.0.1')
        profile.set_preference('network.proxy.socks_port', torPort)
        browser=webdriver.Firefox(profile)
    getPage(browser, dst, port)

# browse with vpn
def vpn_browsing(dst, port):
    if argv['hide']:
        browser = PhantomJSBrowsing(None)
    else:
        print "You'll see the webbrowser..."
        browser=webdriver.Firefox()
    getPage(browser, dst, port)
    return

# browse with proxy
def proxy_browsing(dst, port, proxyIP, proxyPort, proxyType):
    proxySetting = proxyIP + ':' + proxyPort
    if argv['hide']:
        if proxyType == 'HTTP':
            browser = PhantomJSBrowsing(proxySetting + ',' + 'http')
        elif proxyType == 'HTTPS':
            browser = PhantomJSBrowsing(proxySetting + ',' + 'https')
        else:
            browser = PhantomJSBrowsing(proxySetting + ',' + 'socks5')
    else:
        proxy = Proxy({
            'proxyType' : ProxyType.MANUAL,
            'ftpProxy' : proxySetting,
            'sslProxy' : proxySetting,
            'socksProxy' : proxySetting,
            'httpProxy' : proxySetting,
            'noProxy' : ''
        })
        browser = webdriver.Firefox(proxy = proxy)

    getPage(browser, dst, port)
    return

# no anonymization
def normal_browsing(dst, port):
    if(argv['hide']):
        browser = PhantomJSBrowsing(None)
    else:
        print "You'll see the webbrowser..."
        browser=webdriver.Firefox()
    getPage(browser, dst, port)
    return

## start browsing
if __name__ == "__main__":
    for i in range(cycle):
        print '------------------------------------------------------------------'
        print 'Cycle:' + str(i)
        browse(argv['DEST_IP'], argv['DEST_PORT'], argv["MODE"], argv['c'])
