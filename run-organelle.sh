#!/bin/sh
RED='\033[0;31m'
YEL='\033[1;33m'
NC='\033[0m'
stty sane
clear
echo
echo
echo "             Welcome to Organ Donor from Sol Diego and Optimized Tomfoolery"
echo "                          at San Diego Maker Faire 2015"
echo
cd Organelle
sudo ./supervisor.py

