#!/usr/bin/python
from exchange_ec2 import Exchange
from threading import Thread, Lock
from ConfigParser import SafeConfigParser
from Queue import Queue
import sys
from time import sleep

queue = Queue()
threadLock = Lock()

def limH(rate):
    parser = SafeConfigParser()
    parser.read('rate.conf')
    high_limit = parser.getfloat(rate, 'high')
    return high_limit

def limL(rate):
    parser = SafeConfigParser()
    parser.read('rate.conf')
    low_limit = parser.getfloat(rate, 'low')
    return low_limit

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

usdtwd = Exchange('USDTWD', max_rate=limH('usdtwd'), min_rate=limL('usdtwd'))
usdjpy = Exchange('USDJPY', max_rate=limH('usdjpy'), min_rate=limL('usdjpy'))
audusd = Exchange('AUDUSD', max_rate=limH('audusd'), min_rate=limL('audusd'))
audtwd = Exchange('AUDTWD', max_rate=None, min_rate=None)
eurtwd = Exchange('EURTWD', max_rate=None, min_rate=None)
twdjpy = Exchange('TWDJPY', max_rate=None, min_rate=None)
cnytwd = Exchange('CNYTWD', max_rate=None, min_rate=None)


exchanges = [usdtwd, usdjpy, audusd, audtwd, eurtwd, twdjpy, cnytwd]


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
