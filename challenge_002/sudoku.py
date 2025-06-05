#!/usr/bin/env python3

import random
random.seed(42) # Not necessary, but makes runs consistent, so useful for debugging

# All the possible characters we can encode, we start with a null 
# character to handle less than 8 characters
CHARS = "\x00 !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

def header(value):
    # Just dump out a header
    print("-" * 5 + " " + value + " " + "-" * (60 - len(value)))

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

def make_simple_puzzle(grid):
    # Remove some number of cells, ensuring that we never end up with
    # a situation where a cell on the diagonal that we need to worry about
    # has more than one solution

    # The cells we'll try, we shuffle them so we try random cells
    grid = grid[:]
    cells = list(range(81))
    random.shuffle(cells)

    for cell in cells:
        # Remove this cell
        temp = grid[cell]
        grid[cell] = " "

        for off in range(0, 9, 3):
            if grid[cell] == temp: break
            for x, y in enum_xy(3, off, off):
                if len(valid_options(grid, x, y)) != 1:
                    # Oops, we removed a cell that caused more 
                    # than one possibility somewhere, add it back
                    grid[cell] = temp
                    break

    return grid

def create_and_decode(value):
    # Start off making a encoded grid, this will 
    # only have 3 squares of 9 cells filled out
    grid = create_encoded_grid(value)
    # Add the solution to the grid
    grid = add_solution(grid)

    # Remove cells till we have a puzzle
    grid = make_simple_puzzle(grid)
    # Now we have a puzzle that can be solved, but 
    # doesn't directly have the decoded value
    # in it anymore, so solve it
    removed = sum(1 for x in grid if x == ' ')
    header(f"Grid with {removed} removed cells, and solved puzzle")
    solved_grid = add_solution(grid)
    show_grids(grid, solved_grid)
    header("Hidden string")
    decoded = decode_grid(solved_grid)
    print(decoded)
    print("")

    if decoded != value:
        raise Exception("We got the wrong value!")

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
    create_and_decode(value)
