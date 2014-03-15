# -*- coding: utf-8 -*-
import urllib2
import csv
import sys
import smtplib
from ConfigParser import SafeConfigParser
from time import gmtime, strftime, localtime, time, struct_time
from threading import Thread, Lock

threadLock = Lock()

def alertMail(sub, txt):
        parser = SafeConfigParser()
        parser.read('mail.conf')

        gmail_user = parser.get('sender', 'user')
        gmail_pwd = parser.get('sender', 'pwd')

        r1 = parser.get('recipients', 'recipient1')
        r2 = parser.get('recipients', 'recipient2')

        FROM = gmail_user
        BCC = [r1, r2]
        TO = []
        SUBJECT = sub
        TEXT = txt

        # Prepare actual message
        message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            #or port 465 doesn't seem to work!
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_pwd)
            server.sendmail(FROM, BCC, message)
            server.close()
            #sys.stdout.write('successfully sent the mail\n')
            #sys.stdout.flush()
        except:
            sys.stdout.write('failed to send mail\n')
            sys.stdout.flush()

class mailThread (Thread):
    def __init__(self, sub, txt):
        Thread.__init__(self)
        self.sub = sub
        self.txt = txt

    def run(self):
        # Get lock to synchronize threads
        threadLock.acquire()
        alertMail(self.sub, self.txt)
        # Free lock to release next thread
        threadLock.release()

class Exchange(object):
    """docstring for Exchange"""
    def __init__(self, input_code, max_rate=None, min_rate=None):
        #self.input_code = input_code
        self.code = input_code
        self.__translate()        # translate the exchange code for alert email
        self.__getUrl(self.code)  # get exchange code url
        self.rate = 0.0
        self.max_rate = max_rate
        self.min_rate = min_rate
        self.gmt = None

    def __getGmt(self):
        #self.gmt = strftime("%a, %d %b %Y %H:%M:%S", localtime())
        # for localtime in taiwan
        self.gmt = strftime("%a, %d %b %Y %H:%M:%S", gmtime(time() + 28800))
        # for EC2 at America west time

    def __getUrl(self, code=None):
        if code is not None:
            self.url = 'http://download.finance.yahoo.com/d/quotes.csv?e=.csv&f=sl1d1t1&s=' + code + '=x'
        else:
            sys.stdout.write("code has no value")
            sys.stdout.flush()
            #print "code has no value"
            return

    def __getCode(self, url):
        self.code = url[-8:-2]
        # no use

    def __translate(self):
        code_chn = {
            'USDTWD': '1 美元兌換新台幣',
            'USDJPY': '1 美元兌換日幣',
            'AUDUSD': '1 澳幣兌換美金',
            'AUDTWD': '1 澳幣兌換新台幣',
            'EURTWD': '1 歐元兌換新台幣',
            'TWDJPY': '1 新台幣兌換日幣',
            'CNYTWD': '1 人民幣兌換新台幣',
            'HKDTWD': '1 港幣兌換新台幣',
            'SGDTWD': '1 新加坡幣兌換新台幣'
        }
        try:
            self.text = code_chn[self.code]
        except KeyError:
            self.text = self.code

    def getExchange(self):
        self.__getGmt()

        headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1;\
                   en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}
        req = urllib2.Request(self.url, headers=headers)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            print "urllib2.URLError"
            print e
            sys.exit(1)
            # Maybe get 502 Bad Gateway Error
            # Halt python and waitting for whatchdog.sh

        html = response.read()
        data = []

        for row in csv.DictReader(html):
            if row[self.code + '=X'] == '':
                pass
            else:
                data.append(row[self.code + '=X'])

        data.pop()
        data.pop()
        self.rate = float(''.join(data))

    def show(self):
        sys.stdout.write(self.code + ": " + str(self.rate) + '\n')
        sys.stdout.flush()

    def threshold(self, max_rate=None, min_rate=None):
        self.__getGmt()

        if self.min_rate is None and self.max_rate is None:
            return

        base = self.rate
        alerttext = self.text + ": " + str(self.rate) + '\n時間：' + self.gmt
        sub = self.text + ', 匯率觸發通知'
        parser = SafeConfigParser()
        parser.read('rate.conf')

        if self.rate >= self.max_rate:
            t = mailThread(sub, alerttext)
            t.daemon = True
            t.start()
            sys.stdout.write("Max rate + 2% From "
                             + str(base) + " To " + str(base * 1.02) + '\n')
            sys.stdout.flush()
            self.max_rate = base * 1.02
            parser.set(self.code.lower(), "high", str(self.max_rate))
            parser.write(open('rate.conf', 'w'))

        if self.rate <= self.min_rate:
            t = mailThread(sub, alerttext)
            t.daemon = True
            t.start()
            sys.stdout.write("Min rate - 2% From "
                             + str(base) + " To " + str(base * 1.02) + '\n')
            sys.stdout.flush()
            self.min_rate = base * 1.02
            parser.set(self.code.lower(), "low", str(self.min_rate))
            parser.write(open('rate.conf', 'w'))

    def subscription(self, hour=10, mins=0, hour2=14, mins2=0):
        self.__getGmt()
        #tt = struct_time(localtime())
        tt = struct_time(gmtime(time() + 28800))
        # for EC2 at America west time
        # 10:00 Alert
        if tt.tm_hour == hour and tt.tm_min == mins and tt.tm_sec <= 19:
            alerttext = self.text + ": " + str(self.rate) + '\n時間：' + self.gmt
            sub = "每日" + str(hour) + "點匯率通知"

            t = mailThread(sub, alerttext)
            t.daemon = True
            t.start()

        # 14:00 Alert
        elif tt.tm_hour == hour2 and tt.tm_min == mins2 and tt.tm_sec <= 19:
            alerttext = self.text + ": " + str(self.rate) + '\n時間：' + self.gmt
            sub = "每日" + str(hour2) + "點匯率通知"

            t = mailThread(sub, alerttext)
            t.daemon = True
            t.start()
        
        else:
            pass

if __name__ == '__main__':
    pass
