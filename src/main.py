import subprocess
import time
from mlbtv_account import Account
from mlbtv_stream import Stream
import mlb_stats
from datetime import timedelta
import sys
import logging

APP = "mlbtv-pipe"

def main():

    logger = logging.getLogger(__name__)
    logging.basicConfig(filename=f'{APP}.log', 
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
    stream = Stream(account.get_token(), stream_choice["gamepk"], stream_choice["MediaID"])

    stream.gen_playlist()
    mstones = stream.get_milestones()

    subprocess.Popen(["C:/Program Files/VideoLAN/VLC/vlc.exe", stream.stream_url, "--extraintf=http", "--http-host=localhost", "--http-port=8080", "--http-password=mlbtv"])

    print("end of file")

if __name__ == '__main__':
    main()

