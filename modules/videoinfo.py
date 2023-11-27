import modules.utils as utils
import os

# parent class to hold info from a media file
class MediaInfo:
    config = None

    def __init__(self, config):
        self.config = config

    # implemented by child classes
    def find_next_file(self, lastPlayed):
        raise NotImplementedError

    def find_prev_file(self, lastPlayed):
        raise NotImplementedError

# helper class to find the next image to display and analyze it if needed
class ImageInfo(MediaInfo):

    def __init__(self, config):
        super().__init__(config)

    def _get_image(self, lastPlayed):
        fileList = []

        if(os.path.exists(self.config['path'])):
            # list all files in the directory, filter on images
            fileList = utils.list_image_files(self.config['path'])

        if(len(fileList) == 0):
            return {}  # return nothing, no files to find

        index = 0

        # get the index of the last played file (if exists)
        try:
            index = fileList.index(os.path.basename(lastPlayed))
            index = index + 1  # get the next one

        except ValueError:
            index = 0  # just use the first one

        # go back to start of list if we got to the end
        if(index >= len(fileList)):
            index = 0

        # return this video
        result = {"file": os.path.join(self.config['path'], fileList[index])}
        filename = os.path.splitext(os.path.basename(result['file']))[0]
        result['info'] = {"title": filename.replace('.', ' ')}
        result['name'] = filename
        result['pos'] = index

        return result

    def find_next_file(self, lastPlayed):
        # just get a new file that is not the last file
        return self._get_image(lastPlayed)

    def find_prev_file(self, lastPlayed):
        # just get the next image - FIX LATER
        return self._get_image(lastPlayed)

# helper classes to find the right video to play and analyze it if needed
class VideoInfo(MediaInfo):

    def __init__(self, config):
        super().__init__(config)

    def analyze_video(self, file):
        result = {}  # return nothing if file doesn't exist

        if(os.path.exists(file)):
            # save full path plus filename with no ext
            result = {"file": file, 'name': os.path.splitext(os.path.basename(file))[0]}

            # get some info about the video (frame rate, total frames, runtime)
            result['info'] = utils.get_video_info(file)

            # modify the end frame, if needed
            framesOfVideo = utils.seconds_to_frames(self.config['end'], result['info']['fps'])
            result['info']['frame_count'] = result['info']['frame_count'] - framesOfVideo

            # find the saved position and played percent
            result['pos'] = float(utils.seconds_to_frames(self.config['start'], result['info']['fps']))

            result['percent_complete'] = (result['pos'] / result['info']['frame_count']) * 100

        return result

    # in a given directory find the next video that should be played
    def find_next_file(self, lastPlayed):
        fileList = []

        if(os.path.exists(self.config['path'])):
            # list all files in the directory, filter on mp4
            fileList = utils.list_video_files(self.config['path'])

        if(len(fileList) == 0):
            return {}  # return nothing, no files to find

        index = 0

        # get the index of the last played file (if exists)
        try:
            index = fileList.index(os.path.basename(lastPlayed))
            index = index + 1  # get the next one

        except ValueError:
            index = 0  # just use the first one

        # go back to start of list if we got to the end
        if(index >= len(fileList)):
            index = 0

        # return this video
        return self.analyze_video(os.path.join(self.config['path'], fileList[index]))

    def find_prev_file(self, lastPlayed):
        fileList = []

        if(os.path.exists(self.config['path'])):
            # list all files in the directory, filter on mp4
            fileList = utils.list_video_files(self.config['path'])

        if(len(fileList) == 0):
            return {}  # return nothing, no files to find

        index = 0

        # get the index of the last played file (if exists)
        try:
            index = fileList.index(os.path.basename(lastPlayed))
            index = index - 1  # get the previous one

        except ValueError:
            index = 0  # just use the first one

        # go back to the end of the list if below 0
        if(index < 0):
            index = len(fileList) - 1

        # return this video
        return self.analyze_video(os.path.join(self.config['path'], fileList[index]))

    def seek_video(self, aVideo, percent):
        # convert the percent to a frame amount
        frames = (percent / 100) * aVideo['info']['frame_count']

        # check that we aren't below the min start, no need to check end as this is subtacted during analyzer above
        startPos = float(utils.seconds_to_frames(self.config['start'], aVideo['info']['fps']))
        if(frames < startPos):
            frames = startPos

        aVideo['pos'] = frames
        aVideo['percent_complete'] = (aVideo['pos'] / aVideo['info']['frame_count']) * 100

        return aVideo
