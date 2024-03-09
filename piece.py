"""Piece class."""

PIECES = {
    # Letter: (name, value, movement)

    # Standard pieces
    'K': ('king', 20,  # moves 1 square in any direction
          ((0, 1, 1), (1, 1, 1))),  # can also castle, royal in standard chess
    'Q': ('queen', 9,  # rook + bishop
          ((0, 1, float('inf')), (1, 1, float('inf')))),
    'R': ('rook', 5,  # moves vertically or horizontally
          ((0, 1, float('inf')),)),
    'B': ('bishop', 5,  # moves diagonally
          ((1, 1, float('inf')),)),
    'N': ('knight', 3,  # moves 2 squares in one direction, 1 square in another
          ((1, 2, 1),)),
    'P': ('pawn', 1,  # moves 1 square forwards, or 2 from the first 2 ranks
          ((0, 1, 0.4), (1, 1, 0.1))),  # captures 1 square diagonally forwards
                                        # also en passants and promotes

    # Fairy pieces
    'A': ('amazon', 12,  # queen + knight
          ((0, 1, float('inf')), (1, 1, float('inf')), (1, 2, 1))),
    'C': ('camel', 3,  # moves 3 squares in one direction, 1 square in another
          ((1, 3, 1),)),
    'D': ('1-point queen', 1,  # queen but worth 1 point in 4-player chess
          ((0, 1, float('inf')), (1, 1, float('inf')))),
    'E': ('chancellor', 7,  # rook + knight
          ((0, 1, float('inf')), (1, 2, 1))),
    'F': ('ferz', 1,  # moves 1 square diagonally
          ((1, 1, 1),)),
    'G': ('grasshopper', 3,  # queen but must land directly after a piece
          ((0, 1, -1), (1, 1, -1))),  # must jump (hopper)
    'H': ('archbishop', 7,  # bishop + knight
          ((1, 1, float('inf')), (1, 2, 1))),
    'I': ('alfil', 1,  # moves exactly 2 squares diagonally
          ((2, 2, 1),)),
    'J': ('alfil-rider', 5,  # repeated alfil
          ((2, 2, float('inf')),)),
    'L': ('camel-rider', 7,  # repeated camel
          ((1, 3, float('inf')),)),
    'M': ('general', 5,  # king + knight
          ((0, 1, 1), (1, 1, 1), (1, 2, 1))),
    'O': ('knight-rider', 7,  # repeated knight
          ((1, 2, float('inf')),)),
    'S': ('dabbaba', 1,  # moves exactly 2 squares vertically or horizontally
          ((0, 2, 1),)),
    'T': ('dabbaba-rider', 5,  # repeated dabbaba
          ((0, 2, float('inf')),)),
    'U': ('xiangqi horse', 3,  # knight but cannot jump
          ((1, 2, 1),)),  # but cannot jump
    'V': ('wildebeest', 5,  # knight + camel
          ((1, 2, 1), (1, 3, 1))),
    'W': ('wazir', 1,  # moves 1 square vertically or horizontally
          ((0, 1, 1),)),
    'X': ('brick', 0,  # cannot move or be captured, does not have a colour
          ()),
    'x': ('transparent brick', 0,  # same as brick but is transparent
          ()),
    'Y': ('alibaba', 3,  # dabbaba + alfil
          ((0, 2, 1), (2, 2, 1))),
    'Z': ('alibaba-rider', 7,  # repeated alibaba
          ((0, 2, float('inf')), (2, 2, float('inf')))),
    '\u039B': ('dragon bishop', 7,  # bishop + xiangqi horse (lambda, chess.com
                                    # uses delta)
               ((1, 1, float('inf')), (1, 2, 1))),  # but cannot jump as knight
    '\u0398': ('duck', 0,  # brick (theta)
               ()),  # but can be moved to any empty square after each turn

    # Fairy pawns

    # All pawns move 1 square forwards or 2 from the first 2 ranks.
    # Pawns can capture en passant and promote.
    # They only differ in the directions (forward or diagonally forward)
    # they can move and capture.

    '\u0391': ('berolina', 1,  # reverse pawn (alpha)
               ((1, 1, 0.4), (0, 1, 0.1))),  # move diagonal, capture forward
    '\u0392': ('soldier', 1,  # forwards pawn (beta)
               ((0, 1, 0.5),)),  # move and capture forward
    '\u0393': ('stone general', 1,  # diagonal pawn (gamma)
               ((1, 1, 0.5),)),  # move and capture diagonally
    '\u0394': ('sergeant', 1,  # super pawn (delta)
               ((0, 1, 0.5), (1, 1, 0.5))),  # move and capture forward or
                                             # diagonally

    # Other
    ' ': ('empty', 0, ()),
    '?': ('unknown', 0, ())
}


class Piece:
    """
    Piece class.

    Attributes
    ----------
    name : str
        Name of the piece.
    colour : {'', 'w', 'b'}
        Colour of piece. 'w' for white, 'b' for black, '' for empty.
    letter : str
        Single letter to identify the piece, usually the initial of the
        name. Capital letter for white pieces, lowercase letter for
        black pieces, space for 'empty' piece.
    movement : tuple of tuple of (int, int, float)
        Directions the piece can move in. The three elements of each
        inner tuple represent movement in one direction, movement in a
        perpendicular direction, and the range of the piece. A leaper
        will have a range of 1, a rider will have an infinite range, and
        a limited ranging piece will have some integer range > 1.
        Hoppers must land one square after jumping over one piece
        represented by a range of -1. Pawns which only moves forwards
        have a range of 0.1, 0.4, or 0.5. 0.1 represents must capture,
        0.4 represents must not be obstructed, 0.5 represents can move
        or capture, in the direction the tuple represents.
    value : float
        Relative piece value compared to the pawn, based off of 4-player
        chess.
    moves : int
        Number of moves played with this piece.
    distance : float
        Total distance travelled in squares by this piece.
    """
    def __init__(self, letter: str = ' '):
        """
        Initiate piece attributes.

        Parameters
        ----------
        letter : str
            Letter of piece.
        """
        self.letter = letter

        if letter in {'X', 'x'}:
            self.colour = ''
        elif letter in {'\u0398', '\u03B8'}:
            letter = '\u0398'
            self.colour = ''
        elif letter.isupper():
            self.colour = 'w'
        elif letter.islower():
            self.colour = 'b'
            letter = letter.upper()
        else:
            self.colour = ''

        self.name, self.value, self.movement = PIECES.get(letter, PIECES['?'])
        self.moves = 0
        self.distance = 0

    def __bool__(self) -> bool:
        return self.letter != ' '

    def __str__(self) -> str:
        """Return Unicode symbol if standard piece else self.letter."""
        if self.letter in 'KQRBNPkqrbnp':
            return chr(9812 + 'KQRBNPkqrbnp'.index(self.letter))
        return self.letter

    def __eq__(self, other) -> bool:
        if isinstance(other, Piece):
            return self.letter == other.letter
        return False
