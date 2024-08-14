# Guess The Elo
Ethan Oh

## Overview
Guess The Elo is a web application game using Python, Flask, HTML, CSS, Javascript, and SQL. Users can view randomly generated chess games played on chess.com, and guess the elo, or rating, of the white player based on what the user thinks of the game performance. The user can create an account and log in, which will also keep track of simple statistics, including games played, guess distribution, average guess difference, and best guess. Based on GothamChess' (Levy Rozman) Guess The Elo YouTube Series!!

## User Guide

You may use a published website at [guesstheelo.tech](guesstheelo.tech) - This is a 301 redirect to ethon73.pythonanywhere.com (so I don't have to pay for web hosting). If you use this, accounts and stats will not be saved in the same database as the local if running through flask; its likely better to use the actual website for looking at the project.

Dependencies, using Python:
Ensure sqlite3 is accessible:
```
sudo app install sqlite3
```
Download the dependencies through 
```
pip3 install flask
pip3 install flask_session
pip3 install cs50
```
To run the web application locally, ensure you are in the project directory:
```
$ cd project
```
Then, run flask.
```
project/ $ flask run
```
Open the port in your browser, with the link provided by flask.

## Design
Languages Used:
* Python
* HTML
* CSS
* Javascript
* sqlite3
* Flask
* Jinja

In this project, there were three main components:
* Webscraping
* Processing
* Displaying

I used flask/python for back-end and sqlite3 for database management.

The project started with webscraping games from chess.com's public API (not directly from chess.com for legal reasons).

There are many routes/directories in the public API, where each page solely holds json formatted data. The routes I used were:
* List of Monthly Archives for a given user - URL pattern: https://api.chess.com/pub/player/{username}/games/archives
* Complete Month Archive for a given user and month - URL pattern: https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}

See [https://www.chess.com/news/view/published-data-api](https://www.chess.com/news/view/published-data-api) for more details.

I had to implement a dynamic random username, or rather random string of chars, to find if the user exists, if they played games, and to choose a game from the random user at random to ensure the most variability between games. As a note, I also implemented some restrictions for game/user experience, like a limit to the elo differences between players (250). The complete randomness and filters for better user experience is why the webpage may take a while to load.

From there, I processed all the games; the data pulled from the API had lots more data that what we solely need - namely the moves, player ratings, and times if possible. Processing called lots of functions in a systematic order, which eventually parsed all moves into a list, times into a list, and dynamically reverse-engineered each move to add a 2D array representing each position after each move to a list of all positions. One major problem was that certain game modes - specifically daily games - and games seemingly played before an update of the API had a different way to record each move, so I also had to figure out how to convert the new API format of the PGN - portable game notation, containing game data - to old so I could have a wide range of games.

Finally, I worked on the front-end web application portion, with HTML, CSS, and Javascript, as well as sqlite3. It's relatively logically simple, where each interaction triggers reading data processed in python and imported to HTML with Jinja to display the new position or time, and simple page/sql updates.

There is a SQL table of users, and stats.
Stats has a user's best guess, number of games played, average elo and guess distribution over 8 ranges.
It updates via a one-way AJAX query when the form with the user's elo guess is submitted.


### New Things Learned
* Using deepcopy for setting duplcates of arrays
    * Since arrays are linked lists in python, the arrays store pointers, so changing one array's values changes everything else - use deepcopy to properly duplicate without any shared points
* Chart.js
* Webscraping
* Simple AJAX
* JSON formatting, and passing data from Python to JS with JSON

## Acknoledgements/External Code Used

### External Code
* The code used for generating possible moves of a knight of where it came from was taken from a previous project of mine.

* Also Used:

    * https://stackoverflow.com/questions/25373154/how-to-iterate-through-a-list-of-dictionaries-in-jinja-template
    * https://stackoverflow.com/questions/3145030/convert-integer-into-its-character-equivalent-where-0-a-1-b-etc
    * https://www.freecodecamp.org/news/how-to-parse-a-string-in-python/
    * https://stackoverflow.com/questions/61977076/how-to-fetch-data-from-api-using-python
    * https://www.w3schools.com/ai/ai_chartjs.asp / https://www.w3schools.com/js/tryit.asp?filename=tryai_chartjs_bars_horizontal
    * https://stackoverflow.com/questions/2294493/how-to-get-the-position-of-a-character-in-python

## Versions and Bugs
* Version 0.1 - Submission
    * Bugs:
        * No ambiguous character - In rare cases, there are moves in a game where two pieces of the same type can move to the same square. However, one piece is pinned. PGNs and chess notation don't put the ambiguous notation to differ between the two pieces as really only one can legally move there. However, as I have to reverse engineer, the program cannot tell the piece if pinned to the king, so it thinks there are two possibilities and searches for the ambiguous notation when there is none.
            * In the case of such, the website redirects to the same page, for the process of selecting and processing a game to restart - with a different game
        * Game abandonment - In rare cases, players abandon a game; they play no moves. This results in a game without moves or only a move by white not black.
            * This is now nearly impossible with the filter of '20.' in the PGN, but in such case it should redirect to the same page, for the process of selecting and processing a game to restart - with a different game
        * I can't figure out why, but I need a second array to append positions to, likely because I'm somewhere editing the original array but not sure where.
        * Especially after using the web application for a while in one session, flask randomly cannot GET some images, returning 403, 400, or 502 Error. Restarting flask should work.
            * In such case, the alt attribute will appear with the text emoji/icon equivalent of the given piece, albeit tiny
        * Occasionally the layout does not load, returning ```An HHTP/1.x request was sent to an HTTP/2 only server``` in the console. Unsure of why.

I am interested in continuing to develop this project, and possible publishing to the web. Further versions would/may include:
* Better mobile web layout/compatibility
* Addition of a daily game as well, like Wordle
* Better security, less relying on trusting user (though it's a single-player game that doesn't really matter, so user is highly unlikely to change limiting parameters of code)
* Aesthetic user interface
* Highlighting a move by highlighting the move in the display/the squares it moved from and to
* More user-friendly stats page
* Fix rare/minor bugs mentioned above in Version 0.1 - Submission
