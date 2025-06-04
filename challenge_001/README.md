# Stack Overflow Coding challenge

Solution to the [first Stack Overflow coding challenge](https://stackoverflow.com/beta/challenges/79640866/complete-code-challenge-1-implement-a-text-to-baby-talk-translator).  Here you can see how this worked for me.  The work flow is fairly straightforward:

* Create the basic program `baby_talk.py` that does the core of the conversion.  I tried to keep it small because the next step would involve base64 encoding it, and the wasted space with indent characters and variable names adds up.
* Use the simple GUI in `encode_script.py` to turn pixels on and off from the source PNG till I had something that both looked decent, and was the correct number of pixels.  Hitting Q or Escape here will dump out the base64 blob reformatted to look like the changed PNG file.
* And finally, create `final.py` with the base64 blob and a small wrapper around it to run it.
