# VSMP+ (Very Slow Media Player Plus)
I read an [article by Tom Whitwell](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), detailing his process for creating a slow media player using e-paper and a Raspberry Pi 4. His project was in turn inspired by a [2018 article by Bryan Boyer](https://medium.com/s/story/very-slow-movie-player-499f76c48b62) about the same thing. Both of these were very simple, yet visually stunning and led me to create my own version of this project.

Both of the reference articles had pieces I liked and pieces I wanted to enhance about them. That is what this project seeks to do. Combing piece of both of them I ended up with the following, which is both the same and different from their designs.

![](https://github.com/robweber/vsmp-plus/blob/master/pics/front_with_timecode.jpg)

## Basic Usage
Once the requirements are in place (See Install document) the program itself is contained in the ```vsmp.py``` file. This file can take a few arguments, but doesn't need any to run normally:

* ```--config``` - path to a config file where any CLI arguments can be specified, useful for when running as a service
* ```--port``` - the port the web server will run on, default is 5000
* ```--debug``` - when this flag is given the program will run in debug mode

Once started, either with the CLI or as a service, the program will start and the webservice will be active. You can load the web page to continue setup at http://IP:5000. To monitor the progress of the program you can watch the log file using the command:

```
# from the vsmp-plus directory
tail -f tmp/log.log
```

## Web Server

The program runs an embedded web server to control the program status and set additional parameters. The main page will show you the currently playing file and allow you to pause or resume the configured schedule. This is helpful if you wish to pause things and remove a USB stick to add more files without having to shut down the entire Raspberry Pi. The Player Setup page allows for the configuration of more specific parameters. This can be saved and will take effect without a program reboot. Settings do take about 1 min for the program to reload the config.

* Mode - File mode will play a single file whereas directory mode will play all the files in a given directory. This must be local to the Raspberry Pi.
* Path - The absolute path to either the file or the directory
* Update Time - how often to update the display, this is given as a [cron expression](http://en.wikipedia.org/wiki/Cron)
* Start time skip - the number of seconds into the video to start, if you want to skip into the video X amount
* End time skip - the number of seconds to cut off the end of the video, useful for skipping credit sequences
* Display - optionally show the title, timecode of the frame being displayed, or both on the bottom of the display. Time in the form of HH:mm:SS.

Once applied the given cron expression will be used to update the display starting at the ```start``` frame of the video. The image will be displayed and then a save file will be created, specific to this video file, with the next frame to display. At each update time the save file will be read and the next frame will be displayed. Subsequent runs will continue to move forward by the ```increment``` amount. If the video ends it will start over at the ```start``` frame again. If reading from a directory it will start the next video. The save file and log file for the program are both stored in the ```tmp``` directory, which is created the first time the program is run.

## Find Timing
Once the program was up and running, one thing that was very hit/miss was what exactly the input parameters should be for my desired effect. Did I want the video take days, weeks, months to display? What combination of increments and delays would get the effect I wanted? Using the Analyze menu item you can test parameters and see what happens with a given file, or set of files.

By default the analyze program loads the current settings. These can be tweaked without altering the main player that is running. Using the inputs the video is analyzed and some information is displayed regarding projected play times. Tweaking the configuration values you can find the optimum settings to get your desired play time. Each will video will display separately, with a summary at the end. When looking at a whole directory the program will assume the current value of the ```last_played.json``` file is the currently running file and analyze from this point forward.

## REST API

The built in web server uses a few API endpoints to function. These can be utilized by other programs as well if you wish to automate the sign with other systems or scripts. The endpoints available are:

* /api/configuration [GET, POST] - returns the current configuration as a JSON object. Using a POST request you can update data, with settings like the file paths and cron expression being verified. Responses will include a success or failure of the update.
* /api/control/{{action}} [POST] - initiate a control action. Valid actions at this time are <b>resume</b> or <b>pause</b>.
* /api/status [GET] - returns the current status of the sign as a JSON object. This includes information about the currently playing video like it's title, file path, and percent complete.
* /api/analyze [POST] - takes the same parameters as the /api/configuration POST method, however this will run the analyzer on the proposed configuration. The response includes a break down of each video analyzed.

## Config File

Instead of passing in all the arguments on the command line you can also create a config file and pass in your values with the ```-c``` option instead. There is a sample of this file in the ```setup/``` directory. Any command line argument can be specified in the file.

```

# Example Config file
port = 8080

```

## Differences/Additions

I mentioned two other versions of this type of project that I took inspiration from when creating this one. I tried to combine pieces of each that I liked while putting my own spin on things. Below is a quick summary of modifications from these other two projects.

1. Using cron syntax for updating instead of a simple delay in seconds. This allows for more complex schedules, like not updating at night if you don't want to miss something.
2. Added analyzer to help with figuring out video play times
3. Pulling the exact framerate of the video instead of hardcoding it - this fixed issues when the end of the video is close in calculating the timecode
4. Use seconds instead of frames for ```--start``` value. More intuitive
5. Added ```--end``` value to skip end credits
6. Added the ```-display``` value so you can see where the title of the video and/or the timecode for the frame displayed
7. Can use either a configuration (.conf) file or pass in arguments via CLI
8. Added a built in web service for controlling the sign so more can be done without the CLI or restarting the service directly

## Problems With FFMPEG

One common problem when installed FFMPEG from source is that the libraries need to be manually added to your path in order to find the program. This can be done with the following command. It is a good idea to add that to your ```.bashrc``` file. When using cron you must also add this to the top of your cron file so it gets executed each time.

```
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/arm-linux-gnueabihf/:/usr/local/lib/
```

## Notes

The waveshare files are modified from the original repository: [https://github.com/waveshare/e-Paper](https://github.com/waveshare/e-Paper)
