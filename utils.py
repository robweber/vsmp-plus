import argparse
import ffmpeg
import logging
import os
import json
from croniter import croniter

# set path to ffmpeg
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'

# setup some helpful variables
DIR_PATH = os.path.dirname(os.path.realpath(__file__))  # full path to the directory of this script
TMP_DIR = os.path.join(DIR_PATH, 'tmp')
LAST_PLAYED_FILE = os.path.join(TMP_DIR, 'last_played.json')
CONFIG_FILE = os.path.join(TMP_DIR, 'config.json')

intervals = (
    ('months', 2592000),  # 60 * 60 * 24 * 30
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)

def display_time(seconds, granularity=3, timeFormat="{value} {interval_name}",
                 joiner=', ', show_zeros=False, intervals=intervals):
    """
    converts seconds to a display format, default is X weeks, Y days, Z hours
    :param seconds: time in seconds to convert
    :param granularity: how many values to display
    :param timeFormat: adjust layout of format
    :param joiner: string to join time values
    :param show_zeros: if 0 values should be shown, default is False.
    :param intervals: tuple of intervals in the format (interval_name, seconds)
    :return: string result of seconds broken up into time intervals
    """

    result = []

    for name, count in intervals:
        value = int(seconds) // count
        if value or show_zeros:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(timeFormat.format(value=value, interval_name=name))

    return joiner.join(result[:granularity])


def frames_to_seconds(frames, fps):
    return int(frames)/fps


def seconds_to_frames(seconds, fps):
    return int(seconds) * fps


# Check if a file is an mp4
def check_mp4(value):
    if not os.path.exists(value) or not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s does not exist or is not an .mp4 file" % value)
    return value


# Check if directory is valid
def check_dir(value):
    if(not os.path.exists(value) and not os.path.isdir(value)):
        raise argparse.ArgumentTypeError("%s is not a directory" % value)
    return value


# Check if passed in value is a valid cron schedule
def check_cron(schedule):
    if(not croniter.is_valid(schedule)):
        raise argparse.ArgumentTypeError("%s is not a valid cron expression" % schedule)
    return schedule

# Uses ffprobe to get various play details from the video file
def get_video_info(file):
    # get the info from ffprobe
    probeInfo = ffmpeg.probe(file)

    frameCount = int(probeInfo['streams'][0]['nb_frames'])

    # calculate the fps
    frameRateStr = probeInfo['streams'][0]['r_frame_rate'].split('/')
    frameRate = float(frameRateStr[0])/float(frameRateStr[1])

    # get the filename to show as a title
    name = os.path.splitext(os.path.basename(file))[0]
    if('title' in probeInfo['format']['tags']):
        name = probeInfo['format']['tags']['title']
    else:
        # replace common chars with spaces
        name = name.replace('.', ' ')

    return {'frame_count': frameCount, 'fps': frameRate,
            'runtime': frameCount/frameRate, 'title': name}


# get the configuration, use default values where custom don't exist
def get_configuration():
    # default configuration
    result = {'mode': 'file', 'path': '/home/pi/Videos', 'increment': 4, 'update': '* * * * *', 'start': 1, 'end': 0, 'display': []}

    # merge any saved configuration
    result.update(read_json(CONFIG_FILE))

    return result


# read JSON formatted file
def read_json(file):
    result = {}

    try:
        result = json.loads(read_file(file))
    except Exception:
        logging.error('error parsing json from file %s' % file)

    return result


# write JSON to file
def write_json(file, data):
    write_file(file, json.dumps(data))


# read contents of a file
def read_file(file):
    result = ''
    try:
        with open(file) as f:
            result = f.read()
    except Exception:
        logging.error('error opening file %s' % file)

    return result


# write data to a file
def write_file(file, pos):
    try:
        with open(file, 'w') as f:
            f.write(str(pos))
    except Exception:
        logging.error('error writing file')
