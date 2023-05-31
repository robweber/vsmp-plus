import logging
import os
import modules.utils as utils
from croniter import croniter, croniter_range
from datetime import datetime, timedelta


class Analyzer:
    config = None
    db = None

    def __init__(self, config, db):
        self.config = config
        self.db = db

    def run(self, lastPlayedFile):
        result = {'videos': []}

        if(self.config['mode'] == 'file'):
            result['videos'].append(self.analyze_video(self.config['path'], self.config['start'],
                                    self.config['end'], self.config['increment'], self.config['update']))
            result['total_time'] = self.time_to_play(result['videos'][0]['frames_left'],
                                                     self.config['increment'], self.config['update'])
        else:

            # read in all files from the directory
            fileList = utils.list_video_files(self.config['path'])
            index = 0

            # try and get the index of the last played file
            if('file' in lastPlayedFile):
                try:
                    index = fileList.index(os.path.basename(lastPlayedFile['file']))
                except ValueError:
                    index = 0

            # analyze each file
            totalFrames = 0
            for i in range(index, len(fileList)):
                analyzedVideo = self.analyze_video(os.path.join(self.config['path'], fileList[i]),
                                                   self.config['start'], self.config['end'],
                                                   self.config['increment'], self.config['update'])
                totalFrames = totalFrames + analyzedVideo['frames_left']

                result['videos'].append(analyzedVideo)

            # give a summary of the total play time left
            result['total_time'] = self.time_to_play(totalFrames, self.config['increment'], self.config['update'])

        return result

    def analyze_video(self, file, start, end, increment, update_expression):
        result = {}

        # run ffmpeg.probe to get the frame rate and frame count
        videoInfo = utils.get_video_info(file)

        startFrame = utils.seconds_to_frames(start, videoInfo['fps'])
        videoInfo['frame_count'] = videoInfo['frame_count'] - utils.seconds_to_frames(end, videoInfo['fps'])

        # print some initial information
        logging.info(f"Analyzing {file}")
        result['fps'] = videoInfo['fps']
        result['runtime'] = videoInfo['runtime'] / 60

        # video name, no ext
        video_name = os.path.splitext(os.path.basename(file))[0]
        result['file'] = video_name

        # check if we have a "save" file
        currentPosition = startFrame
        saveFile = utils.read_db(self.db, utils.DB_LAST_PLAYED_FILE)
        if(file == saveFile['file']):
            currentPosition = float(saveFile['pos'])

            if(currentPosition < startFrame):
                currentPosition = startFrame

        # find total time to play entire movie
        result['total_time_to_play'] = self.time_to_play(videoInfo['frame_count'] - startFrame,
                                                         float(increment), update_expression)

        # find time to play what's left
        result['remaining_time_to_play'] = self.time_to_play(videoInfo['frame_count'] - currentPosition,
                                                             float(increment), update_expression)

        # figure out how many 'real time' minutes per hour
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        day_total = 0
        for i in croniter_range(now, tomorrow, update_expression):
            day_total = day_total + 1
        secondsPerIncrement = utils.frames_to_seconds(increment, videoInfo['fps'])
        # this is how many "seconds" of film actually shown per second of realtime
        framesPerSecond = secondsPerIncrement / (60 / (day_total / 24) * 60)

        minutesPerHour = (framesPerSecond * 60)
        result['minutes_per_hour'] = minutesPerHour
        result['minutes_per_day'] = minutesPerHour * 24

        # number of frames left to play
        result['frames_left'] = videoInfo['frame_count'] - currentPosition

        return result

    def time_to_play(self, total_frames, increment, update_expression):
        # find out how many frames will display
        frames = total_frames / increment

        # find out how expression matches until frames = 0
        cron = croniter(update_expression, datetime.now())
        iter = cron.all_next(datetime)

        stopDate = datetime.now()  # datetime at which all frames will be displayed
        while(frames > 0):
            stopDate = next(iter)
            frames = frames - 1

        # get seconds between now and then
        total = (stopDate - datetime.now()).total_seconds()
        return utils.display_time(total)
