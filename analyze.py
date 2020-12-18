import argparse
import logging
import os
import fnmatch
import utils

# full path to the directory of this script
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# create the tmp directory if it doesn't exist
TMP_DIR = os.path.join(DIR_PATH, 'tmp')
if (not os.path.exists(TMP_DIR)):
    os.mkdir(TMP_DIR)

def time_to_play(total_frames, increment, delay):
    # find out how many frames will display
    frames = total_frames/increment

    print('%d out of %d frames will display' % (frames, total_frames))

    # frames * delay = total minutes to play
    total = (frames * delay)

    print('Video will take %s to fully play' % utils.display_time(total))

def analyze_video(file, start, end, increment, delay):

    # run ffmpeg.probe to get the frame rate and frame count
    videoInfo = utils.get_video_info(file)

    startFrame = utils.seconds_to_frames(start, videoInfo['fps'])
    videoInfo['frame_count'] = videoInfo['frame_count'] - utils.seconds_to_frames(end, videoInfo['fps'])

    # print some initial information
    print('Analyzing %s' % file) 
    print('Starting Frame: %s, Ending Frame: %s, Frame Increment: %s, Delay between updates: %s' %
          (startFrame, videoInfo['frame_count'] - startFrame, increment, delay))
    print('Video framerate is %ffps, total video is %f minutes long' %
         (videoInfo['fps'], videoInfo['runtime']/60))
    print('')

    # video name, no ext
    video_name = os.path.splitext(os.path.basename(file))[0]

    # check if we have a "save" file
    currentPosition = startFrame
    saveFile = os.path.join(TMP_DIR, video_name + '.txt')
    if(os.path.exists(saveFile)):
        currentPosition = float(utils.read_file(saveFile))

        if(currentPosition < startFrame):
            currentPosition = startFrame

    # find total time to play entire movie
    print('Entire Video:')
    time_to_play(videoInfo['frame_count'] - startFrame,
                 float(increment), float(delay))
    print('')

    # find time to play what's left
    print('Remaining Video:')
    time_to_play(videoInfo['frame_count'] - currentPosition,
                float(increment), float(delay))
    print('')

    # figure out how many 'real time' minutes per hour
    secondsPerIncrement = utils.frames_to_seconds(increment, videoInfo['fps'])
    framesPerSecond = secondsPerIncrement/float(delay)  # this is how many "seconds" of film actually shown per second of realtime

    minutesPerHour = (framesPerSecond * 60)
    print('Minutes of film displayed breakdown:')
    print('%f minutes of film per hour' % (minutesPerHour))
    print('%f minutes of film per day' % (minutesPerHour * 24))

    # return number of frames left to play
    return videoInfo['frame_count'] - currentPosition

# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Analyze Settings')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-f', '--file', type=utils.check_mp4,
                    help="File to analyze")
group.add_argument('-D', '--dir', type=utils.check_dir,
                    help="Directory to analyze")
parser.add_argument('-d', '--delay',  default=120,
                    help="Delay between screen updates, in seconds")
parser.add_argument('-i', '--increment',  default=4,
                    help="Number of frames skipped between screen updates")
parser.add_argument('-s', '--start', default=1,
                    help="Number of seconds into the film to start")
parser.add_argument('-e', '--end', default=0,
                    help="Number of seconds to cut off the end of the video")
args = parser.parse_args()

logging.basicConfig(datefmt='%m/%d %H:%M', format="%(asctime)s: %(message)s",
                    level=getattr(logging, 'INFO'))

# check if we have one file or several
if(args.file is not None):
    analyze_video(args.file, args.start, args.end, args.increment, args.delay)
else:
    # assume files play in order and files prior to the current have already played
    print('Analyzing Entire Directory %s' % args.dir)

    # get the currently playing file, if exists
    lastPlayedFile = utils.read_file(os.path.join(TMP_DIR, 'last_played.txt'))

    # read in all files from the directory
    fileList = sorted(fnmatch.filter(os.listdir(args.dir), '*.mp4'))
    index = 0

    # try and get the index of the last played file
    try:
        index = fileList.index(os.path.basename(lastPlayedFile))
    except ValueError:
        index = 0

    print('%d out of %d files left to play' % (len(fileList) - index, len(fileList)))
    print('')

    # analyze each file
    totalFrames = 0
    for i in range(index, len(fileList)):
        totalFrames = totalFrames + analyze_video(os.path.join(args.dir, fileList[i]), args.start, args.end, args.increment, args.delay)
        print('')

    # give a summary of the total play time left
    print('')
    print('Time to play full directory:')
    time_to_play(totalFrames, float(args.increment), float(args.delay))

exit()
