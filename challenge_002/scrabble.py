#!/usr/bin/env python3

from collections import defaultdict
from urllib.request import urlretrieve
import gzip, os, random, sys

# The number of characters we encode, and the character set
# Only use A-Z and 0-9 since more characters decreases the likelyhood of finding a puzzle
MAX_CHARS = 10
TO_ENCODE = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def get_words():
    # To do this, we need a list of words.  We'll grab the list from online, a 750kb file, and load it.
    fn = "collins-2019.jsonl.gz"
    if not os.path.isfile(fn):
        url = "https://gist.github.com/Q726kbXuN/14cf54435506c644bc0e2af5e35dd301/raw/efa4cf849dc72653d8f34a4609cc3b2144b4137b/collins-2019.jsonl.gz"
        urlretrieve(url, fn)
    with gzip.open(fn, "rt") as f:
        return [x for x in f.read().split("\n") if len(x)]

def get_common_middle_letters():
    # We're going to use the third and forth letters of four or more letter words
    # to encode the target value, to make the encoded string a bit hidden
    # and also prevent some bias problems from using the first letters

    # Get the frequency counts
    hits = defaultdict(int)
    for word in get_words():
        if len(word) >= 4:
            hits[word[2:4]] += 1

    # Turn the frequency counts into a simple list:
    hits = [(k, v) for k, v in hits.items()]
    hits.sort(key=lambda x: x[1])

    # And pull out the most common pairs we can use as our simple 
    # replacement cipher
    cipher = []
    for k, v in hits[-(len(TO_ENCODE) * MAX_CHARS):]:
        cipher.append(k)
    return cipher

def is_in_bag(word, draw_bag, ignore_letters="", update_bag=False):
    # Helper to tell us if a given word could come from a draw bag
    extra = {x: 0 for x in draw_bag}
    for x in ignore_letters:
        if x in extra:
            extra[x] += 1

    for x in word:
        if draw_bag[x] + extra[x] <= 0:
            return False
        extra[x] -= 1

    if update_bag:
        for x, val in extra.items():
            draw_bag[x] += val

    return True

def place_word(word, grid, draw_bag, place, x, y, horiz):
    # Place a word on the board, and remove the tiles from the bag

    # Remove the letters from the draw bag
    is_in_bag(word, draw_bag, grid[(x, y)], True)

    placed_letters = []

    # And place the letters
    for char in word:
        if grid[(x, y)] not in (char, " "): 
            raise Exception()
        if grid[(x, y)] == " ":
            placed_letters.append({"char": char, "pos": (x, y), "placed": True, "horiz": horiz})
            grid[(x, y)] = char
        else:
            placed_letters.append({"char": char, "pos": (x, y), "placed": False, "horiz": horiz})

        if horiz:
            x += 1
        else:
            y += 1

    place.append(placed_letters)    

def show_grid(grid):
    # Just dump out a grid to stdout
    for y in range(15):
        row = ""
        for x in range(15):
            row += " " + grid[(x, y)]
        print(row)

def enum_xy(width, height):
    # Helper to make the x,y enum one level
    for x in range(width):
        for y in range(height):
            yield x, y

def find_place(digit, grid, draw_bag, place, word, first_letter, words, cipher):
    # Find the next word, and place it.  This will be called recursively till
    # we've finished all the letters in word

    if len(word) == 0:
        # We hit the end, go ahead and return the current state as the good state
        return grid, place

    # This is the target letters we need in the word
    cur = word[:1]
    target = cipher[TO_ENCODE.index(cur) + digit * len(TO_ENCODE)]

    if first_letter:
        # All the possible words we could play
        options = [x for x in words if x[2:4] == target and len(x) <= 7]
        # Now filter down to the ones that have enough letters
        # left in the draw bag
        options = [x for x in options if is_in_bag(x, draw_bag)]
        if len(options):
            # For the first word, just pick something and place it on the center of the board
            random.shuffle(options)
            for picked in options:
                grid_copy = grid.copy()
                draw_bag_copy = draw_bag.copy()
                place_copy = place.copy()
                place_word(picked, grid_copy, draw_bag_copy, place_copy, 7 - len(picked) // 2, 7, True)
                ret = find_place(digit + 1, grid_copy, draw_bag_copy, place_copy, word[1:], False, words, cipher)
                if ret is not None:
                    return ret
    else:
        # All the possible words we could play
        options = [x for x in words if x[2:4] == target and len(x) <= 8]

        if len(options):
            random.shuffle(options)
            # Only try a few options at this level, if all of these don't work, the level that
            # called us can try something else
            options = options[:10]

            for picked in options:
                # For each word, try to find a place to put i ton the grid
                for (x, y), val in grid.items():
                    for off, char in enumerate(picked):
                        if char == val:
                            # Ok, this could go on the grid here, but first need to make
                            # sure it doesn't interfer with something elsewhere on the grid
                            if is_in_bag(picked, draw_bag, char):
                                # Try both horiz and veritcal
                                for dir_x, dir_y, horiz in ((0, 1, False), (1, 0, True)):
                                    valid = True
                                    start_x, start_y = x - dir_x * off, y - dir_y * off
                                    if 0 <= start_x < 15 and 0 <= start_y < 15:
                                        # And run through each letter, the first and last need to have
                                        # a space before and after them (or be off the grid)
                                        # The reset either need to intersect with the same letter, or
                                        # have a space on either side of them
                                        cur_x, cur_y = start_x - dir_x, start_y - dir_y
                                        valid = True
                                        intersect, laid_down = 0, 0
                                        for cur in " " + picked + " ":
                                            if cur == " ":
                                                # Checking for a space just means we're checking before or after the word
                                                # make sure it's an empty cell (or outside of the grid)
                                                if grid.get((cur_x, cur_y), " ") != " ":
                                                    valid = False
                                                    break
                                            elif grid.get((cur_x, cur_y), "#") == " ":
                                                # Ok, this cell is empty, meaning we'd palce a letter here, make sure the cells on either side
                                                # are empty (note the swap of dir_x and dir_y, we want to go to the side, not the direction of the word)
                                                if grid.get((cur_x - dir_y, cur_y - dir_x), " ") != " " or grid.get((cur_x + dir_y, cur_y + dir_x), " ") != " ":
                                                    valid = False
                                                    break
                                                laid_down += 1
                                            elif grid.get((cur_x, cur_y), "#") == cur:
                                                # This means this cell already has the letter we want from the word, so it's good
                                                intersect += 1
                                            else:
                                                # Some other scenario means we can't place this word here
                                                valid = False
                                                break
                                            cur_x, cur_y = cur_x + dir_x, cur_y + dir_y

                                        if valid and laid_down > 0:
                                            # If the word looks good and we actually have to place letters to play it
                                            # go ahead and copy our state, and try the next letter
                                            grid_copy = grid.copy()
                                            draw_bag_copy = draw_bag.copy()
                                            place_copy = place.copy()
                                            place_word(picked, grid_copy, draw_bag_copy, place_copy, start_x, start_y, horiz)
                                            ret = find_place(digit + 1, grid_copy, draw_bag_copy, place_copy, word[1:], False, words, cipher)
                                            if ret is not None:
                                                # If we get here, that means the recursive call finally worked, so return the result
                                                return ret
            

# -----------------------------------------------

def decode_grid(grid, cipher):
    # Rather simple worker to run through, find all the words of the grid, get their cipher value, and
    # build up the return word
    ret = {}
    for (x, y), val in grid.items():
        for dir_x, dir_y in ((1, 0), (0, 1)):
            # Find the start of a four or more letter word
            if "".join(" " if grid.get((x + off * dir_x, y + off * dir_y), " ") == " " else "." for off in range(-1, 4)) == " ....":
                # Pull out the target letters for our cipher
                code = "".join(grid.get((x + off * dir_x, y + off * dir_y), " ") for off in range(2, 4))
                # Decode the letter, and which one this is
                code = cipher.index(code)
                ret[code // len(TO_ENCODE)] = TO_ENCODE[code % len(TO_ENCODE)]
    return "".join(ret[x] for x in sorted(ret))

def encode(word):
    draw_bag = {
        "E": 12, "A": 9, "I": 9, "O": 8, "N": 6,    # 1 point
        "R": 6, "T": 6, "L": 4, "S": 4, "U": 4,     # 1 point
        "D": 4, "G": 3,                             # 2 points
        "B": 2, "C": 2, "M": 2, "P": 2,             # 3 points
        "F": 2, "H": 2, "V": 2, "W": 2, "Y": 2,     # 4 points
        "K": 1,                                     # 5 points
        "J": 1, "X": 1,                             # 8 points
        "Q": 1, "Z": 1,                             # 10 points
        "*": 2,                                     # 0 points
    }
    special_cells = {
        (0, 0): 'TW', (0, 3): 'DL', (0, 7): 'TW', (0, 11): 'DL', (0, 14): 'TW', (1, 1): 'DW', 
        (1, 5): 'TL', (1, 9): 'TL', (1, 13): 'DW', (2, 2): 'DW', (2, 6): 'DL', (2, 8): 'DL', 
        (2, 12): 'DW', (3, 0): 'DL', (3, 3): 'DW', (3, 7): 'DL', (3, 11): 'DW', (3, 14): 'DL', 
        (4, 4): 'DW', (4, 10): 'DW', (5, 1): 'TL', (5, 5): 'TL', (5, 9): 'TL', (5, 13): 'TL', 
        (6, 2): 'DL', (6, 6): 'DL', (6, 8): 'DL', (6, 12): 'DL', (7, 0): 'TW', (7, 3): 'DL', 
        (7, 7): 'DW', (7, 11): 'DL', (7, 14): 'TW', (8, 2): 'DL', (8, 6): 'DL', (8, 8): 'DL', 
        (8, 12): 'DL', (9, 1): 'TL', (9, 5): 'TL', (9, 9): 'TL', (9, 13): 'TL', (10, 4): 'DW', 
        (10, 10): 'DW', (11, 0): 'DL', (11, 3): 'DW', (11, 7): 'DL', (11, 11): 'DW', 
        (11, 14): 'DL', (12, 2): 'DW', (12, 6): 'DL', (12, 8): 'DL', (12, 12): 'DW', 
        (13, 1): 'DW', (13, 5): 'TL', (13, 9): 'TL', (13, 13): 'DW', (14, 0): 'TW', 
        (14, 3): 'DL', (14, 7): 'TW', (14, 11): 'DL', (14, 14): 'TW',
    }
    tiles_value = {
        'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4, 'I': 1, 'J': 8, 'K': 5, 
        'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 
        'W': 4, 'X': 8, 'Y': 4, 'Z': 10, '*': 0
    }

    # Create a simple empty grid
    grid = {(x, y): ' ' for x, y in enum_xy(15, 15)}

    # Create the grid
    print("Working...")
    grid, place = find_place(0, grid, draw_bag, [], word, True, get_words(), get_common_middle_letters())

    scores = [0, 0]
    player = 0
    for step in place:
        points = 0
        for tile in step:
            mult = 1
            if tile['placed'] and tile['pos'] in special_cells:
                if special_cells[tile['pos']] == "TL":
                    mult = 3
                elif special_cells[tile['pos']] == "DL":
                    mult = 2
            points += tiles_value[tile['char']] * mult
        for tile in step:
            if tile['placed'] and tile['pos'] in special_cells:
                if special_cells[tile['pos']] == "TW":
                    points *= 3
                elif special_cells[tile['pos']] == "TW":
                    points *= 2

        pos = f"{step[0]['pos'][0] + 1} by {step[0]['pos'][1] + 1}"
        horiz = "across" if step[0]['horiz'] else "down"
        print(f"{scores[0]} / {scores[1]}: Player {player+1} played '{''.join(x['char'] for x in step)}' at {pos} {horiz} for {points} points")
        scores[player] += points
        player = (player + 1) % 2

    show_grid(grid)
    decoded = decode_grid(grid, get_common_middle_letters())
    print(f"That grid decodes to: {decoded}")

def decode_input():
    print("Enter a grid to decode, enter a single '.' to end input:")
    grid = {(x, y): ' ' for x, y in enum_xy(15, 15)}
    y = 0
    while True:
        row = input()
        if row == ".":
            break
        for x, char in enumerate(row):
            if x % 2 == 1:
                grid[(x // 2, y)] = char
        y += 1
    decoded = decode_grid(grid, get_common_middle_letters())
    print(f"That decodes to {decoded}")

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "encode":
        encode(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == "decode":
        decode_input()
    else:
        print("Usage:")
        print("  encode <x> = Encode a word")
        print("  decode = Decode a grid")

if __name__ == "__main__":
    main()
