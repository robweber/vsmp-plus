#!/usr/bin/python
# -*- coding:utf-8 -*-
import argparse, os, time, sys, random
import ffmpeg

# set path to ffmpeg
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'

def time_to_play(frames, delay):
    # frames * delay = total minutes to play
    total = (frames * delay)/60

    if(total / 1440 > 1):
        return (total/1440, 'days')
    elif(total / 60 > 1):
        return (total/60, 'hours')
    else:
        return (total, 'minutes')

def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value

# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-f', '--file', type=check_mp4, required=True,
    help="File to grab screens of")
parser.add_argument('-d', '--delay',  default=120,
    help="Delay between screen updates, in seconds")
parser.add_argument('-i', '--increment',  default=4,
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', default=1,
    help="Start at a specific frame")

args = parser.parse_args()

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
    try:
        f = open(saveFile)
        for line in f:
            currentPosition = float(line.strip())
        f.close()
    except:
        print('error opening save file')

print('Analyzing %s' % args.file)
print('Start %s, Increment %s, Delay %s' % (args.start, args.increment, args.delay))

# Check how many frames are in the movie
frameCount = int(ffmpeg.probe(args.file)['streams'][0]['nb_frames'])

# divide total by increment to get total frames to display
framesToDisplay = frameCount/float(args.increment)

print('Total video will show %d out of %d frames' % (framesToDisplay, frameCount))

# find total time to play
time = time_to_play(framesToDisplay, float(args.delay))

print('It would take %f %s to play the whole video' % time)

# find time to play what's left
frameCount = frameCount - currentPosition
framesToDisplay = frameCount/float(args.increment)
time = time_to_play(framesToDisplay , float(args.delay))

print('It would take %f %s to play based on current position' % time)
exit()
