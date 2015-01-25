#!/bin/bash
echo "installing python-pip"
sudo apt-get install python-pip
echo "installing scratchpy"
sudo pip install scratchpy
echo "installing scratch"
sudo apt-get install scratch
echo "installing aseba"    
sudo add-apt-repository ppa:stephane.magnenat/\`lsb_release -c -s\'
sudo apt-get update
sudo apt-get install Aseba
echo "finished"
