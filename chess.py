"""Chess - Made by Fred Lang."""

import time
import tkinter as tk
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import font
import winsound

import analyse
import computer
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
    mode : {'setup', 'move'}
        In setup mode, pieces can be moved to any square or removed from
        the board. In move mode, only legal moves are allowed.
    auto_promote : bool
        Whether pawn should automatically promote to the default piece
        (usually queen). Hold ctrl, shift, or alt to temporarily disable
        auto-promotion.
    coords : bool
        Whether board should be shown with coordinates.
    rotation : {0, 1, 2, 3}
        Number of 90-degree clockwise rotations from white's perspective
        when showing the board.
    show_legal_moves : bool
        Whether to show legal moves.
    eval_bar : bool
        Whether to show evaluation bar.
    sound : bool
        Whether to play sounds.
    shape : {'square', 'circle', 'dot', 'point'}
        Grid square shape options.
    piece : {'normal', 'disguised', 'identical', 'invisible'}
        Piece design options.
    animation_speed : float
        Time in seconds per move.
    font_size : int
        Font size used to display the moves analysis text.
    pixels : int
        Length of one square in pixels.
    board_pos : tuple of (int, int)
        Coordinates of the top-left corner of the board.
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
    highlight_last : boolean
        Whether to highlight the last move.
    arrow_start : tuple of (int, int) or ()
        Coordinates of start of a possible arrow.
    arrows : dict of {(int, int, int, int): (int, int, int)}
        Colour of each arrow drawn on the board with coordinates of the
        start and end points given as the key.
    move_hints : list of [tuple of (int, int)]
        Coordinates of squares which have move hints.
    canvas : tk.Canvas
        Canvas the board is drawn on.
    moves_text : tk.Text
        Text box for writing moves and analysis.
    buttons : tk.Frame
        Frame for buttons.
    images : dict of {str: tk.PhotoImage}
        Images for the pieces and buttons.
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
        self.show_legal_moves = True
        self.eval_bar = True
        self.sound = True
        self.shape = 'square'
        self.piece = 'normal'
        self.animation_speed = 0.2
        self.font_size = 12
        self.pixels = pixels = 65
        self.board_pos = (65, 65)

        self.colours_rgb = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'light grey': (204, 204, 202),
            'dark grey': (64, 61, 57),
            'move highlight': (103, 102, 99),
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
            'background': (81, 80, 77)
        }
        self.colours_hex = {colour: rgb_to_hex(rgb)
                            for colour, rgb in self.colours_rgb.items()}

        self.selected = []
        self.promotion = []
        self.mouse = ()
        self.highlights = {}
        self.highlight_last = True
        self.arrow_start = ()
        self.arrows = {}
        self.move_hints = []
        self.images = {}

        # Main frame
        tk.Frame.__init__(self, window,
                          background=self.colours_hex['background'])

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family='Segoe UI', size=self.font_size)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(family='Segoe UI', size=self.font_size)
        fixed_font = font.nametofont("TkFixedFont")
        fixed_font.configure(family='Consolas', size=self.font_size)

        # Moves and analysis frame
        moves_frame = tk.Frame(self)
        scrollbar = tk.Scrollbar(window, orient='vertical')
        self.moves_text = tk.Text(moves_frame,
            background=self.colours_hex['dark grey'],
            foreground=self.colours_hex['white'],
            width=18, padx=8, pady=8, wrap='word', borderwidth=2,
            relief='ridge', yscrollcommand=scrollbar.set
        )
        self.moves_text.tag_configure('title',
            font=('Segoe UI', self.font_size+2, 'bold'))
        self.moves_text.tag_configure('Segoe',
            font=('Segoe UI', self.font_size))
        self.moves_text.tag_configure('highlight',
            background=self.colours_hex['move highlight'])
        self.moves_text.tag_configure('center', justify='center')

        moves_frame.grid(row=0, column=1, sticky='news',
            padx=(0, self.board_pos[0]), pady=(self.board_pos[1], 0))
        scrollbar.config(command=self.moves_text.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Disable left click bind on text
        self.moves_text.bind('<Button-1>', lambda event : 'break')

        self.moves_text.grid(sticky='news')
        moves_frame.columnconfigure(0, weight=1)
        moves_frame.rowconfigure(0, weight=1)

        # Buttons
        self.buttons = buttons = tk.Frame(self,
            background=self.colours_hex['background'])
        self.images['undo all'] = tk.PhotoImage(file='images/undo all.png')
        self.images['undo'] = tk.PhotoImage(file='images/undo.png')
        self.images['redo'] = tk.PhotoImage(file='images/redo.png')
        self.images['redo all'] = tk.PhotoImage(file='images/redo all.png')
        self.images['pgn'] = tk.PhotoImage(file='images/pgn.png')
        self.images['new'] = tk.PhotoImage(file='images/new.png')
        self.images['help'] = tk.PhotoImage(file='images/help.png')
        self.images['settings'] = tk.PhotoImage(file='images/settings.png')
        self.images['rotate'] = tk.PhotoImage(file='images/rotate.png')
        self.images['fullscreen'] = tk.PhotoImage(file='images/fullscreen.png')

        undo_all = tk.Button(buttons, image=self.images['undo all'],
                             command=lambda: self.undo(True))
        undo = tk.Button(buttons, image=self.images['undo'],
                         command=self.undo)
        redo = tk.Button(buttons, image=self.images['redo'],
                         command=self.redo)
        redo_all = tk.Button(buttons, image=self.images['redo all'],
                             command=lambda: self.redo(True))
        new = tk.Button(buttons, image=self.images['new'],
                        command=self.new_game)
        pgn = tk.Button(buttons, image=self.images['pgn'], command=self.pgn)
        help_button = tk.Button(buttons, image=self.images['help'],
                                command=self.help)
        analyse = tk.Button(buttons, text="Run Analysis",
            font=('Segoe UI', self.font_size, 'bold'), command=self.analyse)
        settings = tk.Button(buttons, image=self.images['settings'],
                             command=self.settings)
        rotate = tk.Button(buttons, image=self.images['rotate'],
                           command=self.rotate)
        fullscreen = tk.Button(buttons, image=self.images['fullscreen'],
                               command=self.fullscreen)

        buttons.grid(row=1, column=1, padx=(0, self.board_pos[0]), pady=8)
        analyse.grid(row=0, column=0, columnspan=6)
        undo_all.grid(row=1, column=1, pady=8)
        undo.grid(row=1, column=2)
        redo.grid(row=1, column=3)
        redo_all.grid(row=1, column=4)
        new.grid(row=2, column=0)
        pgn.grid(row=2, column=1)
        help_button.grid(row=2, column=2)
        settings.grid(row=2, column=3)
        rotate.grid(row=2, column=4)
        fullscreen.grid(row=2, column=5)

        # Board canvas
        width = size[0] * pixels
        height = size[1] * pixels
        self.canvas = tk.Canvas(self, highlightthickness=0, width=width,
            height=height, background=self.colours_hex['background'])
        self.canvas.grid(row=0, rowspan=2, column=0, sticky='news')
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1, minsize=418)
        self.rowconfigure(0, weight=1)

        self.canvas.focus_set()  # Listens to keyboard inputs
        self.bind()
        self.play_sound('game-start')
        self.update_text()
        self.canvas.after(10, self.try_computer)

    def bind(self, bind: bool = True):
        """Bind or unbind events."""
        binds = (
            ('<Motion>', self.motion),
            ('<Button-1>', self.left_click),
            ('<B1-Motion>', self.left_drag),
            ('<ButtonRelease-1>', self.left_release),
            ('<Button-3>', self.right_click),
            ('<ButtonRelease-3>', self.right_release),
            ('<KeyPress>', self.key_press),
            ('<Configure>', self.refresh)
        )
        if bind:
            for event, method in binds:
                self.canvas.bind(event, method)
        else:
            for event, _ in binds:
                if event == '<Configure>':
                    continue
                self.canvas.unbind(event)


    def refresh(self, event: tk.Event = None):
        """Redraw board."""
        board = self.board
        size = self.size

        if event:
            # Find all necessary piece images and calculate filenames
            names = {piece.letter: f'{piece.colour} {piece.name}'.lstrip()
                     for rank in board.board for piece in rank if piece}
            for colour, pieces in (('w', board.promotion),
                                   ('b', board.promotion.lower())):
                for letter in pieces:
                    if letter not in names:
                        names[letter] = f'{colour} {Piece(letter).name}'

            # Change filenames for abnormal piece styles
            if self.piece == 'disguised':
                for letter, name in names.items():
                    if name[0] == 'w':
                        names[letter] = 'w stone'
                    elif name[0] == 'b':
                        names[letter] = 'b stone'
            elif self.piece == 'identical':
                names = dict.fromkeys(names, 'b stone')

            # Calculate resizing factors
            xsize = event.width - 2*self.board_pos[0]
            xsize = xsize // size[self.rotation % 2]
            ysize = event.height - 2*self.board_pos[1]
            ysize = ysize // size[(self.rotation + 1) % 2]
            self.pixels = pixels = max(1, min(xsize, ysize))
            resize = [(zoom, -(-180 * zoom // pixels)) for zoom in range(1, 6)]
            zoom, subsample = max(resize, key=lambda i: 180 * i[0] // i[1])

            # Open and resize images
            if self.piece == 'invisible':
                self.images.update({letter: tk.PhotoImage()
                                    for letter in names})
            else:
                self.images.update(
                    {letter: tk.PhotoImage(file=f'images/{name}.png')
                    .zoom(zoom).subsample(subsample)
                    for letter, name in names.items()}
                )

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

                # Different grid square shapes
                if self.shape == 'square':
                    self.canvas.create_rectangle(
                        *self.coords_to_pos(x-0.5, y-0.5),
                        *self.coords_to_pos(x+0.5, y+0.5),
                        width=0, fill=colour, tags=((x, y), 'square')
                    )
                elif self.shape == 'circle':
                    self.canvas.create_oval(
                        *self.coords_to_pos(x-0.5, y-0.5),
                        *self.coords_to_pos(x+0.5, y+0.5),
                        width=0, fill=colour, tags=((x, y), 'square')
                    )
                elif self.shape == 'dot':
                    self.canvas.create_oval(
                        *self.coords_to_pos(x-0.1, y-0.1),
                        *self.coords_to_pos(x+0.1, y+0.1),
                        width=0, fill=colour, tags=((x, y), 'square')
                    )
                else:
                    self.canvas.create_oval(
                        *self.coords_to_pos(x, y),
                        *self.coords_to_pos(x, y),
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
        self.update_coords()

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

        # Player names and Elo
        names = [board.tag_pairs['White'], board.tag_pairs['Black']]
        if names[0] == '?':
            names[0] = 'White'
        if names[1] == '?':
            names[1] = 'Black'

        if board.tag_pairs['WhiteElo'] != '?':
            names[0] = f"{names[0]} ({board.tag_pairs['WhiteElo']})"
        if board.tag_pairs['BlackElo'] != '?':
            names[1] = f"{names[1]} ({board.tag_pairs['BlackElo']})"
        if self.rotation in {2, 3}:
            names = names[::-1]

        colour = self.colours_hex['light grey']
        font = ('Segoe UI', self.font_size-2, 'bold')

        if self.rotation in {1, 3}:
            y = self.board_pos[1] + size[0]*self.pixels + 9
            self.canvas.create_text(self.board_pos[0], y,
                text=names[0], anchor='nw', fill=colour, font=font)
            self.canvas.create_text(self.board_pos[0] + size[1]*self.pixels, y,
                text=names[1], anchor='ne', fill=colour, font=font)
        else:
            x, y = self.board_pos
            self.canvas.create_text(x, y + size[1]*self.pixels + 9,
                text=names[0], anchor='nw', fill=colour, font=font)
            self.canvas.create_text(x, y-9,
                text=names[1], anchor='sw', fill=colour, font=font)

        # Evaluation bar
        self.after(0, self.update_eval_bar)

    def colour_square(self, x: int, y: int, colour: tuple, opacity: float):
        """
        Colour square.

        Parameters
        ----------
        x, y : int
            Coordinates of square.
        colour : tuple of (int, int, int)
            RGB colour. If square is already coloured in the same
            colour, colour is removed.
        opacity : float
            Opacity of the colour.
        """
        square = self.canvas.find_withtag((x, y, '&&square'))
        # Calculate whether square is light or dark
        square_colour = 'dark' if (x + y + sum(self.size)) % 2 else 'light'

        if (x, y) in self.highlights and self.highlights[x, y][0] == colour:
            colour = self.colours_hex[square_colour]
            del self.highlights[x, y]
        else:
            self.highlights[x, y] = colour, opacity
            # Calculate colour with given opacity
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

        # Calculate arrow coordinates
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
        # Draw arrow from coordinates and calculated arrow shape
        self.canvas.create_line(*arrow, fill=colour, arrow='last',
            arrowshape=arrowshape, width=width, tags=(coords, 'arrow'))

        self.arrows[coords] = colour

    def update_coords(self):
        """Update board coordinates."""
        # Remove coordinates
        self.canvas.delete('coords')
        if not self.coords:
            return

        # Add coordinates
        size = self.size
        pixels = self.pixels
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

        # Add text
        font = ('Segoe UI', max(1, int(0.17 * pixels)), 'bold')
        x = 0.12 * pixels + self.board_pos[0]
        for i, char in enumerate(column):
            y = (i + 0.17) * pixels + self.board_pos[1]
            colour = 'dark' if (i + column_colour) % 2 else 'light'
            colour = self.colours_hex[colour]
            self.canvas.create_text(x, y, text=char, fill=colour,
                                    font=font, tags='coords')
        y = (size[(self.rotation + 1) % 2] - 0.17) * pixels + self.board_pos[1]
        for i, char in enumerate(row):
            x = (i + 0.85) * pixels + self.board_pos[0]
            colour = 'dark' if (i + row_colour) % 2 else 'light'
            colour = self.colours_hex[colour]
            self.canvas.create_text(x, y, text=char, fill=colour,
                                    font=font, tags='coords')

    def add_move_hint(self, x: int, y: int):
        """Add move hint on square at (x, y)."""
        colour = 'dark' if (x + y + sum(self.size)) % 2 else 'light'
        colour = self.colours_rgb[colour]
        if self.is_last_move(x, y):
            colour = (round(a - 0.5 * (a - b)) for a, b in
                        zip(colour, self.colours_rgb['highlight']))
        colour = rgb_to_hex(round(0.9 * i) for i in colour)
        xpos, ypos = self.coords_to_pos(x, y)

        # Draw move hint circles
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
        self.canvas.itemconfig(piece, state='hidden')
        dy = 1 if self.board.active == 'w' else -1
        # Draw menu rectangle
        self.canvas.create_rectangle(
            *self.coords_to_pos(x-0.5, y-dy*0.5),
            *self.coords_to_pos(x+0.5, y+dy*(len(promotion)-0.5)),
            outline=self.colours_hex['dark grey'],
            fill=self.colours_hex['white'],
            tags='promotion'
        )

        # Add piece images to menu
        for i, piece in enumerate(promotion):
            promote = piece[0]
            if self.board.active == 'b':
                promote = promote.lower()
            self.canvas.create_image(*self.coords_to_pos(x, y+dy*i),
                image=self.images[promote], tags='promotion')
        self.promotion = promotion

    def rotate(self):
        """Rotate board 180-degrees."""
        self.rotation ^= 2
        self.refresh()

    def fullscreen(self):
        """Toggle fullscreen."""
        fullscreen = self.master.attributes('-fullscreen')
        self.master.attributes('-fullscreen', not fullscreen)

    def update_eval_bar(self):
        """Update evaluation bar."""
        # Remove eval bar
        self.canvas.delete('evalbar')
        if not self.eval_bar:
            return

        # Calculate eval bar coordinates
        computer.stockfish(self.board)
        evaluation = self.board.evaluation

        if isinstance(evaluation, int) or abs(evaluation) == float('inf'):
            probability = 0 if evaluation < 0 else 1 if evaluation > 0 else 0.5
        else:
            probability = computer.eval_to_win(evaluation)
            probability = min(max(0.05, probability), 0.95)

        x = [-30, -10, -30, -10, -20]
        height = self.pixels * self.size[1]
        y = [0, (1-probability) * height, (1-probability) * height, height]

        # Evaluation text
        if evaluation < 0:
            y.append(12)
            colour = self.colours_hex['white']
            font = ('Segoe UI', 7, 'bold')
        else:
            y.append(height - 12)
            colour = self.colours_hex['dark grey']
            font = ('Segoe UI', 7)


        if self.rotation in {1, 2}:
            y = [height - i for i in y]
        if self.rotation in {1, 3}:
            x, y = y, x
        x = [self.board_pos[0] + i for i in x]
        y = [self.board_pos[1] + i for i in y]

        # Add eval bar
        if probability != 1:
            self.canvas.create_rectangle(
                x[0], y[0], x[1], y[1], width=0,
                fill=self.colours_hex['dark grey'], tags='evalbar'
            )
        if probability != 0:
            self.canvas.create_rectangle(
                x[2], y[2], x[3], y[3], width=0,
                fill=self.colours_hex['white'], tags='evalbar'
            )

        # Add evaluation text
        evaluation = abs(evaluation)
        if evaluation == float('inf'):
            text = '1-0' if probability else '0-1'  # Game over, win
        elif probability in {0, 1}:
            text = f"M{evaluation}"  # Checkmate in x moves
        elif isinstance(evaluation, int):
            text = "\u00BD-\u00BD"  # Game over, draw
        elif evaluation < 10:
            text = f"{evaluation:.1f}"  # Evaluation is X.X
        else:
            text = f"{evaluation:.0f}"  # Evaluation is XX
        self.canvas.create_text(x[4], y[4], text=text,
                                fill=colour, font=font, tags='evalbar')

    def update_text(self):
        """Update moves list text."""
        moves = self.board.moves
        # Set starting move from FEN if available
        start_num = 1
        if 'FEN' in self.board.tag_pairs:
            fen = self.board.tag_pairs['FEN'].split()
            if moves and fen[1] == 'b':
                moves = [''] + moves
            start_num = int(fen[5])

        # Format moves
        moves = [moves[::2], moves[1::2]]
        if len(moves[0]) != len(moves[1]):
            moves[1].append('')
        moves = [f"{f'{i}.':<5} {w!s:<7} {b!s:<7}\n"
                    for i, (w, b) in enumerate(zip(*moves), start_num)]

        self.moves_text.delete('1.0', 'end')
        self.moves_text.insert('end', "Moves List\n",  'title')
        self.moves_text.insert('end', ''.join(moves))

    def highlight_move(self):
        """Highlight current move in moves text."""
        # Remove highlighted move if it is the start of the game
        if not self.board.moves:
            self.moves_text.tag_remove('highlight', '1.0', 'end')
            self.moves_text.see('1.0')
            return

        move = self.board.moves[-1]
        search = f'\n{move.fullmove}.'
        # Highlight current move in moves list
        if self.moves_text.get('1.0', '2.0') == 'Moves List\n':
            start = 5 if move.active == 'w' else 13
        # Highlight current move in game report
        else:
            if move.active == 'b':
                search += '..'
            start = len(search) - 1
        index = self.moves_text.search(search, '1.0', 'end')
        line = int(index.split('.')[0]) + 1
        self.moves_text.tag_remove('highlight', '1.0', 'end')
        self.moves_text.tag_add('highlight', f'{line}.{start}',
                                f'{line}.{start + len(str(move)) + 2}')

        # Scroll so that the current move is visible
        self.moves_text.see(f'{line-2}.0')
        self.moves_text.see(f'{line+2}.0')

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
        self.arrow_start = ()

        # Promotion selection
        if self.promotion:
            index = y if self.board.active == 'w' else self.size[1] - y - 1
            move = self.promotion[0][1]
            piece = self.canvas.find_withtag((move.x, move.y, '&&piece'))
            if x != move.nx or index >= len(self.promotion):
                self.colour_square(move.x, move.y, highlight, 0.5)
                self.deselect_piece()
                return

            self.canvas.coords(piece, *self.coords_to_pos(move.nx, move.ny))
            self.canvas.itemconfig(piece, state='normal')
            promote, move = self.promotion[index]
            self.board.move(move)
            self.canvas.delete((move.nx, move.ny, '&&piece'))
            if self.board.board[move.ny][move.nx].colour == 'b':
                promote = promote.lower()
            self.canvas.itemconfig(piece, image=self.images[promote],
                                   tags=((move.nx, move.ny), 'piece'))
            self.update_text()
            self.highlight_move()

            # Clear highlights
            for coords, (colour, opacity) in list(self.highlights.items()):
                self.colour_square(*coords, colour, opacity)
            self.colour_square(move.x, move.y, highlight, 0.5)
            self.colour_square(move.nx, move.ny, highlight, 0.5)

            # Sound
            if move.name[-1] in {'+', '#'}:
                self.play_sound('check')
            else:
                self.play_sound('promote')

            # Update evaluation bar
            self.after(0, self.update_eval_bar)

            self.deselect_piece()
            self.try_computer()
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
        if not self.selected or self.promotion:
            return
        piece = self.canvas.find_withtag((*self.selected[:2], '&&piece'))
        # Move piece image to mouse position, restricted to within board
        xpos = min(max(event.x, self.board_pos[0]),
            self.size[self.rotation % 2] * self.pixels + self.board_pos[1])
        ypos = min(max(event.y, self.board_pos[1]),
            self.size[(self.rotation+1) % 2] * self.pixels + self.board_pos[1])
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
            if not self.is_last_move(x, y) and (x, y) in self.highlights:
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
            if tuple(coords) in self.highlights:
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
            1: 'green',  # shift
            4: 'red',  # control
            5: 'orange',  # control + shift
            131072: 'blue',  # alt
            131073: 'cyan',  # shift + alt
            131076: 'magenta',  # control + alt or alt gr
            131077: 'grey'  # control + shift + alt or shift + alt gr
        }
        state = event.state & 131077

        # Highlights
        if self.arrow_start == (x, y):
            if state in {0, 4}:
                state = 4 - state
            colour = self.colours_rgb[colours[state]]
            highlight = self.colours_rgb['highlight']
            if (self.is_last_move(x, y) and (x, y) in self.highlights and
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
        if key == 'up':
            # Undo all moves
            if self.mode == 'setup':
                return
            self.undo(True)
        elif key == 'left':
            # Undo last move
            if self.mode == 'setup':
                return
            self.undo()
        elif key == 'right':
            # Redo last undone move
            if self.mode == 'setup':
                return
            self.redo()
        elif key == 'down':
            # Redo all moves
            if self.mode == 'setup':
                return
            self.redo(True)
        elif key == 'space':
            # Play computer move
            if self.mode == 'setup':
                return
            self.computer()
        elif key == 'x':
            # Rotate board 180-degrees
            self.rotate()
        elif key == 'r':
            # Rotate board 90-degrees clockwise
            self.rotation = (self.rotation + 1) % 4
            if self.size[0] == self.size[1]:
                self.refresh()
            else:
                self.canvas.event_generate('<Configure>',
                    width=self.canvas.winfo_width(),
                    height=self.canvas.winfo_height()
                )
        elif key in {'c', 'l'}:
            # Toggle board coordinates
            self.coords = not self.coords
            self.update_coords()
            self.canvas.tag_raise('movehint')
            self.canvas.tag_raise('piece')
            self.canvas.tag_raise('promotion')
        elif key == 'e':
            # Toggle eval bar
            self.eval_bar = not self.eval_bar
            self.after(0, self.update_eval_bar)
        elif key == 'n':
            # New game
            self.new_game()
        elif key == 'h':
            # Open help window
            self.help()
        elif key == 'p':
            # Open PGN and FEN window
            self.pgn()
        elif key == 's':
            # Open settings
            self.settings()
        elif key == 'a':
            self.analyse()
        elif key in {'f', 'f11'}:
            # Toggle fullscreen
            self.fullscreen()
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
        if self.promotion:
            sx, sy, _ = self.selected
            piece = self.canvas.find_withtag((sx, sy, '&&piece'))
            self.canvas.itemconfig(piece, state='normal')
            self.canvas.delete('promotion')
            self.promotion = []

        self.canvas.delete('movehint')
        self.move_hints = []
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
                    for move in self.board.illegal_moves:
                        if move == (sx, sy, x, y):
                            self.illegal()
                    raise ChessError

            # Promotion selection
            if len(promotion) > 1:
                self.promotion_selection(promotion)
                return

            # Move piece
            update_text = (not self.board.undone_moves or
                           move != self.board.undone_moves[-1])
            self.board.move(move)
            self.play_move(move, not event.state & 256, update_text)
            self.try_computer()

        # Move piece in setup mode
        else:
            self.board.board[y][x] = Piece(self.board.board[sy][sx].letter)
            self.board.board[sy][sx] = Piece()
            self.board.legal_moves = self.board.get_moves()
            self.canvas.coords(piece, *self.coords_to_pos(x, y))
            self.canvas.delete((x, y, '&&piece'))
            self.canvas.itemconfig(piece, tags=((x, y), 'piece'))
            self.deselect_piece()

    def play_move(self, move, animate: bool = True, update_text: bool = False):
        """Play move on screen."""
        # Deselect piece
        if self.selected:
            coords = self.selected[:2]
            piece = self.canvas.find_withtag((*coords, '&&piece'))
            self.canvas.coords(piece, *self.coords_to_pos(*coords))
            self.deselect_piece()

        x = move.x
        y = move.y
        nx = move.nx
        ny = move.ny
        piece = self.canvas.find_withtag((x, y, '&&piece'))
        self.canvas.tag_raise(piece)
        sound = 'move-self'

        # Highlight move and clear arrows
        for coords, (colour, opacity) in list(self.highlights.items()):
            self.colour_square(*coords, colour, opacity)
        self.colour_square(x, y, self.colours_rgb['highlight'], 0.5)
        self.colour_square(nx,ny, self.colours_rgb['highlight'], 0.5)
        self.highlight_last = True
        self.canvas.delete('arrow')
        self.arrows = {}

        # Update move text list if necessary
        if update_text:
            self.update_text()
        self.highlight_move()

        # Sounds
        # Castle
        if '-' in move.name:
            rook = self.canvas.find_withtag((*move.info, '&&piece'))
            nrx = nx + (move.name.count('0') == 3) * 2 - 1
            self.canvas.itemconfig(rook, tags=((nrx, ny), 'piece'))
            sound = 'castle'
        # En passant
        elif move.info:
            self.canvas.delete((*move.info, '&&piece'))
        # Promotion
        if '=' in move.name:
            promote = move.name[move.name.index('=') + 1]
            if self.board.board[ny][nx].colour == 'b':
                promote = promote.lower()
            self.canvas.itemconfig(piece, image=self.images[promote])
            sound = 'promote'
        # Capture
        elif move.capture:
            sound = 'capture'
        # Check
        if move.name[-1] in {'+', '#'}:
            sound = 'check'

        self.play_sound(sound)

        # End game
        if move.type:
            self.after(200, self.play_sound, 'game-end')

        self.canvas.delete((nx, ny, '&&piece'))
        self.canvas.itemconfig(piece, tags=((nx, ny), 'piece'))

        # Update evaluation bar
        self.after(0, self.update_eval_bar)

        # Animate move
        if animate:
            self.animate(piece, x, y, nx, ny)
            if '-' in move.name:
                self.animate(rook, *move.info, nrx, move.info[1])
        else:
            self.canvas.coords(piece, *self.coords_to_pos(nx, ny))
            if '-' in move.name:
                self.canvas.coords(rook, *self.coords_to_pos(nrx, ny))

    def undo(self, undo_all: bool = False):
        """Undo last move or all moves."""
        # Deselect piece
        if self.selected:
            coords = self.selected[:2]
            piece = self.canvas.find_withtag((*coords, '&&piece'))
            self.canvas.coords(piece, *self.coords_to_pos(*coords))
            self.deselect_piece()
        # Clear highlights and arrows
        for coords, (colour, opacity) in list(self.highlights.items()):
            self.colour_square(*coords, colour, opacity)
        self.highlight_last = True
        self.canvas.delete('arrow')
        self.arrows = {}

        # Undo all
        if undo_all:
            while len(self.board.moves) > 1:
                self.board.undone_moves.append(self.board.moves[-1])
                self.board.undo(update_moves=False)
            self.board.undo()
            self.highlight_move()
            self.refresh()
            return

        # Undo last
        move = self.board.undo()
        if not move:
            return
        x = move.x
        y = move.y
        nx = move.nx
        ny = move.ny
        info = move.info
        piece = self.canvas.find_withtag((nx, ny, '&&piece'))
        self.canvas.tag_raise(piece)
        self.highlight_move()

        # Highlight last move
        sound = 'move-self'
        if self.board.moves:
            last_move = self.board.moves[-1]
            highlight = self.colours_rgb['highlight']
            self.colour_square(last_move.x, last_move.y, highlight, 0.5)
            self.colour_square(last_move.nx, last_move.ny, highlight, 0.5)

        # Sound
        # Castle
        if '-' in move.name:
            nrx = nx + (move.name.count('0') == 3) * 2 - 1
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

        self.play_sound(sound)

        # Update evaluation bar
        self.after(0, self.update_eval_bar)

        # Animate move
        self.canvas.itemconfig(piece, tags=((x, y), 'piece'))
        self.animate(piece, nx, ny, x, y)

    def redo(self, redo_all: bool = False):
        """Redo last undone move or all undone moves."""
        # Deselect piece
        if self.selected:
            coords = self.selected[:2]
            piece = self.canvas.find_withtag((*coords, '&&piece'))
            self.canvas.coords(piece, *self.coords_to_pos(*coords))
            self.deselect_piece()
        # Clear highlights and arrows
        for coords, (colour, opacity) in list(self.highlights.items()):
            self.colour_square(*coords, colour, opacity)
        self.highlight_last = False
        self.canvas.delete('arrow')
        self.arrows = {}

        # Redo all
        if redo_all:
            while len(self.board.undone_moves) > 1:
                self.board.redo(update_moves=False)
                self.board.undone_moves.pop()
            self.board.redo()
            self.highlight_move()
            self.refresh()
            return

        # Redo last
        move = self.board.redo()
        if not move:
            return
        self.play_move(move)

    def try_computer(self):
        """Play computer move if it is a computer's turn."""
        if self.mode == 'setup':
            return

        colour = 'White' if self.board.active == 'w' else 'Black'
        player, *args = self.board.tag_pairs[colour].split()
        kwargs = {}

        # Bots which have a time parameter
        if 'fish' in player or player == 'Taunter':
            time = 0
            try:
                if args[-1].endswith('ms'):
                    time = int(args[-1][:-2])
                elif args[-1].endswith('s'):
                    time = int(args[-1][:-1]) * 1000
                if time <= 0:
                    raise ValueError
            except (IndexError, ValueError):
                pass
            else:
                kwargs['time'] = time

        # Bots with adjustable elo
        if player == 'Stockfish':
            try:
                kwargs['elo'] = int(self.board.tag_pairs[f'{colour}Elo'])
            except (KeyError, ValueError):
                pass
        elif player.startswith('Stockfish'):
            try:
                kwargs['elo'] = int(player[9:])
            except ValueError:
                return
            player = 'Stockfish'

        # Percent bots
        if player.endswith('%'):
            if len(args) > 2:
                return
            try:
                kwargs['p'] = float(player[:-1])
            except ValueError:
                return
            if not 0 <= kwargs['p'] <= 100:
                return
            if len(args) in {1, 2}:
                kwargs['engine1'] = computer.get_engine(args[0])
                if not kwargs['engine1']:
                    return
                if len(args) == 2:
                    kwargs['engine2'] = computer.get_engine(args[1])
                    if not kwargs['engine2']:
                        return
            else:
                return
            engine = computer.percent_bot
        # All other bots
        else:
            engine = computer.get_engine(player)
            if not engine:
                return

        delay = int(self.animation_speed * 1000)
        self.bind(False)
        self.canvas.update()
        self.after(delay, self.computer, engine, kwargs)

    def computer(self, engine=computer.stockfish, kwargs=None):
        """Play computer move."""
        self.bind()
        if not kwargs:
            kwargs = {}
        move = engine(self.board, **kwargs)
        if not move:
            return
        update_text = (not self.board.undone_moves or
                       move != self.board.undone_moves[-1])
        self.board.move(move)
        self.play_move(move, True, update_text)
        self.try_computer()

    def play_sound(self, sound: str):
        """Play sound using winsound."""
        if not self.sound:
            return

        winsound.PlaySound(None, winsound.SND_PURGE)
        winsound.PlaySound(
            f'sounds/{sound}.wav',
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
        )

    def animate(self, piece, sx: int, sy: int, x: int, y: int):
        """Animate the movement of a piece from (sx, sy) to (x, y)."""
        def next_frame(start_time, piece, sx, sy, dx, dy, speed):
            proportion = (time.time() - start_time + 0.02) / speed
            if proportion < 1:
                self.canvas.coords(piece, sx+proportion*dx, sy+proportion*dy)
                # Recursive call to animate next frame
                self.after(10, next_frame, start_time, piece,
                           sx, sy, dx, dy, speed)
            else:
                # Base case: place piece at destination coordinates
                self.canvas.coords(piece, sx + dx, sy + dy)

        sx, sy = self.coords_to_pos(sx, sy)
        x, y = self.coords_to_pos(x, y)
        speed = self.animation_speed

        if not speed:
            self.canvas.coords(piece, x, y)
            return

        start_time = time.time()
        next_frame(start_time, piece, sx, sy, x - sx, y - sy, speed)

    def illegal(self):
        """Animate illegal move red flashes and play sound."""
        def toggle(x: int, y: int, count: int):
            self.colour_square(x, y, self.colours_rgb['red'], 0.8)

            if count:
                self.after(250, toggle, x, y, count-1)
            else:
                highlight = self.highlights.get((x, y))
                if highlight:
                    self.colour_square(x, y, *highlight)
                if self.is_last_move(x, y) or self.selected[:2] == [x, y]:
                    self.colour_square(x, y, self.colours_rgb['highlight'],
                                       0.5)

        # Find coordinates of king
        k = 'K' if self.board.active == 'w' else 'k'
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                if self.board.board[y][x].letter == k:
                    break
            else:
                continue
            break

        self.play_sound('illegal')
        toggle(x, y, 5)

    def new_game(self):
        """Open new game window."""
        window = tk.Toplevel(padx=8)
        window.title("New Game")
        icon = tk.PhotoImage(file='images/new.png')
        window.iconphoto(False, icon)
        window.geometry('550x400')

        # PGN or FEN
        pgn_label = tk.Label(window, text="Load PGN or FEN")
        pgn_label.grid(columnspan=3, sticky='w')
        pgn_text = tk.Text(window, wrap='word', relief='groove', borderwidth=2)
        pgn_text.grid(columnspan=3, sticky='news')

        # White player
        white_label = tk.Label(window, text="White Player")
        white_label.grid(row=2, column=0, sticky='w', pady=8)
        white_text = tk.Entry(window, relief='groove', borderwidth=2)
        if self.board.tag_pairs['White'] != '?':
            white_text.insert('end', self.board.tag_pairs['White'])
        white_text.grid(row=2, column=1, sticky='ew', padx=8, pady=8)

        # White Elo
        white_elo_text = tk.Entry(window, width=6, relief='groove',
                                  borderwidth=2)
        if self.board.tag_pairs['WhiteElo'] != '?':
            white_elo_text.insert('end', self.board.tag_pairs['WhiteElo'])
        white_elo_text.grid(row=2, column=2, sticky='ew', pady=8)

        # Black player
        black_label = tk.Label(window, text="Black Player")
        black_label.grid(row=3, column=0, sticky='w')
        black_text = tk.Entry(window, relief='groove', borderwidth=2)
        if self.board.tag_pairs['Black'] != '?':
            black_text.insert('end', self.board.tag_pairs['Black'])
        black_text.grid(row=3, column=1, sticky='ew', padx=8)

        # Black Elo
        black_elo_text = tk.Entry(window, width=6, relief='groove',
                                  borderwidth=2)
        if self.board.tag_pairs['BlackElo'] != '?':
            black_elo_text.insert('end', self.board.tag_pairs['BlackElo'])
        black_elo_text.grid(row=3, column=2, sticky='ew')

        window.columnconfigure(1, weight=1)
        window.rowconfigure(1, weight=1)

        # Save button
        def save():
            pgn = pgn_text.get('1.0', 'end-1c').strip()
            white = white_text.get().strip()
            black = black_text.get().strip()
            white_elo = white_elo_text.get().strip()
            black_elo = black_elo_text.get().strip()
            window.destroy()
            self.deselect_piece()

            # Clear highlights and arrows
            for coords, (colour, opacity) in list(self.highlights.items()):
                self.colour_square(*coords, colour, opacity)
            self.highlight_last = False
            self.canvas.delete('arrow')
            self.arrows = {}

            # Clear analysis text
            self.moves_text.delete('1.0', 'end')

            # Set data
            self.board.__init__(pgn)
            self.size = self.board.size
            self.canvas.event_generate('<Configure>',
                width=self.canvas.winfo_width(),
                height=self.canvas.winfo_height()
            )
            if self.board.get_fen() == '8/8/8/8/8/8/8/8 w KQkq - 0 1':
                if '\n' not in pgn and '/' in pgn:
                    # FEN
                    self.board.load_fen(pgn)
                else:
                    # PGN
                    self.board.load_pgn(pgn)
            if white and self.board.tag_pairs['White'] == '?':
                self.board.tag_pairs['White'] = white
            if black and self.board.tag_pairs['Black'] == '?':
                self.board.tag_pairs['Black'] = black
            if white_elo and self.board.tag_pairs['WhiteElo'] == '?':
                self.board.tag_pairs['WhiteElo'] = white_elo
            if black_elo and self.board.tag_pairs['BlackElo'] == '?':
                self.board.tag_pairs['BlackElo'] = black_elo
            self.update_text()
            self.refresh()
            self.try_computer()

        button = tk.Button(window, text="New Game", command=save)
        button.grid(columnspan=3, pady=8)
        window.mainloop()

    def help(self):
        """Open help window."""
        window = tk.Toplevel()
        window.title("Help")
        icon = tk.PhotoImage(file='images/help.png')
        window.iconphoto(False, icon)
        scrollbar = tk.Scrollbar(window, orient='vertical')
        text = tk.Text(window, wrap='word', relief='groove',
                       yscrollcommand=scrollbar.set)
        
        # Add text from saved file
        with open('manual.txt') as file:
            manual = file.read()
        text.insert('end', manual)
        text.configure(state='disabled')
        scrollbar.config(command=text.yview)
        text.grid(sticky='news', padx=8, pady=8)
        scrollbar.grid(row=0, column=1, sticky='ns')
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        window.mainloop()

    def pgn(self):
        """Open PGN and FEN window, copy and allow download of PGN."""
        window = tk.Toplevel(padx=8)
        window.title("")
        icon = tk.PhotoImage(file='images/pgn.png')
        window.iconphoto(False, icon)

        # FEN
        fen_label = tk.Label(window, text="FEN")
        fen_label.grid(sticky='w')
        fen_text = tk.Text(window, height=1, wrap='none', relief='groove',
                           borderwidth=2)
        fen_text.insert('end', self.board.get_fen())
        fen_text.configure(state='disabled')
        fen_text.grid(sticky='ew')

        # PGN
        pgn_label = tk.Label(window, text="PGN")
        pgn_label.grid(sticky='w')
        pgn_text = tk.Text(window, height=20, wrap='word', relief='groove',
                           borderwidth=2)
        pgn = self.board.get_pgn()
        pgn_text.insert('end', pgn)
        pgn_text.configure(state='disabled')
        pgn_text.grid(sticky='news')

        window.columnconfigure(0, weight=1)
        window.rowconfigure(3, weight=1)

        # Download button
        def download():
            white = self.board.tag_pairs['White']
            black = self.board.tag_pairs['Black']
            date = self.board.tag_pairs['Date']
            name = f"{white} vs {black} {date}.pgn"
            filename = ''.join('_' if i in '\/:*?<>|"' else i for i in name)
            f = filedialog.asksaveasfile(
                initialfile=filename,
                initialdir='pgns',
                defaultextension='.pgn',
                filetypes=[('All Files', '*.*'), ('PGN', '*.pgn')]
            )
            if f is None:
                return
            f.write(pgn)
            f.close()

        button = tk.Button(window, text="Download PGN", command=download)
        button.grid(pady=8)

        # Copy PGN to clipboard
        clipboard = tk.Tk()
        clipboard.withdraw()
        clipboard.clipboard_clear()
        clipboard.clipboard_append(pgn)
        clipboard.update()
        clipboard.destroy()

        window.mainloop()

    def settings(self):
        """Open settings."""
        window = tk.Toplevel(padx=8, pady=8)
        window.title("Settings")
        icon = tk.PhotoImage(file='images/settings.png')
        window.iconphoto(False, icon)

        # Colour pickers
        names = {
            'background': 'background colour',
            'light': 'board colour (light)',
            'dark': 'board colour (dark)',
            'highlight': 'highlight colour'
        }
        def choose_colour(name, button):
            colour = colorchooser.askcolor(self.colours_hex[name],
                title=f"Choose {names[name]}", parent=window)
            if colour[0] is None:
                return
            rgb = tuple(map(int, colour[0]))

            # Update colour attributes
            self.colours_rgb[name] = rgb
            self.colours_hex[name] = colour[1]
            button.configure(background=colour[1])

            # Update background colour
            if name == 'background':
                self.configure(background=colour[1])
                self.canvas.configure(background=colour[1])
                self.buttons.configure(background=colour[1])
            # Update highlight colours
            elif name == 'highlight':
                self.refresh()
                for coords, (colour, opacity) in list(self.highlights.items()):
                    if opacity == 0.5 and colour != rgb:
                        self.colour_square(*coords, rgb, 0.5)
            # Update board colour
            else:
                self.refresh()

        # Add labels and buttons to choose colours
        for i, name in enumerate(names):
            colour_text = tk.Label(window, text=names[name].capitalize(),
                                   anchor='w')
            colour_text.grid(sticky='ew')
            button = tk.Button(window, width=3,
                               background=self.colours_hex[name])
            button.configure(command=lambda button=button, name=name:
                choose_colour(name, button))
            button.grid(row=i, column=1, columnspan=2)

        # Animation speed slider
        def set_animation_speed(speed):
            self.animation_speed = float(speed)

        label = tk.Label(window, text="Animation speed", anchor='w')
        label.grid(sticky='ew', pady=(8, 0))
        slider = tk.Scale(window, length=200, from_=0, to=1, resolution=0.1,
            tickinterval=0.2, orient='horizontal', command=set_animation_speed)
        slider.set(self.animation_speed)
        slider.grid(columnspan=3)

        # Toggleable settings
        def toggle(setting, on, off):
            value = getattr(self, setting)
            setattr(self, setting, not value)
            if value:
                on.configure(background='SystemButtonFace')
                off.configure(background=self.colours_hex['red'])
            else:
                on.configure(background=self.colours_hex['green'])
                off.configure(background='SystemButtonFace')
            self.refresh()

        settings = {
            'Sound': 'sound',
            'Coordinates': 'coords',
            'Auto promote': 'auto_promote',
            'Legal move hints': 'show_legal_moves',
            'Evaluation bar': 'eval_bar'
        }
        for i, (name, setting) in enumerate(settings.items(), 6):
            label = tk.Label(window, text=name, anchor='w')
            on = tk.Button(window, text="On", width=4)
            off = tk.Button(window, text="Off", width=4)
            on.configure(command=lambda setting=setting, on=on,
                off=off : toggle(setting, on, off))
            on.invoke()
            off.configure(command=lambda setting=setting, on=on,
                off=off : toggle(setting, on, off))
            off.invoke()
            label.grid(sticky='ew')
            on.grid(row=i, column=1, sticky='e')
            off.grid(row=i, column=2, sticky='w')

        # Piece styles
        def set_piece(piece):
            self.piece = piece.lower()
            self.canvas.event_generate('<Configure>',
                width=self.canvas.winfo_width(),
                height=self.canvas.winfo_height()
            )

        label = tk.Label(window, text="Piece style", anchor='w')
        label.grid(sticky='ew', pady=(8, 0))
        pieces = ('Normal', 'Disguised', 'Identical', 'Invisible')
        variable = tk.StringVar()
        variable.set(self.piece.title())
        piece_menu = tk.OptionMenu(window, variable, *pieces,
                                   command=set_piece)
        piece_menu.configure(width=7)
        piece_menu.grid(row=11, column=1, columnspan=2, pady=(8, 0))

        # Board grid styles
        def set_shape(shape):
            self.shape = shape.lower()
            self.refresh()

        label = tk.Label(window, text="Board style", anchor='w')
        label.grid(sticky='ew')
        shapes = ('Square', 'Circle', 'Dot', 'Point')
        variable = tk.StringVar()
        variable.set(self.shape.title())
        shapes_menu = tk.OptionMenu(window, variable, *shapes,
                                    command=set_shape)
        shapes_menu.configure(width=7)
        shapes_menu.grid(row=12, column=1, columnspan=2)

        # Done button
        button = tk.Button(window, text="Done", command=window.destroy)
        button.grid(columnspan=3, pady=(8, 0))

        window.mainloop()

    def analyse(self):
        """Analyse game and write game report."""
        if self.board.variant != 'Standard':
            return
        self.moves_text.delete('1.0', 'end')
        self.moves_text.insert('end', "Analysing...")
        self.canvas.update()
        analyse.analyse(self.board)
        counts, accuracy, acpl = analyse.summary(self.board)
        self.deselect_piece()

        # Clear highlights and arrows
        for coords, (colour, opacity) in list(self.highlights.items()):
            self.colour_square(*coords, colour, opacity)
        self.highlight_last = False
        self.canvas.delete('arrow')
        self.arrows = {}
        self.refresh()

        # Write summary
        white = self.board.tag_pairs['White']
        if white == '?':
            white = 'White'
        black = self.board.tag_pairs['Black']
        if black == '?':
            black = 'Black'
        length = max(len(white), len(black))
        result = self.board.tag_pairs['Result']
        if result == '*':
            result = '-'

        self.moves_text.delete('1.0', 'end')
        # Write result, accuracy, and ACPL in a centered table
        self.moves_text.insert('end', "GAME REPORT\n", 'title center')
        self.moves_text.insert('end', (
            f"{white:>{length}}{result:^13}{black:<{length}}\n"
            f"{accuracy['w']:>5.1f}  Accuracy   {accuracy['b']:<5.1f}\n"
            f"{acpl['w']:>5.0f}    ACPL     {acpl['b']:<5.0f}\n\n"
        ).replace('nan', '-'), 'center')

        # Write move classification statistics in a centered table
        for classification, num in counts.items():
            self.moves_text.insert('end',
                f"{num['w']:>5}{classification.title():^13}{num['b']:<5}\n",
                'center'
            )
        self.moves_text.insert('end', '\n')

        # Write move comments
        for move in self.board.moves:
            if move.active == 'w':
                self.moves_text.insert('end', move.comment, 'Segoe')
            else:
                self.moves_text.insert('end', move.comment, 'Segoe')

    def pos_to_coords(self, x: float, y: float) -> tuple:
        """Convert mouse position to board coordinates."""
        x -= self.board_pos[0]
        y -= self.board_pos[1]
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
            x, y = self.size[1] * pixels - y, x
        if self.rotation == 2:
            x = self.size[0] * pixels - x
            y = self.size[1] * pixels - y
        if self.rotation == 3:
            x, y = y, self.size[0] * pixels - x

        return x + self.board_pos[0], y + self.board_pos[1]

    def is_last_move(self, x: int, y: int) -> bool:
        """
        Return True if (x, y) is part of the last move, False otherwise.
        """
        if not self.highlight_last:
            return False
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
        # Using ANSI escape sequences to print squares in colour
        light = f'48;2;{";".join(map(str, self.colours_rgb["light"]))}'
        dark = f'48;2;{";".join(map(str, self.colours_rgb["dark"]))}'

        # Generate string for each square on the board
        for y in range(len(board)):
            for x in range(len(board[0])):
                if board[y][x].letter in {'x', 'X'}:
                    board[y][x] = '  '
                    continue

                fg = '30;' if board[y][x] else ''
                bg = dark if (x + y + sum(size)) % 2 else light
                board[y][x] = f'\x1B[{fg}{bg}m{board[y][x]} \x1B[0m'

        # Rotations
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

            # Add coordinate to start of each row
            for i, (coord, rank) in enumerate(zip(column, board)):
                board[i] = f'{coord:>{length}} {rank}'
            # Add bottom row of coordinates
            board.append(f'{" "*length} {"".join(row)}')

        print('\n'.join(board))

    def perft(self, max_depth: int):
        """Generate perft results."""
        print("Depth Nodes Time(s) Nodes/s")
        for depth in range(1, max_depth+1):
            start = time.perf_counter()
            nodes = self.board.perft(depth)
            end = time.perf_counter()
            run_time = end-start
            # Print data (times are reported to the nearest millisecond)
            print(depth, nodes, f"{run_time:.3f}", f"{nodes/run_time:.3f}")


def rgb_to_hex(rgb: tuple) -> str:
    """Convert RGB colour to HEX."""
    return '#' + ''.join(f'{i:02x}' for i in rgb)


def command_line_interface(tkboard: TkBoard):
    """Command line interface version."""
    board = tkboard.board
    while True:
        print(board.get_fen())
        print(board.get_pgn())
        print(*board.legal_moves)
        tkboard.print()
        try:
            # Take user input to play move on board
            board.move(input(f"{board.active}: "))
        except ChessError:
            print("Illegal move")
        tkboard.refresh()


def main():
    """Starts the graphical user interface."""
    window = tk.Tk()
    window.title("Chess")
    window.iconphoto(False, tk.PhotoImage(file='images/chess.png'))

    board = Board()
    tkboard = TkBoard(window, board)
    tkboard.grid(row=0, column=0, sticky='news')

    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)
    window.geometry('1150x650+125+41')
    tk.mainloop()


if __name__ == '__main__':
    main()
