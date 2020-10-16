#!/usr/bin/python
# -*- coding:utf-8 -*-
import argparse, logging, os, time, sys, random, utils

# set path to ffmpeg
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'

# found this on https://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-hours-and-days
intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)

def display_time(seconds, granularity=3):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])

def time_to_play(total_frames, increment, delay):
    # find out how many frames will display
    frames = total_frames/increment

    print('%d out of %d frames will display' % (frames, total_frames))

    # frames * delay = total minutes to play
    total = (frames * delay)

    print('Video will take %s to fully play' % display_time(total))


# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-f', '--file', type=utils.check_mp4, required=True,
    help="File to analyze")
parser.add_argument('-d', '--delay',  default=120,
    help="Delay between screen updates, in seconds")
parser.add_argument('-i', '--increment',  default=4,
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', default=1,
    help="Start at a specific frame")

args = parser.parse_args()

logging.basicConfig(datefmt='%m/%d %H:%M', format="%(asctime)s: %(message)s", level=getattr(logging, 'INFO'))

# run ffmpeg.probe to get the frame rate and frame count
videoInfo = utils.get_video_info(args.file)

# print some initial information
print('Analyzing %s' % args.file)
print('Starting Frame: %s, Frame Increment: %s, Delay between updates: %s' % (args.start, args.increment, args.delay))
print('Video framerate is %ffps, total video is %f minutes long' % (videoInfo['fps'], videoInfo['runtime']/60))
print('')

# setup some helpful variables
dir_path = os.path.dirname(os.path.realpath(__file__)) # full path to the directory of this script
video_name = os.path.splitext(os.path.basename(args.file))[0] # video name, no ext

# create the tmp directory if it doesn't exist
tmpDir = os.path.join(dir_path, 'tmp')
if (not os.path.exists(tmpDir)):
    os.mkdir(tmpDir)

# check if we have a "save" file
currentPosition = float(args.start)
saveFile = os.path.join(tmpDir,video_name + '.txt')
if( os.path.exists(saveFile)):
    currentPosition = float(utils.read_file(saveFile))

# find total time to play entire movie
print('Entire Video:')
time = time_to_play(videoInfo['frame_count'], float(args.increment), float(args.delay))
print('')


# find time to play what's left
print('Remaining Video:')
time = time_to_play(videoInfo['frame_count'] - currentPosition, float(args.increment), float(args.delay))
print('')

# figure out how many 'real time' minutes per hour
secondsPerIncrement = float(args.increment)/videoInfo['fps']
framesPerSecond = secondsPerIncrement/float(args.delay) # this is how many "seconds" of film actually shown per second of realtime

minutesPerHour = (framesPerSecond * 60)
print('Minutes of film displayed breakdown:')
print('%f minutes of film per hour' % (minutesPerHour))
print('%f minutes of film per day' % (minutesPerHour * 24))

exit()
