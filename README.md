# VSMP (Very Slow Media Player)
I read an [article by Tom Whitwell](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), detailing his process for creating a slow media player using e-paper and a Raspberry Pi 4. His project was in turn inspired by a [2018 article by Bryan Boyer](https://medium.com/s/story/very-slow-movie-player-499f76c48b62) about the same thing. Both of these were very simple, yet visually stunning and led me to create my own version of this project. 

Both of the reference articles had pieces I liked and pieces I wanted to enhance about them. That is what this project seeks to do. Combing piece of both of them I ended up with the following, which is both the same and different from their designs. 

## Basic Usage
Once the requirements are in place (See Install document) the program itself is contained in the ```vsmp.py``` file. This file can take a variety of arguments: 

* ```--file``` - the video file to pull frames from. Must be an MP4 
* ```--increment``` - how many frames to increment
* ```--start``` - the frame to start on, if you want to skip into the video X amount

Rather than running as a service the program will run once, starting at the ```start``` frame of the video. The image will be displayed and then a save file will be created, specific to this video file, with the next frame to display. On the next run the save file will be read and this frame will be displayed. Subsequent runs will continue to move forward by the ```increment``` amount. If the video ends it will start over at the ```start``` frame again. The save file and log file for the program are both stored in the ```tmp``` directory, which is created the first time the program is run. 

To get the program to run continuously simply use __cron__ to schedule the program to run on any schedule of your choosing. I found using cron perferable to making a service as it allowed more customization of the display timing. Plus it was less taxing and error prone than having a python script run indefinitely. An example cron schedule would be: 

``` 

python /home/pi/very-slow-media-player/vsmp.py --file /path/to/file.mp4 --increment 100

```

## Find Timing
Once the program was up and running, one thing that was very hit/miss was what exactly the input parameters should be for my desired effect. Did I want the video take days, weeks, months to display? What combination of increments and delays would get the effect I wanted? With this in mind the ```analyze.py`` file was born. 

The analyze program will take the same inputs as above the addition of the ```--delay``` argument. Delay is the amount of time in seconds between runs you intend to set with cron. Using these inputs the video is analyzed and some information is displayed regarding projected play times. 

```
Analyzing /home/pi/Videos/Test.Video.mp4 
Starting Frame: 200, Frame Increment: 30, Delay between updates: 120
Video framerate is 29.970000fps, total video is 103.810477 minutes long

Entire Video: 
6222 out of 186672 frames will display
Video will take 1.0 week, 1.0 day, 15.0 hours to fully play

Remaining Video:
5072 out of 152172 frames will display
Video will take 1.0 week, 1.0 hour, 4.0 minutes to fully play

Minutes of film displayed breakdown:
0.500501 minutes of film per hour
12.012012 minutes of film per day

```

Tweaking these values you can find the optimum settings to get your desired play time. 

### Links
https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4

https://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/

https://linuxconfig.org/how-to-change-from-default-to-alternative-python-version-on-debian-linux

https://magpi.raspberrypi.org/articles/samba-file-server

https://gist.github.com/jjangsangy/058456fe2d04e3c5f6107d62b60542e3

https://stackoverflow.com/questions/61384486/error-dav1d-0-2-1-not-found-using-pkg-config
