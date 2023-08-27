#!/bin/bash
#for DEV in /proc/sys/net/ipv4/conf/*/rp_filter
#do
#    echo 0 > $DEV
#done

for DEV in /proc/sys/net/ipv4/conf/*/rp_filter
do
    echo $DEV $(cat $DEV)
done
