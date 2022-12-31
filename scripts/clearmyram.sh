#!/bin/sh

chckusr=$(id -u);

if [ $chckusr = "0" ] ; then
    echo "Cleaning RAM and SWAP, please, just wait."
    sync;
    echo 3 > /proc/sys/vm/drop_caches;
    swapoff -a
    swapon -a
    echo "Cleaned!";
else
    filepath="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
    echo "Starting as root...";
    sudo "$filepath/clearmyram.sh";
fi
