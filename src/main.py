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

    account = Account()
    game = mlb_stats.prompt_games()
    stream = mlb_stats.prompt_streams(game)

    sys.exit()

    game_info = mlb_stats.get_game_info_for_team_on_date(team_name="Arizona Diamondbacks")

    stream = Stream(account.get_token(), game_info["gamepk"], game_info["stream_id"])

    print(f"stream playback URL: {stream.get_manifest()}")
    print("generating choices...")
    stream.gen_playlist()
    mstones = stream.get_milestones()

    subprocess.Popen(["C:/Program Files/VideoLAN/VLC/vlc.exe", stream.stream_url, "--extraintf=http", "--http-host=localhost", "--http-port=8080", "--http-password=mlbtv"])

    print("end of file")

if __name__ == '__main__':
    main()

