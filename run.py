#!/usr/bin/python
import os
import sys
from progressBar import progress
from exchange import Exchange
from ConfigParser import SafeConfigParser
from time import sleep

flag = []

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

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
        ex.getExchange()
        ex.show()
        ex.threshold()
        ex.subscription()

    #sys.stdout.write('==========\n')
    #sys.stdout.flush()
    progress(40, 0.5)
