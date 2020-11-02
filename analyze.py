import argparse
import logging
import os
import utils


def time_to_play(total_frames, increment, delay):
    # find out how many frames will display
    frames = total_frames/increment

    print('%d out of %d frames will display' % (frames, total_frames))

    # frames * delay = total minutes to play
    total = (frames * delay)

    print('Video will take %s to fully play' % utils.display_time(total))


# parse the arguments
parser = argparse.ArgumentParser(description='VSMP Settings')
parser.add_argument('-f', '--file', type=utils.check_mp4, required=True,
                    help="File to analyze")
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

# run ffmpeg.probe to get the frame rate and frame count
videoInfo = utils.get_video_info(args.file)

startFrame = utils.seconds_to_frames(args.start, videoInfo['fps'])
videoInfo['frame_count'] = videoInfo['frame_count'] - utils.seconds_to_frames(args.end, videoInfo['fps'])

# print some initial information
print('Analyzing %s' % args.file)
print('Starting Frame: %s, Ending Frame: %s, Frame Increment: %s, Delay between updates: %s' %
      (startFrame, videoInfo['frame_count'], args.increment, args.delay))
print('Video framerate is %ffps, total video is %f minutes long' %
      (videoInfo['fps'], videoInfo['runtime']/60))
print('')

# full path to the directory of this script
dir_path = os.path.dirname(os.path.realpath(__file__))
# video name, no ext
video_name = os.path.splitext(os.path.basename(args.file))[0]

# create the tmp directory if it doesn't exist
tmpDir = os.path.join(dir_path, 'tmp')
if (not os.path.exists(tmpDir)):
    os.mkdir(tmpDir)

# check if we have a "save" file
currentPosition = startFrame
saveFile = os.path.join(tmpDir, video_name + '.txt')
if(os.path.exists(saveFile)):
    currentPosition = float(utils.read_file(saveFile))

# find total time to play entire movie
print('Entire Video:')
time_to_play(videoInfo['frame_count'] - startFrame,
             float(args.increment), float(args.delay))
print('')


# find time to play what's left
print('Remaining Video:')
time_to_play(videoInfo['frame_count'] - currentPosition,
             float(args.increment), float(args.delay))
print('')

# figure out how many 'real time' minutes per hour
secondsPerIncrement = utils.frames_to_seconds(args.increment, videoInfo['fps'])
framesPerSecond = secondsPerIncrement/float(args.delay)  # this is how many "seconds" of film actually shown per second of realtime

minutesPerHour = (framesPerSecond * 60)
print('Minutes of film displayed breakdown:')
print('%f minutes of film per hour' % (minutesPerHour))
print('%f minutes of film per day' % (minutesPerHour * 24))

exit()
