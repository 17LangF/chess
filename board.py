"""Board class."""

import random

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
    active : str
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

    moves : list of str
        Moves played on the board.
    promotion : str
        Letters of every piece a pawn can promote to.
    legal_moves: list
        All legal moves of the current position.

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
        self.variant = variant
        self.size = size = 8, 8
        self.board = [[Piece()] * size[0] for _ in range(size[1])]
        pieces = list('RNBQKBNR')

        if variant in {'Chess960', '960', 'Fisher random', 'Chess9LX'}:
            random.shuffle(pieces) # check valid positions

        self.board[0] = [Piece(piece.lower()) for piece in pieces]
        self.board[1] = [Piece('p') for _ in range(size[0])]
        self.board[-2] = [Piece('P') for _ in range(size[0])]
        self.board[-1] = [Piece(piece.upper()) for piece in pieces]

        self.active = 'w'
        self.castling = 'KQkq'
        self.en_passant = '-'
        self.halfmove = 0
        self.fullmove = 1
        self.details = {
            'Event': '?',
            'Site': '?',
            'Date': '????.??.??',
            'Round': '?',
            'White': '?',
            'Black': '?',
            'Result': '*'
        }
        self.moves = []
        self.promotion = 'QNRB'
        self.legal_moves = self.get_moves()

    def move(self, move):
        """
        Play move on the board.

        Parameters
        ----------
        move : Move or str
            Move to play on the board.

        Raises
        ------
        ChessError
            If move is illegal.
        """
        if isinstance(move, str):
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

        board = self.board
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
            nrx = nx + (name == '0-0-0') * 2 - 1
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
            if self.active == 'w':
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

        if self.active == 'w':
            self.active = 'b'
        else:
            self.active = 'w'
            self.fullmove += 1

        self.legal_moves = self.get_moves()

    def get_moves(self, check=True) -> list:
        """
        Get all moves of the current position of the game.

        Parameters
        ----------
        check : bool, default=True
            Whether moves must ensure the current king is not in check.

        Returns
        -------
        list of Move
            Legal moves.
        """
        board = self.board
        size = self.size
        moves = []
        disambiguate = {}

        for y in range(size[1]):
            for x in range(size[0]):
                piece = board[y][x]
                letter = piece.letter.upper()
                if self.active != piece.colour:
                    continue

                # Pawn moves
                if letter == 'P':
                    dy = -1 if piece.colour == 'w' else 1
                    file = chr(97+x)
                    ny = y + dy
                    if not board[ny][x]:
                        # Move pawn one square forwards
                        rank = size[1] - ny
                        if y == (0, size[1]-2, 1)[dy]:
                            # Promotion
                            for end in self.promotion:
                                move = f'{file}{rank}={end}'
                                moves.append(Move(move, x, y, x, ny, self))
                        else:
                            move = f'{file}{rank}'
                            moves.append(Move(move, x, y, x, ny, self))

                        # Move pawn two squares forwards
                        if dy * y < (0, 2, 3-size[1])[dy]:
                            ny += dy
                            if not board[ny][x]:
                                rank -= dy
                                if y == (0, size[1]-2, 1)[dy]:
                                    # Promotion
                                    for end in self.promotion:
                                        move = f'{file}{rank}={end}'
                                        moves.append(Move(move, x, y, x, ny,
                                                          self))
                                else:
                                    move = f'{file}{rank}'
                                    moves.append(Move(move, x, y, x, ny, self))

                    # Pawn captures and en passant
                    ny = y + dy
                    for nx in x-1, x+1:
                        if not 0 <= nx < size[0]:
                            continue

                        capture = board[ny][nx]
                        if piece.colour == capture.colour:
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
                                moves.append(Move(move, x, y, nx, ny, self,
                                                  capture, info))
                        else:
                            move = f'{file}x{new_file}{rank}'
                            moves.append(Move(move, x, y, nx, ny, self,
                                              capture, info))
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
                                moves.append(Move('0-0', x, y, nx, y, self,
                                                  info=(rx, y)))
                            else:
                                moves.append(Move('0-0-0', x, y, 2, y, self,
                                                  info=(rx, y)))

                # Moves of symmetrically moving pieces
                for move_x, move_y, maximum in piece.movement:
                    maximum = min(max(size), maximum)
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
                            nx += dx
                            if not 0 <= nx < size[0]:
                                break
                            ny += dy
                            if not 0 <= ny < size[1]:
                                break

                            destination = board[ny][nx]

                            if piece.colour == destination.colour:
                                break

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
                            move = Move(move, x, y, nx, ny, self, capture)
                            if move.name in disambiguate:
                                disambiguate[move.name].append(move)
                            elif move in moves:
                                index = moves.index(move)
                                disambiguate[move.name] = [moves.pop(index)]
                                disambiguate[move.name].append(move)
                            else:
                                moves.append(move)
                                if capture:
                                    break

        #Remove moves if check

        # Disambiguate moves
        for move, details in disambiguate.items():
            xs = [detail.x for detail in details]
            ys = [detail.y for detail in details]
            for detail in details:
                x = detail.x
                y = detail.y
                nx = detail.nx
                ny = detail.ny
                capture = detail.capture
                if xs.count(x) == 1:
                    middle = chr(97+x)
                elif ys.count(y) == 1:
                    middle = size[1]-y
                else:
                    middle = f'{chr(97+x)}{size[1]-y}'
                new_move = f'{move[0]}{middle}{move[1:]}'
                moves.append(Move(new_move, x, y, nx, ny, self, capture))

        #Add + and # for checks and checkmate
        return moves

    def ischeck(self, square: tuple = None, active: str = None) -> bool:
        board = self.board
        size = self.size

        if not active:
            active = self.active
        if not square:
            if active == 'w':
                k = 'K'
            else:
                k = 'k'
            k = 'K' if active == 'w' else 'k'
            for y in range(size[1]):
                for x in range(size[0]):
                    if board[y][x].letter == k:
                        break
                else:
                    continue
                break
            square = y, x

        for ny in range(size[1]):
            for nx in range(size[0]):
                if board[ny][nx] and board[ny][nx] != active:
                    for dx, dy in board[ny][nx].movement:
                        if 0 == (nx-x) % dx == (ny-y) % dy:
                            pass

        return False

    def undo(self):
        """Undo last move."""
        if not self.moves:
            return

        board = self.board
        move = self.moves[-1]
        x = move.x
        y = move.y
        nx = move.nx
        ny = move.ny
        info = move.info
        board[ny][nx].moves -= 1
        board[ny][nx].distance -= move.distance
        self.moves.pop()

        # Castle
        if '-' in move.name:
            nrx = nx + (move.name == '0-0-0') * 2 - 1
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

        self.active = move.active
        self.castling = move.castling
        self.en_passant = move.en_passant
        self.halfmove = move.halfmove
        self.fullmove = move.fullmove
        self.legal_moves = self.get_moves()

    def get_fen(self) -> str:
        """Return FEN (Forsyth-Edwards Notation) of board position."""
        board = '/'.join(''.join(piece.letter for piece in rank)
                         for rank in self.board)
        for n in range(8, 0, -1):
            board = board.replace(' '*n, str(n))
        return (f'{board} {self.active} {self.castling} {self.en_passant} '
                f'{self.halfmove} {self.fullmove}')

    def get_pgn(self) -> str:
        """Returns PGN (Portable Game Notation) of game."""
        details = [f'[{tag} "{info}"]' for (tag, info) in self.details.items()]
        details = '\n'.join(details)
        moves = [self.moves[::2], self.moves[1::2]]
        if len(self.moves) % 2:
            moves[1].append('')
        moves = [f'{i}. {w} {b} ' for i, (w, b) in enumerate(zip(*moves), 1)]
        moves = ''.join(moves).replace('0-0-0', 'O-O-O').replace('0-0', 'O-O')
        return f'{details}\n\n{moves}{self.details["Result"]}'

    def load_fen(self, fen: str):
        """
        Load FEN (Forsyth-Edwards Notation).

        Parameters
        ----------
        fen : str
            FEN to load.
        """
        # Validate FEN checking pawns, checks

    def load_pgn(self, pgn: str):
        """
        Load PGN (Portable Game Notation).

        Parameters
        ----------
        fen : str
            PGN to load.
        """


class ChessError(Exception):
    """Raise when there is an error due to the rules of chess."""