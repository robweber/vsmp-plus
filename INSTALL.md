# Install

I installed this on a base install of [Raspberry Pi OS](https://www.raspberrypi.org/downloads/) (formally Raspbian). If you use some other method some of this libraries may already exist but this is assuming you have a fresh OS. 

## Hardware

Most of this hardware is identical to the build by Tom Whitwell, although I used a different picture frame. Any frame you can modify will work. 

* RaspberyPi 4 with SD card and power suppply
* 7.5 inch e-paper screen [link](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm)
* A photo frame. I used [this one from Target](https://www.target.com/p/5-34-x-7-34-picture-holder-frame-black-room-essentials-8482/-/A-77656810#lnk=sametab). 

__Notes on the frame:__ I found this one to be a good buy since it has a slideout piece with a gap behind it. This was useful for mounting some of the components. The base is also super sturdy. 

The display itself connects to the GPIO pins of the Pi. There are some pictures in the above link and some basic instructions with the device. 

## Software Install

I won't get into the details of installing the Raspberry Pi OS. There are other good guides on that if you're unsure. Just make sure you have it installed with SSH enabled. Once you have access to the system you can run the following commands to get the software components working. 

```
# enable SPI - very important https://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/
sudo raspi-config

# clone this repo
git clone https://github.com/robweber/vsmp-plus.git
cd vsmp-plus

# install required system libraries
sudo apt-get install ffmpeg python3-dev python3-rpi.gpio python3-pil python3-numpy python3-pip libopenjp2-7 libtiff5 samba samba-common-bin ffmpeg-python

# setup the waveshare library
cd ../waveshare_lib
sudo python setup.py install
cd ../scripts
```

You must then set python 3 as the default for the system. Use the following commands to do this, adjust directories to python 3.8 or 3.9 as needed. 

```

# set python3 as default https://linuxconfig.org/how-to-change-from-default-to-alternative-python-version-on-debian-linux
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
sudo update-alternatives --config python

```

Next install some python libraries needed. 

```

sudo pip3 install -r scripts/requirements.txt

```

This next step is optional but it is probably a good idea at this point to check that the e-ink display is working. 

```

# OPTIONAL - check if the e-paper sign is working properly
python examples/epd_7in5_V2_test.py

```

Now we have to build the FFMPEG library. If using a NOOBS install you may already have this installed but on a base system you have to compile it yourself. __This will take a long time__. Be patient. 

```
# get out of the waveshare lib
cd ..

# run the ffmpeg installer
sudo ./scripts/ffmpeg-rpi-4.sh

# set the path to the av libs
sudo cp ffmpeglibs.conf /etc/ld.so.conf.d/ffmpeglibs.conf
sudo ldconfig

```

Finally you have to update your local library path. This has to be done each time you login or as part of your bash profile. If using cron to trigger the program you must also include this in your cron file. 

```

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/arm-linux-gnueabihf/:/usr/local/lib/

```

## USB Automount

If you want to pull files from a USB device you may want to setup auto mount functionality for USB sticks. This can easily be done by installing the ```usbmount``` package. 

```

sudo apt-get install usbmount

```

Once installed for the RaspberryPi OS you need to modify one line of the ```/lib/systemd/system/systemd-udevd.service``` file. 

```

[Service]
...
PrivateMounts=no
...

```

There is an already modified version of this file in the ```scripts``` directory you can copy to the above file location. After this reboot your system. USB drives will be auto mounted to ```/media/usb``` after a reboot. 
