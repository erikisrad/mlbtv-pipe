import logging

logger = logging.getLogger(__name__)

def prompt_streams(game):
    """
    Prompt the user to select a stream for the given game.
    Returns a stream object
    """
    
    game_pk = game["gamePk"]
    

