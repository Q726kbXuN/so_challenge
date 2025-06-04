#!/usr/bin/env python3

from urllib.request import urlretrieve
from collections import defaultdict
import os, gzip, json, re, html

# This is the data that powers the archive at https://q726kbxun.github.io/xwords/xwords.html
# See this python script for more details:
# https://github.com/Q726kbXuN/q726kbxun.github.io/blob/main/xwords/view_archive.py

_cache = {}
def get_data(num, start, len, mode='json', header=None, cache=False):
    url = "https://q726kbxun.github.io/xwords/xwords_data_{num:02d}.dat"
    url = url.format(num=num)
    fn = url.split("/")[-1]

    if fn not in _cache:
        if not os.path.isfile(fn):
            print(f"Caching {fn}...")
            urlretrieve(url, fn)
        with open(fn, "rb") as f:
            print(f"Reading {fn}...")
            _cache[fn] = f.read()

    data = _cache[fn][start:start+len]
    
    if header is not None:
        data = header + data

    if mode == 'json':
        return json.loads(data)
    elif mode == 'raw':
        return data
    elif mode == 'gzip':
        data = gzip.decompress(data)
        return json.loads(data)

# Two helpers to load and get the clues and answers out of each crossword
def enum_clues(data):
    quotes = {180: "'", 699: "'", 701: "'", 8216: "'", 8217: "'", 8220: '"', 8221: '"', 8242: "'", 8243: '"'}
    for dir_num, dir_desc, xstep, ystep in ((0, "Across", 1, 0), (1, "Down", 0, 1)):
        for cur in data[3]:
            if cur[1] == dir_num:
                clue = cur[0]
                answer = ""
                all_x = set()
                all_y = set()
                for i in range(3, len(cur), 2):
                    x, y = cur[i], cur[i+1]
                    all_x.add(x)
                    all_y.add(y)
                    if 0 <= x < data[0] and 0 <= y < data[1] and isinstance(data[2][y][x], str):
                        answer += data[2][y][x]
                    else:
                        answer = None

                # Ignore answers shorter than 4 letters, and oddball multi-spot answers
                if answer is not None and len(answer) >= 4 and (len(all_x) == 1 or len(all_y) == 1):
                    clue = re.sub(" \\([0-9,-]+\\)", "", clue)
                    # Only use answers that use letters
                    if re.match("^[A-Z]+$", answer):
                        # De HTMLify the clue since many of these include HTML entities
                        clue = html.unescape(clue)
                        # Normalize quotes so we find the different variants
                        clue = clue.translate(quotes)
                        # Strip simple quoted strings
                        if clue.startswith('"') and clue.endswith('"') and sum(1 for x in clue if x == '"') == 2:
                            clue = clue.strip('"')
                        if clue.startswith("'") and clue.endswith("'") and sum(1 for x in clue if x == '"') == 2:
                            clue = clue.strip("'")
                        
                        # Ignore clues like "See 12 Down"
                        if not clue.lower().startswith("see "):
                            yield clue, answer

def enum_all(bail=-1):
    meta = get_data(0, 22, 78)
    header = get_data(*meta[5:8], mode='raw')
    data = get_data(*meta[2:5], mode='gzip', header=header)

    for xword, years in data.items():
        for year, months in years.items():
            for month, days in months.items():
                for puz, info in days.items():
                    data = get_data(*info, mode='gzip', header=header, cache=True)
                    for info in enum_clues(data):
                        yield info
                        bail -= 1
                        if bail == 0:
                            return


# Ok, pull in a bunch of clues, and build up ones that are reused
clues = defaultdict(int)
print("Loading clues...")

bail, challenge = -1, 5  # Target levels
# bail, challenge = 100000, 1 # Test levels
for clue, answer in enum_all(bail=bail):
    if re.match("&[^ ]+;", clue):
        raise Exception("HTML Enttity! " + clue)
    clues[(clue, answer)] += 1

# Filter to clues that are used often enough to give us somewhat possible clues
clues = [(clue, answer, hits) for (clue, answer), hits in clues.items() if hits > challenge]
for i, (clue, answer, hits) in enumerate(clues):
    print(f"{i}: '{clue}' == '{answer}' / {hits}")

with open("clues.json", "wt", encoding="utf-8") as f:
    json.dump(clues, f, indent=4)

print("All done!")
