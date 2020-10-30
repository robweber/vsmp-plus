import argparse
import ffmpeg
import logging
import os
import utils
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2  # ensure this is the correct import for your screen

# setup some helpful variables
dir_path = os.path.dirname(os.path.realpath(__file__))  # full path to the directory of this script

# create the tmp directory if it doesn't exist
tmpDir = os.path.join(dir_path, 'tmp')
if (not os.path.exists(tmpDir)):
    os.mkdir(tmpDir)

# Modify these to match your particular screen
width = 800
height = 480


def generate_frame(in_filename, out_filename, time, width, height):
    ffmpeg.input(in_filename, ss=time) \
          .filter('scale', width, height, force_original_aspect_ratio=1) \
          .filter('pad', width, height, -1, -1) \
          .output(out_filename, vframes=1) \
          .overwrite_output() \
          .run(capture_stdout=True, capture_stderr=True)


def check_dir(value):
    if(not os.path.exists(value) and not os.path.isdir(value)):
        raise argparse.ArgumentTypeError("%s is not a directory" % value)
    return value


def find_video(args, lastPlayed):
    result = {}

    # if in file mode, just use the file name
    if(args.file is not None):
        result = args.file
    else:
        # we're in dir mode, use the name of the last played file
        if(lastPlayed != ''):
            result['file'] = lastPlayed
        else:
            result['file'] = find_next_video(args.dir, lastPlayed)

    result['name'] = os.path.splitext(os.path.basename(result['file']))[0] #video name, no ext
    return result


def find_next_video(dir, lastPlayed):
    # list all files in the directory
    fileList = os.listdir(dir)

    index = 0  # assume we'll just use the first video
    if(lastPlayed != ''):
        for aFile in fileList:
            index = index + 1
            if(aFile == os.path.basename(lastPlayed)):
                break

    # go back to start of list if we got to the end
    if(index >= len(fileList)):
        index = 0

    # return this video
    return os.path.join(dir, fileList[index])


# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Settings')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-f', '--file', type=utils.check_mp4,
                   help="File to grab screens of")
group.add_argument('-d', '--dir', type=check_dir,
                   help="Dir to play videos from (in order)")
parser.add_argument('-i', '--increment',  default=4,
                    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', default=1,
                    help="Start at a specific frame")
parser.add_argument('-t', '--timecode', action='store_true',
                    help='show the video timecode on the bottom of the display')

args = parser.parse_args()

lastPlayedFile = os.path.join(tmpDir, 'last_played.txt')

# setup the logger, log to tmp/log.log
logging.basicConfig(filename=os.path.join(tmpDir, 'log.log'), datefmt='%m/%d %H:%M',
                    format="%(levelname)s %(asctime)s: %(message)s",
                    level=getattr(logging, 'INFO'))

# set the video file information
video_file = find_video(args, utils.read_file(lastPlayedFile))

# check if we have a "save" file
currentPosition = float(args.start)
saveFile = os.path.join(tmpDir, video_file['name'] + '.txt')
if(os.path.exists(saveFile)):
    currentPosition = float(utils.read_file(saveFile))

# setup the screen
epd = epd7in5_V2.EPD()

# Initialize the screen
epd.init()

grabFile = os.path.join(tmpDir, 'grab.jpg')

logging.info('Loading %s' % video_file['file'])

# get some info about the video (frame rate, total frames, runtime)
videoInfo = utils.get_video_info(video_file['file'])

if(currentPosition >= videoInfo['frame_count']):
    video_file = find_video(args, utils.read_file(lastPlayedFile))
    currentPosition = args.start  # in case we went over the frame count

# set the position we want to use
frame = currentPosition

# Convert that frame to ms from start of video (frame/fps) * 1000
msTimecode = "%dms" % ((frame/videoInfo['fps']) * 1000)

# Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as grab.jpg
generate_frame(video_file['file'], grabFile, msTimecode, width, height)

# Open grab.jpg in PIL
pil_im = Image.open(grabFile)

if(args.timecode):
    font18 = ImageFont.truetype(os.path.join(dir_path, 'waveshare_lib', 'pic', 'Font.ttc'), 18)

    # show the timecode of the video in the format HH:mm:SS
    message = '%s' % utils.display_time(seconds=frame/videoInfo['fps'],
                                        granularity=3,
                                        timeFormat='{value:02d}',
                                        joiner=':',
                                        show_zeros=True,
                                        intervals=utils.intervals[2:])

    # get a draw object
    draw = ImageDraw.Draw(pil_im)
    draw.rectangle((width/2-100, 0, width/2+100, 20), fill=(0, 0, 0))
    tw, th = draw.textsize(message)  # gets the width and height of the text drawn

    # draw timecode, centering on the middle
    draw.text(((width-tw)/2, height-20), message, font=font18, fill=(255, 255, 255))

# Dither the image into a 1 bit bitmap (Just zeros and ones)
pil_im = pil_im.convert(mode='1', dither=Image.FLOYDSTEINBERG)

# display the image
epd.display(epd.getbuffer(pil_im))
logging.info('Diplaying frame %d (%d seconds) of %s' % (frame, frame/videoInfo['fps'], video_file['name']))

# save the next position
currentPosition = currentPosition + float(args.increment)
if(currentPosition >= videoInfo['frame_count']):
    video_file = find_video(args, utils.read_file(lastPlayedFile))
    logging.info('Will start %s on next run' % video_file)

    # start over if we got to the end
    currentPosition = args.start

# save the next position and last video played filename
utils.write_file(saveFile, currentPosition)
utils.write_file(lastPlayedFile, video_file['file'])

epd.sleep()
exit()
