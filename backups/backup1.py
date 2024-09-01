# basic ludo works normally
# clockwise / anticlockwise traversal works
# blocks aren't implemented
# rare edge case;
#               if multiple blocks meet going in opposite directions
#               all players will have no possible moves and loops infinitely

import random
import time


class Piece:
    def __init__(self, cellNum, tokenName, direction, captured, approachPass, bhavanaMultiplier):
        self.cellNum = cellNum
        self.tokenName = tokenName
        self.direction = direction
        self.captured = captured
        self.approachPass = approachPass
        self.bhavanaMultiplier = bhavanaMultiplier


def rollDice():
    return random.randint(1, 6)


def flipCoin():
    return random.randint(0, 1)


def blockMembers(pID, blockCell):
    # + Returns +
    # members of the block in a cell

    members = []
    for index, token in enumerate(tokens[pID]):
        if token.cellNum == blockCell:
            # if token in checking cell
            members.append(index)
    return members


def distanceTo(src, dest, direct):
    # + Returns +
    # absolute distance in spaces from source cell

    dist = 0
    if src <= dest:
        # src is numerically lower/equal to dest
        # could also be wrap around when going anticlockwise
        # eg; src 37, dest 41, clockwise = 4
        # eg; src 2, dest 50, anticlockwise = 48 (will adjust before return)
        dist = dest - src
    else:
        # src is greater than dest
        # could also be wrap around when going clockwise
        # eg; src 41, dest 37, anticlockwise = 52 - 41 + 37 = 48 (will adjust before return)
        # eg; src 50, dest 2, clockwise = 52 - 50 + 2 = 4
        dist = (52 - src) + (dest)

    if direct == 1:
        # clockwise distance
        return dist
    else:
        # anticlockwise distance, adjusted
        # i.e; dist from 50 -> 2 in clockwise, is 4 spaces
        #    ; dist from 2 -> 50 in clockwise, is 48 spaces
        #    ; dist from 2 -> 50 in anticlockwise, is 4 spaces
        #    ; therefore, dist from a -> b (anti-cw) == b -> a (clockwise)
        return 52 - dist


def cellAtMove(src, spaces, direct):
    # + Returns +
    # cell index after stdPath traversal of spaces

    if direct == 1:
        # clockwise, normalize to fit array index range
        src += spaces
        src %= 52
    else:
        # anti-clockwise
        src -= spaces
        if src < 0:
            # normalize to wrap around back from 52
            src = 52 + src
    return src


def checkPath(src, moves, pID, direct):
    # + Return +
    # furthest cell a token can go to in a path specified
    # checks for blocks
    # will return cell preceding block, IF dice roll takes token PAST the block
    # will return source cell, if token is to land directly on opposing block
    # will return cellAtMove cell if no opposing block encountered

    furthest = src
    for move in range(1, moves + 1):
        # iterate from 1 space to 'moves' spaces ahead
        # cell index
        movedCell = cellAtMove(src, move, direct)
        if stdPath[movedCell][0] == -1 or stdPath[movedCell][0] == pID:
            # if cell is free or cell occupied by same color
            furthest = movedCell

        elif stdPath[movedCell][1] > 1:
            # opposing block in checking cell

            if move == moves:
                # landing on block, can't move
                return -1
            else:
                # overshooting block, move to adjacent
                return furthest

        else:
            # opposing piece, capturable
            furthest = movedCell

    return furthest


def capture(cell, capturerID, capturingTokenID, capturedID):
    # no returns
    # updates tokens captured
    # DOES NOT change stdPath array

    capturerName = playerInfo[capturerID][0]
    capturedName = playerInfo[capturedID][0]
    capturerToken = tokens[capturerID][capturingTokenID].tokenName

    for capturedToken in tokens[capturedID]:
        if capturedToken.cellNum == cell:
            # token in capturing cell
            # reset all attributes
            capturedToken.cellNum = -1
            capturedToken.direction = 1
            capturedToken.captured = 0
            capturedToken.approachPass = 0
            capturedToken.bhavanaMultiplier = 0

            # update inBase / onBoard counters for captured player
            playerInfo[capturedID][3] += 1
            playerInfo[capturedID][4] -= 1

            print(f"\t{capturerName} piece {capturerToken} lands on square {cell}, captures {capturedName} piece {capturedToken.tokenName}, and returns it to Base")

    print(f"\t{playerInfo[capturedID][0]} Player now has {playerInfo[capturedID][4]}/4 Pieces on the Board, and {playerInfo[capturedID][3]}/4 Pieces in the Base", end="")
    if playerInfo[capturedID][5]:
        # has pieces in home
        print(f", and {playerInfo[capturedID][5]} Pieces in Home")
    print()


def moveToken(src, dest, pID, tID, direct):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming block
    # 2 - moved successfully to cell occupied by opposing color, capturing opponent
    # 3 - failed to move to cell due to opposing block

    if 0 <= src < 52:
        # prev position was in stdPath
        stdPath[src][1] -= 1
        # Note### might have to update block direction on size change
        if stdPath[src][1] == 0:
            # previous postition is now empty
            stdPath[src] = [-1, -1, 0]

        # data for std out messages
        dist = distanceTo(src, dest, direct)
        directionStr = "clockwise" if direct == 1 else "anti-clockwise"

    # moving player / token data
    pName = playerInfo[pID][0]
    tName = tokens[pID][tID].tokenName

    if stdPath[dest][0] == -1:
        # moving to free cell

        if src != -1:
            # moving from stdPath
            print(f"{pName} moves piece {tName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        else:
            # moving from base
            print(f"{pName} moves piece {tName} from the Base to the Starting Point ({dest})")

        # update new stdPath and token data
        stdPath[dest] = [pID, 1, direct]
        tokens[pID][tID].cellNum = dest
        return 0

    elif stdPath[dest][0] == pID:
        # occupied by same color

        if src != -1:
            # moving from stdPath
            print(f"{pName} moves piece {tName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        else:
            # moving from base
            print(f"{pName} moves piece {tName} from the Base to the Starting Point ({dest})")

        print(f"\tForming Block with; ", end="")
        for blockMember in blockMembers(pID, dest):
            # identify player tokens in same cell
            print(f"{tokens[pID][blockMember].tokenName} ", end="")
        print()

        # Note### might have to update block direction
        # updating new stdPath and token data
        stdPath[dest][1] += 1
        tokens[pID][tID].cellNum = dest
        return 1

    else:
        # occupied by opposing color
        if stdPath[dest][1] == 1:
            # can capture
            if src != -1:
                # moving from stdPath
                print(f"{pName} moves piece {tName} from location {src} to {dest} by {dist} units in {directionStr} direction")
            else:
                # moving from base
                print(f"{pName} moves piece {tName} from the Base to the Starting Point ({dest})")

            # capture opposing token
            capture(dest, pID, tID, stdPath[dest][0])

            # update new stdPath and token data
            stdPath[dest] = [pID, 1, direct]
            tokens[pID][tID].captured += 1
            tokens[pID][tID].cellNum = dest
            return 2

        else:
            # can't capture
            blockingColor = stdPath[dest][0]
            print(f"{pName} piece {tName} is blocked from moving from {src} to {dest}, by {playerInfo[blockingColor][0]} pieces; ", end="")
            for blockMember in blockMembers(blockingColor, dest):
                print(f"{tokens[blockingColor][blockMember].tokenName} ", end="")
            print()

            if src != -1:
                # move token back to previous location in stdPath
                if stdPath[src][0] == -1:
                    # re-occupy previous cell
                    stdPath[src] = [pID, 1, direct]
                else:
                    # add back to block
                    stdPath[src][1] += 1
            return 3


def moveBlock(src, dest, pID, tID, direct, size):
    return 0


def playTurn(pID, roundNum):
    # + Returns +
    # 0 if turn played out normally
    # -1 if move is not possible
    # 1 if a piece reached home
    # -2 if player awarded bonus roll

    # retrieve player data
    pName = playerInfo[pID][0]
    pStart = playerInfo[pID][1]
    pApproach = playerInfo[pID][2]

    # player's home straight
    # home straights and homes are;
    #       green: 65-69, 70
    #       yellow: 75-79, 80
    #       blue: 85-89, 90
    #       red: 95-99, 100
    pHome = 70 + 10*pID
    pHomeStrt = 65 + 10*pID

    diceValue = rollDice()
    print()
    print(f"{pName}'s Turn (Round {roundNum})")
    print(f"{pName} rolled {diceValue}")

    # find possible moves for player with dice roll
    # Note### might change as failure to move will print message and return -1
    options = []
    for index, token in enumerate(tokens[pID]):
        if token.cellNum == -1:
            # token in base
            if diceValue == 6:
                # only an option if 6 rolled
                options.append(index)

        elif 0 <= token.cellNum < 52:
            # token in stdPath
            cellAhead = cellAtMove(token.cellNum, diceValue, token.direction)
            if stdPath[cellAhead][1] > 1 and stdPath[cellAhead][0] != pID:
                # if block in expected cell and not same team, not an option
                continue
            options.append(index)

        else:
            # token in home straight
            if token.cellNum + diceValue <= pHome:
                # only an option if dice roll is less / equal to dist from home
                options.append(index)

    if not options:
        # no options possible
        print(f"{pName} has no possible moves, Skipping Turn")
        return 0

    # TEMPORARY RANDOM AI
    selectTID = tempPlayerAI(options)

    # retrieve token data
    currPos = tokens[pID][selectTID].cellNum
    tName = tokens[pID][selectTID].tokenName
    tDir = tokens[pID][selectTID].direction
    tCapt = tokens[pID][selectTID].captured
    tAppP = tokens[pID][selectTID].approachPass
    tBhaMul = tokens[pID][selectTID].bhavanaMultiplier

    if currPos == -1:
        # token is in base
        m = moveToken(-1, pStart, pID, selectTID, 1)
        if m == 3:
            return -1

        print("Flipping Coin to Pick Direction")
        coinVal = flipCoin()
        if coinVal:
            print(f"\tHeads, {tName} will move Clockwise")
        else:
            print(f"\tTails, {tName} will move Anti-Clockwise")
            tokens[pID][selectTID].direction = -1

        # update inBase / onBoard counters
        playerInfo[pID][3] -= 1
        playerInfo[pID][4] += 1

        print(f"{pName} Player now has {playerInfo[pID][4]}/4 Pieces on the Board, and {playerInfo[pID][3]}/4 Pieces in the Base", end="")
        if playerInfo[pID][5]:
            # if any tokens in Home
            print(f", and {playerInfo[pID][5]} Pieces in Home")
        print()
        return 0

    # token is in stdPath
    if 0 <= currPos < 52:
        # find next position
        nextPos = cellAtMove(currPos, diceValue, tDir)

        # check if path to next position is clear
        allowedPos = checkPath(currPos, diceValue, pID, tDir)
        if allowedPos == -1:
            # not allowed to move due to block
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[stdPath[nextPos][0]][0]} block")
            return -1
        
        if allowedPos == currPos:
            # block in immediate cell
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[stdPath[(currPos + 1) % 52][0]][0]} block")
            return -1

        if allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[stdPath[(allowedPos + 1) % 52][0]][0]} block at square {(allowedPos + 1) % 52}")
            print(f"\tMoving piece {tName} to square {allowedPos} which is the cell before the block")

        # check if passing approach
        nextPos = allowedPos
        distToApproach = distanceTo(currPos, pApproach, tDir)
        distToNextPos = distanceTo(currPos, nextPos, tDir)

        if distToApproach < distToNextPos:
            # if distance to approach is less than stdPath next pos
            # means the roll takes us past approach cell

            if (tDir == 1 or tAppP > 0):
                # travelling clockwise or passed approach when anti

                if tCapt > 0:
                    # captured at least 1 piece
                    nextPos = pHomeStrt
                    # -1 coz going from apprch -> hmstrt
                    nextPos += diceValue - \
                        distanceTo(currPos, pApproach, tDir) - 1

                    print(f"{pName} piece {tName} is moving to Home Straight")
                    print(f"\t{tName} is {pHome - nextPos} squares away from Home")

                    # update flags
                    tokens[pID][selectTID].cellNum = nextPos
                    stdPath[currPos] = [-1, -1, 0]
                    return 0

                else:
                    # aint captured nun
                    print(f"{pName} piece {tName} hasn't captured any tokens, Cannot enter Home-Straight")

            if 3 == moveToken(currPos, nextPos, pID, selectTID, tDir):
                return -1
            # approachPass counter for anticlockwise tokens
            tokens[pID][selectTID].approachPass += 1

        else:
            # regular stdPath move without passing approach
            if 3 == moveToken(currPos, nextPos, pID, selectTID, tDir):
                return -1
        return 0

    # token is in home straight
    # will also catch if going directly to home from approach by rolling 6
    if pHomeStrt <= currPos <= pHome:
        spacesLeft = pHome - currPos

        if diceValue < spacesLeft:
            # moving up home straight
            nextPos = currPos + diceValue
            tokens[pID][selectTID].cellNum = nextPos

            print(f"{pName} piece {tName} is moving up the Home Straight")
            print(f"\t{tName} is {pHome - nextPos} squares away from Home")
            return 0

        elif diceValue == spacesLeft:
            # going home
            tokens[pID][selectTID].cellNum = pHome

            # update onBoard / inHome counters
            playerInfo[pID][4] -= 1
            playerInfo[pID][5] += 1

            print(f"{pName} piece {tName} has reached Home")
            print(f"{pName} Player now has {playerInfo[pID][4]}/4 Pieces on the Board, and {playerInfo[pID][3]}/4 Pieces in the Base", end="")
            print(f", and {playerInfo[pID][5]}/4 Pieces in Home")
            return 1

        else:
            # overshot home
            print(f"{pName} piece {tName} over-shoots home; Rolled {diceValue} while {spacesLeft} from Home")
            return -1


def tempPlayerAI(options):
    return random.choice(options)

##################################################################################################

# data about players
playerInfo = [
    # name / color, starting cell, approach cell, inBase count, onBoard count, inHome count
    ["Green", 41, 39, 4, 0, 0],
    ["Yellow", 2, 0, 4, 0, 0],
    ["Blue", 15, 13, 4, 0, 0],
    ["Red", 28, 26, 4, 0, 0],
]

# tokens array
# array index == playerID
# subarray index == tokenID
tokens = [
    [
        Piece(-1, "G1", 1, 0, 0, 0),
        Piece(-1, "G2", 1, 0, 0, 0),
        Piece(-1, "G3", 1, 0, 0, 0),
        Piece(-1, "G4", 1, 0, 0, 0)
    ],
    [
        Piece(-1, "Y1", 1, 0, 0, 0),
        Piece(-1, "Y2", 1, 0, 0, 0),
        Piece(-1, "Y3", 1, 0, 0, 0),
        Piece(-1, "Y4", 1, 0, 0, 0)
    ],
    [
        Piece(-1, "B1", 1, 0, 0, 0),
        Piece(-1, "B2", 1, 0, 0, 0),
        Piece(-1, "B3", 1, 0, 0, 0),
        Piece(-1, "B4", 1, 0, 0, 0)
    ],
    [
        Piece(-1, "R1", 1, 0, 0, 0),
        Piece(-1, "R2", 1, 0, 0, 0),
        Piece(-1, "R3", 1, 0, 0, 0),
        Piece(-1, "R4", 1, 0, 0, 0)
    ]
]

# array to represent stdPath
# player ID, number of tokens in cell, direction of token / block
stdPath = [[-1, -1, 0]] * 52

###################################################################################################


def gameLoop(firstPlayer):
    roundNum = 0
    currPlayer = firstPlayer
    while True:
        for _ in range(4):
            # time.sleep(0.05)
            # Note### NEED LOGIC FOR REPLAYING TURNS AND SKIPPED TURNS
            turnRes = playTurn(currPlayer, roundNum)
            if turnRes == 1:
                # player reached home

                if playerInfo[currPlayer][5] == 4:
                    # win condition
                    print("#####################################")
                    print(f"{playerInfo[currPlayer][0]} Player has all 4 Pieces in Home")
                    print(f"{playerInfo[currPlayer][0]} Player Wins!!!")
                    print("#####################################")
                    return

            # move on to next player, wrap around if needed
            currPlayer += 1
            currPlayer %= 4
        # round number
        roundNum += 1

        # TEMPORARY
        print(f"\t\t\t\t\t\t\t\tENDOFROUND: IN HOME {playerInfo[0][5]} {playerInfo[1][5]} {playerInfo[2][5]} {playerInfo[3][5]}")
        for i in range(4):
            for j in range(4):
                print(tokens[i][j].tokenName, tokens[i][j].cellNum, tokens[i][j].captured, tokens[i][j].direction, tokens[i][j].approachPass)
            print()


def main():
    for i in range(4):
        # iterate over all players and display tokens
        print(f"\nThe {playerInfo[i][0]} player has 4 Pieces named", end=" ")
        for pToken in tokens[i]:
            print(pToken.tokenName, end=" ")
    print("\n")

    # find out starting player
    maxRoll = 0
    firstPlayer = -1
    print("Deciding who plays first\n")
    for i in range(4):
        # iterate over all players and roll dice
        playerRoll = rollDice()
        print(f"{playerInfo[i][0]} rolls {playerRoll}")
        if playerRoll > maxRoll:
            # update max roll value and leading player
            maxRoll = playerRoll
            firstPlayer = i

    print(f"\n{playerInfo[firstPlayer][0]} has the highest roll and will begin the game")
    print(f"The order of a single round will be {playerInfo[firstPlayer][0]}, {playerInfo[(firstPlayer+1) % 4][0]}, {playerInfo[(firstPlayer+2) % 4][0]}, {playerInfo[(firstPlayer+3) % 4][0]}")

    # start actual game loop
    gameLoop(firstPlayer)


main()
