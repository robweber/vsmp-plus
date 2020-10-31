import argparse
import ffmpeg
import logging
import os

# set path to ffmpeg
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'

intervals = (
    ('months', 604800),  # 60 * 60 * 24 * 30
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
    return frames/fps


def seconds_to_frames(seconds, fps):
    return seconds * fps


# Check if a file is an mp4
def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value


# Uses ffprobe to get various play details from the video file
def get_video_info(file):
    # get the info from ffprobe
    probeInfo = ffmpeg.probe(file)

    frameCount = int(probeInfo['streams'][0]['nb_frames'])

    # calculate the fps
    frameRateStr = probeInfo['streams'][0]['r_frame_rate'].split('/')
    frameRate = float(frameRateStr[0])/float(frameRateStr[1])

    return {'frame_count': frameCount, 'fps': frameRate,
            'runtime': frameCount/frameRate}


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
