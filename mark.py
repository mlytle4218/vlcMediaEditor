class Mark():
    def __init__(self):
        self.start = -1
        self.end = -1

    def __str__(self):
        return str(self.start) + ":" + str(self.end)

    def __getitem__(self, item):
        return self.start

    def reset(self):
        if self.start > self.end:
            temp = self.start
            self.start = self.end
            self.end = temp