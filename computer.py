"""Chess computers."""

import subprocess
import random


def first_move(board):
    """Return first legal move found."""
    if not board.legal_moves:
        return None

    return board.legal_moves[0]


def random_move(board):
    """Return random legal move."""
    if not board.legal_moves:
        return None

    return random.choice(board.legal_moves)


def open_stockfish(board):
    """Open stockfish and return stockfish."""
    if not hasattr(board, 'stockfish'):
        board.stockfish = subprocess.Popen(
            'stockfish_15_win_x64_avx2\stockfish_15_x64_avx2.exe',
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        board.stockfish.stdout.readline()
    return board.stockfish


def stockfish(board, time: int = 50, elo: int = 3600):
    """Return stockfish move and update evaluation."""
    if board.variant != 'Standard':
        return
    stockfish = open_stockfish(board)
    if elo > 2850:
        stockfish.stdin.write('setoption name UCI_LimitStrength value false\n')
    else:
        elo = max(elo, 1350)
        stockfish.stdin.write('setoption name UCI_LimitStrength value true\n')
        stockfish.stdin.write(f'setoption name UCI_Elo value {elo}\n')

    stockfish.stdin.write(f'position fen {board.get_fen()}\n')
    stockfish.stdin.write(f'go movetime {time}\n')
    stockfish.stdin.flush()
    stockfish.stdout.readline()

    while True:
        line = stockfish.stdout.readline().strip().split()
        if not line:
            continue
        if line[0] == 'bestmove':
            break
        if 'cp' in line:
            score_type = 'cp'
        elif 'mate' in line:
            score_type = 'mate'
        else:
            continue
        evaluation = line[line.index(score_type) + 1]

    evaluation = int(evaluation)
    if board.active == 'b':
        evaluation *= -1

    # Centipawn evaluation
    if score_type == 'cp':
        board.evaluation = evaluation / 100
    # Moves until mate
    else:
        if not evaluation:
            evaluation = float('inf') if board.active == 'b' else float('-inf')
        board.evaluation = evaluation

    move = line[1]
    ysize = board.size[1]

    for legal_move in board.legal_moves:
        if '=' in legal_move.name:
            promote = legal_move.name[legal_move.name.index('=') + 1].lower()
        else:
            promote = ''
        uci = (f'{chr(97+legal_move.x)}{ysize-legal_move.y}'
               f'{chr(97+legal_move.nx)}{ysize-legal_move.ny}{promote}')
        if move == uci:
            return legal_move
