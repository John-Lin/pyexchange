# -*- coding: utf-8 -*-
import urllib2
import csv
import sys
import smtplib
import os
from email.mime.text import MIMEText
from ConfigParser import SafeConfigParser
from time import sleep, gmtime, strftime, localtime, time, struct_time
from threading import Thread, Lock
from Queue import Queue

queue = Queue()
threadLock = Lock()

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def alertMail(sub, txt):
        parser = SafeConfigParser()
        parser.read('mail.conf')

        gmail_user = parser.get('sender', 'user')
        gmail_pwd = parser.get('sender', 'pwd')

        r1 = parser.get('recipients', 'recipient1')
        #r2 = parser.get('recipient', 'recipient2')

        FROM = gmail_user
        BCC = [r1] #must be a list
        TO = [] #for testing
        SUBJECT = sub
        TEXT = txt

        # Prepare actual message
        message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_pwd)
            server.sendmail(FROM, BCC, message)
            server.close()
            sys.stdout.write('successfully sent the mail\n')
            sys.stdout.flush()
        except:
            sys.stdout.write('failed to send mail\n')
            sys.stdout.flush()

class myThread (Thread):
    def run(self):
        # Get lock to synchronize threads
        threadLock.acquire()
        obj = queue.get()
        obj.getExchange()
        obj.show()
        obj.threshold()
        obj.subscription()
        # Free lock to release next thread
        threadLock.release()
        queue.task_done()

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
        self.__translate() # translate the exchange code for alert email
        self.__getUrl(self.code)    # get exchange code url
        self.rate = 0.0
        self.max_rate = max_rate
        self.min_rate = min_rate
        self.gmt = None

    def __getGmt(self):
        self.gmt = strftime("%a, %d %b %Y %H:%M:%S", localtime())
        # for localtime in taiwan
        #self.gmt = strftime("%a, %d %b %Y %H:%M:%S", gmtime(time()+28800))
        # for EC2 at America west time

    def __getUrl(self, code=None):
        if code != None:
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
            'USDTWD':'美金對新台幣',
            'USDJPY':'美金對日幣',
            'AUDUSD':'澳幣對美金',
            'AUDTWD':'澳幣對新台幣',
            'EURTWD':'歐元對新台幣',
            'TWDJPY':'新台幣對日幣',
            'CNYTWD':'人民幣對新台幣',
            'HKDTWD':'港幣對新台幣',
            'SGDTWD':'新加坡幣對新台幣'
        }
        try:
            self.text = code_chn[self.code]
        except KeyError:
            self.text = self.code

    def getExchange(self):
        self.__getGmt()

        headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}
        req = urllib2.Request(self.url, headers=headers)

        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            print "urllib2.URLError"
            sys.exit(1)
            # Maybe get 502 Bad Gateway Error
            # Halt python and waitting for whatchdog.sh

        html = response.read()
        data = []
        for row in csv.DictReader(html):
            if row[self.code+'=X'] == '':
                pass
            else:
                data.append(row[self.code+'=X'])

        times = data.pop() # no use
        date = data.pop()  # no use
        self.rate = float(''.join(data))

    def show(self):
        sys.stdout.write(self.code+": " + str(self.rate)+ '\n')
        #sys.stdout.write("\r"+self.code+": " + str(self.rate) + ' ' + ' ' + self.gmt)
        sys.stdout.flush()

    def threshold(self, max_rate=None, min_rate=None):
        self.__getGmt()
        def __alertthread(fun, sub, txt):
            t = Thread(target=fun, args=(sub, txt))
            t.start()

        if self.min_rate == None and self.max_rate == None:
            return

        base = self.rate

        if self.rate >= self.max_rate:
            alerttext = self.text + ": " + str(self.rate) + '\n時間：'+ self.gmt
            __alertthread(alertMail, "匯率觸發通知", alerttext)
            #self.__alertMail()
            sys.stdout.write("Max rate + 0.05 from: " + str(base) + " --> " + str(base+0.05))
            sys.stdout.flush()
            self.max_rate = base + 1
            # send max_rate mail

        if self.rate <= self.min_rate:
            alerttext = self.text + ": " + str(self.rate) + '\n時間：'+ self.gmt
            __alertthread(alertMail, "匯率觸發通知", alerttext)
            #self.__alertMail()
            sys.stdout.write("Min rate - 0.05 from: " + str(base) + " --> " + str(base-0.05))
            sys.stdout.flush()
            self.min_rate = base - 1
            #send min_rate mail


    def subscription(self, hour=10, mins=0, hour2=14, mins2=0):
        self.__getGmt()
        #tt = struct_time(localtime())
        tt = struct_time(gmtime(time()+28800))
        # for EC2 at America west time
        # 10:00 Alert
        if tt.tm_hour == hour and tt.tm_min == mins and tt.tm_sec <= 19:
            alerttext = self.text + ": " + str(self.rate) + '\n時間：'+ self.gmt
            sub = "每日" + str(hour) + "點匯率通知"

            t = mailThread(sub, alerttext)
            t.daemon = True
            t.start()
            #t = Thread(target=self.__alertMail, args=(sub, alerttext))
            #t.start()

        # 14:00 Alert
        elif tt.tm_hour == hour2 and tt.tm_min == mins2 and tt.tm_sec <= 19:
            alerttext = self.text + ": " + str(self.rate) + '\n時間：'+ self.gmt
            sub = "每日" + str(hour2) + "點匯率通知"

            t = mailThread(sub, alerttext)
            t.daemon = True
            t.start()
            #t = Thread(target=self.__alertMail, args=(sub, alerttext))
            #t.start()
        else:
            return

if __name__ == '__main__':

    usdtwd = Exchange('USDTWD', max_rate=31.5, min_rate=29.3)
    usdjpy = Exchange('USDJPY', max_rate=103.0, min_rate=101.0)
    cnytwd = Exchange('AUDUSD', max_rate=0.905, min_rate=0.88)
    audtwd = Exchange('AUDTWD', max_rate=None, min_rate=None)
    eurtwd = Exchange('EURTWD', max_rate=None, min_rate=None)
    twdjpy = Exchange('TWDJPY', max_rate=None, min_rate=None)
    audusd = Exchange('CNYTWD', max_rate=None, min_rate=None)

    exchanges = [usdtwd, usdjpy, cnytwd, audtwd, eurtwd, twdjpy, audusd]


    while True:
        for ex in exchanges:
            queue.put(ex)

        for ex in exchanges:
           th = myThread()
           th.daemon = True
           th.start()

        sys.stdout.write('==========\n')
        sys.stdout.flush()
        #print th.isAlive() #True
        queue.join()
        #print th.isAlive() #False
        sleep(20)




