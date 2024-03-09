"""Board class."""

import random
from datetime import datetime

from move import Move
from piece import Piece


class Board:
    """
    Board class.

    Attributes
    ----------
    variant : str
        Variant.
    size : tuple of (int, int)
        Number of columns and rows of the board.
    board : list of list of Piece
        State of the chess board.
    active : {'w', 'b'}
        Active colour. 'w' means White moves next, 'b' means Black moves
        next.
    castling : str
        Castling availability. If neither side can castle, this is '-'.
        Otherwise, this has one or more letters:
            'K': White can castle kingside
            'Q': White can castle queenside
            'k': Black can castle kingside
            'q': Black can castle queenside
    en_passant : str
        En passant target square in algebraic notation. If a pawn has
        just made a two-square move, this is the square behind the pawn.
        Otherwise, '-'.
    halfmove : int
        The number of halfmoves since the last capture or pawn move.
    fullmove : int
        Starts at 1 and is incremented after every Black move.
    tag_pairs : dict of {str: str}
        Details of the game, used in PGN.
    moves : list of Move
        Moves played on the board.
    undone_moves : list of Move
        Moves that have been undone in order. Used to redo moves.
    legal_moves : list of Move
        All legal moves of the current position.
    illegal_moves : list of Move
        All illegal moves of the current position due to king in check.
    promotion : str
        Letters of every piece a pawn can promote to.
    evaluation : float
        Computer evaluation of the position. Infinity for checkmate.
        Integer type means moves until mate. Positive for white
        advantage, negative for black advantage, 0 for draw.

    Raises
    ------
    ChessError
        When there is an error due to the rules of chess.
    """
    def __init__(self, variant: str = 'Standard'):
        """
        Initiate class.

        Parameters
        ----------
        variant : str, default='Standard'
            Chess variant to set up board.
        """
        self.reset()

        # Board covered in ducks (used primarily for testing)
        if variant.startswith('Duckboard'):
            try:
                size = variant[10:].split('x')
                self.size = size = x, y = tuple(map(int, size))
                if x <= 0 or y <= 0:
                    raise ValueError
            except ValueError:
                variant = 'Duckboard'
                self.size = size = 8, 8
            self.board = [[Piece('\u0398')] * size[0] for _ in range(size[1])]

        # 8xn variants
        elif variant.startswith('8x'):
            try:
                y = int(variant[2:])
                if y < 4 or y == 8:
                    raise ValueError
            except ValueError:
                y = 8
                variant = 'Standard'
            self.size = size = 8, y
            self.board = [[Piece()] * size[0] for _ in range(size[1])]

        # [backrank pieces]
        elif len(variant) > 2 and variant[0] == '[' and variant[-1] == ']':
            pieces = variant[1:-1]
            self.size = size = len(pieces), 8
            self.board = [[Piece()] * size[0] for _ in range(size[1])]
            self.board[0] = [Piece(piece) for piece in pieces.lower()]
            self.board[1] = [Piece('p') for _ in range(size[0])]
            self.board[-2] = [Piece('P') for _ in range(size[0])]
            self.board[-1] = [Piece(piece) for piece in pieces.upper()]

        # Chess960
        if variant in {'Chess960', '960', 'Fisherandom', 'Fisher random',
                       'Chess9LX'}:
            pieces = [None] * 8
            # Place opposite-coloured bishops randomly
            pieces[random.randrange(0, 8, 2)] = 'B'
            pieces[random.randrange(1, 8, 2)] = 'B'
            # Place queen and two knights randomly
            empty = [i for i, piece in enumerate(pieces) if not piece]
            sample = random.sample(empty, 3)
            for i, piece in zip(sample, ('Q', 'N', 'N')):
                pieces[i] = piece
            # Place king between two rooks randomly
            empty = sorted(set(empty) - set(sample))
            for i, piece in zip(empty, ('R', 'K', 'R')):
                pieces[i] = piece

            self.board[0] = [Piece(piece.lower()) for piece in pieces]
            self.board[1] = [Piece('p') for _ in range(8)]
            self.board[-2] = [Piece('P') for _ in range(8)]
            self.board[-1] = [Piece(piece) for piece in pieces]

        # Standard
        elif variant == 'Standard' or variant.startswith('8x'):
            self.board[0] = [Piece(piece) for piece in 'rnbqkbnr']
            self.board[1] = [Piece('p') for _ in range(8)]
            self.board[-2] = [Piece('P') for _ in range(8)]
            self.board[-1] = [Piece(piece) for piece in 'RNBQKBNR']

        self.variant = variant
        if variant != 'Standard':
            self.tag_pairs['Variant'] = variant
            self.tag_pairs['SetUp'] = '1'
            self.tag_pairs['FEN'] = self.get_fen()

        self.legal_moves = self.get_moves()

    def reset(self):
        """Resets board to empty 8x8."""
        self.variant = 'Empty'
        self.size = size = 8, 8
        self.board = [[Piece()] * size[0] for _ in range(size[1])]
        self.active = 'w'
        self.castling = 'KQkq'
        self.en_passant = '-'
        self.halfmove = 0
        self.fullmove = 1
        self.tag_pairs = {
            'Event': '?',
            'Site': 'Python Chess',
            'Date': datetime.today().strftime('%Y.%m.%d'),
            'Round': '?',
            'White': '?',
            'Black': '?',
            'Result': '*',

            'Time': datetime.today().strftime('%H:%M:%S'),
            'WhiteElo': '?',
            'BlackElo': '?',
            'TimeControl': '-'
        }
        self.moves = []
        self.undone_moves = []
        self.legal_moves = []
        self.illegal_moves = []
        self.promotion = 'QNRB'
        self.evaluation = 0.0

    def move(self, move, *, update_moves: bool = True):
        """
        Play move on the board.

        Parameters
        ----------
        move : Move or str
            Move to play on the board.
        update_moves : bool
            Whether to update list of legal moves.

        Raises
        ------
        ChessError
            If move is illegal.
        """
        if isinstance(move, str):
            # Validate whether the given string is a legal move
            if len(move) < 2:
                raise ChessError

            if move[1] == '-':
                piece = 'K'
                move = move.replace('O', '0')
            elif move[0].isupper():
                piece = move[0]
            else:
                piece = 'P'

            for legal_move in self.legal_moves:
                if move == legal_move:
                    move = legal_move
                    break
            else:
                raise ChessError
        elif isinstance(move, Move):
            piece = self.board[move.y][move.x].letter.upper()
        else:
            raise TypeError

        board = self.board
        active = self.active
        name = move.name
        x = move.x
        y = move.y
        nx = move.nx
        ny = move.ny
        capture = move.capture
        board[y][x].moves += 1
        board[y][x].distance += move.distance
        self.moves.append(move)

        # Castle
        if '-' in name:
            rx = move.info[0]
            king = board[y][x]
            rook = board[y][rx]
            board[y][x] = Piece()
            board[y][rx] = Piece()
            board[y][nx] = king
            nrx = nx + (name.count('0') == 3) * 2 - 1
            rook.distance += abs(nrx - rx)
            board[y][nrx] = rook

        # Move piece
        else:
            board[ny][nx] = board[y][x]
            board[y][x] = Piece()

        if piece == 'P':
            # Promotion
            if '=' in name:
                promote = name[name.index('=') + 1]
                if board[ny][nx].colour == 'b':
                    promote = promote.lower()
                moves = board[ny][nx].moves
                distance = board[ny][nx].distance
                board[ny][nx] = Piece(promote)
                board[ny][nx].moves = moves
                board[ny][nx].distance = distance

            # En passant
            if abs(y-ny) == 2:
                file = chr(97+x)
                rank = self.size[1] - (y+ny) // 2
                self.en_passant = f'{file}{rank}'
            else:
                if move.info:
                    board[y][nx] = Piece()
                self.en_passant = '-'
        else:
            self.en_passant = '-'

        # Update castling
        if self.castling != '-':
            if active == 'w':
                k = 'K'
                q = 'Q'
            else:
                k = 'k'
                q = 'q'

            replace = ''

            # Moving king or rook
            if piece == 'K':
                replace = k, q
            elif piece == 'R' and board[ny][nx].moves == 1:
                for kx in range(self.size[0]):
                    if board[y][kx].letter == k:
                        if x > kx:
                            replace = k
                        else:
                            replace = q

            elif capture and not capture.moves:
                if capture.colour == 'w':
                    k = 'K'
                    q = 'Q'
                    r = 'R'
                else:
                    k = 'k'
                    q = 'q'
                    r = 'r'

                # Capturing king or rook
                if capture.letter == k:
                    replace = k, q
                elif capture.letter == r:
                    for kx in range(self.size[0]):
                        if board[ny][kx].letter == k:
                            if kx > nx:
                                if all(board[ny][rx].letter != r or
                                       board[ny][rx].moves
                                       for rx in range(kx)):
                                    replace = q
                            elif all(board[ny][rx].letter != r or
                                     board[ny][rx].moves
                                     for rx in range(kx+1, self.size[0])):
                                replace = k
                            break

            for i in replace:
                self.castling = self.castling.replace(i, '')

            if not self.castling:
                self.castling = '-'

        # Update active, halfmove, fullmove
        if piece == 'P' or 'x' in name:
            self.halfmove = 0
        else:
            self.halfmove += 1

        if active == 'w':
            self.active = 'b'
        else:
            self.active = 'w'
            self.fullmove += 1

        if update_moves:
            # Redo last move
            if self.undone_moves and move == self.undone_moves[-1]:
                self.undone_moves.pop()
                self.legal_moves = self.get_moves()
                return

            self.undone_moves = []
            self.tag_pairs['Result'] = '*'
            self.tag_pairs.pop('Termination', None)
            self.tag_pairs.pop('EndTime', None)

            # Move terminates game
            if move.type == 'checkmate':
                if active == 'w':
                    self.tag_pairs['Result'] = '1-0'
                    self.tag_pairs['Termination'] = f'White won by {move.type}'
                else:
                    self.tag_pairs['Result'] = '0-1'
                    self.tag_pairs['Termination'] = f'Black won by {move.type}'
                time = datetime.today().strftime('%H:%M:%S')
                self.tag_pairs['EndTime'] = time

            elif move.type in {'stalemate', 'insufficient material',
                            '50-move rule', 'repetition'}:
                self.tag_pairs['Result'] = '1/2-1/2'
                self.tag_pairs['Termination'] = f'Game drawn by {move.type}'
                time = datetime.today().strftime('%H:%M:%S')
                self.tag_pairs['EndTime'] = time

            self.legal_moves = self.get_moves()

    def get_moves(self, *, depth: float = 3) -> list:
        """
        Get all moves of the current position of the game.

        Parameters
        ----------
        depth : {3, 2, 1, 0.5, 0}
            0: returns psuedo-legal moves (moves ignoring checks).
            0.5: returns a single legal move if one exists, else [].
            1: returns all legal moves and updates `self.illegal_moves`.
            2: same as 1 but also checks for checkmate and stalemate.
            3: same as 2 but also checks for fifty-move rule and
            threefold repetition.

        Returns
        -------
        list of Move
            Moves of the current position of the game.
        """
        if (self.tag_pairs['Result'] != '*' and not self.undone_moves
                and depth >= 2):
            self.illegal_moves = []
            return []

        board = self.board
        hash = self.get_hash()
        size = self.size
        moves = {}

        for y in range(size[1]):
            for x in range(size[0]):
                piece = board[y][x]
                letter = piece.letter.upper()
                if self.active != piece.colour:
                    continue
                if letter in {'\u0391', '\u0392', '\u0393', '\u0394'}:
                    continue

                # Pawn moves
                if letter == 'P':
                    dy = -1 if piece.colour == 'w' else 1
                    file = chr(97+x)
                    ny = y + dy
                    if not 0 <= ny < size[1]:
                        continue
                    if not board[ny][x]:
                        # Move pawn one square forwards
                        rank = size[1] - ny
                        if y == (0, size[1]-2, 1)[dy]:
                            # Promotion
                            for end in self.promotion:
                                move = f'{file}{rank}={end}'
                                moves[move] = [Move(move, x, y, x, ny, self,
                                                    hash)]
                        else:
                            move = f'{file}{rank}'
                            moves[move] = [Move(move, x, y, x, ny, self, hash)]

                        # Move pawn two squares forwards
                        if dy * y < (0, 2, 3-size[1])[dy]:
                            ny += dy
                            if not board[ny][x]:
                                rank -= dy
                                if y == (0, size[1]-3, 2)[dy]:
                                    # Promotion
                                    for end in self.promotion:
                                        move = f'{file}{rank}={end}'
                                        moves[move] = [Move(move, x, y, x, ny,
                                                            self, hash)]
                                else:
                                    move = f'{file}{rank}'
                                    moves[move] = [Move(move, x, y, x, ny,
                                                        self, hash)]

                    # Pawn captures and en passant
                    ny = y + dy
                    for nx in x-1, x+1:
                        if not 0 <= nx < size[0]:
                            continue

                        capture = board[ny][nx]
                        if capture:
                            if (piece.colour == capture.colour or
                                    not capture.colour):
                                continue

                        new_file = chr(97+nx)
                        rank = size[1] - ny
                        info = None

                        if not capture:
                            if self.en_passant == f'{new_file}{rank}':
                                capture = board[y][nx]
                                info = (nx, y)
                            else:
                                continue

                        if y == (0, size[1]-2, 1)[dy]:
                            # Promotion
                            for end in self.promotion:
                                move = f'{file}x{new_file}{rank}={end}'
                                moves[move] = [Move(move, x, y, nx, ny, self,
                                                    hash, capture, info)]
                        else:
                            move = f'{file}x{new_file}{rank}'
                            moves[move] = [Move(move, x, y, nx, ny, self, hash,
                                                capture, info)]
                    continue

                # Castle
                if letter == 'K':
                    if piece.colour == 'w':
                        k = 'K'
                        q = 'Q'
                        r = 'R'
                    else:
                        k = 'k'
                        q = 'q'
                        r = 'r'

                    for side in k, q:
                        if side not in self.castling:
                            continue

                        if side == k:
                            for rx in range(x+1, size[0]):
                                square = board[y][rx]
                                if square.letter == r and not square.moves:
                                    break
                            else:
                                rx = size[0] - 1
                            start = min(x, size[0]-3)
                            end = max(rx, size[0]-2)
                        else:
                            for rx in range(x-1, -1, -1):
                                square = board[y][rx]
                                if square.letter == r and not square.moves:
                                    break
                            start = min(rx, 2)
                            end = max(x, 3)

                        king = 0
                        rook = 0
                        castle = True

                        for square in board[y][start:end+1]:
                            if square.letter == k and not square.moves:
                                king += 1
                            elif square.letter == r and not square.moves:
                                rook += 1
                            elif square:
                                castle = False
                                break

                        if castle and king == rook == 1:
                            if side == k:
                                nx = size[0]-2
                                moves['0-0'] = [Move('0-0', x, y, nx, y, self,
                                                     hash, info=(rx, y))]
                            else:
                                moves['0-0-0'] = [Move('0-0-0', x, y, 2, y,
                                    self, hash, info=(rx, y))]

                # Moves of symmetrically moving pieces
                for move_x, move_y, maximum in piece.movement:
                    maximum = min(max(size), maximum)
                    # Rotate/reflect the movement vector in all 8 directions
                    for direction in range(8):
                        if direction % 2:
                            if move_x == move_y:
                                continue
                            dx = move_y
                            dy = move_x
                        else:
                            dx = move_x
                            dy = move_y
                        if direction // 2 % 2:
                            if not dy:
                                continue
                            dy *= -1
                        if direction // 4 % 2:
                            if not dx:
                                continue
                            dx *= -1

                        nx = x
                        ny = y
                        for _ in range(maximum):
                            # Break if move takes piece off the board
                            nx += dx
                            if not 0 <= nx < size[0]:
                                break
                            ny += dy
                            if not 0 <= ny < size[1]:
                                break

                            # Disallow capturing own piece
                            destination = board[ny][nx]
                            if piece.colour == destination.colour:
                                break
                            # Capturing opponent's piece
                            if destination:
                                if not destination.colour:
                                    break
                                middle = 'x'
                                capture = board[ny][nx]
                            else:
                                middle = ''
                                capture = None

                            file = chr(97+nx)
                            rank = size[1]-ny
                            move = f'{letter}{middle}{file}{rank}'
                            move = Move(move, x, y, nx, ny, self, hash,
                                        capture)
                            moves.setdefault(move.name, []).append(move)
                            if capture:
                                break

        # Remove moves if illegal due to check
        if depth:
            if depth >= 1:
                self.illegal_moves = []
            for name, details in moves.items():
                for i, move in list(enumerate(details))[::-1]:
                    self.move(move, update_moves=False)

                    # Illegal castling
                    illegal_castle = False
                    if '-' in move.name:
                        step = 1 if move.name.count('0') == 2 else -1
                        king_range = range(move.x, move.nx, step)
                        if any(self.is_check((x, move.y)) for x in king_range):
                            illegal_castle = True

                    # Move is illegal
                    if illegal_castle or self.is_check(self.active):
                        illegal_move = moves[name].pop(i)
                        if depth >= 2:
                            self.illegal_moves.append(illegal_move)
                    # Move is legal
                    elif depth == 0.5:
                        self.undo(update_moves=False)
                        return [move]
                    self.undo(update_moves=False)

        # Disambiguate moves
        for name, details in moves.items():
            if len(details) == 1:
                continue

            xs = [move.x for move in details]
            ys = [move.y for move in details]
            for move in details:
                x = move.x
                y = move.y

                if xs.count(x) == 1:
                    middle = chr(97+x)
                elif ys.count(y) == 1:
                    middle = size[1]-y
                else:
                    middle = f'{chr(97+x)}{size[1]-y}'

                move.name = f'{name[0]}{middle}{name[1:]}'

        moves = [move for detail in moves.values() for move in detail]

        # Check for game termination and checks
        if depth >= 2:
            colour = self.active
            for move in moves:
                self.move(move, update_moves=False)

                if not self.get_moves(depth=0.5):
                    self.active = colour
                    if self.is_check(colour):
                        move.name = move.name + '#'
                        move.type = 'checkmate'
                    else:
                        move.type = 'stalemate'
                else:
                    if depth == 3:
                        hash = self.get_hash()

                        # Draw by insufficient material
                        if move.capture:
                            position = hash[1]
                            pieces = [i for i in position
                                      if i not in {' ', 'K', 'k'}]
                            # King vs king
                            if not pieces:
                                move.type = 'insufficient material'
                            # King vs king + minor piece
                            elif (len(pieces) == 1 and
                                  pieces[0] in {'N', 'n', 'B', 'b'}):
                                move.type = 'insufficient material'
                            # Kings and bishops of the same colour
                            elif set(pieces).issubset({'B', 'b'}):
                                bishops = [0, 0]
                                for y in range(size[1]):
                                    for x in range(size[0]):
                                        if board[y][x].letter in {'B', 'b'}:
                                            bishops[(x + y) % 2] = 1
                                if sum(bishops) == 1:
                                    move.type = 'insufficient material'

                        # Draw by fifty-move rule
                        elif self.halfmove >= 100:
                            move.type = '50-move rule'

                        # Draw by repetition
                        else:
                            repetitions = 1
                            for past_move in reversed(self.moves):
                                if past_move.hash == hash:
                                    repetitions += 1
                                    if repetitions == 3:
                                        move.type = 'repetition'
                                        break

                                if (not past_move.halfmove or
                                        past_move.castling != self.castling):
                                    break

                    self.active = colour
                    if self.is_check(colour):
                        move.name += '+'

                self.undo(update_moves=False)

        return moves

    def is_check(self, coord) -> bool:
        """
        Return whether the specified colour checks the opposing king.

        Parameters
        ----------
        coord : tuple of (int, int) or {'w', 'b'}
            If tuple, coordinates of square to be checked for attacks.
            If string, use the coordinates of the king of the opposing
            colour.

        Returns
        -------
        bool
            Whether the king is checked by the specified colour.
        """
        if isinstance(coord, str):
            k = 'k' if coord == 'w' else 'K'
            for y in range(self.size[1]):
                for x in range(self.size[0]):
                    if self.board[y][x].letter == k:
                        coord = (x, y)
                        break
                else:
                    continue
                break

        moves = self.get_moves(depth=0)
        return any((move.nx, move.ny) == coord for move in moves)

    def undo(self, *, update_moves: bool = True):
        """Undo last move."""
        if not self.moves:
            return

        board = self.board
        move = self.moves.pop()
        x = move.x
        y = move.y
        nx = move.nx
        ny = move.ny
        info = move.info
        board[ny][nx].moves -= 1
        board[ny][nx].distance -= move.distance

        # Castle
        if '-' in move.name:
            nrx = nx + (move.name.count('0') == 3) * 2 - 1
            king = board[y][nx]
            rook = board[y][nrx]
            board[y][nx] = Piece()
            board[y][nrx] = Piece()
            board[y][x] = king
            rook.distance -= abs(nrx - info[0])
            board[y][info[0]] = rook

        else:
            board[y][x] = board[ny][nx]
            # Capture
            if move.capture:
                if move.info:
                    # En passant
                    board[ny][nx] = Piece()
                    board[info[1]][info[0]] = move.capture
                else:
                    board[ny][nx] = move.capture
            else:
                board[ny][nx] = Piece()

            # Promotion
            if '=' in move.name:
                moves = board[ny][nx].moves
                distance = board[ny][nx].distance
                board[y][x] = Piece('P' if board[y][x].colour == 'w' else 'p')
                board[y][x].moves = moves
                board[y][x].distance = distance

        # Update board attributes
        self.active = move.active
        self.castling = move.castling
        self.en_passant = move.en_passant
        self.halfmove = move.halfmove
        self.fullmove = move.fullmove

        if update_moves:
            self.undone_moves.append(move)
            self.legal_moves = self.get_moves()

        return move

    def redo(self, *, update_moves: bool = True):
        """Redo last undone move."""
        if not self.undone_moves:
            return
        move = self.undone_moves[-1]
        self.move(move, update_moves=update_moves)
        return move

    def perft(self, depth: int = 1) -> int:
        """Return number of move paths of certain depth."""
        # Base cases
        if not depth:
            return 1
        if depth == 1:
            return len(self.get_moves(depth=2))

        nodes = 0
        for move in self.get_moves(depth=2):
            self.move(move, update_moves=False)
            nodes += self.perft(depth-1)  # Recursive call
            self.undo(update_moves=False)

        return nodes

    def get_hash(self) -> tuple:
        """Return hash of position."""
        hash = ''.join(''.join(piece.letter for piece in rank)
                       for rank in self.board)
        en_passant = self.en_passant
        if en_passant != '-':
            x = ord(en_passant[0]) - 97
            y = self.size[1] - int(en_passant[1])
            y += 1 if self.active == 'w' else -1
            pawn = 'P' if self.active == 'w' else 'p'
            if not (x > 0 and self.board[y][x-1].letter == pawn or
                    x < self.size[0]-1 and self.board[y][x+1].letter == pawn):
                en_passant = '-'

        return self.active, hash, self.castling, en_passant

    def get_fen(self) -> str:
        """Return FEN (Forsyth-Edwards Notation) of board position."""
        board = '/'.join(''.join(piece.letter for piece in rank)
                         for rank in self.board)
        for n in range(self.size[0], 0, -1):
            board = board.replace(' '*n, str(n))
        return (f'{board} {self.active} {self.castling} {self.en_passant} '
                f'{self.halfmove} {self.fullmove}')

    def get_pgn(self) -> str:
        """Return PGN (Portable Game Notation) of game."""
        # Format tags
        tags = [f'[{tag} "{info}"]' for (tag, info) in self.tag_pairs.items()]
        tags = '\n'.join(tags)
        moves = self.moves + self.undone_moves[::-1]

        # Set starting move from FEN if available
        black_first = False
        start_num = 1
        if 'FEN' in self.tag_pairs:
            fen = self.tag_pairs['FEN'].split()
            if moves and fen[1] == 'b':
                black_first = True
                moves = ['..'] + moves
            start_num = int(fen[5])

        # Format moves
        moves = [moves[::2], moves[1::2]]
        if len(moves[0]) != len(moves[1]):
            moves[1].append('')
        moves = [f'{i}. {w} {b}'
                 for i, (w, b) in enumerate(zip(*moves), start_num)]
        moves = ' '.join(moves).replace('0-0-0', 'O-O-O').replace('0-0', 'O-O')
        if moves and moves[-1] != ' ':
            moves += ' '
        if black_first:
            moves = moves.replace(' ', '', 1)

        return f'{tags}\n\n{moves}{self.tag_pairs["Result"]}'

    def load_fen(self, fen: str):
        """
        Load FEN (Forsyth-Edwards Notation).

        Parameters
        ----------
        fen : str
            FEN to load.
        """
        self.reset()
        board, *info = fen.strip().split(' ')

        # Replace numbers with empty squares
        numbers = ['']
        for letter in board:
            if letter.isdecimal():
                numbers[-1] += letter
            else:
                numbers.append('')

        for number in sorted(numbers, key=len, reverse=True):
            if not number:
                break
            board = board.replace(number, int(number) * ' ')

        if not set(board).issubset('KQRBNPkqrbnp /'):
            self.variant = 'Fairy'
        elif not 1 == board.count('K') == board.count('k'):
            self.variant = 'Bad number of kings'
        else:
            self.variant = 'Standard'

        # Format piece placement data into array
        board = board.split('/')
        size = len(max(board, key=len)), len(board)
        if not size[0] * size[1]:
            # Boards with 0 area are invalid
            self.variant = 'Empty'
            return
        self.size = size
        board = [row.ljust(size[0]) for row in board]
        self.board = [[Piece(letter) for letter in row] for row in board]

        # Parse other information in FEN
        info = (info + 5*[' '])[:5]
        active, castling, en_passant, halfmove, fullmove = info
        self.active = 'b' if active == 'b' else 'w'
        self.castling = castling if (castling and
            set(castling).issubset('KQkq')) else '-'
        self.en_passant = en_passant if (len(en_passant) > 1 and
            en_passant[0].isalpha() and en_passant[1:].isdecimal()) else '-'

        self.halfmove = int(halfmove) if halfmove.isdecimal() else 0
        self.fullmove = int(fullmove) if halfmove.isdecimal() else 1

        self.tag_pairs['SetUp'] = '1'
        self.tag_pairs['FEN'] = self.get_fen()

        if size != (8, 8):
            self.variant = f'{size[0]}x{size[1]}'
        elif self.is_check(self.active):
            self.variant = 'No king'

        self.legal_moves = self.get_moves()

        # FEN position is checkmate or stalemate
        if not self.legal_moves:
            self.active = 'b' if self.active == 'w' else 'w'
            if self.is_check(self.active):
                if self.active == 'w':
                    self.tag_pairs['Result'] = '1-0'
                    self.tag_pairs['Termination'] = f'White won by checkmate'
                else:
                    self.tag_pairs['Result'] = '0-1'
                    self.tag_pairs['Termination'] = f'Black won by checkmate'
            else:
                self.tag_pairs['Result'] = '1/2-1/2'
                self.tag_pairs['Termination'] = f'Game drawn by stalemate'

            self.active = 'b' if self.active == 'w' else 'w'
            self.tag_pairs['EndTime'] = datetime.today().strftime('%H:%M:%S')

    def load_pgn(self, pgn: str):
        """
        Load PGN (Portable Game Notation).

        Parameters
        ----------
        pgn : str
            PGN to load.
        """
        self.reset()
        tag_pairs = {}
        moves = ''

        # Parse tag pairs and moves
        pgn = '\n'.join([line.strip() for line in pgn.splitlines()])
        if pgn.startswith('['):
            try:
                tags, moves, *_ = pgn.split('\n\n', maxsplit=2)
                for tag in tags.splitlines():
                    if tag.startswith('[') and tag.endswith(']'):
                        key, value = tag[1:-1].split(maxsplit=1)
                        if value.startswith('"') and value.endswith('"'):
                            if len(value) > 2:
                                tag_pairs[key] = value[1:-1]
                            else:
                                tag_pairs[key] = '?'
                            continue
                    return
            except ValueError:
                return
        else:
            moves = pgn.split('\n\n', maxsplit=1)[0]

        if 'FEN' in tag_pairs:
            self.load_fen(tag_pairs['FEN'])
        else:
            self.variant = 'Standard'
            self.board[0] = [Piece(piece) for piece in 'rnbqkbnr']
            self.board[1] = [Piece('p') for _ in range(8)]
            self.board[-2] = [Piece('P') for _ in range(8)]
            self.board[-1] = [Piece(piece) for piece in 'RNBQKBNR']
            self.legal_moves = self.get_moves()

        self.tag_pairs.update(tag_pairs)

        # Remove comments
        moves = list(moves.replace('\\\\', '').replace('\}', ''))
        while ('{' in moves and '}' in moves and
               moves.index('{') < moves.index('}')):
            del moves[moves.index('{'):moves.index('}')+1]

        # Remove variations in parentheses
        cleaned_moves = []
        nest = 0
        for i in moves:
            if i == '(':
                nest += 1
            elif i == ')':
                nest -= 1
            elif not nest:
                cleaned_moves.append(i)

        moves = ''.join(cleaned_moves).split()
        for move in moves:
            # Remove move numbers and other non-moves
            if not (move[0].isalpha() or move == '0-0' or move == '0-0-0'):
                continue
            # Remove annotations
            while not (move[-1].isalnum() or move[-1] in {'+', '#'}):
                move = move[:-1]
                if not move:
                    break
            # Play through all moves on the board
            try:
                self.move(move)
            except ChessError:
                return

        # Set "Result" tag pair
        if moves:
            result = moves[-1]
            if result in {'1-0', '1/2-1/2', '0-1'}:
                self.legal_moves = []
                self.illegal_moves = []
                self.tag_pairs['Result'] = result


class ChessError(Exception):
    """Raise when there is an error due to the rules of chess."""
