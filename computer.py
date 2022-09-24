"""Chess computers."""

import random


def random_move(board):
    return random.choice(board.legal_moves)
