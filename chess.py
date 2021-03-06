"""Chess - Made by Fred Lang."""

import time
import tkinter as tk
import winsound

from board import Board, ChessError
from piece import Piece


class TkBoard(tk.Frame):
    """
    Tkinter frame with chess board.

    Attributes
    ----------
    board : Board
        State of the board.
    size : tuple of (int, int)
        Number of columns and rows of the board.
    mode : {'setup', 'moves'}
        In setup mode, pieces can be moved to any square or removed from
        the board. In moves mode, only legal moves are allowed.
    auto_promote : bool
        Whether pawn should automatically promote to the default piece
        (usually queen). Hold ctrl, shift, or alt to temporarily disable
        auto-promotion.
    coords : bool
        Whether board should be shown with coordinates.
    rotation : {0, 1, 2, 3}
        Number of 90 degree clockwise rotations from white's perspective
        when showing the board.
    show_legal_moves : bool
        Whether to show legal moves.
    animation_speed : float
        Time in seconds per move.
    pixels : int
        Length of one square in pixels.
    colours_rgb : dict of {str: tuple of (int, int, int)}
        RGB colours of the squares and background.
    colours_hex : dict of {str: str}
        HEX colours of the squares and background.
    selected : list of [int, int, bool] or []
        Coordinates of selected piece and whether the piece should be
        unselected if dropped on the same square.
    promotion : list of [(str, Move)]
        The promotion pieces and corresponding moves when the selection
        menu is currently open.
    mouse : tuple of (int, int) or ()
        Coordinates of the left mouse button if it is down.
    highlights : dict of {(int, int): ((int, int, int), float)}
        Colour and opacity of each highlighted square with coordinates
        given as the key.
    arrow_start : tuple of (int, int) or ()
        Coordinates of start of a possible arrow.
    arrows : dict of {(int, int, int, int): (int, int, int)}
        Colour of each arrow drawn on the board with coordinates of the
        start and end points given as the key.
    move_hints : list of [tuple of (int, int)]
        Coordinates of squares which have move hints.
    canvas : tk.Canvas
        Canvas the board is drawn on.
    images : dict of {str: tk.PhotoImage}
        Images of the pieces.
    """
    def __init__(self, window: tk.Tk, board: Board):
        """
        Initiate class.

        Parameters
        ----------
        window : tk.Tk
            Parent window.
        board : Board
            State of the board.
        """
        self.board = board
        self.size = size = board.size
        self.mode = 'move'
        self.auto_promote = False
        self.coords = True
        self.rotation = 0
        self.show_legal_moves = False
        self.animation_speed = 0.2
        self.pixels = pixels = 78

        self.colours_rgb = {
            'light': (238, 238, 210),
            'dark': (118, 150, 86),
            'highlight': (255, 255, 0),
            'red': (235, 97, 80),
            'orange': (245, 138, 57),
            'yellow': (255, 170, 0),
            'green': (172, 206, 89),
            'cyan': (135, 192, 168),
            'blue': (82, 176, 220),
            'magenta': (176, 142, 166),
            'grey': (175, 166, 145),
            'background': (81, 80, 76)
        }
        self.colours_hex = {colour: rgb_to_hex(rgb)
                            for colour, rgb in self.colours_rgb.items()}

        self.selected = []
        self.promotion = []
        self.mouse = ()
        self.highlights = {}
        self.arrow_start = ()
        self.arrows = {}
        self.move_hints = []

        width = size[0] * pixels
        height = size[1] * pixels

        tk.Frame.__init__(self, window)
        self.canvas = tk.Canvas(self, highlightthickness=0, width=width,
            height=height, background=self.colours_hex['background'])
        self.canvas.pack(fill='both', expand=True)

        # Key bindings
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind('<Button-1>', self.left_click)
        self.canvas.bind('<B1-Motion>', self.left_drag)
        self.canvas.bind('<ButtonRelease-1>', self.left_release)
        self.canvas.bind('<Button-3>', self.right_click)
        self.canvas.bind('<ButtonRelease-3>', self.right_release)
        self.canvas.bind('<KeyPress>', self.key_press)
        self.canvas.bind('<Configure>', self.refresh)
        self.canvas.focus_set()

    def refresh(self, event: tk.Event = None):
        """Redraw board."""
        board = self.board
        size = self.size

        if event:
            # Open and resize piece images
            names = {piece.letter: f'{piece.colour} {piece.name}'.lstrip()
                     for rank in board.board for piece in rank if piece}
            for colour, pieces in (('w', board.promotion),
                                   ('b', board.promotion.lower())):
                for letter in pieces:
                    if letter not in names:
                        names[letter] = f'{colour} {Piece(letter).name}'

            xsize = event.width // size[self.rotation % 2]
            ysize = event.height // size[(self.rotation + 1) % 2]
            self.pixels = pixels = max(1, min(xsize, ysize))
            resize = [(zoom, -(-180 * zoom // pixels)) for zoom in range(1, 5)]
            zoom, subsample = max(resize, key=lambda i: 180 * i[0] // i[1])
            self.images = {letter: tk.PhotoImage(file=f'images/{name}.png')
                           .zoom(zoom).subsample(subsample)
                           for letter, name in names.items()}
        else:
            pixels = self.pixels

        self.canvas.delete('all')
        for y in range(size[1]):
            for x in range(size[0]):
                piece = board.board[y][x]
                if piece.letter == 'x' and self.mode == 'move':
                    continue

                # Squares and highlights
                colour = 'dark' if (x + y + sum(size)) % 2 else 'light'
                if (x, y) in self.highlights:
                    highlight, opacity = self.highlights[x, y]
                    colour = rgb_to_hex(round(a - opacity * (a - b))
                        for a, b in zip(self.colours_rgb[colour], highlight))
                else:
                    colour = self.colours_hex[colour]

                self.canvas.create_rectangle(
                    *self.coords_to_pos(x-0.5, y-0.5),
                    *self.coords_to_pos(x+0.5, y+0.5),
                    width=0, fill=colour, tags=((x, y), 'square')
                )

                if not piece:
                    continue

                # Pieces
                self.canvas.create_image(*self.coords_to_pos(x, y),
                    image=self.images[piece.letter], tags=((x, y), 'piece'))

        # Arrows
        arrows = list(self.arrows.items())
        self.arrows = {}
        for coords, colour in arrows:
            self.draw_arrow(*coords, colour)

        # Coordinates
        if self.coords:
            if self.rotation == 1:
                column = [chr(97+x) for x in range(size[0])]
                row = range(1, size[1]+1)
                column_colour = size[0]
                row_colour = 1
            elif self.rotation == 2:
                column = range(1, size[1]+1)
                row = [chr(96+x) for x in range(size[0], 0, -1)]
                column_colour = 1
                row_colour = size[1]
            elif self.rotation == 3:
                column = [chr(96+x) for x in range(size[0], 0, -1)]
                row = range(size[1], 0, -1)
                column_colour = size[1]
                row_colour = sum(size) + 1
            else:
                column = range(size[1], 0, -1)
                row = [chr(97+x) for x in range(size[0])]
                column_colour = sum(size) + 1
                row_colour = size[0]

            font = ('Segoe UI', int(0.17 * pixels), 'bold')
            x = 0.12 * pixels
            for i, char in enumerate(column):
                y = (i + 0.17) * pixels
                colour = 'dark' if (i + column_colour) % 2 else 'light'
                colour = self.colours_hex[colour]
                self.canvas.create_text(x, y, text=char, fill=colour,
                                        font=font, tags='coords')
            y = (size[(self.rotation + 1) % 2] - 0.17) * pixels
            for i, char in enumerate(row):
                x = (i + 0.85) * pixels
                colour = 'dark' if (i + row_colour) % 2 else 'light'
                colour = self.colours_hex[colour]
                self.canvas.create_text(x, y, text=char, fill=colour,
                                        font=font, tags='coords')

        # Move hints
        move_hints = self.move_hints
        self.move_hints = []
        for move_hint in move_hints:
            self.add_move_hint(*move_hint)

        self.canvas.tag_lower('movehint')
        self.canvas.tag_lower('coords')
        self.canvas.tag_lower('square')

        # Piece dragged
        if self.selected:
            self.canvas.tag_raise((*self.selected[:2], '&&piece'))
            if self.mouse:
                self.canvas.event_generate('<B1-Motion>', x=self.mouse[0],
                                           y=self.mouse[1])

        # Promotion selection menu
        if self.promotion:
            self.promotion_selection(self.promotion)

    def colour_square(self, x: int, y: int, colour: tuple, opacity: float):
        """
        Colour square.

        Parameters
        ----------
        x, y : int
            Coordinate of square.
        colour : tuple of (int, int, int)
            RGB colour. If square is already coloured in the same
            colour, colour is removed.
        opacity : float
            Opacity of the colour.
        """
        square = self.canvas.find_withtag((x, y, '&&square'))
        square_colour = 'dark' if (x + y + sum(self.size)) % 2 else 'light'

        if (x, y) in self.highlights and self.highlights[x, y][0] == colour:
            colour = self.colours_hex[square_colour]
            del self.highlights[x, y]
        else:
            self.highlights[x, y] = colour, opacity
            colour = rgb_to_hex(round(a - opacity * (a - b)) for a, b in
                                zip(self.colours_rgb[square_colour], colour))

        self.canvas.itemconfig(square, fill=colour)

    def draw_arrow(self, x1: int, y1: int, x2: int, y2: int, colour: str):
        """
        Draw arrow.

        Parameters
        ----------
        x1, y1 : int
            Coordinates of start of arrow.
        x2, y2 : int
            Coordinates of end of arrow.
        colour : str
            HEX colour of arrow. If arrow already exists in the same
            colour, arrow is removed.
        """
        coords = x1, y1, x2, y2
        if coords in self.arrows:
            arrow = self.canvas.find_withtag((*coords, '&&arrow'))
            if self.arrows[coords] == colour:
                self.canvas.delete(arrow)
                del self.arrows[coords]
            else:
                self.canvas.itemconfig(arrow, fill=colour)
                self.arrows[coords] = colour
            return

        offset = 0.36
        if x1 == x2:
            if y2 - y1 < 0:
                offset *= -1
            y1 += offset
        else:
            gradient = (y2 - y1) / (x2 - x1)
            offset /= (1 + gradient**2) ** 0.5
            if x2 - x1 < 0:
                offset *= -1
            x1 += offset
            y1 += gradient * offset

        pixels = self.pixels
        arrow = [*self.coords_to_pos(x1, y1), *self.coords_to_pos(x2, y2)]
        width = 0.22 * pixels
        arrowshape = (0.36 * pixels, 0.36 * pixels, 0.15 * pixels)
        self.canvas.create_line(*arrow, fill=colour, arrow=tk.LAST,
            arrowshape=arrowshape, width=width, tags=(coords, 'arrow'))

        self.arrows[coords] = colour

    def add_move_hint(self, x: int, y: int):
        """Add move hint on square at (x, y)."""
        colour = 'dark' if (x + y + sum(self.size)) % 2 else 'light'
        colour = self.colours_rgb[colour]
        if self.is_last_move(x, y):
            colour = (round(a - 0.5 * (a - b)) for a, b in
                        zip(colour, self.colours_rgb['highlight']))
        colour = rgb_to_hex(round(0.9 * i) for i in colour)
        xpos, ypos = self.coords_to_pos(x, y)

        if self.board.board[y][x]:
            width = 0.083 * self.pixels
            r = (self.pixels - width) / 2
            self.canvas.create_oval(xpos-r, ypos-r, xpos+r-1, ypos+r-1,
                width=width, outline=colour, tags='movehint')
        else:
            r = self.pixels / 6
            self.canvas.create_oval(xpos-r, ypos-r, xpos+r-1, ypos+r-1,
                                    fill=colour, width=0, tags='movehint')
        self.move_hints.append((x, y))

    def promotion_selection(self, promotion: list):
        """Create promotion selection menu."""
        sx, sy, _ = self.selected
        x = promotion[0][1].nx
        y = promotion[0][1].ny
        self.canvas.delete('movehint')
        self.move_hints = []
        piece = self.canvas.find_withtag((sx, sy, '&&piece'))
        if not (sx, sy) in self.highlights:
            self.colour_square(sx, sy, self.colours_rgb['highlight'], 0.5)
        self.canvas.coords(piece, *self.coords_to_pos(x, y))
        dy = 1 if self.board.active == 'w' else -1
        self.canvas.create_rectangle(
            *self.coords_to_pos(x-0.5, y-dy*0.5),
            *self.coords_to_pos(x+0.5, y+dy*(len(promotion)-0.5)),
            outline='#7F7F7F', fill='#ffffff', tags='promotion'
        )

        for i, piece in enumerate(promotion):
            promote = piece[0]
            if self.board.active == 'b':
                promote = promote.lower()
            self.canvas.create_image(*self.coords_to_pos(x, y+dy*i),
                image=self.images[promote], tags='promotion')
        self.promotion = promotion

    def motion(self, event: tk.Event):
        """Update cursor graphic."""
        x, y = self.pos_to_coords(event.x, event.y)
        cursor = ''
        if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
            if self.mode == 'setup':
                if self.selected or self.board.board[y][x]:
                    cursor = 'hand2'
            elif self.promotion:
                index = y if self.board.active == 'w' else self.size[1] - y - 1
                move = self.promotion[0][1]
                if x == move.nx and index < len(self.promotion):
                    cursor = 'hand2'
            else:
                if (x, y) in self.board.legal_moves:
                    cursor = 'hand2'
                elif (self.selected and
                      (*self.selected[:2], x, y) in self.board.legal_moves):
                    cursor = 'hand2'
        self.canvas.configure(cursor=cursor)

    def left_click(self, event: tk.Event):
        """Select or drop piece, clear highlights, highlight square."""
        self.mouse = event.x, event.y
        x, y = self.pos_to_coords(event.x, event.y)
        highlight = self.colours_rgb['highlight']

        # Promotion selection
        if self.promotion:
            index = y if self.board.active == 'w' else self.size[1] - y - 1
            move = self.promotion[0][1]
            if x != move.nx or index >= len(self.promotion):
                piece = self.canvas.find_withtag((move.x, move.y, '&&piece'))
                self.canvas.coords(piece, *self.coords_to_pos(move.x, move.y))
                self.colour_square(move.x, move.y, highlight, 0.5)
                self.deselect_piece()
                return

            promote, move = self.promotion[index]
            self.board.move(move)
            self.canvas.delete((move.nx, move.ny, '&&piece'))
            piece = self.canvas.find_withtag((move.x, move.y, '&&piece'))
            if self.board.board[move.ny][move.nx].colour == 'b':
                promote = promote.lower()
            self.canvas.itemconfig(piece, image=self.images[promote],
                                   tags=((move.nx, move.ny), 'piece'))

            for coords, (colour, opacity) in list(self.highlights.items()):
                self.colour_square(*coords, colour, opacity)
            self.colour_square(move.x, move.y, highlight, 0.5)
            self.colour_square(move.nx, move.ny, highlight, 0.5)

            # Sound
            sound = 'promote'
            if move.name[-1] in {'+', '#'}:
                sound = 'check'
            winsound.PlaySound(f'sounds/{sound}.wav', winsound.SND_FILENAME |
                               winsound.SND_ASYNC | winsound.SND_NODEFAULT)

            self.deselect_piece()
            return

        # Click off the board
        if not (0 <= x < self.size[0] and 0 <= y < self.size[1]):
            if self.selected:
                if not self.is_last_move(*self.selected[:2]):
                    self.colour_square(*self.selected[:2], highlight, 0.5)
                self.deselect_piece()
            return

        # Clear highlights and arrows
        for coords, (colour, opacity) in list(self.highlights.items()):
            if self.is_last_move(*coords):
                if colour != highlight:
                    self.colour_square(*coords, highlight, 0.5)
            else:
                self.colour_square(*coords, colour, opacity)
        self.canvas.delete('arrow')
        self.arrows = {}

        # Move by clicking two squares
        if self.selected and self.selected != [x, y, False]:
            try:
                self.move(event, x, y)
            except ChessError:
                if self.board.board[y][x]:
                    if not self.is_last_move(x, y):
                        self.colour_square(x, y, highlight, 0.5)
                    self.select_piece(event, x, y)
                else:
                    self.deselect_piece()

        # Select piece
        elif self.board.board[y][x]:
            if not self.is_last_move(x, y):
                self.colour_square(x, y, highlight, 0.5)
            if self.selected == [x, y, False]:
                self.select_piece(event, x, y)
                self.selected[2] = True
            else:
                self.select_piece(event, x, y)

    def left_drag(self, event: tk.Event):
        """Drag piece."""
        self.mouse = event.x, event.y
        if not self.selected:
            return
        piece = self.canvas.find_withtag((*self.selected[:2], '&&piece'))
        xpos = min(max(0, event.x), self.size[self.rotation % 2] * self.pixels)
        ypos = min(max(0, event.y),
                   self.size[(self.rotation + 1) % 2] * self.pixels)
        self.canvas.coords(piece, xpos, ypos)

    def left_release(self, event: tk.Event):
        """Drop piece."""
        self.mouse = ()
        if not self.selected:
            self.motion(event)
            return

        x, y = self.pos_to_coords(event.x, event.y)
        coords = self.selected[:2]
        piece = self.canvas.find_withtag((*coords, '&&piece'))

        # Drag piece off board
        if not (0 <= x < self.size[0] and 0 <= y < self.size[1]):
            self.canvas.coords(piece, self.coords_to_pos(*coords))
            self.selected[2] = False
            self.motion(event)
            return

        self.canvas.coords(piece, *self.coords_to_pos(*coords))

        # Move piece
        if coords != [x, y]:
            try:
                self.move(event, x, y)
            except ChessError:
                pass
            else:
                if not (self.is_last_move(*coords) or self.promotion):
                    self.colour_square(*coords, self.colours_rgb['highlight'],
                                       0.5)
        elif self.selected == [x, y, True]:
            if not self.is_last_move(x, y):
                self.colour_square(x, y, *self.highlights[x, y])
            self.deselect_piece()

        self.motion(event)

    def right_click(self, event: tk.Event):
        """Deselect piece, start arrow or highlight."""
        if not (self.mouse or self.promotion):
            x, y = self.pos_to_coords(event.x, event.y)
            if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
                self.arrow_start = x, y

        if self.selected:
            coords = self.selected[:2]
            colour, opacity = self.highlights[tuple(coords)]
            if not self.is_last_move(*coords):
                self.colour_square(*coords, colour, opacity)
            piece = self.canvas.find_withtag((*coords, '&&piece'))
            self.canvas.coords(piece, *self.coords_to_pos(*coords))
            self.deselect_piece()
            self.motion(event)

    def right_release(self, event: tk.Event):
        """Highlight square or end arrow."""
        if not self.arrow_start:
            return

        x, y = self.pos_to_coords(event.x, event.y)
        if not (0 <= x < self.size[0] and 0 <= y < self.size[1]):
            self.arrow_start = ()
            return

        colours = {
            0: 'yellow',
            1: 'green', # shift
            4: 'red', # control
            5: 'orange', # control + shift
            131072: 'blue', # alt
            131073: 'cyan', # shift + alt
            131076: 'magenta', # control + alt or alt gr
            131077: 'grey' # control + shift + alt or shift + alt gr
        }
        state = event.state & 131077

        # Highlights
        if self.arrow_start == (x, y):
            if state in {0, 4}:
                state = 4 - state
            colour = self.colours_rgb[colours[state]]
            highlight = self.colours_rgb['highlight']
            if (self.is_last_move(x, y) and
                self.highlights[x, y] != (highlight, 0.5)):
                self.colour_square(x, y, highlight, 0.5)
            else:
                self.colour_square(x, y, colour, 0.8)

        # Arrows
        else:
            colour = self.colours_hex[colours[state]]
            self.draw_arrow(*self.arrow_start, x, y, colour)

        self.arrow_start = ()

    def key_press(self, event: tk.Event):
        """Keyboard shortcuts."""
        key = event.keysym.lower()
        if key == 'left':
            # Undo last move
            self.undo()
        elif key == 'x':
            # Flip how board is shown
            self.rotation ^= 2
            self.refresh()
        elif key == 'r':
           # Rotate board 90 degrees clockwise
           self.rotation = (self.rotation + 1) % 4
           self.refresh()
        elif key in {'c', 'l'}:
            # Toggle board coordinates
            self.coords = not self.coords
            self.refresh()
        elif key == 'h':
            # Open help
            help_window = tk.Toplevel()
            help_window.title('Help')
            icon = tk.PhotoImage(file='images/help.png')
            help_window.iconphoto(False, icon)
        elif key == 's':
            # Open settings
            self.settings()
        elif key in {'f', 'f11'}:
            # Toggle fullscreen
            fullscreen = self.master.attributes('-fullscreen')
            self.master.attributes('-fullscreen', not fullscreen)
        elif key == 'escape':
            # Exit fullscreen
            self.master.attributes('-fullscreen', False)

    def select_piece(self, event: tk.Event, x: int, y: int):
        """Select the piece at (x, y) and add move hints."""
        self.selected = [x, y, False]
        piece = self.canvas.find_withtag((x, y, '&&piece'))
        self.canvas.coords(piece, event.x, event.y)
        self.canvas.delete('movehint')
        self.move_hints = []

        if self.show_legal_moves or event.state % 2:
            for move in self.board.legal_moves:
                if (x, y) == move:
                    self.add_move_hint(move.nx, move.ny)
            self.canvas.tag_raise('piece')

        self.canvas.tag_raise(piece)

    def deselect_piece(self):
        """Deselect piece and remove move hints."""
        self.canvas.delete('movehint')
        self.canvas.delete('promotion')
        self.move_hints = []
        self.promotion = []
        self.selected = []

    def move(self, event: tk.Event, x: int, y: int):
        """Move selected piece to (x, y)."""
        sx, sy, _ = self.selected
        piece = self.canvas.find_withtag((sx, sy, '&&piece'))

        # Move piece in move mode
        if self.mode == 'move':
            promotion = []
            for move in self.board.legal_moves:
                if move == (sx, sy, x, y):
                    if '=' not in move.name:
                        break
                    promote = move.name[move.name.index('=') + 1]
                    promotion.append((promote, move))
                    if self.auto_promote and not event.state & 131077:
                        break
            else:
                if not promotion:
                    raise ChessError

            # Promotion selection
            if len(promotion) > 1:
                self.promotion_selection(promotion)
                return

            # Move piece
            self.board.move(move)
            sound = 'move-self'

            # Highlight move
            for coords, (colour, opacity) in list(self.highlights.items()):
                self.colour_square(*coords, colour, opacity)
            self.colour_square(sx, sy, self.colours_rgb['highlight'], 0.5)
            self.colour_square(x, y, self.colours_rgb['highlight'], 0.5)

            # Castle
            if '-' in move.name:
                rook = self.canvas.find_withtag((*move.info, '&&piece'))
                nrx = x + (move.name == '0-0-0') * 2 - 1
                self.canvas.itemconfig(rook, tags=((nrx, y), 'piece'))
                sound = 'castle'
            # En passant
            elif move.info:
                self.canvas.delete((*move.info, '&&piece'))
            # Promotion
            if '=' in move.name:
                if self.board.board[y][x].colour == 'b':
                    promote = promote.lower()
                self.canvas.itemconfig(piece, image=self.images[promote])
                sound = 'promote'
            # Capture
            elif move.capture:
                sound = 'capture'
            # Check
            if move.name[-1] in {'+', '#'}:
                sound = 'check'

            winsound.PlaySound(f'sounds/{sound}.wav', winsound.SND_FILENAME |
                               winsound.SND_ASYNC | winsound.SND_NODEFAULT)

        # Move piece in setup mode
        else:
            self.board.board[y][x] = Piece(self.board.board[sy][sx].letter)
            self.board.board[sy][sx] = Piece()
            self.board.legal_moves = self.board.get_moves()
            self.canvas.coords(piece, *self.coords_to_pos(x, y))

        self.canvas.delete((x, y, '&&piece'))
        self.canvas.itemconfig(piece, tags=((x, y), 'piece'))
        self.deselect_piece()

        if self.mode == 'setup':
            return

        # Animate piece movement
        if event.state & 256:
            self.canvas.coords(piece, *self.coords_to_pos(x, y))
            if '-' in move.name:
                self.canvas.coords(rook, *self.coords_to_pos(nrx, y))
            return

        self.animate(piece, sx, sy, x, y)
        if '-' in move.name:
            self.animate(rook, *move.info, nrx, move.info[1])

    def undo(self):
        """Undo last move."""
        if not self.board.moves:
            return

        move = self.board.moves[-1]
        x = move.x
        y = move.y
        nx = move.nx
        ny = move.ny
        info = move.info

        # Move piece
        self.board.undo()
        piece = self.canvas.find_withtag((nx, ny, '&&piece'))
        self.canvas.itemconfig(piece, tags=((x, y), 'piece'))
        self.animate(piece, nx, ny, x, y)
        sound = 'move-self'

        # Highlight last move
        for coords, (colour, opacity) in list(self.highlights.items()):
            self.colour_square(*coords, colour, opacity)

        if self.board.moves:
            last_move = self.board.moves[-1]
            highlight = self.colours_rgb['highlight']
            self.colour_square(last_move.x, last_move.y, highlight, 0.5)
            self.colour_square(last_move.nx, last_move.ny, highlight, 0.5)

        # Castle
        if '-' in move.name:
            nrx = nx + (move.name == '0-0-0') * 2 - 1
            rook = self.canvas.find_withtag((nrx, info[1], '&&piece'))
            self.canvas.itemconfig(rook, tags=(info, 'piece'))
            self.animate(rook, nrx, info[1], *info)
            sound = 'castle'
        # Capture
        elif move.capture:
            letter = move.capture.letter
            if info:
                # En passant
                self.canvas.create_image(*self.coords_to_pos(*info),
                    image=self.images[letter], tags=(info, 'piece'))
            else:
                self.canvas.create_image(*self.coords_to_pos(nx, ny),
                    image=self.images[letter], tags=((nx, ny), 'piece'))
            sound = 'capture'
        # Promotion
        if '=' in move.name:
            letter = self.board.board[y][x].letter
            self.canvas.itemconfig(piece, image=self.images[letter])
            sound = 'promote'
        # Check
        if move.name[-1] in {'+', '#'}:
            sound = 'check'

        winsound.PlaySound(f'sounds/{sound}.wav', winsound.SND_FILENAME |
                           winsound.SND_ASYNC | winsound.SND_NODEFAULT)

    def animate(self, piece, sx: int, sy: int, x: int, y: int):
        """Animate the movement of a piece from (sx, sy) to (x, y)."""
        def next_frame(start_time, piece, sx, sy, dx, dy, speed):
            proportion = (time.time() - start_time) / speed
            if proportion < 1:
                self.canvas.coords(piece, sx+proportion*dx, sy+proportion*dy)
                self.canvas.after(10, next_frame, start_time, piece,
                                  sx, sy, dx, dy, speed)

            else:
                self.canvas.coords(piece, sx + dx, sy + dy)

        sx, sy = self.coords_to_pos(sx, sy)
        x, y = self.coords_to_pos(x, y)
        speed = self.animation_speed

        if not speed:
            self.canvas.coords(piece, x, y)
            return

        start_time = time.time()
        next_frame(start_time, piece, sx, sy, x - sx, y - sy, speed)

    def settings(self):
        """Open settings."""
        settings = tk.Toplevel()
        settings.title('Settings')
        icon = tk.PhotoImage(file='images/settings icon.png')
        settings.iconphoto(False, icon)
        label = tk.Label(settings, text='hello')
        label.pack(side='top', pady=10)
        button = tk.Button(settings, text='Done', command=settings.destroy)
        button.pack()
        settings.mainloop()

    def pos_to_coords(self, x: float, y: float) -> tuple:
        """Convert mouse position to board coordinates."""
        x //= self.pixels
        y //= self.pixels
        if self.rotation == 1:
            return y, self.size[1] - x - 1
        if self.rotation == 2:
            return self.size[0] - x - 1, self.size[1] - y - 1
        if self.rotation == 3:
            return self.size[0] - y - 1, x
        return x, y

    def coords_to_pos(self, x: float, y: float) -> tuple:
        """Convert board coordinates to the position on the screen."""
        pixels = self.pixels
        x = (x + 0.5) * pixels
        y = (y + 0.5) * pixels
        if self.rotation == 1:
            return self.size[1] * pixels - y, x
        if self.rotation == 2:
            return self.size[0] * pixels - x, self.size[1] * pixels - y
        if self.rotation == 3:
            return y, self.size[0] * pixels - x
        return x, y

    def is_last_move(self, x: int, y: int) -> bool:
        """
        Return True if (x, y) is part of the last move, False otherwise.
        """
        if self.board.moves:
            return (x, y) in {
                (self.board.moves[-1].x, self.board.moves[-1].y),
                (self.board.moves[-1].nx, self.board.moves[-1].ny)
            }
        return False

    def print(self):
        """Print board using unicode characters for pieces."""
        board = [rank[:] for rank in self.board.board]
        size = self.size
        light = f'48;2;{";".join(map(str, self.colours_rgb["light"]))}'
        dark = f'48;2;{";".join(map(str, self.colours_rgb["dark"]))}'

        for y in range(len(board)):
            for x in range(len(board[0])):
                if board[y][x].letter in {'x', 'X'}:
                    board[y][x] = '  '
                    continue

                fg = '30;' if board[y][x] else ''
                bg = dark if (x + y + sum(size)) % 2 else light
                board[y][x] = f'\x1B[{fg}{bg}m{board[y][x]} \x1B[0m'

        # Rotation
        if self.rotation == 1:
            board = [list(row)[::-1] for row in zip(*board)]
        elif self.rotation == 2:
            board = [rank[::-1] for rank in board[::-1]]
        elif self.rotation == 3:
            board = [list(row) for row in list(zip(*board))[::-1]]

        board = [''.join(rank) for rank in board]

        # Coordinates
        if self.coords:
            if self.rotation == 1:
                length = 1
                column = [chr(97+x) for x in range(size[0])]
                row = [f'{i:>2}'[-2:] for i in range(1, size[1]+1)]
            elif self.rotation == 2:
                length = len(str(size[1]))
                column = range(1, size[1]+1)
                row = [chr(96+x).ljust(2) for x in range(size[0], 0, -1)]
            elif self.rotation == 3:
                length = 1
                column = [chr(96+x) for x in range(size[0], 0, -1)]
                row = [f'{i:>2}'[-2:] for i in range(size[1], 0, -1)]
            else:
                length = len(str(size[1]))
                column = range(size[1], 0, -1)
                row = [chr(97+x).ljust(2) for x in range(size[0])]

            for i, (coord, rank) in enumerate(zip(column, board)):
                board[i] = f'{coord:>{length}} {rank}'

            board.append(f'{" "*length} {"".join(row)}')

        print('\n'.join(board))


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB colour to HEX."""
    return '#' + ''.join(f'{i:02x}' for i in rgb)


def command_line_interface(tkboard: TkBoard):
    """Command line interface version."""
    while True:
        board = tkboard.board
        print(' '.join(map(str, board.legal_moves)))
        print(len(board.legal_moves))
        print(board.get_fen())
        print(board.get_pgn())
        tkboard.print()
        try:
            board.move(input(f"{board.active}: "))
        except ChessError:
            print("Illegal move")


def main():
    """Graphical user interface version."""
    board = Board()
    window = tk.Tk()
    window.title('Chess')
    icon = tk.PhotoImage(file='images/icon.png')
    window.iconphoto(False, icon)

    tkboard = TkBoard(window, board)
    tkboard.grid(column=0, row=0, sticky='NEWS', padx=16, pady=16)
    window.configure(background=tkboard.colours_hex['background'])

    button = tk.Button(window, text='Refresh', command=tkboard.refresh)
    button.grid(row=0, column=1, sticky='SE')
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)
    window.geometry('1126x656+120+40')

    tk.mainloop()


if __name__ == "__main__":
    main()
