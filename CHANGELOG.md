# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## 2021-02-16

### Added

- added ability to pause or resume the player via the web interface

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
