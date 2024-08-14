import urllib.request
import json
from random import randint
import copy
from flask import render_template

def generateArchive():

    playerFound = False
    counter = 0

    while playerFound == False:

        player = ""

        #generate random player to find list of monthly archives w/games
        for i in range(randint(3,9)):
            letter = chr(randint(97, 122))
            player = player + letter

            # print(player)
        #failsafe, so likely to have a relatively quick load(my own profile)
        if counter >= 10:
            player = "raponto"

        url = "https://api.chess.com/pub/player/" + player + "/games/archives"

        #http request, webscraping API
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() == 200:
                httpCode = 200
        except urllib.error.HTTPError:
            httpCode = 404


        if httpCode == 200:
            allArchives = json.loads(response.read())
            archives = allArchives["archives"]

            if not archives:
                playerFound = False
            else:
                playerFound = True

        if httpCode == 404:
            # print("finding another player")
            pass

        counter += 1

    #random monthly archive when valid player found
    archive = archives[randint(0, len(archives)-1)]

    game = loadGame(archive)
    return game

def loadGame(archive):

    #opens link randomly chosen from api's list of monthly archives, and webscrapes those games then choose a random game
    response = urllib.request.urlopen(archive)
    allGames = json.loads(response.read())
    games = allGames["games"]

    game = games[randint(0, len(games)-1)]

    #IMPORTANT DATA VARS
    whiteElo = game["white"]["rating"]
    blackElo = game["black"]["rating"]
    timeControl = game["time_control"]
    time = game["time_class"]
    whiteResult = game["white"]["result"]
    blackResult = game["black"]["result"]
    gameType = game["rules"]

    # print(whiteElo, blackElo, time, whiteResult, blackResult, gameType)

    #ensures elo gap isn't too wide, or not regular chess (altered starting position or variation like bughouse), also tries to get longer games with at least 30 moves
        #some small games go through as pgn may includes times, so 2:30.000 may be included, which is fine as doesnt lengthen search process as not often foudn)
    if gameType != "chess":
        return "invalid"
    if abs(whiteElo - blackElo) > 250:
        return "invalid"
    if game["initial_setup"] != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
        return "invalid"
    if "20." not in game["pgn"]:
        return "invalid"
    # if timeControl == "daily":
    #     return "invalid"

    gameData = {
        "whiteElo" : whiteElo,
        "blackElo" : blackElo,
        "time" : time,
        "timeControl" : timeControl,
        "gameType" : gameType,
        "whiteResult" : whiteResult,
        "blackResult" : blackResult,
        "pgn" : game["pgn"]
    }
    return gameData


def parseMoves(pgn):
    moves = pgn.split()
    times = []

    #removes starter data
    while moves[0] != "1.":
        del moves[0]
    # print(moves)


    #seperate times
    for i in moves:
        if "{[%" in i:
            moves.remove(i)

    for i in moves:
        if "]}" in i:
            newstr = i.replace("]}", "")
            moves.remove(i)
            times.append(newstr)

    #converts new format to same as old format/daily format (daily has no times, and old format just had 1. e5 c4 instead of 1. e5 1... c4)
    for i in range(len(moves)-1, 0, -1):
        if "..." in moves[i]:
            del moves[i]

    # print("\n", moves)

    orgMoves = {}
    fullMoves = (len(moves)-1)//3

    #creates dictionary of moveColour:move. like 1W : e4
    for i in range(fullMoves):
        moveNum = moves[i*3]
        whiteMove = moveNum.replace(".", "W")
        blackMove = moveNum.replace(".", "B")
        orgMoves[whiteMove] = moves[i*3+1]
        orgMoves[blackMove] = moves[i*3+2]

    #if white had last move, and not black (as moves includes move#, two moves, and a FINAL result, so if white finished the game, it would be moves*3 (move#+2 moves), + move#, white move, end result)
    if len(moves) % 3 == 0:
        moveNum = str(i+2) + "W"
        orgMoves[moveNum] = moves[i*3+4]

    orgMoves["end"] = moves[-1]

    #daily and old api webscraping data does not include timess
    if len(times) == 0:
        times.append("daily or old API")

    # print(orgMoves, times)

    return orgMoves, times

#watch out for immutable and mutable objects, i.e. lists are pointers to them so if list = list, changing 1st list changes second, use copy or deepcopy, mutable is list
def generatePositions(moves):

    #array of two d array, white starts at first row of array of each position, lowercase = black, uppercase = white,
    #r = rook, p = pawn, k - king, n = knight, b = bishop, q = queen
    startPosition = [["R", "N", "B", "Q", "K", "B", "N", "R"], ["P", "P", "P", "P", "P", "P", "P", "P"], ["-", "-", "-", "-", "-", "-", "-", "-"], ["-", "-", "-", "-", "-", "-", "-", "-"], ["-", "-", "-", "-", "-", "-", "-", "-"], ["-", "-", "-", "-", "-", "-", "-", "-"], ["p", "p", "p", "p", "p", "p", "p", "p"], ["r", "n", "b", "q", "k", "b", "n", "r"]]
    positions = []
    #for some reason, to fix/debug later, positions is being edited when im moving pieces, so heres one that just gets moves added and not checked otherwise
    #or something with mutable/immutable objects, copyiung lists or their items and such... idk
    uneditedPositions = []

    positions.append(startPosition)
    uneditedPositions.append(startPosition)

    if len(moves) % 2 == 0:
        numMoves = int(len(moves) / 2)
    else:
        numMoves = (len(moves)-1) // 2
    # print(numMoves)

    for i in range(1, numMoves+1):

        #WHITE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        colour = "white"
        string = str(i) + "W"
        move = moves[string]
        promotion = False

        #check piece
        if ord(move[0]) >= 97 and ord(move[0]) <= 104:
            piece = "P"
            if "=" in move:
                promotion = True
        else:
            piece = move[0].upper()


        if move[-1] == "+":
            move = move.replace("+", "")
        elif move[-1] == "#":
            move = move.replace("#","")

        #square col, row, not zero indexed
        movedTo = move[-1] + str(ord(move[-2])-96)
        # print(movedTo)

        prevPosition = positions[(i-1)*2]
        possiblePieces = []

        if piece == "P":
            #remove promotion Notation
            if promotion == True:
                promoteTo = str(move[-1]).upper()
                move = move[:-2]
                movedTo = move[-1] + str(ord(move[-2])-96)
            # no captures
            if len(move) == 2:
                # initial two move
                if movedTo[0] == "4" and prevPosition[2][int(movedTo[1])-1] == "-":
                    possiblePieces.append("2"+movedTo[1])
                possiblePieces.append(str(int(movedTo[0])-1)+movedTo[1])
            else:
                #captures
                possiblePieces.append(str(int(movedTo[0])-1)+str(int(ord(move[0]))-96))
        else:
            findPieces(movedTo, piece, possiblePieces, colour, prevPosition)

        if move == "O-O":
            newPosition = copy.deepcopy(prevPosition)
            newPosition[0][4] = "-"
            newPosition[0][7] = "-"
            newPosition[0][5] = "R"
            newPosition[0][6] = "K"
        elif move == "O-O-O":
            newPosition = copy.deepcopy(prevPosition)
            newPosition[0][4] = "-"
            newPosition[0][0] = "-"
            newPosition[0][3] = "R"
            newPosition[0][2] = "K"
        else:
            validPieces = validatePieces(prevPosition, possiblePieces, piece, move)
            if validPieces == "ERROR": #bug from non-ambiguous char from illegal move, see README
                return "ERROR"
            newPosition = movePiece(prevPosition, validPieces, movedTo, piece)

        if promotion == True:
            newPosition[7][int(movedTo[1])-1] = promoteTo
        #checks en passant
        if piece == "P":
            if "x" in move:
                #only can be en passant if pawn captures to a square that was previously empty
                if prevPosition[int(movedTo[0])-1][int(movedTo[1])-1] == "-":
                    # print("en passant")
                    #row behind (for white, forward = 1->8), but same column
                    newPosition[int(movedTo[0])-2][int(movedTo[1])-1] = "-"

        positions.append(newPosition)
        uneditedPositions.append(newPosition.copy())

        # print(move, movedTo, possiblePieces, validPieces, piece, newPosition, prevPosition, positions)
        # print(i, colour, positions[-1])
        # print(i, colour, "\n", positions)

        #BLACK ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        colour = "black"
        string = str(i) + "B"
        try:
            move = moves[string]
        except KeyError:
            break
        promotion = False

        #check piece
        if ord(move[0]) >= 97 and ord(move[0]) <= 104:
            piece = "p"
            if "=" in move:
                promotion = True
        else:
            piece = move[0].lower()


        if move[-1] == "+":
            move = move.replace("+", "")
        elif move[-1] == "#":
            move = move.replace("#","")

        #square col, row
        movedTo = move[-1] + str(ord(move[-2])-96)
        # print(movedTo)

        prevPosition = positions[(i-1)*2+1]
        possiblePieces = []

        if piece == "p":
            #remove promotion Notation
            if promotion == True:
                promoteTo = str(move[-1]).lower()
                move = move[:-2]
                movedTo = move[-1] + str(ord(move[-2])-96)
                # print("\n", move, promoteTo)
            # no captures
            if len(move) == 2:
                # initial two move
                if movedTo[0] == "5" and prevPosition[5][int(movedTo[1])-1] == "-":
                    possiblePieces.append("7"+movedTo[1])
                possiblePieces.append(str(int(movedTo[0])+1)+movedTo[1])
            else:
                #captures
                possiblePieces.append(str(int(movedTo[0])+1)+str(int(ord(move[0]))-96))
        else:
            findPieces(movedTo, piece, possiblePieces, colour, prevPosition)

        if move == "O-O":
            newPosition = copy.deepcopy(prevPosition)
            newPosition[7][4] = "-"
            newPosition[7][7] = "-"
            newPosition[7][5] = "r"
            newPosition[7][6] = "k"
        elif move == "O-O-O":
            newPosition = copy.deepcopy(prevPosition)
            newPosition[7][4] = "-"
            newPosition[7][0] = "-"
            newPosition[7][3] = "r"
            newPosition[7][2] = "k"
        else:
            validPieces = validatePieces(prevPosition, possiblePieces, piece, move)
            if validPieces == "ERROR": #bug from non-ambiguous char from illegal move, see README
                return "ERROR"
            newPosition = movePiece(prevPosition, validPieces, movedTo, piece)

        if promotion == True:
            newPosition[0][int(movedTo[1])-1] = promoteTo
        #checks en passant
        if piece == "p":
            if "x" in move:
                #only can be en passant in pawn captures to a square that was previously empty
                if prevPosition[int(movedTo[0])-1][int(movedTo[1])-1] == "-":
                    print("en passant")
                    #row behind (for black, forwards = 8 -> 1), but same column
                    newPosition[int(movedTo[0])][int(movedTo[1])-1] = "-"


        positions.append(newPosition)
        uneditedPositions.append(newPosition.copy())

        # print(move, movedTo, possiblePieces, validPieces, piece, newPosition, prevPosition, positions)
        # print(i, colour, positions[-1])
        # print(i, colour, "\n", positions)

    # print(positions[-1], moves["end"])
    return uneditedPositions


def findPieces(movedTo, piece, possiblePieces, colour, prevPosition):
    #used for checking if it is itself in prevposition that couldbe blocking, takes colour into account
    colourPiece = piece
    #so it can compare, as all pieces move same (except pawn which is done before function called)
    if colour == "black":
        piece = piece.upper()
    if piece == "K":
        height = int(movedTo[0])
        width = int(movedTo[1])
        #Possible origin points, and excludes a move to the same square/outside of the boad
        for x in range(-1, 2):
            for y in range(-1,2):
                toAdd = str(height+x)+str(width+y)
                if toAdd != movedTo:
                    if "0" not in toAdd and "9" not in toAdd:
                        possiblePieces.append(toAdd)

    elif piece == "N":

        k_x = int(movedTo[1])
        k_y = int(movedTo[0])

        ##THIS IS CODE I WROTE PREVIOUSLY FOR A SCHOOL ASSIGNMENT, altered to fit my design (only this elif block for knight)
        move_X = [k_x + 1, k_x + 2, k_x - 1, k_x - 2]
        move_Y = [k_y + 1, k_y + 2, k_y - 1, k_y - 2]

        #uses arrays to check is possible moves are within the chess board - legal, and if so will add it to a list of possible moves, and works as it must move 1 then 2 squares in different directions
        for j in range(4):
            if move_X[j] >=1 and move_X[j] <= 8:
                if move_Y[(j+1)%4] >= 1 and move_Y[(j+1)%4] <= 8:
                    possMove = str(move_Y[(j+1)%4]) + str(move_X[j])
                    possiblePieces.append(possMove)

                if move_Y[(j+3)%4] >= 1 and move_Y[(j+3)%4] <= 8:
                    possMove = str(move_Y[(j+3)%4]) + str(move_X[j])
                    possiblePieces.append(possMove)

    elif piece == "R":
        r_x = int(movedTo[1])
        r_y = int(movedTo[0])

        for j in range(1,8):
            toAdd = str(r_y) + str(r_x+j)
            #FOR ALL BISHOP< ROOK< QUEEN, as they move linearly,
            #stops if reach outside board
            #stops if a piece is blocking
            #BUT< previous position includes the piece that just moved, so it may appear like it is blocking itself, so if it is itself, add that space and then stop
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[r_y-1][r_x+j-1] != "-" and prevPosition[r_y-1][r_x+j-1] != colourPiece:
                break
            if prevPosition[r_y-1][r_x+j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(r_y) + str(r_x-j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[r_y-1][r_x-j-1] != "-" and prevPosition[r_y-1][r_x-j-1] != colourPiece:
                break
            if prevPosition[r_y-1][r_x-j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(r_y+j) + str(r_x)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[r_y+j-1][r_x-1] != "-" and prevPosition[r_y+j-1][r_x-1] != colourPiece:
                break
            if prevPosition[r_y+j-1][r_x-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(r_y-j) + str(r_x)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[r_y-j-1][r_x-1] != "-" and prevPosition[r_y-j-1][r_x-1] != colourPiece:
                break
            if prevPosition[r_y-j-1][r_x-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)

    elif piece == "B":
        b_x = int(movedTo[1])
        b_y = int(movedTo[0])

        for j in range(1,8):
            toAdd = str(b_y+j) + str(b_x+j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[b_y+j-1][b_x+j-1] != "-" and prevPosition[b_y+j-1][b_x+j-1] != colourPiece:
                break
            if prevPosition[b_y+j-1][b_x+j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(b_y+j) + str(b_x-j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[b_y+j-1][b_x-j-1] != "-" and prevPosition[b_y+j-1][b_x-j-1] != colourPiece:
                break
            if prevPosition[b_y+j-1][b_x-j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(b_y-j) + str(b_x+j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[b_y-j-1][b_x+j-1] != "-" and prevPosition[b_y-j-1][b_x+j-1] != colourPiece:
                break
            if prevPosition[b_y-j-1][b_x+j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(b_y-j) + str(b_x-j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[b_y-j-1][b_x-j-1] != "-" and prevPosition[b_y-j-1][b_x-j-1] != colourPiece:
                break
            if prevPosition[b_y-j-1][b_x-j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)

    elif piece == "Q":
        q_x = int(movedTo[1])
        q_y = int(movedTo[0])

        for j in range(1,8):
            toAdd = str(q_y+j) + str(q_x+j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y+j-1][q_x+j-1] != "-" and prevPosition[q_y+j-1][q_x+j-1] != colourPiece:
                break
            if prevPosition[q_y+j-1][q_x+j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y+j) + str(q_x-j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y+j-1][q_x-j-1] != "-" and prevPosition[q_y+j-1][q_x-j-1] != colourPiece:
                break
            if prevPosition[q_y+j-1][q_x-j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y-j) + str(q_x+j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y-j-1][q_x+j-1] != "-" and prevPosition[q_y-j-1][q_x+j-1] != colourPiece:
                break
            if prevPosition[q_y-j-1][q_x+j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y-j) + str(q_x-j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y-j-1][q_x-j-1] != "-" and prevPosition[q_y-j-1][q_x-j-1] != colourPiece:
                break
            if prevPosition[q_y-j-1][q_x-j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y) + str(q_x+j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y-1][q_x+j-1] != "-" and prevPosition[q_y-1][q_x+j-1] != colourPiece:
                break
            if prevPosition[q_y-1][q_x+j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y) + str(q_x-j)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y-1][q_x-j-1] != "-" and prevPosition[q_y-1][q_x-j-1] != colourPiece:
                break
            if prevPosition[q_y-1][q_x-j-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y+j) + str(q_x)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y+j-1][q_x-1] != "-" and prevPosition[q_y+j-1][q_x-1] != colourPiece:
                break
            if prevPosition[q_y+j-1][q_x-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)
        for j in range(1,8):
            toAdd = str(q_y-j) + str(q_x)
            if "0" in toAdd or "9" in toAdd:
                break
            if prevPosition[q_y-j-1][q_x-1] != "-" and prevPosition[q_y-j-1][q_x-1] != colourPiece:
                break
            if prevPosition[q_y-j-1][q_x-1] == colourPiece:
                possiblePieces.append(toAdd)
                break
            possiblePieces.append(toAdd)

def validatePieces(prevPosition, possiblePieces, piece, move):

    # print("\n\n\n", prevPosition, possiblePieces, piece)
    validPieces = []
    for square in possiblePieces:
        #adjusted for zero index, rank = horizontal line
        file = int(square[1]) - 1
        rank = int(square[0]) - 1
        # print(prevPosition[file][rank])

        if prevPosition[rank][file] == piece:
            validPieces.append(str(rank+1) + str(file+1))

    if len(validPieces) == 0:
        print("HELP") #SHOULDNT HAPPEN, FROM DEBUGGING
    elif len(validPieces) != 1:
        # print(move)
        # regularly move should be 3 chars -> previously removed # or +, promotion notation for pawn, castling does not go through this function, and now captures are removed
        #however, duplicate pieces being able to move to the position (so validPieces has more than one item), have more chars, between Piece, 1st char, and square moved to (2 last chars)
        #thus we can isolate
        move = move.replace("x", "")
        move = move[:-2]
        move = move[1:]
        # print(move, validPieces)

        if len(move) == 2:
            validPieces.insert(0, move[1]+str(ord(move[0])-96))
        else:
            if len(move) == 0: #bug from non-ambiguity from illegal piece, see READ ME
                return "ERROR"

            if ord(move[0]) < 57 and ord(move[0]) > 48:
                for i in validPieces:
                    if move[0] == i[0]:
                        correctPiece = i
            else:
                checkfor = ord(move[0])-96
                # print(checkfor)
                for i in validPieces:
                    # print(i, i[1])
                    if i[1] == str(checkfor):
                        correctPiece = i

            validPieces.insert(0, correctPiece)
    return validPieces[0]

def movePiece(prevPosition, validPieces, movedTo, piece):
    #adjusted for zero index, rank = horizontal line
    oldFile = int(validPieces[1]) - 1
    oldRank = int(validPieces[0]) - 1
    newFile = int(movedTo[1]) - 1
    newRank = int(movedTo[0]) - 1

    newPosition = copy.deepcopy(prevPosition)
    newPosition[oldRank][oldFile] = "-"
    newPosition[newRank][newFile] = piece

    return newPosition


#formats moves in white:black move dict so easy to display in html webpage
def htmlMoves(moves):
    htmlMoves = {}
    values = list(moves.values())
    for i in range(0, len(values), 2):
        try:
            htmlMoves[str(values[i])] = str(values[i+1])
        except IndexError:
            htmlMoves[str(values[i])] = ""

    return htmlMoves

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

