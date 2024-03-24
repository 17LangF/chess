"""Analyse and review chess games."""

import random

import computer

WIN_CHANGES = {
    # Classification: lower bound of win probability change
    'best': 0.0,
    'excellent': -0.02,
    'good': -0.04,
    'inaccuracy': -0.08,
    'mistake': -0.18,
    'blunder': -1.0
}

BOOK_COMMENTS = {
    'best': (
        " and it is a good choice",
        " and it is a great option",
        " and it is a nice move",
        " and it is a strong decision"
    ),
    'bad': (
        ", but is considered to be a bad move. The best move is []",
        ", but this leads to worse positions. [] would be better",
        ", but this can lead to a lot of trouble. A better move is []",
        ", but [] would be a much better move"
    ),
    'dubious': (
        ", but it is a dubious decision. The best move is []",
        ", but there are better moves to play such as []",
        ", but stronger openings are possible such as []",
        ", but this is not the best opion available. [] is better"
    )
}

COMMENTS = {
    'best': ("best", "the best move"),
    'excellent': ("excellent", "an excellent move"),
    'good': ("good", "a good move"),
    'book': ("a book move",),
    'inaccuracy': ("inaccurate", "an inaccuracy"),
    'mistake': ("a mistake",),
    'blunder': ("a blunder",),
}

BEST_COMMENTS = {
    'good': (
        ". The best move is []",
        ". [] is best",
        ", but [] is even better",
        ". [] is even better",
        ". Even better is []"
    ),
    'bad': (
        ". The best move is []",
        ". [] is best",
        ". [] is a better move",
        ". [] would be better",
        ". [] would be much better",
        ". A better move is []",
        ". A much better move is []"
    )
}

def analyse(board):
    """Analyse moves played and update move classifications/comments."""
    # Undo all moves
    while len(board.moves) > 1:
        board.undone_moves.append(board.moves[-1])
        board.undo(update_moves=False)
    board.undo()

    best = computer.stockfish(board)
    evaluation = board.evaluation
    in_book = True

    # Play moves until no undone moves left
    while board.undone_moves:
        move = board.undone_moves[-1]
        move.classification = ''
        board.redo()

        if move == best:
            move.classification = 'best'

        # Check for book moves
        if in_book:
            opening = book(board.moves)
            if opening:
                move.classification = 'book'
            else:
                in_book = False

        new_best = computer.stockfish(board)
        eval_change = (computer.standardise_eval(board.evaluation) -
                       computer.standardise_eval(evaluation))
        win_change = (computer.eval_to_win(board.evaluation) -
                      computer.eval_to_win(evaluation))
        # Flip evaluation and win probability for black's move
        if move.active == 'b':
            eval_change *= -1
            win_change *= -1

        if not move.classification:
            # Find first move classification win_change is greater than
            for classification, difference in WIN_CHANGES.items():
                if win_change >= difference:
                    break
            move.classification = classification

        evaluation = board.evaluation
        move.eval_change = eval_change
        move.win_change = win_change

        # Generate comments and explanations
        comment = random.choice(COMMENTS[move.classification])
        move.comment = f"{move.fullmove}. {move} is {comment}"
        if move.active == 'b':
            move.comment = move.comment.replace('.', '...', 1)

        if move.classification == 'book':
            # Add opening name to comment
            eco, name = opening
            if eco is None:
                move.comment += f". This leads to the {name}"
            else:
                move.comment += f". This is the {name}"
            if 'Opening' not in name and 'Game' not in name:
                move.comment += " opening"

            if move.fullmove == 1:
                # Do not add comment for the first move
                pass
            # Add appropriate book comment
            elif (eval_change > -0.1 and
                    (move.active == 'w' and evaluation > 0 or
                     move.active == 'b' and evaluation < 0.5)
                ):
                move.comment += random.choice(BOOK_COMMENTS['best'])
            elif eval_change < -1:
                move.comment += random.choice(BOOK_COMMENTS['bad'])
            elif eval_change < -0.5:
                move.comment += random.choice(BOOK_COMMENTS['dubious'])

        elif move.classification in {'excellent', 'good'}:
            move.comment += random.choice(BEST_COMMENTS['good'])
        elif move.classification in {'inaccuracy', 'mistake', 'blunder'}:
            move.comment += random.choice(BEST_COMMENTS['bad'])

        move.comment += ".\n\n"
        move.comment = move.comment.replace('[]', str(best))
        best = new_best


def summary(board):
    """
    Calculate summary statistics of game.

    Returns
    -------
    dict of {str: dict of {str, int}}, dict of {str, float},\
    dict of {str, float}
        Counts, accuracy, average centipawn loss of white and black.
    """
    counts = {classification: {'w': 0, 'b': 0} for classification in COMMENTS}
    accuracies = {'w': [], 'b': []}
    eval_change = {'w': [], 'b': []}
    accuracy = {'w': float('nan'), 'b': float('nan')}
    acpl = {'w': float('nan'), 'b': float('nan')}
    for move in board.moves:
        counts[move.classification][move.active] += 1
        eval_change[move.active].append(max(-move.eval_change, 0))
        # Give more generous accuracies in the opening
        win_change = move.win_change
        if move.classification == 'book':
            win_change += 0.02
        move_accuracy = 103.1668 * 10**(1.891*win_change) - 3.1668
        move_accuracy = max(min(move_accuracy, 100), 0)
        move_accuracy = 100 * (move_accuracy/100) ** 1.3
        accuracies[move.active].append(move_accuracy)

    # Calculate average evaluation change and accuracy for both sides
    for colour in ['w', 'b']:
        moves = len(eval_change[colour])
        book_moves = sum(move.classification == 'book'
                         for move in board.moves if move.active == colour)
        if not moves:
            continue
        # Accuracy calculated using a weighted harmonic mean shifted
        values = [1/(accuracy+10) for accuracy in accuracies[colour]]
        # Weigh book moves half as much
        for move in range(book_moves):
            values[move] *= 0.5
        accuracy[colour] = (moves-0.5*book_moves) / sum(values) - 10
        # ACPL calculated using arithmetic mean
        acpl[colour] = 100 * sum(eval_change[colour]) / moves

    return counts, accuracy, acpl


def book(moves: list):
    """Return the opening if book move, otherwise False."""
    with open('openings.txt') as file:
        openings = file.readlines()

    search = ' '.join(map(str, moves))  # Create string of moves
    search = search.replace('0', 'O')

    # Binary search to find moves in openings
    start = 0
    end = len(openings) - 1
    while start <= end:
        middle = (start + end) // 2
        eco, name, moves = openings[middle][:-1].split('"')
        if search == moves:
            return eco, name
        if search < moves:
            end = middle - 1
        else:
            start = middle + 1

    for middle in (end, start):
        eco, name, moves = openings[middle][:-1].split('"')
        if moves.startswith(search):  # Moves are partway into opening
            return (None, name)
    return False
