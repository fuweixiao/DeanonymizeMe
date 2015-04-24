from flask import Flask, render_template, request
import urllib
import urllib2
app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def identify():
    if request.method == 'GET':
        ip = request.remote_addr
        url = 'http://torstatus.blutmagie.de/tor_exit_query.php'
        data = urllib.urlencode({'QueryIP' : ip, 'DestinationIP' : '', 'DestinationPort':''})
        results = urllib2.urlopen(url, data)
        flag = False
        line = results.readline()
        while line: 
            if 'matches' in line:
                flag = True
            line = results.readline()
        if flag:
            return render_template('index.html', ipaddr = ip, tor = '')
        else:
            return render_template('index.html', ipaddr = ip, tor = 'not')
if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 7000)


