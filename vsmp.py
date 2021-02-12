
import configargparse
import ffmpeg
import logging
import os
import utils
import fnmatch
import signal
import sys
import time
import threading
import webapp
from croniter import croniter
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2 as epd_driver  # ensure this is the correct import for your screen

# create the tmp directory if it doesn't exist
if (not os.path.exists(utils.TMP_DIR)):
    os.mkdir(utils.TMP_DIR)

# pull width/height from driver
width = epd_driver.EPD_WIDTH
height = epd_driver.EPD_HEIGHT


# function to handle when the is killed and exit gracefully
def signal_handler(signum, frame):
    logging.info('Exiting Program')
    epd_driver.epdconfig.module_exit()
    sys.exit(0)


def generate_frame(in_filename, out_filename, time):
    ffmpeg.input(in_filename, ss=time) \
          .filter('scale', 'iw*sar', 'ih') \
          .filter('scale', width, height, force_original_aspect_ratio=1) \
          .filter('pad', width, height, -1, -1) \
          .output(out_filename, vframes=1) \
          .overwrite_output() \
          .run(capture_stdout=True, capture_stderr=True)


def analyze_video(args, file):
    # save full path plus filename with no ext
    result = {"file": file, 'name': os.path.splitext(os.path.basename(file))[0]}

    # get some info about the video (frame rate, total frames, runtime)
    result['info'] = utils.get_video_info(file)

    # modify the end frame, if needed
    result['info']['frame_count'] = result['info']['frame_count'] - utils.seconds_to_frames(args.end, result['info']['fps'])

    # find the saved position
    result['pos'] = float(utils.seconds_to_frames(args.start, result['info']['fps']))

    saveFile = os.path.join(utils.TMP_DIR, result['name'] + '.json')
    if(os.path.exists(saveFile)):
        savedData = utils.read_json(saveFile)
        result['pos'] = float(savedData['pos'])

    return result


def find_video(args, lastPlayed, next=False):
    result = {}

    # if in file mode, just use the file name
    if(args.file is not None):
        if(args.file == lastPlayed['file']):
            result = lastPlayed
        else:
            result = analyze_video(args, args.file)
    else:
        # we're in dir mode, use the name of the last played file if it exists in the directory
        if('file' in lastPlayed and os.path.basename(lastPlayed['file']) in os.listdir(args.dir) and not next):
            # use information loaded from last played file
            result = lastPlayed
        else:
            result = analyze_video(args, find_next_video(args.dir, lastPlayed['file']))

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


def update_display(args, epd):
    # Initialize the screen
    epd.init()

    # set the video file information
    video_file = find_video(args, utils.read_json(utils.LAST_PLAYED_FILE))

    # save grab file in memory as a bitmap
    grabFile = os.path.join('/dev/shm/', 'frame.bmp')

    logging.info('Loading %s' % video_file['file'])

    if(video_file['pos'] >= video_file['info']['frame_count']):
        # set 'next' to true to force new video file
        video_file = find_video(args, utils.read_json(utils.LAST_PLAYED_FILE), True)

    # set the position we want to use
    frame = video_file['pos']

    # Convert that frame to ms from start of video (frame/fps) * 1000
    msTimecode = "%dms" % (utils.frames_to_seconds(frame, video_file['info']['fps']) * 1000)

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it in memory
    generate_frame(video_file['file'], grabFile, msTimecode)

    # Open grab.jpg in PIL
    pil_im = Image.open(grabFile)

    if(args.display):
        font18 = ImageFont.truetype(os.path.join(utils.DIR_PATH, 'waveshare_lib', 'pic', 'Font.ttc'), 18)

        message = '%s %s'
        title = ''
        timecode = ''

        if('title' in args.display):
            title = video_file['info']['title']

        if('timecode' in args.display):
            # show the timecode of the video in the format HH:mm:SS
            timecode = utils.display_time(seconds=utils.frames_to_seconds(frame, video_file['info']['fps']),
                                          granularity=3,
                                          timeFormat='{value:02d}',
                                          joiner=':',
                                          show_zeros=True,
                                          intervals=utils.intervals[3:])

        message = message % (title, timecode)

        # get a draw object
        draw = ImageDraw.Draw(pil_im)
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
        # delete the old save file
        if(os.path.exists(os.path.join(utils.TMP_DIR, video_file['name'] + '.json'))):
            os.remove(os.path.join(utils.TMP_DIR, video_file['name'] + '.json'))

        # set 'next' to True to force new file
        video_file = find_video(args, utils.read_json(utils.LAST_PLAYED_FILE), True)
        logging.info('Will start %s on next run' % video_file)

    # save the next position and last video played filename
    utils.write_json(os.path.join(utils.TMP_DIR, video_file['name'] + '.json'), video_file)
    utils.write_json(utils.LAST_PLAYED_FILE, video_file)

    epd.sleep()


# parse the arguments
parser = configargparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-c', '--config', is_config_file=True,
                    help='Path to custom config file')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-f', '--file', type=utils.check_mp4,
                   help="File to grab screens of")
group.add_argument('-d', '--dir', type=utils.check_dir,
                   help="Dir to play videos from (in order)")
parser.add_argument('-i', '--increment',  default=4,
                    help="Number of frames skipped between screen updates")
parser.add_argument('-u', '--update', type=utils.check_cron, default='* * * * *',
                    help="when to update the display as a cron expression")
parser.add_argument('-s', '--start', default=1,
                    help="Number of seconds into the video to start")
parser.add_argument('-e', '--end', default=0,
                    help="Number of seconds to cut off the end of the video")
parser.add_argument('-D', '--display', nargs='*', default=[], choices=['timecode', 'title'],
                    help='show a display on the bottom of the screen, can be the title of the video, timecode, or both')

args = parser.parse_args()

# add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# setup the logger, log to tmp/log.log
logging.basicConfig(filename=os.path.join(utils.TMP_DIR, 'log.log'), datefmt='%m/%d %H:%M',
                    format="%(levelname)s %(asctime)s: %(message)s",
                    level=getattr(logging, 'INFO'))

logging.info('Starting with options Frame Increment: %s frames, Video start: %s seconds, Ending Cutoff: %s seconds, Updating on schedule: %s' %
      (args.increment, args.start, args.end, args.update))

# setup the screen
epd = epd_driver.EPD()

# start the web app
webAppThread = threading.Thread(name='Web App', target=webapp.webapp_thread, args=(5000,))
webAppThread.setDaemon(True)
webAppThread.start()

# initialize the cron scheduler and get the next update time
cron = croniter(args.update, datetime.now())
nextUpdate = cron.get_next(datetime)
logging.info('Next update: %s' % nextUpdate)

while 1:
    now = datetime.now()

    # check if the display should be updated
    if(nextUpdate <= now):
        update_display(args, epd)
        nextUpdate = cron.get_next(datetime)
        logging.info('Next update: %s' % nextUpdate)

    # sleep for one minute
    time.sleep(60 - datetime.now().second)
