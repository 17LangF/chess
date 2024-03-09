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
    nx, ny : int
        Coordinates of ending square of move.
    active : {'w', 'b'}
        Active colour of the move. 'w' means white move, 'b' means Black
        move.
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
    evaluation : float
        Computer evaluation of the position. Infinity for checkmate.
        Integer type means moves until mate. Positive for white
        advantage, negative for black advantage, 0 for draw.
    hash : tuple of (str, str, str, str)
        Hash of board state before the move is played.
    capture : Piece or None
        Piece which is captured if move is a capture else None.
    info : tuple of (int, int) or None
        If move is castle, these are the coordinates of the starting
        square of the rook. If move is en passant, these are the
        coordinates of the square of the pawn which is captured. Else
        None.
    type : {'', 'checkmate', 'stalemate', 'insufficient material',\
        '50-move rule', 'repetition'}
        Whether the move results in checkmate, stalemate, fifty-move
        rule, or repetition. If move does not end game, this is an empty
        string.
    distance : float
        Distance the piece moving travels, calculated using the
        Pythagorean theorem.
    eval_change : float or None
        The change in evaluation due to the move.
    win_change : float or None
        The change in win probability for white due to the move.
    classification : {'', 'Best', 'Excellent', 'Good', 'Inaccuracy',\
        'Mistake', 'Blunder'}
        Classification of the strength of the move.
    comment : str
        Comment of the move.
    """
    def __init__(self, name: str, x: int, y: int, nx: int, ny: int, board,
            hash: tuple, capture=None, info: tuple = None, type: str = ''):
        """
        Initiate move attributes.

        Parameters
        ----------
        name : str
            Move in Standard Algebraic Notation.
        x, y : int
            Coordinates of starting square of move.
        nx, ny : int
            Coordinates of ending square of move.
        board : Board
            Board state before the move is played.
        hash : tuple of (str, str, str, str)
            Hash of board state before the move is played.
        capture : Piece, default=None
            Piece which is captured if move is a capture else None.
        info : tuple of (int, int), default=None
            If move is castle, these are the coordinates of the starting
            square of the rook. If move is en passant, these are the
            coordinates of the square of the pawn which is captured.
            Else None.
        type : {'', 'checkmate', 'stalemate', 'insufficient material',\
            '50-move rule', 'repetition'}
            Whether the move results in checkmate, stalemate, fifty-move
            rule, or repetition. If move does not end game, this is an
            empty string.
        """
        self.name = name
        self.x = x
        self.y = y
        self.nx = nx
        self.ny = ny
        self.active = board.active
        self.castling = board.castling
        self.en_passant = board.en_passant
        self.halfmove = board.halfmove
        self.fullmove = board.fullmove
        self.evaluation = board.evaluation
        self.hash = hash
        self.capture = capture
        self.info = info
        self.type = type
        self.distance = ((nx-x)**2 + (ny-y)**2) ** 0.5
        self.eval_change = None
        self.win_change = None
        self.classification = ''
        self.comment = ''

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if isinstance(other, tuple):
            return (self.x, self.y, self.nx, self.ny)[:len(other)] == other
        return self.name == str(other)
