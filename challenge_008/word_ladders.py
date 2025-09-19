#!/usr/bin/env python3

from collections import defaultdict, deque
from urllib.request import urlretrieve
import os

# Simple helper to return a list of possible place holders
# for a given word, i.e., (".ne", "o.e", "on." for "one")
def get_placeholders(word):
    for i in range(len(word)):
        yield word[:i] + "." + word[i+1:]

# Load all of the words, putting each word in each possible
# placeholder for that word
words = defaultdict(list)
url = "https://cs.stanford.edu/%7Eknuth/sgb-words.txt"
fn = "sgb-words.txt"
if not os.path.isfile(fn):
    urlretrieve(url, fn)
with open("sgb-words.txt", "rt") as f:
    for row in f:
        row = row.strip()
        for placeholder in get_placeholders(row):
            words[placeholder].append(row)

# And now find the ladders for each given pair:
pairs = [
    ['stone', 'money'],
    ['bread', 'crumb'],
    ['smile', 'giant'],
    ['apple', 'zebra'],
    ['other', 'night'],
    ['bread', 'blood'],
    ['black', 'white'],
]

for start_word, end_word in pairs:
    # Run through a simple A* path finding for going from the start word to
    # the end word, keeping track of all of the words we use along the way    
    stack = deque([(start_word, [start_word])])
    # Don't both using the same word more than once, so track each 
    # word we've used
    seen = set()

    while True:
        if len(stack) == 0:
            # No path from start to end
            print("")
            print(f"{start_word} to {end_word}:")
            print("No ladder found!")
            break

        cur_word, path = stack.pop()
        if cur_word == end_word:
            # We found the word, dump out the path
            print("")
            print(f"{start_word} to {end_word}:")
            print(f"{len(path)} steps for {start_word} to {end_word}")
            print(" -> ".join(path))
            break

        # Add each word from each placeholder to the stack of things to try
        for placeholder in get_placeholders(cur_word):
            for next_word in words[placeholder]:
                if next_word not in seen:
                    seen.add(next_word)
                    # Just to make it obvious which letter is changing
                    changed_letter = placeholder.index(".")
                    changed_word = next_word[:changed_letter] + next_word[changed_letter].upper() + next_word[changed_letter+1:]
                    stack.appendleft((next_word, path + [changed_word]))
