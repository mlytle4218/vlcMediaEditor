    def milliseconds_to_hms(self, millis):
        millis = int(millis)
        seconds = (millis/1000)%60
        part_of_seconds = int((seconds - math.floor(seconds)) * 1000)
        seconds = int(seconds)
        minutes = (millis/(1000*60))%60
        minutes = int(minutes)
        hours = (millis/(1000*60*60))%24
        time = ''
        if hours >= 1 and minutes >= 1:
            time = ("{}:{:02d}:{:02d}.{}".format(
                hours, minutes, seconds, part_of_seconds))
        elif minutes >= 1:
            time = ("{:02d}:{:02d}.{}".format(
                minutes, seconds, part_of_seconds))
        else:
            time = ("{:02d}.{}".format(seconds, part_of_seconds))

        return time
