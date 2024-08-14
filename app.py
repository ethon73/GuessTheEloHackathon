from functions import generateArchive, parseMoves, generatePositions, htmlMoves, apology

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///gte.db")

# ~~~~

positions = []

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":
        #LOAD GAME AND GET POSITIONS
        validGame = False

        while validGame == False:

            game = generateArchive()

            if game != "invalid":
                validGame = True

        # print(game)
        elo = game["whiteElo"]
        moves, times = parseMoves(game["pgn"])

        htmlmoves = htmlMoves(moves)

        #adds time before moves to the times array, but not if daily -> no slashes and not one length
        initialTime = game["timeControl"]
        if "/" not in initialTime and len(times) != 1:
            if "+" in initialTime:
                index = initialTime.find("+")
                initialTime = initialTime[:index]
            initialTime = int(initialTime)

            #now initial time is number of seconds.
            hours = initialTime // 3600
            minutes = (initialTime - hours*3600) // 60
            seconds = (initialTime - hours*3600 - minutes*60)

            startTime = str(hours)+":"+str(minutes)+":"+str(seconds)+".0"

            times.insert(0, startTime)
            times.insert(0, startTime)

        # print("\n\n", moves, times)

        if len(moves) < 2:
            # print("ABANDONMENT ERROR")
            return redirect("/")

        global positions

        positions = generatePositions(moves)

        if positions == "ERROR": #bug from non-ambiguous char from illegal move, see README
            # print("NONAMBIGUOUS ERROR")
            return redirect("/")

        return render_template("index.html", positions = positions, moves = htmlmoves, elo = elo, times = times)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure all fields were submitted
        if not username:
            return apology("must provide username", 400)

        elif not password:
            return apology("must provide password", 400)

        elif not confirmation:
            return apology("must retype password", 400)

        if password != confirmation:
            return apology("passwords do not match", 400)

        try:
            db.execute("INSERT INTO users (username, password) VALUES(?, ?)",
                       username, generate_password_hash(password))
        except ValueError:
            return apology("username already taken", 400)

        # Remember which user has logged in
        dbusers = db.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1;")
        session["user_id"] = dbusers[0]["id"]

        #add new user to stats
        db.execute("INSERT INTO stats (person, gamesPlayed, u10, u25, u50, u100, u250, u500, u1000, other, bestGuess, average) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   session["user_id"], 0, 0, 0, 0, 0, 0, 0, 0, 0, 99999, 0)

        return redirect("/")

    else:
        return render_template("register.html")


@app.route('/log_game', methods=['POST'])
def log_game():
    diff = abs(int(request.form['guessDiff']))

    # Process the single variable

    if session["user_id"]:

        #general Data to update
        gamesPlayed = db.execute("SELECT gamesPlayed FROM stats WHERE person = ?", session["user_id"])
        gamesPlayed = gamesPlayed[0]["gamesPlayed"] + 1
        prevBestGuess = db.execute("SELECT bestGuess FROM stats WHERE person = ?", session["user_id"])
        prevBestGuess = prevBestGuess[0]["bestGuess"]

        if diff < prevBestGuess:
            db.execute("UPDATE stats SET bestGuess = ? WHERE person = ?", diff, session["user_id"])
        db.execute("UPDATE stats SET gamesPlayed = ? WHERE person = ?", gamesPlayed, session["user_id"])


        #game data, how well they played to udate
        if diff <= 10:
            tableRange = "u10"
        elif diff <= 25:
            tableRange = "u25"
        elif diff <= 50:
            tableRange = "u50"
        elif diff <= 100:
            tableRange = "u100"
        elif diff <= 250:
            tableRange = "u250"
        elif diff <= 500:
            tableRange = "u500"
        elif diff <= 1000:
            tableRange = "u1000"
        else:
            tableRange = "other"

        query = f"SELECT {tableRange} FROM stats WHERE person = ?"
        gamesRanking = db.execute(query, session["user_id"])

        gamesRanking = gamesRanking[0][tableRange] + 1

        # db.execute("UPDATE stats SET ? = ? WHERE person = ?", tableRange, gamesRanking, session["user_id"])
        update_query = f"UPDATE stats SET {tableRange} = ? WHERE person = ?"
        db.execute(update_query, gamesRanking, session["user_id"])

        previousAvg = db.execute("SELECT average FROM stats WHERE person = ?", session["user_id"])
        previousAvg = previousAvg[0]["average"]

        average = (gamesPlayed - 1) * previousAvg
        average = (average+diff) / gamesPlayed

        db.execute("UPDATE stats SET average = ? WHERE person = ?", average, session["user_id"])

    return jsonify({'status': 'success'})


@app.route('/stats', methods=['GET'])
def stats():
    userStats = db.execute("SELECT * FROM stats WHERE person = ?", session["user_id"])
    userStats = userStats[0]

    user = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
    user = user[0]["username"]

    return render_template("stats.html", userStats = userStats, user = user)

@app.route('/favicon.ico')
def favicon():
    return '', 204

# CREATE TABLE users (
#     id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
#     username TEXT UNIQUE NOT NULL,
#     password TEXT NOT NULL
# );

# CREATE TABLE stats (
#      person INTEGER UNIQUE NOT NULL,
#      gamesPlayed INTEGER NOT NULL,
#      u10 INTEGER NOT NULL,
#      u25 INTEGER NOT NULL,
#      u50 INTEGER NOT NULL,
#      u100 INTEGER NOT NULL,
#      u250 INTEGER NOT NULL,
#      u500 INTEGER NOT NULL,
#      u1000 INTEGER NOT NULL,
#      other INTEGER NOT NULL,
#      bestGuess INTEGER NOT NULL,
#      average INTEGER NOT NULL,
#      FOREIGN KEY (person) REFERENCES users(id)
# );


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#FOR DEBUGGING WITH PYTHON, no web app
# validGame = False

# while validGame == False:

#     game = generateArchive()

#     if game != "invalid":
#         validGame = True

# print(game)
# moves, times = parseMoves(game["pgn"])

# print(moves, times)

# global positions
# positions = generatePositions(moves)
