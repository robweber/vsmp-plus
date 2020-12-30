# VSMP+ (Very Slow Media Player Plus)
I read an [article by Tom Whitwell](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), detailing his process for creating a slow media player using e-paper and a Raspberry Pi 4. His project was in turn inspired by a [2018 article by Bryan Boyer](https://medium.com/s/story/very-slow-movie-player-499f76c48b62) about the same thing. Both of these were very simple, yet visually stunning and led me to create my own version of this project.

Both of the reference articles had pieces I liked and pieces I wanted to enhance about them. That is what this project seeks to do. Combing piece of both of them I ended up with the following, which is both the same and different from their designs.

![](https://github.com/robweber/vsmp-plus/blob/master/pics/front_with_timecode.jpg)

## Basic Usage
Once the requirements are in place (See Install document) the program itself is contained in the ```vsmp.py``` file. This file can take a variety of arguments:

* ```--config``` - path to a config file, see below
* ```--file``` - the video file to pull frames from. Must be an MP4 _mutually exclusive with --dir_
* ```--dir``` - a directory of video files to pull frames from. _mutually exclusive with --file_
* ```--increment``` - how many frames to increment
* ```--update``` - how often to update the display, this is given as a [cron expression](http://en.wikipedia.org/wiki/Cron).
* ```--start``` - the number of seconds into the video to start, if you want to skip into the video X amount
* ```--end``` - the number of seconds to cut off the end of the video, useful for skipping credit sequences
* ```--timecode``` - show the timecode HH:mm:SS of the video on the bottom of the display, default is false

Once started, either with the CLI or as a service, the given cron expression will be used to update the display starting at the ```start``` frame of the video. The image will be displayed and then a save file will be created, specific to this video file, with the next frame to display. At each update time the save file will be read and the next frame will be displayed. Subsequent runs will continue to move forward by the ```increment``` amount. If the video ends it will start over at the ```start``` frame again. If reading from a directory it will start the next video. The save file and log file for the program are both stored in the ```tmp``` directory, which is created the first time the program is run.

To monitor the progress of the program you can watch the log file using the command:

```
# from the vsmp-plus directory
tail -f tmp/log.log
```

## Find Timing
Once the program was up and running, one thing that was very hit/miss was what exactly the input parameters should be for my desired effect. Did I want the video take days, weeks, months to display? What combination of increments and delays would get the effect I wanted? With this in mind the ```analyze.py``` file was born.

The analyze program will take the same inputs as above. Using these inputs the video is analyzed and some information is displayed regarding projected play times.

```
Analyzing /home/pi/Videos/Test.Video.mp4
Starting Frame: 200, Ending Frame: 186672, Frame Increment: 30, Delay between updates: 120
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

Tweaking these values you can find the optimum settings to get your desired play time. Additionally you can specify ```-d``` instead of ```-f``` to analyze an entire directory of files. Each will show separately, with a summary at the end. When looking at a whole directory the program will assume the current value of the ```last_played.txt``` file is the currently running file and analyze from this point forward.

## Config File

Instead of passing in all the arguments on the command line you can also create a config file and pass in your values with the ```-c``` option instead. There is a sample of this file in the ```setup/``` directory. Any command line argument can be specified in the file.

```

# Example Config file
dir = /path/to/directory/
increment = 50
start = 100
end = 300

```

Using a config file also makes it easier to test settings with the ```analyze.py``` file as you can use one file for both.

## Differences/Additions

I mentioned two other versions of this type of project that I took inspiration from when creating this one. I tried to combine pieces of each that I liked while putting my own spin on things. Below is a quick summary of modifications from these other two projects.

1. Using cron syntax for updating instead of a simple delay in seconds. This allows for more complex schedules, like not updating at night if you don't want to miss something.
2. Added analyzer to help with figuring out video play times
3. Pulling the exact framerate of the video insteading of hardcoding it - this fixed issues when the end of the video is close in calculating the timecode
4. Use seconds instead of frames for ```--start``` value. More intuitive
5. Added ```--end``` value to skip end credits
6. Added the ```-timecode``` value so you can see where you are in the video compared to "realtime" playing
7. Can use either a configuration (.conf) file or pass in arguments via CLI

## Problems With FFMPEG

One common problem when installed FFMPEG from source is that the libraries need to be manually added to your path in order to find the program. This can be done with the following command. It is a good idea to add that to your ```.bashrc``` file. When using cron you must also add this to the top of your cron file so it gets executed each time.

```
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/arm-linux-gnueabihf/:/usr/local/lib/
```

## Notes

The waveshare files are modified from the original repository: [https://github.com/waveshare/e-Paper](https://github.com/waveshare/e-Paper)
