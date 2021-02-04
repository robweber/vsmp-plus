# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## 2021-02-04

### Fixed

- check that ```last_played.txt``` file value is contained in the video directory when using the ```--dir``` option before using the saved value. Fixes issues where the video was deleted or the program restarted with a new directory option

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
