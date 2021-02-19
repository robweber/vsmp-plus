
import configargparse
import ffmpeg
import logging
import os
import modules.utils as utils
import fnmatch
import signal
import sys
import time
import threading
import json
import redis
import modules.webapp as webapp
from croniter import croniter
from datetime import datetime, timedelta
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
    logging.debug('Exiting Program')
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


def analyze_video(config, file):
    # save full path plus filename with no ext
    result = {"file": file, 'name': os.path.splitext(os.path.basename(file))[0]}

    # get some info about the video (frame rate, total frames, runtime)
    result['info'] = utils.get_video_info(file)

    # modify the end frame, if needed
    result['info']['frame_count'] = result['info']['frame_count'] - utils.seconds_to_frames(config['end'], result['info']['fps'])

    # find the saved position and played percent
    result['pos'] = float(utils.seconds_to_frames(config['start'], result['info']['fps']))

    result['percent_complete'] = (result['pos']/result['info']['frame_count']) * 100

    return result


def find_video(config, lastPlayed, next=False):
    result = {}

    # if in file mode, just use the file name
    if(config['mode'] == 'file'):
        if(config['path'] == lastPlayed['file']):
            result = lastPlayed
        else:
            result = analyze_video(config, config['path'])
    else:
        # we're in dir mode, use the name of the last played file if it exists in the directory
        if('file' in lastPlayed and os.path.basename(lastPlayed['file']) in os.listdir(config['path']) and not next):
            # use information loaded from last played file
            result = lastPlayed
        else:
            # file might not exist (first run) just make it blank
            if('file' not in lastPlayed):
                lastPlayed['file'] = ''
            result = analyze_video(config, find_next_video(config['path'], lastPlayed['file']))

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


def update_display(config, epd, db):
    # Initialize the screen
    epd.init()

    # set the video file information
    video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE))

    # save grab file in memory as a bitmap
    grabFile = os.path.join('/dev/shm/', 'frame.bmp')

    logging.info('Loading %s' % video_file['file'])

    if(video_file['pos'] >= video_file['info']['frame_count']):
        # set 'next' to true to force new video file
        video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE), True)

    # calculate the percent percent_complete
    video_file['percent_complete'] = (video_file['pos']/video_file['info']['frame_count']) * 100

    # set the position we want to use
    frame = video_file['pos']

    # Convert that frame to ms from start of video (frame/fps) * 1000
    msTimecode = "%dms" % (utils.frames_to_seconds(frame, video_file['info']['fps']) * 1000)

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it in memory
    generate_frame(video_file['file'], grabFile, msTimecode)

    # Open grab.jpg in PIL
    pil_im = Image.open(grabFile)

    if(len(config['display']) > 0):
        font18 = ImageFont.truetype(os.path.join(utils.DIR_PATH, 'waveshare_lib', 'pic', 'Font.ttc'), 18)

        message = '%s %s'
        title = ''
        timecode = ''

        if('title' in config['display']):
            title = video_file['info']['title']

        if('timecode' in config['display']):
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
    video_file['pos'] = video_file['pos'] + float(config['increment'])

    if(video_file['pos'] >= video_file['info']['frame_count']):
        # set 'next' to True to force new file
        video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE), True)
        logging.info('Will start %s on next run' % video_file)

    # save the last video played info
    utils.write_db(db, utils.DB_LAST_PLAYED_FILE, video_file)

    epd.sleep()


# parse the arguments
parser = configargparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-c', '--config', is_config_file=True,
                    help='Path to custom config file')
parser.add_argument('-p', '--port', default=5000,
                    help="Port number to run the web server on, 5000 by default")
parser.add_argument('-D', '--debug', action='store_true',
                    help='If the program should run in debug mode')

args = parser.parse_args()

# add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# setup the logger, log to tmp/log.log
logLevel = 'INFO' if not args.debug else 'DEBUG'
logging.basicConfig(filename=os.path.join(utils.TMP_DIR, 'log.log'), datefmt='%m/%d %H:%M',
                    format="%(levelname)s %(asctime)s: %(message)s",
                    level=getattr(logging, logLevel))
logging.debug('Debug Mode On')

# setup the screen and database connection
epd = epd_driver.EPD()
db = redis.Redis('localhost', decode_responses=True)

if(not db.exists(utils.DB_PLAYER_STATUS)):
    utils.write_db(utils.DB_PLAYER_STATUS, {'running': False})  # default to False as default settings probably won't load a video

# load the player configuration
config = utils.get_configuration(db)
logging.info('Starting with options Frame Increment: %s frames, Video start: %s seconds, Ending Cutoff: %s seconds, Updating on schedule: %s' %
      (config['increment'], config['start'], config['end'], config['update']))

# start the web app
webAppThread = threading.Thread(name='Web App', target=webapp.webapp_thread, args=(args.port, args.debug))
webAppThread.setDaemon(True)
webAppThread.start()

# initialize the cron scheduler and get the next update time
updateExpression = config['update']
cron = croniter(updateExpression, datetime.now())
nextUpdate = cron.get_next(datetime)
logging.info('Next update: %s' % nextUpdate)

while 1:
    now = datetime.now()

    config = utils.get_configuration(db)

    # refresh update if changed
    if(config['update'] != updateExpression):
        updateExpression = config['update']
        cron = croniter(updateExpression, now)
        nextUpdate = cron.get_next(datetime)
        logging.info('Next update: %s' % nextUpdate)

    # check if the display should be updated
    pStatus = utils.read_db(db, utils.DB_PLAYER_STATUS)
    if(nextUpdate <= now):
        if(pStatus['running']):
            update_display(config, epd, db)
        else:
            logging.debug('Updating display paused, skipping this time')
        nextUpdate = cron.get_next(datetime)
        logging.info('Next update: %s' % nextUpdate)

    # sleep for one minute
    time.sleep(60 - datetime.now().second)
