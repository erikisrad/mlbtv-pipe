from datetime import timedelta
import logging

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

logger = logging.getLogger(__name__)

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
            logger.error(f"no valid milestone type in {milestone}")
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
                logger.error(f"failed to process inning {milestone}")
                raise err

            return

        if hasattr(self, mt):
            raise ValueError(f"duplicate milestone type: {mt}")

        try:
            setattr(self, mt, milestone)
        except Exception as err:
            logger.error(f"failed to create attribute for: {milestone}")
            raise err
        
    def get_stream_duration(self, pretty=True):
        time = self.STREAM_STOP[RELATIVE_TIME] - self.STREAM_START[RELATIVE_TIME]
        if pretty:
            time = str(timedelta(seconds=time))
        return time
