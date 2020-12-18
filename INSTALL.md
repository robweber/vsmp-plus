# Install

I installed this on a base install of [Raspberry Pi OS](https://www.raspberrypi.org/downloads/) (formally Raspbian). If you use some other method some of this libraries may already exist but this is assuming you have a fresh OS. 

## Prerequisites

Make sure you have a working base install of Raspberry Pi OS with SSH enabled. 


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
