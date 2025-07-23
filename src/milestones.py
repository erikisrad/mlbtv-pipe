from datetime import timedelta

MILESTONE_TYPE = "milestoneType"
RELATIVE_TIME = "relativeTime"
ABSOLUTE_TIME = "absoluteTime"
TITLE = "title"
KEYWORDS = "keywords"
NAME = "name"
VALUE = "value"
INNING = "INNING"
END = "END"
START = "START"
TOP ="TOP"
BOT = "BOT"
LAST = "LAST"


class Milestones:
    
    def __init__(self, json):

        self._json = json

        self.INNINGS = {}

        for ms in self._json:
            self.add_milestone(ms)

    def add_milestone(self, milestone):

        try:
            mt = milestone.pop(MILESTONE_TYPE)
        except Exception as err:
            print(f"no valid milestone type in {milestone}")
            raise err

        if INNING in mt:
            try:
                keywords = milestone.pop(KEYWORDS)
                kws = {}
                for k in keywords:
                    kws[k[NAME]] = k[VALUE]

                if kws["inning"] not in self.INNINGS:
                    self.INNINGS[kws["inning"]] = {}

                half = "TOP" if kws["top"] == "true" else "BOT"
                if half not in self.INNINGS[kws["inning"]]:
                    self.INNINGS[kws["inning"]][half] = {}

                se = START if START in milestone[TITLE] else END
                # if se not in self.innings[kws["inning"]][half]:
                #     self.innings[kws["inning"]][half][se] = {}

                self.LAST_INNING = (kws["inning"], half)
                self.INNINGS[kws["inning"]][half][se] = milestone

            except Exception as err:
                print(f"failed to process inning {milestone}")
                raise err

            return

        if hasattr(self, mt):
            raise ValueError(f"duplicate milestone type: {mt}")

        try:
            setattr(self, mt, milestone)
        except Exception as err:
            print(f"failed to create attribute for: {milestone}")
            raise err
        
    def get_inning_time(self, inning, half, start_end=START):
        return self.INNINGS[str(inning)][half][start_end][RELATIVE_TIME]

    def get_game_duration(self, pretty=True):
        time = self.get_inning_time(self.LAST_INNING[0], self.LAST_INNING[1], END) - self.get_inning_time(1, TOP, START)
        if pretty:
            time = str(timedelta(seconds=time))
        return time
    
    def get_gameplay_duration(self, pretty=True):
        times = {}
        gameplay = 0
        for inning_key, inning_data in self.INNINGS.items(): #todo take out time between end of top and start of bot
            times[inning_key] = 0
            for half in inning_data:
                start = self.get_inning_time(inning_key, half, START)
                end = self.get_inning_time(inning_key, half, END)
                duration = end - start
                gameplay = gameplay + duration
                times[inning_key] = times[inning_key] + duration
        
        if pretty:
            res = ""
            for k, v in times.items():
                res = res + f"\n{k}: {timedelta(seconds=v)}"
            res = res + f"\ntotal: {timedelta(seconds=gameplay)}"   
            return res
        
        return gameplay
        
    def get_stream_duration(self, pretty=True):
        time =  self.STREAM_STOP[RELATIVE_TIME] - self.STREAM_START[RELATIVE_TIME]
        if pretty:
            time = str(timedelta(seconds=time))
        return time
