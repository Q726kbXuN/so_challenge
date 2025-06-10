#!/usr/bin/env python3

import random, sys

# All the possible characters we can encode, we start with a null 
# character to handle less than 8 characters
CHARS = "\x00 !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
# Optional, spend more time finding the hardest possible puzzle
HARD_MODE = False

def header(value):
    # Just dump out a header
    value = "-" * 5 + " " + value + " "
    print(value + "-" * (60 - len(value)))

def enum_xy(size, off_x=0, off_y=0):
    # Simple helper to only do the nested x/y enumeration one place
    for x in range(size):
        for y in range(size):
            yield x + off_x, y + off_y

def show_grids(*grids):
    # Dump out Sudoku grids
    rows = []
    cur_row = 0
    def add_to_row(value):
        nonlocal cur_row, rows
        if cur_row == len(rows):
            rows.append("")
        else:
            rows[cur_row] += "    "
        rows[cur_row] += value
        cur_row += 1

    for grid in grids:
        cur_row = 0
        if isinstance(grid, str):
            temp = [' ' * len(grid)] * len(rows)
            temp[len(temp) // 2] = grid
            for cur in temp:
                add_to_row(cur)
        else:
            for y in range(9):
                if y > 0 and y % 3 == 0:
                    add_to_row("-" * 7 + "+" + "-" * 7 + "+" + "-" * 7)
                row = " "
                for x in range(9):
                    if x > 0 and x % 3 == 0:
                        row += "| "
                    row += f"{grid[x + y * 9]} "
                add_to_row(row)

    for row in rows:
        print(row)

def valid_options(grid, x, y):
    # Return all valid answers for a cell, ignoring the cell itself
    ret = set(range(1, 10))
    for check_x in range(9):
        if check_x != x:
            ret.discard(grid[check_x + y * 9])
    for check_y in range(9):
        if check_y != y:
            ret.discard(grid[x + check_y * 9])
    off_x, off_y = (x // 3) * 3, (y // 3) * 3
    for check_x, check_y in enum_xy(3, off_x, off_y):
        if (check_x, check_y) != (x, y):
            ret.discard(grid[check_x + check_y * 9])
    return ret

def add_solution(grid, cell=0):
    # Recursive function, tries to add a valid solution and move on the 
    # next cell.  If a cell has no solution, backtrack and pick another 
    # solution from a cell with more than one option
    if cell == 81:
        # Hit the end, must have found the solution
        return grid
    elif grid[cell] == " ":
        options = valid_options(grid, cell % 9, cell // 9)
        if len(options) == 0:
            # Oops, nothing found, backtrack
            return None
        else:
            # Try each option, in a random order to prevent bias
            options = list(options)
            random.shuffle(options)
            for x in options:
                temp = grid[:]
                temp[cell] = x
                temp = add_solution(temp, cell + 1)
                if temp is not None:
                    # If we ran all the way to the end, just
                    # return what we found
                    return temp
    else:
        # This cell already has something, just use it as is
        return add_solution(grid, cell+1)

def create_encoded_grid(str):
    if len(str) > 8: raise Exception("String is too long")

    # Covert the string into a single number
    val = 0
    for x in str[::-1]:
        val *= len(CHARS)
        val += CHARS.index(x)

    # Create a Sudoku grid based off that value
    grid = [" "] * 81
    for off in range(3):
        # Fill diagonal squares, since they don't impact each other 
        # we can fill them with any permutation of digits
        numbers = list(range(1, 10))
        for x, y in enum_xy(3):
            # We have len(numbers) possible for this cell, so
            # pick the number based off of that
            temp = val % len(numbers)
            val //= len(numbers)
            # Store the value in the grid
            grid[x + off * 3 + (y + off * 3) * 9] = numbers.pop(temp)

    # And find a solution for the remaining cells, any solution
    # will do as there will likely be multiple options
    return add_solution(grid, 0)

def decode_grid(grid):
    # Opposite logic of create_encoded_grid

    mul, val = 1, 0
    # Run through the three diagonal squares
    for off in range(0, 9, 3):
        numbers = list(range(1, 10))
        for x, y in enum_xy(3, off, off):
            # Figure out the index of this cell from our list
            # of possible numbers
            temp = numbers.index(grid[x + y * 9])
            # That gets placed in the final number, and our multipler moved up
            val += temp * mul
            mul *= len(numbers)
            numbers.pop(temp)

    # Now take that final number and pull out each character from it
    decoded = ""
    for _ in range(8):
        decoded += CHARS[val % len(CHARS)]
        val //= len(CHARS)

    # If we hit the end of value, it'll start returning 0, which
    # is the one character we don't encode, using it to detect
    # short strings here
    return decoded.split("\x00")[0]

def create_worker(worker_id, grid, lock, global_best, global_grid):
    import time

    # Make sure this worker works on a different set than other workers
    random.seed(worker_id)

    # Our local best hit
    best, puzzle = 0, None

    bail_at = time.time() + 30  # Just try things for 30 seconds
    bail_hard = 40              # Or, till any worker finds one with 40 removed

    while time.time() < bail_at and global_best.value < bail_hard:
        test = make_single_puzzle(grid)
        removed = sum(1 if cell == ' ' else 0 for cell in test)
        if removed > best:
            best, puzzle = removed, test
            if best > global_best.value:
                with lock:
                    if best > global_best.value:
                        global_best.value = best
                        for i, val in enumerate(puzzle):
                            global_grid[i] = 0 if val == ' ' else val

def try_multiple_puzzles(grid):
    # Run through the puzzle maker worker multiple times, 
    # finding the hardest possible puzzle

    best, puzzle = 0, None
    if HARD_MODE:
        # For hard mode, just try a whole bunch for a while on 
        # all the cores we have available
        from multiprocessing import cpu_count, Value, Array, Lock, Process
        lock = Lock()
        best_value = Value('i')
        best_grid = Array('i', [0] * 81)
        procs = [Process(target=create_worker, args=(i, grid, lock, best_value, best_grid)) for i in range(cpu_count())]
        [x.start() for x in procs]
        [x.join() for x in procs]
        puzzle = [' ' if x == 0 else x for x in best_grid]
    else:
        for _ in range(100):
            test = make_single_puzzle(grid)
            removed = sum(1 if cell == ' ' else 0 for cell in test)
            if removed > best:
                best, puzzle = removed, test
                # Limit of 30 here as a reasonable cut off point, and to 
                # prevent from spinning too long looking for something
                if best >= 30: break
    
    return puzzle
    
def make_single_puzzle(grid):
    # Remove some number of cells, ensuring that we never end up with
    # a situation where a cell on the diagonal that we need to worry about
    # has more than one solution

    # Create a list of cells we can never have more than one solution to
    specials = []
    for off in range(0, 9, 3):
        for x, y in enum_xy(3, off, off):
            specials.append((x, y))

    grid = grid[:]
    bail = 5
    bail_reset = bail
    while bail > 0:
        # Create a list of boxes and how many cells still have a clue
        boxes = []
        for box_x, box_y in enum_xy(3):
            boxes.append([])
            for x, y in enum_xy(3):
                x, y = box_x * 3 + x, box_y * 3 + y
                if isinstance(grid[x + y * 9], int):
                    boxes[-1].append(x + y * 9)
        
        # Get all the boxes with the most number of answers in it
        boxes.sort(key=lambda x: len(x))
        boxes = [x for x in boxes if len(x) == len(boxes[-1])]

        # Pull out the cell we'll try to use
        cell = random.choice(random.choice(boxes))
        was_value = grid[cell]
        grid[cell] = ' '

        # And now see if we messed up any of the special values
        if all(len(valid_options(grid, x, y)) == 1 for x, y in specials):
            # This is all good, reset our bail out
            bail = bail_reset
        else:
            # Oops, this breaks one of the special cells, go ahead and revert it
            grid[cell] = was_value
            bail -= 1

    return grid

def write_html(grid):
    import json
    with open("sudoku_template.html", "rt", encoding="utf-8") as f:
        page = f.read()
    
    page = page.replace("['NEEDED']", json.dumps(grid))

    with open("sudoku_output.html", "wt", newline="", encoding="utf-8") as f:
        f.write(page)

def create_and_decode(value, create_html=False):
    # Start off making a encoded grid, this will 
    # only have 3 squares of 9 cells filled out
    grid = create_encoded_grid(value)
    # Add the solution to the grid
    grid = add_solution(grid)

    # Remove cells till we have a puzzle
    grid = try_multiple_puzzles(grid)
    # Now we have a puzzle that can be solved, but 
    # doesn't directly have the decoded value
    # in it anymore, so solve it
    removed = sum(1 for x in grid if x == ' ')
    header(f"Grid with {removed} removed cells, and solved puzzle")
    solved_grid = add_solution(grid)
    show_grids(grid, "--->", solved_grid)
    if create_html:
        write_html(grid)
    header("Hidden string")
    decoded = decode_grid(solved_grid)
    print(decoded)
    print("")

    if decoded != value:
        raise Exception("We got the wrong value!")

def decode_input():
    print("Enter a new line to end input")
    import re

    grid = []
    while True:
        temp = input()
        m = re.search("([1-9 ]) ([1-9 ]) ([1-9 ]) \\| ([1-9 ]) ([1-9 ]) ([1-9 ]) \\| ([1-9 ]) ([1-9 ]) ([1-9 ])", temp)
        if m is not None:
            for val in m.groups():
                if val == " ":
                    grid.append(' ')
                else:
                    grid.append(int(val))
        if len(temp) == 0:
            break

    if len(grid) == 81:
        solved_grid = add_solution(grid)
        decoded = decode_grid(solved_grid)
        print(decoded)
    else:
        print("Malformed grid")

def main():
    random.seed(42) # Not necessary, but makes runs consistent, so useful for debugging
    create_html = False

    if len(sys.argv) > 1:
        to_test = []
        for cur in sys.argv[1:]:
            if cur == "HARD_MODE":
                global HARD_MODE
                HARD_MODE = True
            elif cur == "SAVE_HTML":
                create_html = True
            elif cur == "decode":
                # A simple way to decode a grid
                decode_input()
                exit(0)
            else:
                # Allow passing in a string from the command line
                to_test.append(cur)
    else:
        to_test = [
            "TREASURE",
            "LOOKLEFT",
            "SECRETED",
            "DIGHERE!",
            "TOMORROW",
            "SMALL",
            "|-|311()",
        ]

    for value in to_test:
        create_and_decode(value, create_html=create_html)

if __name__ == "__main__":
    main()
