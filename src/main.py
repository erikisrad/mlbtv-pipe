import subprocess
import time
from mlbtv_account import Account
from mlbtv_stream import Stream
import mlb_stats
from datetime import timedelta
import sys
import logging
import os
from vlc_driver import VLC_Handler

APP = "mlbtv-pipe"

def main():

    # CONFIGURE LOGGING
    appdata_local = os.getenv("LOCALAPPDATA")
    log_file_path = os.path.join(appdata_local, APP, f"{APP}.log")
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=log_file_path, 
                        encoding='utf-8',
                        format='%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    logger.debug(f"{APP} started")

    # file_handler = next(
    #     (h for h in logging.getLogger().handlers if isinstance(h, logging.FileHandler)),
    #     None
    # )

    # if file_handler:
    #     print(f"Log file location: {file_handler.baseFilename}")
    # else:
    #     print("No FileHandler found.")

    account = Account()
    game = mlb_stats.prompt_games()
    stream_choice = mlb_stats.prompt_streams(game)
    stream = Stream(account.get_token(), stream_choice["GamePK"], stream_choice["MediaID"])

    media = stream._gen_commercial_breaks()

    vh = VLC_Handler(stream)
    vh.start()

    logger.info("end of file")

if __name__ == '__main__':
    main()

