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
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# create the tmp directory if it doesn't exist
if (not os.path.exists(utils.TMP_DIR)):
    os.mkdir(utils.TMP_DIR)


# function to handle when the is killed and exit gracefully
def signal_handler(signum, frame):
    logging.debug('Exiting Program')
    epd.close()
    sys.exit(0)


# helper method to get the local IP address of this machine, doesn't matter if test address is "real"
def get_local_ip():
    result = "127.0.0.1"  # if no network return this
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(('192.168.0.255', 1))  # connect() for UDP doesn't send packets
        result = s.getsockname()[0]
    except Exception:
        logging.warning("No LAN address found")
    finally:
        s.close()

    return result


def changed_ip_check(config, db):
    # test if IP has changed
    saved_ip = utils.read_db(db, utils.CURRENT_IP)
    current_ip = get_local_ip()

    if(saved_ip['ip'] != current_ip):
        # the ip address has changed
        utils.write_db(db, utils.CURRENT_IP, {'ip': current_ip})

        # modify the UI to display this new IP visually
        if('ip' not in config['display']):
            config['display'].append('ip')
            utils.write_db(db, utils.DB_CONFIGURATION, config)


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


def show_startup(epd, db, messages=[]):
    epd.prepare()

    # display startup message on the display
    font30 = ImageFont.truetype(utils.FONT_PATH, 30)
    font24 = ImageFont.truetype(utils.FONT_PATH, 24)

    current_ip = utils.read_db(db, utils.CURRENT_IP)
    messages.append(f"Configure at http://{current_ip['ip']}:{args.port}")

    # load a background image
    splash_image = os.path.join(utils.DIR_PATH, "web", "static", "images", "splash.jpg")
    background_image = Image.open(splash_image).resize((width, height))

    draw = ImageDraw.Draw(background_image)

    # calculate the size of the text we're going to draw
    title = "VSMP+"
    left, top, right, bottom = draw.textbbox((0, 0), text=title, font=font30)
    tw, th = right - left, bottom - top

    draw.text(((width - tw) / 2, (height - th) / 4), title, font=font30, fill=0)

    offset = th * 1.5  # initial offset is height of title plus spacer
    for m in messages:
        left, top, right, bottom = draw.textbbox((0, 0), text=m, font=font24)
        mw, mh = right - left, bottom - top
        draw.text(((width - mw) / 2, (height - mh) / 4 + offset), m, font=font24, fill=0)
        offset = offset + (th * 1.5)

    epd.display(background_image)

    epd.sleep()


def update_display(config, epd, db):

    # get the video file information
    video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE))

    # check if we have a properly analyzed video file
    if('file' not in video_file):
        # log an error message
        logging.error('No video file to load')

        show_startup(epd, db, ["No Video Loaded"])

        # set to "paused" so this isn't constantly Updating
        utils.write_db(db, utils.DB_PLAYER_STATUS, {'running': False})

        return

    # Initialize the screen
    epd.prepare()

    # save grab file in memory as a bitmap
    grabFile = os.path.join('/dev/shm/', 'frame.bmp')
    validImg = False

    while(not validImg):
        logging.info(f"Loading {video_file['file']}")

        if(video_file['pos'] >= video_file['info']['frame_count']):
            # set 'next' to true to force new video file
            video_file = find_video(config, utils.read_db(db, utils.DB_LAST_PLAYED_FILE), True)

        # calculate the percent percent_complete
        video_file['percent_complete'] = (video_file['pos'] / video_file['info']['frame_count']) * 100

        # set the position we want to use
        frame = video_file['pos']

        # Convert that frame to ms from start of video (frame/fps) * 1000
        msTimecode = f"{utils.frames_to_seconds(frame, video_file['info']['fps']) * 1000}ms"

        # Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it in memory
        generate_frame(video_file['file'], grabFile, msTimecode)

        # save the next position
        video_file['pos'] = video_file['pos'] + float(config['increment'])

        # Open grab.jpg in PIL
        pil_im = Image.open(grabFile)

        # image not valid if skipping blank (None == blank)
        validImg = (not config['skip_blank']) or (pil_im.getbbox() is not None and config['skip_blank'])

        if(not validImg):
            logging.info('Image is all black, try again')

    if(len(config['display']) > 0):
        font18 = ImageFont.truetype(utils.FONT_PATH, 18)

        title = ''
        timecode = ''

        if('title' in config['display']):
            title = video_file['info']['title']

        if('ip' in config['display']):
            current_ip = utils.read_db(db, utils.CURRENT_IP)
            title = f"(IP: {current_ip['ip']}) {title}"

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
        left, top, right, bottom = draw.textbbox((0, 0), text=message, font=font18)
        tw, th = right - left, bottom - top  # gets the width and height of the text drawn
        # draw timecode, centering on the middle
        draw.text(((width - tw) / 2, height - th), message, font=font18, fill=(255, 255, 255))

    # display the image
    epd.display(pil_im)
    secondsOfVideo = utils.frames_to_seconds(frame, video_file['info']['fps'])
    logging.info(f"Diplaying frame {frame} ({secondsOfVideo} seconds) of {video_file['name']}")

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

logging.info(f"Starting with options Frame Increment: {config['increment']} frames, "
             f"Video start: {config['start']} seconds, Ending Cutoff: {config['end']} seconds, "
             f"Updating on schedule: {config['update']}")

# get the current ip address
utils.write_db(db, utils.CURRENT_IP, {'ip': get_local_ip()})

# start the web app
webAppThread = threading.Thread(name='Web App', target=webapp.webapp_thread, args=(args.port, args.debug, logHandlers))
webAppThread.setDaemon(True)
webAppThread.start()

# set to now, or now + 60 depending on if we are showing the splash screen
now = datetime.now() if not config['startup_screen'] else datetime.now() + timedelta(seconds=60)

# initialize the cron scheduler and get the next update time - based on the previous time
updateExpression = config['update']
lastUpdate = utils.read_db(db, utils.DB_LAST_RUN)

cron = croniter(updateExpression, datetime.fromtimestamp(lastUpdate['last_run']))
nextUpdate = cron.get_next(datetime)
if(nextUpdate < now):
    nextUpdate = now  # we may have missed a previous update

utils.write_db(db, utils.DB_NEXT_RUN, {'next_run': nextUpdate.timestamp()})
logging.info(f"Next Update: {nextUpdate} based on last update {datetime.fromtimestamp(lastUpdate['last_run'])}")

# show the startup screen for 1 min before proceeding
if(config['startup_screen']):
    logging.info("Showing startup screen")
    show_startup(epd, db, [f"Next Update: {nextUpdate.strftime('%m/%d at %H:%M')}"])
    time.sleep(60)

# reset cronitor to current time
cron = croniter(updateExpression, datetime.now())

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

        # check if the IP address has changed
        changed_ip_check(config, db)

    # sleep for one minute
    time.sleep(60 - datetime.now().second)
