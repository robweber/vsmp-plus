import configargparse
import ffmpeg
import logging
import os
import modules.utils as utils
from modules.videoinfo import VideoInfo
import signal
import sys
import time
import threading
import redis
import socket
import modules.webapp as webapp
from omni_epd import displayfactory
from croniter import croniter
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# create the tmp directory if it doesn't exist
if (not os.path.exists(utils.TMP_DIR)):
    os.mkdir(utils.TMP_DIR)


# function to handle when the is killed and exit gracefully
def signal_handler(signum, frame):
    logging.debug('Exiting Program')
    epd.close()
    sys.exit(0)


# helper method to get the local IP address of this machine, uses CloudFlare DNS so internet must work
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('1.1.1.1', 1))  # connect() for UDP doesn't send packets
    return s.getsockname()[0]


def generate_frame(in_filename, out_filename, time):
    ffmpeg.input(in_filename, ss=time) \
          .filter('scale', 'iw*sar', 'ih') \
          .filter('scale', width, height, force_original_aspect_ratio=1) \
          .filter('pad', width, height, -1, -1) \
          .output(out_filename, vframes=1) \
          .overwrite_output() \
          .run(capture_stdout=True, capture_stderr=True)


def find_video(config, lastPlayed, next=False):
    result = {}

    # if in file mode, just use the file name
    if(config['mode'] == 'file'):
        if(config['path'] == lastPlayed['file']):
            result = lastPlayed
        else:
            info = VideoInfo(config)
            result = info.analyze_video(config['path'])
    else:
        # we're in dir mode, use the name of the last played file if it exists in the directory
        if('file' in lastPlayed and os.path.basename(lastPlayed['file']) in os.listdir(config['path']) and not next):
            # use information loaded from last played file
            result = lastPlayed
        else:
            # file might not exist (first run) just make it blank
            if('file' not in lastPlayed):
                lastPlayed['file'] = ''

            info = VideoInfo(config)
            result = info.find_next_video(lastPlayed['file'])

    return result


def show_startup(epd, title):
    epd.prepare()

    # display startup message on the display
    font24 = ImageFont.truetype(utils.FONT_PATH, 24)

    message = f"Configure at http://{get_local_ip()}:{args.port}"

    background_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(background_image)
    tw, th = draw.textsize(message)

    # calculate the size of the text we're going to draw
    tw, th = draw.textsize(title, font=font24)
    mw, mh = draw.textsize(message, font=font24)

    draw.text(((width-tw)/2, (height-th)/2), title, anchor="ms", font=font24, fill=0)
    draw.text(((width-mw)/2, (height-mh)/2 + (th * 1.8)), message, anchor="ms", font=font24, fill=0)
    epd.display(background_image)

    epd.sleep()


def update_display(config, epd, db):

    # get the video file information
    video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE))

    # check if we have a properly analyzed video file
    if('file' not in video_file):
        # log an error message
        logging.error('No video file to load')

        show_startup(epd, "No Video Loaded")

        # set to "paused" so this isn't constantly Updating
        utils.write_db(db, utils.DB_PLAYER_STATUS, {'running': False})

        return

    # Initialize the screen
    epd.prepare()

    # save grab file in memory as a bitmap
    grabFile = os.path.join('/dev/shm/', 'frame.bmp')

    logging.info(f"Loading {video_file['file']}")

    if(video_file['pos'] >= video_file['info']['frame_count']):
        # set 'next' to true to force new video file
        video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE), True)

    # calculate the percent percent_complete
    video_file['percent_complete'] = (video_file['pos']/video_file['info']['frame_count']) * 100

    # set the position we want to use
    frame = video_file['pos']

    # Convert that frame to ms from start of video (frame/fps) * 1000
    msTimecode = f"{utils.frames_to_seconds(frame, video_file['info']['fps']) * 1000}ms"

    # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it in memory
    generate_frame(video_file['file'], grabFile, msTimecode)

    # Open grab.jpg in PIL
    pil_im = Image.open(grabFile)

    if(len(config['display']) > 0):
        font18 = ImageFont.truetype(utils.FONT_PATH, 18)

        title = ''
        timecode = ''

        if('title' in config['display']):
            title = video_file['info']['title']

        if('ip' in config['display']):
            title = f"(IP: {get_local_ip()}) {title}"

        if('timecode' in config['display']):
            # show the timecode of the video in the format HH:mm:SS
            timecode = utils.display_time(seconds=utils.frames_to_seconds(frame, video_file['info']['fps']),
                                          granularity=3,
                                          timeFormat='{value:02d}',
                                          joiner=':',
                                          show_zeros=True,
                                          intervals=utils.intervals[3:])

        message = f"{title} - {timecode}"

        # get a draw object
        draw = ImageDraw.Draw(pil_im)
        tw, th = draw.textsize(message)  # gets the width and height of the text drawn

        # draw timecode, centering on the middle
        draw.text(((width-tw)/2, height-20), message, font=font18, fill=(255, 255, 255))

    # Dither the image into a 1 bit bitmap (Just zeros and ones)
    pil_im = pil_im.convert(mode='1', dither=Image.FLOYDSTEINBERG)

    # display the image
    epd.display(pil_im)
    secondsOfVideo = utils.frames_to_seconds(frame, video_file['info']['fps'])
    logging.info(f"Diplaying frame {frame} ({secondsOfVideo} seconds) of {video_file['name']}")

    # save the next position
    video_file['pos'] = video_file['pos'] + float(config['increment'])

    if(video_file['pos'] >= video_file['info']['frame_count']):
        # set 'next' to True to force new file
        video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE), True)
        logging.info(f"Will start {video_file} on next run")

    # save the last video played info
    utils.write_db(db, utils.DB_LAST_PLAYED_FILE, video_file)

    epd.sleep()


# parse the arguments
parser = configargparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-c', '--config', is_config_file=True,
                    help='Path to custom config file')
parser.add_argument('-p', '--port', default=5000,
                    help="Port number to run the web server on, %(default)d by default")
parser.add_argument('-e', '--epd', default='waveshare_epd.epd7in5_V2',
                    help="The type of EPD driver to use, default is %(default)s")
parser.add_argument('-D', '--debug', action='store_true',
                    help='If the program should run in debug mode')

args = parser.parse_args()

# add hooks for interrupt signal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# setup the logger, log to tmp/log.log
logLevel = 'INFO' if not args.debug else 'DEBUG'
logHandlers = [logging.FileHandler(os.path.join(utils.TMP_DIR, 'log.log'))]

if(args.debug):
    logHandlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(datefmt='%m/%d %H:%M',
                    format="%(levelname)s %(asctime)s: %(message)s",
                    level=getattr(logging, logLevel),
                    handlers=logHandlers)
logging.debug('Debug Mode On')

# check the epd driver
validEpds = displayfactory.list_supported_displays()

if(args.epd not in validEpds):
    # can't find the driver
    logging.error(f"{args.epd} is not a valid EPD name, valid names are:")
    logging.error("\n".join(map(str, validEpds)))

    # can't get past this
    exit(1)

# setup the screen and database connection
epd = displayfactory.load_display_driver(args.epd)

# pull width/height from driver
width = epd.width
height = epd.height

db = redis.Redis('localhost', decode_responses=True)

# default to False as default settings probably won't load a video
if(not db.exists(utils.DB_PLAYER_STATUS)):
    utils.write_db(db, utils.DB_PLAYER_STATUS, {'running': False})
    utils.write_db(db, utils.DB_LAST_RUN, {'last_run': 0})

# load the player configuration
config = utils.get_configuration(db)

logging.info(f"Starting with options Frame Increment: {config['increment']} frames, " +
             f"Video start: {config['start']} seconds, Ending Cutoff: {config['end']} seconds, "
             f"Updating on schedule: {config['update']}")

# start the web app
webAppThread = threading.Thread(name='Web App', target=webapp.webapp_thread, args=(args.port, args.debug, logHandlers))
webAppThread.setDaemon(True)
webAppThread.start()

# show the startup screen for 1 min before proceeding
if(config['startup_screen']):
    logging.info("Showing startup screen")
    show_startup(epd, "VSMP+")
    time.sleep(60)

# initialize the cron scheduler and get the next update time
updateExpression = config['update']
cron = croniter(updateExpression, datetime.now())
nextUpdate = cron.get_next(datetime)
utils.write_db(db, utils.DB_NEXT_RUN, {'next_run': nextUpdate.timestamp()})
logging.info(f"Next update: {nextUpdate}")

while 1:
    now = datetime.now()

    config = utils.get_configuration(db)

    # refresh update if changed
    if(config['update'] != updateExpression):
        updateExpression = config['update']
        cron = croniter(updateExpression, now)
        nextUpdate = cron.get_next(datetime)
        utils.write_db(db, utils.DB_NEXT_RUN, {'next_run': nextUpdate.timestamp()})
        logging.info(f"Next update: {nextUpdate}")

    # check if the display should be updated
    pStatus = utils.read_db(db, utils.DB_PLAYER_STATUS)
    if(nextUpdate <= now):
        if(pStatus['running']):
            update_display(config, epd, db)
            utils.write_db(db, utils.DB_LAST_RUN, {'last_run': now.timestamp()})
        else:
            logging.debug('Updating display paused, skipping this time')
        nextUpdate = cron.get_next(datetime)
        utils.write_db(db, utils.DB_NEXT_RUN, {'next_run': nextUpdate.timestamp()})
        logging.info(f"Next update: {nextUpdate}")

    # sleep for one minute
    time.sleep(60 - datetime.now().second)
