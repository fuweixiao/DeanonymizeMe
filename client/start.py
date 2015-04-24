import argparse
import socket,sys
from selenium import webdriver
from selenium.webdriver.common.proxy import * 

## add arguments
parser = argparse.ArgumentParser(description='Browse a site')
parser.add_argument('DEST_IP', help='destination IP')
parser.add_argument('MODE',  help='tor|vpn|proxy|normal')
##parser.add_argument('--port', help="Only use this if MODE is tor or proxy")

args = parser.parse_args()
argv = vars(args)

## check validity of arguments
try:
    socket.inet_aton(argv['DEST_IP'])
except:
    print("Invalid IP address!")
    sys.exit(-1)
mode = {'tor', 'vpn', 'proxy', 'normal'} 
if argv['MODE'] not in mode:
    print("Invalid Mode!")
    sys.exit(-1)
    

def browse(dst, mode):
    if mode == 'tor':
        tor_browsing(dst, 9150)
    elif mode == 'vpn':
        vpn_browsing(dst)
    elif mode == 'proxy':
        proxy_browsing(dst, '127.0.0.1', 9150)
    else:
        normal_browsing(dst)


## browse with tor 
def tor_browsing(dst, torPort):
    profile=webdriver.FirefoxProfile()
    profile.set_preference('network.proxy.type', 1)
    profile.set_preference('network.proxy.socks', '127.0.0.1')
    profile.set_preference('network.proxy.socks_port', torPort)
    browser=webdriver.Firefox(profile)
    browser.get('http://' + dst)

# browse with vpn
def vpn_browsing(dst):
    ## To be done
    return

# browse with proxy
def proxy_browsing(dst, proxyIP, proxyPort):
    proxySetting = proxyIP + ':' + str(proxyPort)
    proxy = Proxy({
            'proxyType' : ProxyType.MANUAL,
            'ftpProxy' : proxySetting,
            'sslProxy' : proxySetting,
            'socksProxy' : proxySetting,
            'httpProxy' : proxySetting,
            'noProxy' : ''
        })
    browser = webdriver.Firefox(proxy = proxy)
    browser.get('http://' + dst)
    return

# no anonymization
def normal_browsing(dst):
    browser=webdriver.Firefox()
    browser.get('http://' + dst)
    return

## start browsing
if __name__ == "__main__":
    browse(argv['DEST_IP'], argv["MODE"])

