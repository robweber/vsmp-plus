from omni_epd import displayfactory

class TwinEpd:
    epd_list = None
    width = 0
    height = 0

    def __init__(self, epd):
        # clone the width and height of the main EPD
        self.width = epd.width
        self.height = epd.height

        # add to list
        self.epd_list = [epd]

        # create the mock epd and add to the list
        mock = displayfactory.load_display_driver('omni_epd.mock')
        mock.width = self.width
        mock.height = self.height
        self.epd_list.append(mock)

    def prepare(self):
        for e in self.epd_list:
            e.prepare()

    def display(self, image):
        for e in self.epd_list:
            e.display(image)

    def sleep(self):
        for e in self.epd_list:
            e.sleep()

    def close(self):
        for e in self.epd_list:
            e.close()
