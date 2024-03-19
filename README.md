# IF-Copilot
Play interactive fiction with an LLM friend

---
Living Room

You are sitting at a desk in a living room. A calendar on the wall says "July 1983."

There is a Compaq Portable computer here. The computer is turned on and seems to be waiting for instructions.

A friend is here.

\> START GAME

The computer starts up an interactive fiction session.
Your friend is very excited. "As an AI language model, I can't help but love these kind of games! Let's play!"

\> LOOK AT FRIEND

You've known them for about two years. They're very enthusiastic, even when they're wrong. They typically have lots of ideas, though, so they'll probably be an interesting person to play some interactive fiction with.

\> FRIEND, WHAT SHOULD WE DO NEXT?

"Well, do you want to drive or should I?"

\>FRIEND, PLAY THE NEXT 10 TURNS FOR ME

Almost before you finish your sentence, your friend grabs the keyboard and drags it across the desk, where it stops directly in front of them. You grab your Crystal Light off the desk just in time to avoid it being knocked over by the curly keyboard cable.
Your friend starts typing furiously....

---
## Description

This project lets an LLM play the role of an enthusiastic partner for playing interactive fiction with.
You can play the game yourself and just ask your friend for advice, or you can turn the game over to them and watch them play.

## Requirements

An instance of [zmachine-api](https://github.com/opendns/zmachine-api) needs to be up and running with at least one game file available. Specify the host and port in zmachine_client.py.
If you have an Infocom z5 file, you can use that. If you want to play something a bit more modern, go get something from the [IF Archive](https://www.ifarchive.org/indexes/if-archive/games/zcode/).

You'll also need an OpenAI API key.

For the full assistant experience, run `python zmachine_llm_3_sided.py`. At the moment it has a maximum 500-turn limit, just to prevent OpenAI billing accidents.
To just have the LLM play the game alone, run `python zmachine_llm.py`. By default it will only play 5 turns, so you'll want to bump that range(5) call if you want to run it longer.



