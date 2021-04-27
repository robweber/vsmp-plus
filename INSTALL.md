# Install

I installed this on a base install of [Raspberry Pi OS](https://www.raspberrypi.org/downloads/) (formally Raspbian). If you use some other method some of this libraries may already exist but this is assuming you have a fresh OS.

## Hardware

Most of this hardware is identical to the build by Tom Whitwell, although I used a different picture frame. Any frame you can modify will work. The Electronic Paper Display (EPD) can be any display known to work with the [vsmp-epd abstraction library](https://github.com/robweber/vsmp-epd). Most Waveshare displays are compatible.

* RaspberyPi 4 with SD card and power suppply
* 7.5 inch e-paper screen [link](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm)
* A photo frame. I used [this one from Target](https://www.target.com/p/5-34-x-7-34-picture-holder-frame-black-room-essentials-8482/-/A-77656810#lnk=sametab).

__Notes on the frame:__ I found this one to be a good buy since it has a slideout piece with a gap behind it. This was useful for mounting some of the components. The base is also super sturdy.

The display itself connects to the GPIO pins of the Pi. There are some pictures in the above link and some basic instructions with the device.

## Software Install

I won't get into the details of installing the Raspberry Pi OS. There are other good guides on that if you're unsure. Just make sure you have it installed with SSH enabled. Once you have access to the system you can run the following commands to get the software components working.

The quickest way to get this done is just to run the following command but if you want to install manually you can follow these instructions.

```

# install script, performs everything listed below
curl https://raw.githubusercontent.com/robweber/vsmp-plus/master/setup/install.sh | bash

```

### Clone Repo and Install Libraries
```
# enable SPI - very important https://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/
sudo raspi-config

# clone this repo
git clone https://github.com/robweber/vsmp-plus.git


# install required system libraries
sudo apt-get install ffmpeg fonts-freefont-ttf git python3-dev python3-rpi.gpio python3-pil python3-numpy python3-pip libopenjp2-7 libtiff5 redis-server

```

You must then set python 3 as the default for the system. Use the following commands to do this, adjust directories to python 3.8 or 3.9 as needed.

```

# set python3 as default https://linuxconfig.org/how-to-change-from-default-to-alternative-python-version-on-debian-linux
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 2
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
sudo update-alternatives --config python

```

Next install some python libraries needed.

```
cd vsmp-plus

# this will build libraries for any supported displays (see omni-epd for more info)
sudo pip3 install -r setup/requirements.txt

```

### Test E-Ink Display
This next step is optional but it is probably a good idea at this point to check that the e-ink display is working.

```

# OPTIONAL - check if the e-paper sign is working properly, substitute your own display type here
python /home/pi/e-Paper/examples/epd_7in5_V2_test.py

```

### Build FFmpeg - not needed if installing from apt-get above
Now we have to build the FFMPEG library. If using a NOOBS install you may already have this installed but on a base system you have to compile it yourself. __This will take a long time__. Be patient.

```

# run the ffmpeg installer
sudo ./setup/ffmpeg-rpi-4.sh

# set the path to the av libs
sudo cp setup/ffmpeglibs.conf /etc/ld.so.conf.d/ffmpeglibs.conf
sudo ldconfig

```

### Modify the Configuration File

By default the service file looks for a configuration file in `/home/pi/vsmp-plus/custom-conf.conf`. You can modify the service file if you want to store it somewhere else. Copy the conf file to avoid errors on startup:

```

cp setup/vsmp.conf ./custom-conf.conf

```

Check the README file for valid values to change in this file. This is necessary if you wish to change the port or EPD driver being loaded at startup.

### Install service

You can run the program on it's own but to keep it running after you close your SSH session you'll need to install it as a service. The file to do this is in the ```setup``` folder. If you edit the service file you can pass in any arguments or the location of your configuration file. By default it will run the program with the defaults.

```
# install the service on the system
sudo cp setup/vsmp.service /etc/systemd/system/vsmp.service
sudo chown root:root /etc/systemd/system/vsmp.service
sudo systemctl enable vsmp

# start the service
sudo systemctl start vsmp

# stop the Service
sudo systemctl stop vsmp
```

Finally you have to update your local library path. This has to be done each time you login or as part of your bash profile.

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

There is an already modified version of this file in the ```setup``` directory you can copy to the above file location. After this reboot your system. USB drives will be auto mounted to ```/media/usb``` after a reboot.
