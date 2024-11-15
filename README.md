# VSMP+ (Very Slow Media Player Plus)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg)](https://github.com/RichardLitt/standard-readme)

This project is one of many Very Slow Media Player projects floating around the internet. VSMP+ will display both image files and video frames on an e-ink display utilizing a web interface for playback control.

## Background

I read an [article by Tom Whitwell](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4), detailing his process for creating a slow media player using e-paper and a Raspberry Pi 4. His project was in turn inspired by a [2018 article by Bryan Boyer](https://medium.com/s/story/very-slow-movie-player-499f76c48b62) about the same thing. Both of these were very simple, yet visually stunning and led me to create my own version of an e-ink media player.

Both of the reference articles had pieces I liked and pieces I wanted to enhance about them. This particular project takes the strengths of their ideas and adds a few "ease of use" elements. The biggest of these is the ability to specify different displays and a built in web service to control file selection and playback. Once setup you shouldn't need CLI access to modify any parameters or change running files.

![](https://github.com/robweber/vsmp-plus/blob/master/pics/front_with_timecode.jpg)

## Table Of Contents

- [Install](#install)
  - [Display Hardware](#display-hardware)
- [Usage](#usage)
  - [Config File](#config-file)
- [Web Interface](#web-interface)
  - [Finding Timings](#finding-timings)
- [REST API](#rest-api)
- [Differences/Additions](#differencesadditions)
- [Contributing](#contributing)
- [License](#license)


## Install

For detailed installation instructions read the [Install](https://github.com/robweber/vsmp-plus/blob/master/INSTALL.md) document. An [install script](https://raw.githubusercontent.com/robweber/vsmp-plus/master/setup/install.sh) is also available in the `setup` directory.

### Display Hardware

Display hardware is a big choice for this project. I used the [Waveshare 7.5in E-ink display](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm). Using the `--epd` argument from above you can specify any display that works with the [EPD abstraction library](https://github.com/robweber/omni-epd). This allows dynamic loading of different display types depending on what you've purchased. You can see [an exhaustive list](https://github.com/robweber/omni-epd#displays-implemented) here. In general, most Waveshare displays are compatible.

## Usage
Once the requirements are in place the program itself is contained in the ```vsmp.py``` file. This file can take a few arguments, but doesn't need any to run normally:

* ```--config``` - path to a config file where any CLI arguments can be specified, useful for when running as a service
* ```--port``` - the port the web server will run on, default is 5000
* ```--epd``` - the e-ink display driver to use. Valid displays can be [found here](https://github.com/robweber/vsmp-epd/blob/main/README.md). __waveshare_epd.epd7in5_V2__ is the default.
* ```--debug``` - when this flag is given the program will run in debug mode

Once started, either with the CLI or as a service, the program will start and the web service will be active. The display should also show a startup page that prompts you to continue setup. Load the web interface to continue setup at http://IP:5000. To monitor the progress of the program you can watch the log file using the command:

```
# from the vsmp-plus directory
tail -f tmp/log.log
```

### Config File

Instead of passing in all the arguments on the command line you can also create a config file and pass in your values with the ```-c``` option instead. There is a sample of this file in the ```setup/``` directory. Any command line argument can be specified in the file.

```

# Example Config file
port = 8080

```

## Web Interface

The program runs an embedded web server to control the program status and set additional parameters. The main page will show you the currently playing file and allow you to pause or resume the configured schedule. This is helpful if you wish to pause things and remove a USB stick to add more files without having to shut down the entire Raspberry Pi. When first run the player will be paused so you can change the settings to correct values. If running in directory mode you can also click the Next or Prev to cycle through files in the directory. If the file type is a video file, clicking on the progress bar will seek the video to that percentage. This can be disabled on the setup page if unwanted.

![](https://github.com/robweber/vsmp-plus/blob/master/pics/web_server_player_status.png)

The Player Setup page allows for the configuration of more specific parameters. This can be saved and will take effect without a program reboot. Settings do take about 1 min for the program to reload the config. Some settings only affect specific media types.

__General__
* Show Startup Screen - enables or disables the display of a startup screen when VSMP+ starts.

__Media__
* Media - media types can be either __images__ or __video__
* Mode - File mode will play a single file whereas directory mode will play all the files in a given directory. This must be local to the Raspberry Pi.
* Path - The absolute path to either the file or the directory
* Update Time - how often to update the display, this is given as a [cron expression](http://en.wikipedia.org/wiki/Cron)

__Image Options__
* Image Rotation - order to display the images. Default is In Order as sorted alphabetically. Choosing Random will randomly select an image from the directory.
* Display - optionally show the image filename and/or the device IP on the bottom of the display. The device IP will automatically toggle itself on if the IP address of the system changes while the player is running. This helps prevents a "lost" player on the network due to DHCP.

__Video Options__
* Start time skip - the number of seconds into the video to start, if you want to skip into the video X amount
* End time skip - the number of seconds to cut off the end of the video, useful for skipping credit sequences
* Display - optionally show any combination of the title, timecode of the frame being displayed, or the device IP on the bottom of the display. Time in the form of HH:mm:SS. The device IP will automatically toggle itself on if the IP address of the system changes while the player is running. This helps prevents a "lost" player on the network due to DHCP.
* Allow Seeking - this will enable or disable seeking when clicking on the progress bar in the web interface. Useful to disable if this is happening on accident.
* Skip Blank Frames - when enabled frames that are all black (blank) will not be displayed. Useful for black screens at the start, end, or even middle of video files.

Once applied the given cron expression will be used to update the display on a schedule. The log file for the program is stored in the `tmp` directory, which is created the first time the program is run. Information related to the current player status and configuration is stored in a Redis database.

## Images

A new image will display every time the cron schedule executes. These will either be _In Order_ or _Random_ depending on the Image Rotation option selected on the Setup page. If displaying images In Order you can also cycle through them using the Prev and Next buttons on the web interface. Pressing either one will skip one image forward or backwards on the next update. Hitting the buttons successively will skip multiple images on the next update.

## Videos

When playing video playback will start at the `start` frame of the video. The image will be displayed and then status information, specific to the video file, will be written to the database with the next frame to display. At each update time the database will be checked and the next frame will be displayed. Subsequent runs will continue to move forward by the `increment` amount. If the video ends it will start over at the `start` frame again. If reading from a directory it will start the next video.

### Finding Video Timings

Once the program was up and running, one thing that was very hit/miss was what exactly the input parameters for video be to achieve the desired effect. Did I want the video to take days, weeks, or months to display? What combination of increments and delays would get the effect I wanted? Using the Analyze menu item you can test parameters and see what happens with a given file, or set of files.

By default the analyze program loads the current settings. These can be tweaked without altering the main player that is running. Using the inputs the video is analyzed and some information is displayed regarding projected play times. Tweaking the configuration values you can find the optimum settings to get your desired play time. Each video will display separately, with a summary at the end. When looking at a whole directory the program will use the position of the currently playing file and analyze from this point forward.

## REST API

The built in web server uses a few API endpoints to function. These can be utilized by other programs as well if you wish to automate the sign with other systems or scripts. The endpoints available are:

### /api/configuration [GET, POST]
This returns the current configuration as a JSON object. Using a POST request you can update data, with settings like the file paths and cron expression being verified. Responses will include a success or failure of the update.

__Example__

```
curl http://localhost:5000/api/configuration

{
  "media": "video",
  "allow_seek": false,
  "display": ["timecode"],
  "end": 300,
  "image_rotation": "in_order",
  "increment": 50,
  "mode": "dir",
  "path": "/media/usb/Videos",
  "start":100,
  "update":"*/5 7-15 * * 1-5",
  "show_startup": true,
  "skip_blank": false
}

```

### /api/control/{{action}} [POST]
Initiate a player control action. Valid actions at this time are <b>resume</b>, <b>pause</b>, <b>next</b>, <b>prev</b>, and <b>seek</b>. Note that next and prev functions will return an error when not in directory mode. Seeking requires an additional parameter in the POST body: `{amount: percent}` where the percentage is a whole number 0-100.

__Examples__

```
# Pause Play
curl http://localhost:5000/api/action/pause

{
  "action": "pause",
  "message": "Action pause executed",
  "success": true
}

# Seek
curl http://localhost:5000/api/control/seek -d '{"amount": 20}' -X POST
{
  "action":"seek",
  "data": ...same as /api/status...,
  "message": "Seeking to  20.00 percent on next update",
  "success":true
}
```

### /api/status [GET]

Returns the current status of the sign as a JSON object. This includes information about the currently playing file like it's media type, title, file path, and percent complete. The `pos` key value is the current frame being displayed.

__Example__
```
curl http://localhost:5000/api/status

{
  "file": "/media/usb/Videos/Path.To.Video.mp4",
  "info":  {
    "fps": 29.97,
    "frame_count": 60725.0,
    "runtime": 2326.192859526193,
    "title":"Friendly Name of Video"
   },
   "player": {
     "last_run": 1620242760.1,
     "next_run": 1620242880.0,
     "running": true
   },
  "media": "video",
  "name": "Video.File.Name.No.Ext",
  "percent_complete": 20.5,
  "pos": 12145.0
}
```

### /api/screenshot [GET]

Returns the currently displayed image on the EPD. This is a binary PNG file. Can be saved directly via something like `curl` or embedded in another web application.

### /api/analyze [POST]

Takes the same parameters as the ```/api/configuration``` POST method, however this will run the analyzer on the proposed configuration. The response includes a break down of each video analyzed.

### /api/browse_files/{{path}} [GET]

Returns a list of directories and files within the given file path. Files are filtered to include only valid video files. Used by the web interface file browser. The user running the `vsmp.py` file must have READ access to the directories to list them.

__Example__

```
curl http://localhost:5000/api/browse_files/media/usb/Videos

{
  "dirs":[
    "Dir 1",
    "Dir 2"
  ],
  "files": [
    "Video.File.1.mp4",
    "Video.File.2.mp4"
  ],
  "path": "/media/usb/Videos",
  "success": true
}

```

## Differences/Additions

I mentioned two other versions of this type of project that I took inspiration from when creating this one. I tried to combine pieces of each that I liked while putting my own spin on things. Below is a quick summary of differences from other implementations. This may be overkill for some users, and if so checkout one of the other great VSMP projects.

1. Using cron syntax for updating instead of a simple delay in seconds. This allows for more complex schedules, like not updating at night if you don't want to miss something.
2. Added analyzer to help with figuring out video play times
3. Use seconds instead of frames for `--start` value. More intuitive
4. Added `--end` value to skip end credits
5. Adding display options so you can see where the title of the video and/or the timecode for the frame displayed
6. Added a built in web service for controlling the sign so more can be done without the CLI or restarting the service directly
7. Use a Redis database to store information rather than a host of flat files. This should help limit reads/writes to the Raspberry PI SD card
8. Added ability to jump to a specific time in the video (via web UI)
9. Added blank frame (black screen) detection
10. Added an abstraction library to load multiple types of e-ink displays
11. Allowing the display of either images or videos controlled via the setup screen

## Contributing

PRs accepted! If there a fix for any of the documentation or something is not quite clear, please [point it out](https://github.com/robweber/vsmp-plus/issues). I made this mostly for fun to get experience with libraries I wasn't very familiar with. Not really looking to enhance it too far from where it is but definitely want to keep it functional as dependencies change.


## License

[MIT](/LICENSE)
