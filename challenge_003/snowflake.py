#!/usr/bin/env python3

import math, random, sys

def show_grid(grid):
    # Just find the limits of the grid, and show 
    # whatever text is in it
    min_x, max_x = min(x for x, y in grid), max(x for x, y in grid)
    min_y, max_y = min(y for x, y in grid), max(y for x, y in grid)
    # Add some padding 
    min_x -= 2
    min_y -= 1
    max_y += 1
    for y in range(min_y, max_y + 1):
        row = ""
        for x in range(min_x, max_x + 1):
            row += grid.get((x, y), " ")
        print(row)

def make_snowflake(ice, size, seed=None, grid={}, center=(0, 0)):
    if seed is not None: random.seed(seed)

    # Pick the size of the snowflake at random as well
    if isinstance(size, int):
        size = [random.randint(size - 4, size)]
        for _ in range(0, len(ice) - 1):
            if random.random() > 0.25: size.append(random.randint(size[-1] // 3, size[-1] // 2))

    # Nothing to do when we run out of values
    if len(size) == 0: return
    
    # Place center, note that the grid can extend into the negative values
    if center not in grid: grid[center] = ice[0]
    
    # Find a few points along each branch that'll trigger a sub-branch
    next_branches = list(range(size[0] // 4, size[0]))
    random.shuffle(next_branches)
    next_branches = next_branches[:random.randint(0, 3)]

    sub_branches = []
    # Generate 6 branches for this point
    for r in range(1, size[0]):
        # Use a sub-seed based off our RNG so each branch looks the same
        sub_seed = random.random()
        for branch in range(6):
            base_angle = branch * math.pi / 3

            x = ((r / 2) * math.cos(base_angle))
            y = ((r / 2) * math.sin(base_angle))
            # When calculating the postiion, double X so it looks reasonable in a ASCII output
            pt = (center[0] + round(x * 2), center[1] + round(y))

            if pt not in grid: grid[pt] = ice[0]

            if r in next_branches:
                # And based off our random picks, add some sub-branches
                sub_branches.append((pt, sub_seed))
                pass

    # Draw out the sub-branches    
    for pt, sub_seed in sub_branches:
        make_snowflake(ice=ice[1:], size=size[1:], center=pt, grid=grid, seed=sub_seed)

    return grid

def main():
    # Either use some hardcoded seeds, or let the user enter their own
    if len(sys.argv) == 1:
        seeds = [42, 123, 999]
    else:
        seeds = map(int, sys.argv[2:])

    for i, seed in enumerate(seeds, 1):
        print("")
        msg = f"Snowflake {i} (seed: {seed}):"
        print("-" * 5 + " " + msg + " " + "-" * (50 - len(msg)))
        snowflake = make_snowflake(ice="Xo.", size=20, seed=seed)
        show_grid(snowflake)

if __name__ == "__main__":
    main()
