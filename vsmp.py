#!/usr/bin/python
# -*- coding:utf-8 -*-

# *************************
# ** Before running this **
# ** code ensure you've  **
# ** turned on SPI on    **
# ** your Raspberry Pi   **
# ** & installed the     **
# ** Waveshare library   **
# *************************

import argparse, os, time, sys, random
from PIL import Image
import ffmpeg

# Ensure this is the correct import for your particular screen
from waveshare_epd import epd7in5_V2

# set path to ffmpeg
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'

def generate_frame(in_filename, out_filename, time, width, height):
    ffmpeg.input(in_filename, ss=time).filter('scale', width, height, force_original_aspect_ratio=1).filter('pad', width, height, -1, -1).output(out_filename, vframes=1).overwrite_output().run(capture_stdout=True, capture_stderr=True)

def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value

def save_position(file, pos):
    try:
        f = open(file, 'w')
        f.write(str(pos))
        f.close()
    except Exception:
        print('error writing file')

# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-f', '--file', type=check_mp4, required=True,
    help="File to grab screens of")
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

# setup the screen
epd = epd7in5_V2.EPD()

# Initialise and clear the screen
epd.init()
#epd.Clear()

grabFile = os.path.join(tmpDir,'grab.jpg')

print('Using %s' % args.file)
# Ensure this matches your particular screen
width = 800
height = 480

# Check how many frames are in the movie
frameCount = int(ffmpeg.probe(args.file)['streams'][0]['nb_frames'])

# Pick a random frame
frame = currentPosition

# Convert that frame to Timecode
msTimecode = "%dms"%(frame*41.666666)

# Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as grab.jpg
generate_frame(args.file, grabFile, msTimecode, width, height)

# Open grab.jpg in PIL
pil_im = Image.open(grabFile)

# Dither the image into a 1 bit bitmap (Just zeros and ones)
pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

# display the image
epd.display(epd.getbuffer(pil_im))
print('Diplaying frame %d of %s' % (frame,video_name))

# save the next position
currentPosition = currentPosition + float(args.increment)
if(currentPosition >= frameCount):
    # start over if we got to the end
    currentPosition = args.start

save_position(saveFile, currentPosition)

# NB We should run sleep() while the display is resting more often, but there's a bug in the driver that's slightly fiddly to fix. Instead of just sleeping, it completely shuts down SPI communication 
epd.sleep()
#epd7in5.epdconfig.module_exit()
exit()
