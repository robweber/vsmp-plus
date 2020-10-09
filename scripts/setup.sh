sudo apt-get install ffmpeg python3-dev python3-rpi.gpio python3-pil python3-numpy python3-pip libopenjp2-7 libtiff5 samba samba-common-bin ffmpeg-python

# setup the waveshare library
cd ../waveshare_lib
sudo python setup.py install
cd ../scripts

# set python3 as default
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
sudo update-alternatives --config python

sudo pip3 install spidev
sudo pip3 install image
sudo pip4 install ffmpeg-python

# set the path to the av libs
sudo cp ffmpeglibs.conf /etc/ld.so.conf.d/ffmpeglibs.conf
sudo ldconfig
