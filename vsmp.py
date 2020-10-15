import argparse, ffmpeg, logging, os, time, sys, random
from PIL import Image
from waveshare_epd import epd7in5_V2 # ensure this is the correct import for your screen

# set path to ffmpeg
os.environ['PATH'] += os.pathsep + '/usr/local/bin/'

def generate_frame(in_filename, out_filename, time, width, height):
    ffmpeg.input(in_filename, ss=time).filter('scale', width, height, force_original_aspect_ratio=1).filter('pad', width, height, -1, -1).output(out_filename, vframes=1).overwrite_output().run(capture_stdout=True, capture_stderr=True)

def check_mp4(value):
    if not value.endswith('.mp4'):
        raise argparse.ArgumentTypeError("%s should be an .mp4 file" % value)
    return value

def check_dir(value):
    if(not os.path.exists(value) and not os.path.isdir(value)):
        raise argparse.ArgumentTypeError("%s is not a directory" % value)
    return value

def find_video(args, lastPlayed):
    result = None

    # if in file mode, just use the file name
    if(args.file is not None):
        result = args.file
    else:
        #we're in dir mode, use the name of the last played file
        if(lastPlayed != ''):
            result = lastPlayed
        else:
            result = find_next_video(args.dir, lastPlayed)

    return result

def find_next_video(dir, lastPlayed):
    #list all files in the directory
    fileList = os.listdir(dir)

    index = 0  # assume we'll just use the first video
    if(lastPlayed != ''):
        for aFile in fileList:
            index = index + 1
            if(aFile == os.path.basename(lastPlayed)):
                break;

    # go back to start of list if we got to the end
    if(index >= len(fileList)):
        index = 0

    # return this video
    return os.path.join(dir, fileList[index])

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

def write_file(file, pos):
    try:
        f = open(file, 'w')
        f.write(str(pos))
        f.close()
    except Exception:
        logging.error('error writing file')

# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Settings')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-f', '--file', type=check_mp4,
    help="File to grab screens of")
group.add_argument('-d', '--dir', type=check_dir,
    help="Dir to play videos from (in order)")
parser.add_argument('-i', '--increment',  default=4,
    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', default=1,
    help="Start at a specific frame")

args = parser.parse_args()

# setup some helpful variables
dir_path = os.path.dirname(os.path.realpath(__file__)) # full path to the directory of this script

# Modify these to match your particular screen
width = 800
height = 480

# create the tmp directory if it doesn't exist
tmpDir = os.path.join(dir_path, 'tmp')
if (not os.path.exists(tmpDir)):
    os.mkdir(tmpDir)
lastPlayedFile = os.path.join(tmpDir, 'last_played.txt')

# set the video file information
video_file = find_video(args, read_file(lastPlayedFile))
video_name = os.path.splitext(os.path.basename(video_file))[0] # video name, no ext

# setup the logger, log to tmp/log.log
logging.basicConfig(filename=os.path.join(tmpDir,'log.log'), datefmt='%m/%d %H:%M', format="%(levelname)s %(asctime)s: %(message)s", level=getattr(logging, 'INFO'))

# check if we have a "save" file
currentPosition = float(args.start)
saveFile = os.path.join(tmpDir, video_name + '.txt')
if( os.path.exists(saveFile)):
    currentPosition = float(read_file(saveFile))

# setup the screen
epd = epd7in5_V2.EPD()

# Initialize the screen
epd.init()

grabFile = os.path.join(tmpDir,'grab.jpg')

logging.info('Loading %s' % video_file)

# Check how many frames are in the movie
frameCount = int(ffmpeg.probe(video_file)['streams'][0]['nb_frames'])

if(currentPosition >= frameCount):
    currentPosition = args.start # in case we went over the frameCount

# set the position we want to use
frame = currentPosition

# Convert that frame to Timecode
msTimecode = "%dms"%(frame*41.666666)

# Use ffmpeg to extract a frame from the movie, crop it, letterbox it and save it as grab.jpg
generate_frame(video_file, grabFile, msTimecode, width, height)

# Open grab.jpg in PIL
pil_im = Image.open(grabFile)

# Dither the image into a 1 bit bitmap (Just zeros and ones)
pil_im = pil_im.convert(mode='1',dither=Image.FLOYDSTEINBERG)

# display the image
epd.display(epd.getbuffer(pil_im))
logging.info('Diplaying frame %d of %s' % (frame,video_name))

# save the next position
currentPosition = currentPosition + float(args.increment)
if(currentPosition >= frameCount):
    if(args.dir is not None):
        # if in dir mode find the next video
        video_file = find_next_video(args.dir, read_file(lastPlayedFile))
        logging.info('Will play %s on next run' % video_file)

    # start over if we got to the end
    currentPosition = args.start

# save the next position and last video played filename
write_file(saveFile, currentPosition)
write_file(lastPlayedFile, video_file)

# NB We should run sleep() while the display is resting more often, but there's a bug in the driver that's slightly fiddly to fix. Instead of just sleeping, it completely shuts down SPI communication 
epd.sleep()
#epd7in5.epdconfig.module_exit()
exit()
