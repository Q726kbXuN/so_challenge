#!/usr/bin/env python3

with open("template.html", "rt", encoding="utf-8") as f:
    html = f.read()

with open("puzzle.json", "rt", encoding="utf-8") as f:
    puzzle = f.read()

html = html.replace('{"data": "placeholder"}', puzzle)

with open("puzzle.html", "wt", encoding="utf-8") as f:
    f.write(html)

print("Wrote out puzzle.html")
