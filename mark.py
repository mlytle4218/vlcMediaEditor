class Mark():
    """
        A Class that holds the data for the positions of the edits. They represent
        the beginning of audio that will be removed and the position where the audio
        will begin again.
    """
    def __init__(self, position=-1):
        self.start = position
        self.end = position

    def timeStamp(self,duration,current):
        out = duration * current
        millis = int(out)
        seconds = round((millis/1000) % 60, 3)
        minutes = (millis/(1000*60)) % 60
        minutes = int(minutes)
        hours = int((millis/(1000*60*60)) % 24)
        time = ""
        if hours >= 1:
            time = "{} hours ".format(hours)
        if minutes >= 1:
            time += "{} minutes ".format(minutes)
        if seconds >= 1:
            time  += "{} seconds".format(seconds)
        return time

    def get_time(self, duration):
        return self.timeStamp(duration, self.start) + " - " + self.timeStamp(duration, self.end)
        
    
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
        Method to check if a position overlaps with current mark

        Arguments - position - float - the proposed position

        Returns True if there is overlap and False if not
        """
        return self.start <= position <= self.end


    # def sortMarks(self):
    #     """
    #     Method to sort the marks into time displacement order. ie - if you have 
    #     two marks and add a third between the first and second, it makes the reorders
    #     the list to put it in the middle for cycling
    #     """
    #     pass

    def __eq__(self, other):
        return (self.start == other.start)

    def __ne__(self, other):
        return (self.start != other.start)

    def __lt__(self, other):
        return (self.start < other.start)

    def __le__(self, other):
        return (self.start <= other.start)

    def __gt__(self, other):
        return (self.start > other.start)

    def __ge__(self, other):
        return (self.start >= other.start)