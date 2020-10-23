import argparse, logging, ffmpeg

# found this on https://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-h$
intervals = (
    #('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)

# calculates total time based on seconds
# Example of default format is X weeks, Y days, Z hours
# granularity = how many values to display
# timeFormat = adjust layout of format, default is 'value interval_name'
# joiner = string to join time values, default is ', '
# show_zeros = if 0 values should be shown, default is False. Difference betwen 0 weeks, 3 days, 2 hours and 3 days, 2 hours, 3 minutes
# intervals = tuple of intervals in the format (interval_name, seconds) default is weeks, days, hours, minutes, seconds
def display_time(seconds, granularity=3, timeFormat="{value} {interval_name}", joiner=', ', show_zeros=False, intervals=intervals):
    result = []

    for name, count in intervals:
        value = int(seconds) // count
        if value or show_zeros:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(timeFormat.format(value=value, interval_name=name))

    return joiner.join(result[:granularity])

def display_time_code(seconds):
    result = []

    # time code format is HH:mm:SS
    timecode_intervals = intervals[2:]

    return ':'.join(result)


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

    return {'frame_count': frameCount, 'fps': frameRate, 'runtime': frameCount/frameRate}

# read contents of a file
def read_file(file):
    result = ''
    try:
        f = open(file)
        for line in f:
            result = result + line
        f.close()
    except Exception:
        logging.error('error opening file %s' % file)

    return result

# write data to a file
def write_file(file, pos):
    try:
        f = open(file, 'w')
        f.write(str(pos))
        f.close()
    except Exception:
        logging.error('error writing file')

