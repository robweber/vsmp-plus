import argparse, logging, ffmpeg

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

