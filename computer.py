"""Chess computers."""

import random
import subprocess
import time

from piece import PIECES


def get_engine(engine: str):
    """Return engine function."""
    engines = {
        'Firstmove': first_move,
        'Random': random_move,
        'Stockfish': stockfish,
        'Taunter': taunter,
        'Drawfish': drawfish,
        'Badfish': badfish
    }
    engines['Mystery'] = random.choice(list(engines.values()))

    # Search if name given is an engine implemented
    if engine in engines:
        return engines[engine]

    if engine.startswith('Stockfish') and engine[9:].isdecimal():
        return lambda board: stockfish(board, elo=int(engine[9:]))

    if engine.endswith('lover'):
        piece = engine[:-5]
        if piece in [info[0].title() for info in PIECES.values()]:
            return lambda board: piece_lover(board, piece.lower())


def open_stockfish(board):
    """Open Stockfish and return Stockfish."""
    if not hasattr(board, 'stockfish'):
        board.stockfish = subprocess.Popen(
            'stockfish\stockfish-windows-x86-64-avx2.exe',
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        board.stockfish.stdout.readline()
    return board.stockfish


def standardise_eval(evaluation: float):
    """Standardise evaluation to between -10 and 10."""
    if evaluation and isinstance(evaluation, int):
        return 10 if evaluation > 0 else -10
    return max(min(evaluation, 10), -10)


def eval_to_win(evaluation: float):
    """Convert engine evaluation to win probability for white."""
    if evaluation and isinstance(evaluation, int):
        return 1 if evaluation > 0 else 0
    return 1 / (1 + 10**(-0.16*evaluation))


def first_move(board):
    """Return first legal move found."""
    if not board.legal_moves:
        return

    return board.legal_moves[0]


def random_move(board):
    """Return random legal move."""
    if not board.legal_moves:
        return

    return random.choice(board.legal_moves)


def piece_lover(board, piece: str):
    """Return random move that moves the specified piece if possible."""
    if not board.legal_moves:
        return

    piece_moves = []
    for move in board.legal_moves:
        if piece == board.board[move.y][move.x].name:
            piece_moves.append(move)
    if piece_moves:
        return random.choice(piece_moves)
    return random_move(board)


def stockfish(board, time: int = 50, elo: int = 3600):
    """Return Stockfish move and update evaluation."""
    # Check whether the variant is standard and has legal moves
    if board.variant != 'Standard' or not board.legal_moves:
        result = board.tag_pairs['Result']
        if result != '*' and not board.undone_moves:
            # Update evaluation to signify the game has finished
            if result == '1-0':
                board.evaluation = float('inf')
            elif result == '0-1':
                board.evaluation = float('-inf')
            else:
                board.evaluation = 0
        return

    # Initialise Stockfish
    stockfish = open_stockfish(board)
    if elo > 2850:
        stockfish.stdin.write('setoption name UCI_LimitStrength value false\n')
    else:
        elo = max(elo, 1350)
        stockfish.stdin.write('setoption name UCI_LimitStrength value true\n')
        stockfish.stdin.write(f'setoption name UCI_Elo value {elo}\n')

    stockfish.stdin.write('setoption name MultiPV value 1\n')
    stockfish.stdin.write(f'position fen {board.get_fen()}\n')
    stockfish.stdin.write(f'go movetime {time}\n')
    stockfish.stdin.flush()
    stockfish.stdout.readline()

    # Read lines to find the 'bestmove' line
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

    # Search for move in list of legal moves
    for legal_move in board.legal_moves:
        if '=' in legal_move.name:
            promote = legal_move.name[legal_move.name.index('=') + 1].lower()
        else:
            promote = ''
        uci = (f'{chr(97+legal_move.x)}{ysize-legal_move.y}'
               f'{chr(97+legal_move.nx)}{ysize-legal_move.ny}{promote}')
        if move == uci:
            return legal_move


def taunter(board, time: int = 50):
    """Return worst stockfish move with an evaluation > 3 until mate."""
    if board.variant != 'Standard' or not board.legal_moves:
        return

    # Initialise Stockfish
    stockfish = open_stockfish(board)
    stockfish.stdin.write('setoption name UCI_LimitStrength value false\n')
    stockfish.stdin.write('setoption name MultiPV value 5\n')
    stockfish.stdin.write(f'position fen {board.get_fen()}\n')
    stockfish.stdin.write(f'go movetime {time}\n')
    stockfish.stdin.flush()
    stockfish.stdout.readline()

    # Search for worst move with evaluation > 300 centipawns
    taunt_move = ''
    while True:
        line = stockfish.stdout.readline().strip().split()
        if not line:
            continue
        if line[0] == 'bestmove':
            if not taunt_move:
                taunt_move = move
            break
        if 'multipv' in line:
            if line[line.index('multipv') + 1] == '1':
                taunt_move = ''
                move = line[line.index('pv') + 1]
            if taunt_move:
                continue

            if 'cp' in line:
                score_type = 'cp'
            else:
                score_type = 'mate'
            evaluation = int(line[line.index(score_type) + 1])

            if evaluation < 300 or score_type == 'mate' and evaluation < 0:
                taunt_move = move
            else:
                move = line[line.index('pv') + 1]

    ysize = board.size[1]

    # Search for move in list of legal moves
    for legal_move in board.legal_moves:
        if '=' in legal_move.name:
            promote = legal_move.name[legal_move.name.index('=') + 1].lower()
        else:
            promote = ''
        uci = (f'{chr(97+legal_move.x)}{ysize-legal_move.y}'
               f'{chr(97+legal_move.nx)}{ysize-legal_move.ny}{promote}')
        if taunt_move == uci:
            return legal_move


def drawfish(board, time: int = 100):
    """Return worst Stockfish move that is not losing."""
    if board.variant != 'Standard' or not board.legal_moves:
        return

    # Intialise Stockfish
    stockfish = open_stockfish(board)
    stockfish.stdin.write('setoption name UCI_LimitStrength value false\n')
    stockfish.stdin.write('setoption name MultiPV value 500\n')
    stockfish.stdin.write(f'position fen {board.get_fen()}\n')
    stockfish.stdin.write(f'go movetime {time}\n')
    stockfish.stdin.flush()
    stockfish.stdout.readline()

    # Search for worst move that is not losing
    draw_move = ''
    while True:
        line = stockfish.stdout.readline().strip().split()
        if not line:
            continue
        if line[0] == 'bestmove':
            if not draw_move:
                draw_move = move
            break
        if 'multipv' in line:
            if line[line.index('multipv') + 1] == '1':
                draw_move = ''
                move = line[line.index('pv') + 1]
            if draw_move:
                continue

            if 'cp' in line:
                score_type = 'cp'
            else:
                score_type = 'mate'
            evaluation = int(line[line.index(score_type) + 1])

            if evaluation < 0:
                draw_move = move
            else:
                move = line[line.index('pv') + 1]

    ysize = board.size[1]

    # Search for move in list of legal moves
    for legal_move in board.legal_moves:
        if '=' in legal_move.name:
            promote = legal_move.name[legal_move.name.index('=') + 1].lower()
        else:
            promote = ''
        uci = (f'{chr(97+legal_move.x)}{ysize-legal_move.y}'
               f'{chr(97+legal_move.nx)}{ysize-legal_move.ny}{promote}')
        if draw_move == uci:
            return legal_move


def badfish(board, time: int = 50):
    """Return worst Stockfish move."""
    if board.variant != 'Standard' or not board.legal_moves:
        return

    # Initialise Stockfish
    stockfish = open_stockfish(board)
    stockfish.stdin.write('setoption name UCI_LimitStrength value false\n')
    stockfish.stdin.write('setoption name MultiPV value 500\n')
    stockfish.stdin.write(f'position fen {board.get_fen()}\n')
    stockfish.stdin.write(f'go movetime {time}\n')
    stockfish.stdin.flush()
    stockfish.stdout.readline()

    # Find the worst move
    while True:
        line = stockfish.stdout.readline().strip().split()
        if not line:
            continue
        if line[0] == 'bestmove':
            break
        if 'pv' in line:
            move = line[line.index('pv') + 1]

    ysize = board.size[1]

    # Find move in list of legal moves
    for legal_move in board.legal_moves:
        if '=' in legal_move.name:
            promote = legal_move.name[legal_move.name.index('=') + 1].lower()
        else:
            promote = ''
        uci = (f'{chr(97+legal_move.x)}{ysize-legal_move.y}'
               f'{chr(97+legal_move.nx)}{ysize-legal_move.ny}{promote}')
        if move == uci:
            return legal_move


def percent_bot(board, engine1, p: float, engine2=random_move):
    """Return engine1 move p% of the time otherwise engine2 move."""
    start_time = time.time()
    if random.random() < p/100:
        move = engine1(board)
    else:
        move = engine2(board)

    # Always make sure to return after at least 50ms
    time.sleep(max(0, 0.05-time.time()+start_time))
    return move
