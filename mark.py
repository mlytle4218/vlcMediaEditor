class Mark():
    """
        A Class that holds the data for the positions of the edits. They represent
        the beginning of audio that will be removed and the position where the audio
        will begin again.
    """
    def __init__(self, position=-1):
        self.start = position
        self.end = position
    
    def is_null(self):
        """
        Method to show if the mark is not fully developed
        """
        return self.start == -1 or self.end == -1

    def __str__(self):
        return str(self.start) + ":" + str(self.end)

    def __getitem__(self, item):
        return self.start

    def reset(self):
        """
        Method to exchange the start and end points if they are backwards.
        """
        if self.start > self.end:
            temp = self.start
            self.start = self.end
            self.end = temp

    def overlap(self, position):
        """
        Method to check if a position is overlaps with current mark

        Arguments - position - float - the proposed position

        Returns True if there is overlap and False if not
        """
        return self.start <= position <= self.end