#!/usr/local/bin/bash
# shell name: watchdog.sh
 
ps=`ps ax > /tmp/ps.txt`
 
p=`grep "m python run.py" /tmp/ps.txt | awk '{print $9}'`

#echo $p

if [ "$p" != "run.py" ]; then
#if [ "$p" == " " ]; then
    echo "Starting PyExchang..."
    #nohup python pyexchange/run.py &
    screen -d -m python run.py
    sleep 1
#elif [ "$p" == "pyexchange/run.py" ]; then
#    echo $p "is running."
else
    echo $p "is running."
fi


p=''
