# fullmoon
An IRC bot to run the game Werewolf

## Disclaimer
This code was written between 2009 and 2011 for Python 2.5. The original source code is currently
missing, so this version has been salvaged from an old test deployment. It is not expected to work
at all in its current form.

## About
Fullmoon was a game based on Werewolf or Mafia that was played over IRC. The program connects to
IRC to create a Narrator bot in a dedicated channel. This bot was responsible for assigning roles,
keeping track of game state, and allowing some actions to be hidden in private messages whilst
other actions were performed publicly in the channel.

This project also contains some helper modules that had been used to make other bots. Low level
IRC protocol was managed by [lolbot](lolbot.py), with state management features and other helper
functions added by [winbot](winbot.py).
