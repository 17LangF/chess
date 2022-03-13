"""Move class."""


class Move:
    """
    Move class.

    Attributes
    ----------
    name : str
        Move in Standard Algebraic Notation.
    x, y : int
        Coordinates of starting square of move.
    nx, ny : tuple of int
        Coordinates of ending square of move.
    castling : str
        Castling availability just before the move is played. If neither
        side can castle, this is '-'. Otherwise, this has one or more
        letters:
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
        Starts at 1 and is incremented after every black move.
    capture : Piece or None
        Piece which is captured if move is a capture else None.
    info : tuple of (int, int) or None
        If move is castle, this is the coordinate of the starting square
        of the rook. If move is en passant, this is the coordinate of
        the square of the pawn which is captured. Else None.
    distance : float
        Distance the piece moving travels, calculated using the
        Pythagorean theorem.
    """
    def __init__(self, name: str, x: int, y: int, nx: int, ny: int, board,
                 capture=None, info: tuple = None):
        """
        Initiate move attributes.

        Parameters
        ----------
        name : str
            Move in Standard Algebraic Notation.
        x, y : int
            Coordinates of starting square of move.
        nx, ny : int, int
            Coordinates of ending square of move.
        board : Board
            Board state before the move is played.
        capture : Piece, default=None
            Piece which is captured if move is a capture else None.
        info : tuple of (int, int), default=None
            If move is castle, this is the coordinate of the starting
            square of the rook. If move is en passant, this is the
            coordinate of the square of the pawn which is captured. Else
            None.
        """
        self.name = name
        self.y = y
        self.x = x
        self.ny = ny
        self.nx = nx
        self.active = board.active
        self.castling = board.castling
        self.en_passant = board.en_passant
        self.halfmove = board.halfmove
        self.fullmove = board.fullmove
        self.capture = capture
        self.info = info
        self.distance = ((nx-x)**2 + (ny-y)**2) ** 0.5

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if isinstance(other, tuple):
            return (self.x, self.y, self.nx, self.ny)[:len(other)] == other
        return self.name == str(other)
