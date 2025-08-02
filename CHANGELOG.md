# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## 2025-07-02

### Fixed
- Pos now reset when starting a new file

### Added
- Image enhancement using PIL contrast & brightness settings for better
- Full screen images without black bars
- Startup messages now appear on RHS of screen, image on LHS
- QR Code on RHS of startup screen for config URL

## 2025-07-02

### Fixed
- Skipping blank frames did not advance. Changed logic of main loop in update_display and use new function to get ffmpeg to find the next non-black frame.

## 2025-05-31

### Fixed

- Seek fails due to config variable not being set (moved db read of config to beginning of execute_action in webapp.py
- Fix to seek commands being ignored (caused by data being over-written by update_display()) 
- Fix hour value in seek tooltip

## 2025-05-28

### Fixed

- title and ip settings not working in the Setup page area closes #13

## 2024-11-15

### Added

- added support for displaying images as well as video. Images can now be displayed from a directory of images and cycled on the cron schedule
- updated web UI to accommodate image and video modes

### Changed

- Pin croniter lib at version 3.0.3. Versions greater than this seem to have issues calculating proper next date values.

### Fixed

- minor syntax and spelling issues

## 2023-11-16

### Changed

- updated Install instructions for latest Raspberry Pi OS (12).
- utilize Python virtual environment instead of installing to system libraries
- layout of README for better readability and compatibility with the [README Standard](https://github.com/RichardLitt/standard-readme)

### Remove

- removed manual FFMPEG build instructions. No longer needed as apt libraries work just fine

## 2023-09-15

### Fixed

- added try/except around FFMPEG call so returned errors can be logged

## 2023-06-26

### Added

- new `/api/screenshot` API call to stream image currently displayed on EPD
- added screenshot page to web interface that mirrors image shown on screen

### Changed

- renamed __Status__ to __Controls__ in menu to better reflect use

## 2023-06-07

### Changed

- the additional display options are now listed as `title - timecode (ip)` instead of `(ip) title - timecode` for better readability

### Fixed

- fixed `textsize()` deprecation and removal planned for [Pillow 10](https://pillow.readthedocs.io/en/stable/deprecations.html#font-size-and-offset-methods). Using `textbbox()` instead.

## 2023-05-31

### Fixed

- issue with the file browser when at the root `/` of the filesystem

## 2023-02-10

### Fixed

- fixed issue with file system browser where no path would be returned if the initial path was non existent (video files deleted)

## 2022-02-25

### Removed

- removed conversion to BW image in `vsmp.py` - let the EPD driver do this

## 2021-11-23

### Added

- new setting Skip Blank Frames uses [Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.getbbox) to check if frame is all black and tries to get the next one
- display timecode on progress slider on homepage (HH:MM:SS)

## 2021-08-13

### Added

- added dependency to vsmp service file, the service now depends on redis and will wait for it to be available

## 2021-07-06

### Added

- if IP changes while running toggle IP display setting so it shows visually, prevents DHCP from creating a lost player

## 2021-06-02

### Changed

- use `v` to select the video stream only with `ffmpeg.probe()`

## 2021-05-05

### Added

- added support for additional video formats, AVI, MKV, M4V, and MOV
- added configuration option for a startup screen on first boot
- added `last_run` as part of player status, used to calculate if an update was missed when sign was missing and force update on startup

### Removed

- removed fnmatch dependency, use python `filter` method instead

## 2021-04-27

### Added

- added OS dependency for [Free Fonts](http://savannah.gnu.org/projects/freefont/) instead of using waveshare bundled font

### Removed

- removed requirement to clone Waveshare lib manually

## 2021-04-21

### Changed

- `vsmp-epd` rebranded to `omni-epd`

## 2021-04-15

### Added

- added `vsmp-epd` as dependency for abstracting displays, multiple displays now supported

### Changed

- added `--epd` command line argument to pass in valid EPD driver name to load

## 2021-04-14

### Added

- added install.sh script

### Changed

- updated Install file with current instructions

## 2021-04-08

### Changed

- changed logging behavior, console logging enabled when in debug mode and web server logging disabled when not in debug mode (stop spamming journal)

### Fixed

- changed path to Font files to match new location of waveshare repository

## 2021-04-07

### Removed

- Don't need waveshare lib any more in this repo, modified instructions to build from source

## 2021-04-05

### Added

- added flake8 syntax check via Github Actions

### Changed

- updated all python code to be pep8 compatible

## 2021-04-01

### Changed

- use f-strings instead of % formatting

## 2021-03-29

### Added

- added API examples to README

## 2021-03-22

### Added

- added API endpoint ```/api/browse_files/<path>``` to return a listing of files and folders in a given directory
- using browse_files endpoint added file browser to setup and analyzer pages instead of having to type full path to files/folders
- tooltip showing percent on seek bar to eliminate guesswork when clicking

### Fixed

- fixed issue in calculating percent for seeking. Need to use jquery offset() function to get correct values

## 2021-03-11

### Fixed

- fixed issue with analyzer where Remaining Time To Play wasn't loading current position of video correctly

## 2021-02-22

### Added

- added Device IP as a valid display option as part of the configuration. Helpful when trying to find the device on the network.
- when no video loaded display message with address of web management page on display
- player status (paused or running) included as part of ```/api/status``` command
- show next run time as part of ```/api/status```
- include next run time on web display
- use boot strap icons to show some icons in various areas

### Fixed

- fixed crash when no video file loaded due to empty directory or bad file location
- error when setting up player status on first run
- use title tag instead of name tag for video title display, this is pulled from meta data

## 2021-02-20

### Fixed

- fixed button toggle on "pause" in ```index.html``` file
- added natsort to help with sorting videos better in a directory

## 2021-02-19

### Added

- added redis-server and the python redis library as dependencies
- added ```/api/control/next``` and ```/api/control/prev``` functions. These will allow you to advance through videos when in directory mode
- added buttons to web interface for prev and next when in directory mode
- support for seeking to a specific point in a video file using the ```/api/control/seek``` endpoint
- new configuration setting ```allow_seek```. Will toggle the ability to seek in the web interface to avoid seeking on accident

### Changed

- moved the current program status, last played file status, and player configuration options to redis instead of flat files. This should help reduce read/writes to the SD filesystem
- made the program "paused" by default on first run. This gives the user a chance to edit settings before starting
- return some generic "no file loaded" messaging if requesting status and no last played file information
- separated the "find video" logic into it's own class so it can be reused elsewhere

### Removed

- removed saving individual video information files. These weren't read in for any real reason any more since the last played status had everything needed

## 2021-02-18

### Changed

- moved files to ```modules``` directory to keep local python source files a bit cleaner
- changed menu to separate player from analyzer controls

### Removed

- removed legacy ```analyze.py``` file as it has been merged into the web service

## 2021-02-17

### Added

- can update settings from web interface via ```/api/configuration``` API call
- added ```-D``` arg to toggle debug logging on/off
- config validation now handles checking for int values as well
- converted ```analyze.py``` file to add functionality to web interface

### Changed

- updated README with info on the new CLI args, web service, and API endpoints

## 2021-02-16

### Added

- added ability to pause or resume the player via the web interface

### Changed

- updated bootstrap version to 4.3.1 and updated web app theme
- fixed percent complete calculation, was done prior to loading current position resulting in incorrect percent value

## 2021-02-14

### Added

- added ability to POST values to ```/api/configuration``` and update configuration
- added setup web page to view current configuration values (no update yet)
- added ```running``` key to config.json file. When set to false will pause the program, even if update time is triggered

## 2021-02-13

### Added

- added ```percent_complete``` key in the status .json files, can be returned with status endpoint

### Fixed

- fixed error when no last_played.json file existed, how handled correctly

## 2021-02-12

### Added

- added ability to refresh config while program is running. Adjustments to ```config.json``` file will update config without program restart

### Changed

- changed arguments to main ```vsmp.py``` file. Only webserver port is given as an argument. Other parameters are either defaults or pulled from ```tmp/config.json```

## 2021-02-11

### Added

- added Flask based web service with some basic endpoints. will eventually allow for on the fly program control

### Changed

- moved some global values to the utils file to be used more generally

## 2021-02-04

### Changed

- save file information as a JSON object instead of just the positional information
- dump all file info to ```last_played.json``` and reload this when continuing the same file instead of re-probing the file each time

### Fixed

- check that ```last_played``` file value is contained in the video directory when using the ```--dir``` option before using the saved value. Fixes issues where the video was deleted or the program restarted with a new directory option

## 2021-02-03

### Added

- Added ability to extract title information from the video file, if it exists

### Changed

- changed ```-t``` to ```-D``` (display). This allows for displaying the video title, timecode or both through the use of ```-D title timecode``` or just ```-D timecode``` as examples

## 2020-12-29

### Added

- added ability to pass in .conf file with ```-c``` arg

### Changed

- updated Install document
- use [configargparse](https://pypi.org/project/ConfigArgParse/) library instead of argparse as found in the @missionfloyd branch
- changed ```-d``` arg  to ```-D``` so both analyze and vsmp file args match


## 2020-12-28

### Added

- license - [GPLv3](https://github.com/robweber/vsmp-plus/blob/master/LICENSE)
- pictures of working version in frame

### Changed

- updated loading of EPD driver as defined in original SlowMovie branch V2
- pull screen height/width from the EPD driver now

### Fixed

- removed black rectangle from top of screen, leftover from testing
- fixed ```epd.sleep()``` method as defined in the SlowMovie branch V2


## Older

Modifications made before start of changelog can be found in the commit history.
