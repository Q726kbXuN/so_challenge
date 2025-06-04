#!/usr/bin/env python3

import json

with open("clues.json", encoding="utf-8") as f:
    clues = json.load(f)

with open("source_data.json", encoding="utf-8") as f:
    data = json.load(f)

print("Creating puzzle")

puzzle = data['seed_phrase']
to_encodes = data['to_encodes']

def add_to_stack(puzzle, chars, used_answers=set()):
    # Start at the end, since this needs to be solved last clue first to
    # handle nested clues
    cur_char = chars[-1]
    # Find a letter, we return None if we can't find one, causing the recursive caller
    # to try another combination.

    possibles = []
    answers = set()
    for clue, answer, hits in clues:
        if clue[0].lower() == cur_char.lower() and answer.lower() in puzzle.lower():
            if answer not in used_answers and answer not in answers:
                answers.add(answer)
                possibles.append({
                    "clue": clue,
                    "answer": answer,
                    "hits": hits,
                })

    if len(possibles) == 0:
        # Nothing found, bail and hope the caller tries some other combo
        return None

    # Sort by longest, then most used, hopefully building a list of most interesting clues
    possibles.sort(key=lambda x: (len(x['answer']), x['hits']))
    for possible in possibles:
        # Pull out the answer, and call ourselvces for the next letter
        i = puzzle.lower().index(possible['answer'].lower())
        before, final, after = puzzle[:i], puzzle[i:i+len(possible['answer'])], puzzle[i+len(possible['answer']):]
        ret = {
            "puzzle": f"{before}[{possible['clue']}]{after}",
            "answer": final,
            "clue": possible["clue"]
        }
        
        if len(chars) == 1:
            # All done!
            return [ret]
        else:
            # If this returns none, it means this clue leads to a situation where we can't build the puzzle
            next_puzzle = add_to_stack(ret["puzzle"], chars[:-1], used_answers | {possible['answer']})
            if next_puzzle is not None:
                return [ret] + next_puzzle

    # If we got here, this branch is broken
    return None

to_output = []
for to_encode, title in to_encodes:
    print("-" * 5 + f" {to_encode} " + (70 - len(to_encode)) * "-")
    stack = add_to_stack(puzzle, to_encode)
    if stack is None:
        raise Exception(f"Unable to build puzzle with clues for '{puzzle}' -> '{to_encode}'!")

    to_output.append({
        "title": title,
        "answer": data['seed_phrase'],
        "puzzle": None,
        "solutions": [],
    })

    for cur in stack[::-1]:
        print(f"{cur['clue']} -> {cur['answer']} == {cur['puzzle']}")
        to_output[-1]['solutions'].append([cur['clue'], cur['answer']])
    to_output[-1]['puzzle'] = stack[-1]['puzzle']

print("-" * 100)
# Make the final json a little cleaner, just because
with open("puzzle.json", "wt", encoding="utf-8") as f:
    def pad(level):
        return " " * (level * 4)
    def dump_value(level, value):
        if isinstance(value, dict):
            f.write(pad(level) + "{\n")
            for i, (item_key, item_value) in enumerate(value.items()):
                f.write(pad(level + 1) + json.dumps(item_key) + ": ")
                dump_value(level + 1, item_value)
                f.write(("," if i < len(value) - 1 else "") + "\n")
            f.write(pad(level) + "}")
        elif isinstance(value, list):
            if all(isinstance(x, str) for x in value):
                f.write(pad(level) + json.dumps(value))
            else:
                f.write("\n" + pad(level) + "[\n")
                for i, item in enumerate(value):
                    dump_value(level + 1, item)
                    f.write(("," if i < len(value) - 1 else "") + "\n")
                f.write(pad(level) + "]")
        else:
            f.write(json.dumps(value))
    dump_value(0, to_output)
    f.write("\n")