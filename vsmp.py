import argparse
import ffmpeg
import logging
import os
import utils
import fnmatch
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2  # ensure this is the correct import for your screen

# setup some helpful variables
DIR_PATH = os.path.dirname(os.path.realpath(__file__))  # full path to the directory of this script

# create the tmp directory if it doesn't exist
TMP_DIR = os.path.join(DIR_PATH, 'tmp')
if (not os.path.exists(TMP_DIR)):
    os.mkdir(TMP_DIR)

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


def find_video(args, lastPlayed, next=False):
    result = {}

    # if in file mode, just use the file name
    if(args.file is not None):
        result = args.file
    else:
        # we're in dir mode, use the name of the last played file
        if(lastPlayed != '' and not next):
            result['file'] = lastPlayed
        else:
            result['file'] = find_next_video(args.dir, lastPlayed)

    result['name'] = os.path.splitext(os.path.basename(result['file']))[0]  # video name, no ext

    # get some info about the video (frame rate, total frames, runtime)
    result['info'] = utils.get_video_info(result['file'])

    # modify the end frame, if needed
    result['info']['frame_count'] = result['info']['frame_count'] - utils.seconds_to_frames(args.end, result['info']['fps'])

    # find the saved position
    result['pos'] = float(utils.seconds_to_frames(args.start, result['info']['fps']))

    saveFile = os.path.join(TMP_DIR, result['name'] + '.txt')
    if(os.path.exists(saveFile)):
        result['pos'] = float(utils.read_file(saveFile))

    return result


def find_next_video(dir, lastPlayed):
    # list all files in the directory, filter on mp4
    fileList = sorted(fnmatch.filter(os.listdir(dir), '*.mp4'))

    index = 0

    # get the index of the last played file (if exists)
    try:
        index = fileList.index(os.path.basename(lastPlayed))
        index = index + 1  # get the next one

    except ValueError:
        index = 0  # just use the first one

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
group.add_argument('-d', '--dir', type=utils.check_dir,
                   help="Dir to play videos from (in order)")
parser.add_argument('-i', '--increment',  default=4,
                    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', default=1,
                    help="Number of seconds into the video to start")
parser.add_argument('-e', '--end', default=0,
                    help="Number of seconds to cut off the end of the video")
parser.add_argument('-t', '--timecode', action='store_true',
                    help='show the video timecode on the bottom of the display')

args = parser.parse_args()

lastPlayedFile = os.path.join(TMP_DIR, 'last_played.txt')

# setup the logger, log to tmp/log.log
logging.basicConfig(filename=os.path.join(TMP_DIR, 'log.log'), datefmt='%m/%d %H:%M',
                    format="%(levelname)s %(asctime)s: %(message)s",
                    level=getattr(logging, 'INFO'))

# set the video file information
video_file = find_video(args, utils.read_file(lastPlayedFile))

# setup the screen
epd = epd7in5_V2.EPD()

# Initialize the screen
epd.init()

grabFile = os.path.join(TMP_DIR, 'grab.jpg')

logging.info('Loading %s' % video_file['file'])

if(video_file['pos'] >= video_file['info']['frame_count']):
    # set 'next' to true to force new video file
    video_file = find_video(args, utils.read_file(lastPlayedFile), True)

# set the position we want to use
frame = video_file['pos']

# Convert that frame to ms from start of video (frame/fps) * 1000
msTimecode = "%dms" % (utils.frames_to_seconds(frame, video_file['info']['fps']) * 1000)

# Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as grab.jpg
generate_frame(video_file['file'], grabFile, msTimecode, width, height)

# Open grab.jpg in PIL
pil_im = Image.open(grabFile)

if(args.timecode):
    font18 = ImageFont.truetype(os.path.join(DIR_PATH, 'waveshare_lib', 'pic', 'Font.ttc'), 18)

    # show the timecode of the video in the format HH:mm:SS
    message = '%s' % utils.display_time(seconds=utils.frames_to_seconds(frame, video_file['info']['fps']),
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
logging.info('Diplaying frame %d (%d seconds) of %s' % (frame, utils.frames_to_seconds(frame, video_file['info']['fps']), video_file['name']))

# save the next position
video_file['pos'] = video_file['pos'] + float(args.increment)

if(video_file['pos'] >= video_file['info']['frame_count']):
    # save position of old video
    video_file['pos'] = args.start
    utils.write_file(os.path.join(TMP_DIR, video_file['name'] + '.txt'), video_file['pos'])

    # set 'next' to True to force new file
    video_file = find_video(args, utils.read_file(lastPlayedFile), True)
    logging.info('Will start %s on next run' % video_file)

# save the next position and last video played filename
utils.write_file(os.path.join(TMP_DIR, video_file['name'] + '.txt'), video_file['pos'])
utils.write_file(lastPlayedFile, video_file['file'])

epd.sleep()
exit()
