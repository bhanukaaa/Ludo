# something somewhere is fucking up std path token counter
# if going back to prev version, token going to home directly by rolling 6 is messed up
import random
import time

# color codes for terminal output
RED = '\033[91m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
RESET = '\033[0m'

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


def blockName(pID, blockCell):
    # + Returns +
    # symbolic name of a block
    name = ";"
    for token in tokens[pID]:
        if token.cellNum == blockCell:
            name += token.tokenName
            name += ";"
    return name


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


def blockDirection(cell, pID):
    # + Returns +
    # -1 if greatest distance to home in a block is in anticlockwise
    # 1 if greatest distance to home in a block is in clockwise
    return 0


def capture(cell, capturerID, capturingName, capturedID):
    # no returns
    # updates tokens captured
    # DOES NOT change stdPath array

    capturerName = playerInfo[capturerID][0]
    capturedName = playerInfo[capturedID][0]

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

            print(f"\t{capturerName} piece {capturingName} lands on square {cell}, captures {capturedName} piece {capturedToken.tokenName}, and returns it to Base")
            print(f"\t{playerInfo[capturedID][0]} Player now has {playerInfo[capturedID][4]}/4 Pieces on the Board, and {playerInfo[capturedID][3]}/4 Pieces in the Base", end="")
            if playerInfo[capturedID][5]:
                # has pieces in home
                print(f", and {playerInfo[capturedID][5]} Pieces in Home")
            print()
            break


def captureBlock(cell, capturerID, capturingName, capturedID):
    # no returns
    # updates tokens captured
    # DOES NOT change stdPath array

    capturerName = playerInfo[capturerID][0]
    capturedName = playerInfo[capturedID][0]
    print(f"\t{capturerName} block {capturingName} lands on square {cell}, captures {capturedName} block {blockName(capturedID, cell)} and returns it to Base")

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
            print(f"{pName} moves piece {tName} from the Base to the Starting Point (Cell {dest})")

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
            print(f"{pName} moves piece {tName} from the Base to the Starting Point (Cell {dest})")
        print("\tMerging with", blockName(pID, dest), end="")

        # Note### might have to update block direction
        # updating new stdPath and token data
        stdPath[dest][1] += 1
        if not -1 <= stdPath[dest][1] <= 4:
            print("\n\n\n\n\n\n\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\n\n\n\n\n\n")
            print(stdPath)
            time.sleep(5)
        tokens[pID][tID].cellNum = dest

        print(" to form block", blockName(pID, dest))
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
                print(f"{pName} moves piece {tName} from the Base to the Starting Point (Cell {dest})")

            # capture opposing token
            capture(dest, pID, tName, stdPath[dest][0])

            # update new stdPath and token data
            stdPath[dest] = [pID, 1, direct]
            tokens[pID][tID].captured += 1
            tokens[pID][tID].cellNum = dest
            return 2

        else:
            # can't capture
            blockingID = stdPath[dest][0]
            print(f"{pName} piece {tName} is blocked from moving from {src} to {dest}, by {playerInfo[blockingID][0]} block {blockName(blockingID, dest)}")

            if src != -1:
                # move token back to previous location in stdPath
                if stdPath[src][0] == -1:
                    # re-occupy previous cell
                    stdPath[src] = [pID, 1, direct]
                else:
                    # add back to block
                    stdPath[src][1] += 1
                    if not -1 <= stdPath[src][1] <= 4:
                        print("\n\n\n\n\n\n\BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\n\n\n\n\n\n\n") 
                        print(stdPath)
                        time.sleep(5)
            return 3


def moveBlock(src, dest, pID, direct, size):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming larger block
    # 2 - moved successfully to cell occupied by opposing block of same size, capturing opponent
    # 3 - failed to move to cell due to opposing block
    
    stdPath[src] = [-1, -1, 0]

    # data for std out messages
    dist = distanceTo(src, dest, direct)
    directionStr = "clockwise" if direct == 1 else "anti-clockwise"

    # moving player / token data
    pName = playerInfo[pID][0]
    bName = blockName(pID, src)

    if stdPath[dest][0] == -1:
        # moving to free cell
        print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")

        stdPath[dest] = [pID, size, direct]
        for pToken in tokens[pID]:
            if pToken.cellNum == src:
                pToken.cellNum == dest
        return 0

    elif stdPath[dest][0] == pID:
        # occupied by same color

        print(f"{pName} moves piece {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        print(f"\tMerging with", blockName(pID, dest), end="")
        
        ###Note### might have to update block direction
        stdPath[dest][1] += size
        if not -1 <= stdPath[dest][1] <= 4:
            print("\n\n\n\n\n\n\CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\n\n\n\n\n\n\n")
            print(stdPath)
            time.sleep(5)
        for pToken in tokens[pID]:
            if pToken.cellNum == src:
                pToken.cellNum == dest

        print(" to form block ", blockName(pID, dest))
        return 1
    
    else:
        # occupied by opposing color
        if stdPath[dest][1] == size:
            # can capture
            print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")

            # capture opposing token
            captureBlock(dest, pID, bName, stdPath[dest][0])

            # update new stdPath and token data
            stdPath[dest] = [pID, size, direct]
            for pToken in tokens[pID]:
                if pToken.cellNum == src:
                    pToken.cellNum = dest
            return 2
        else:
            # can't capture
            blockingID = stdPath[dest][0]
            print(f"{pName} block {bName} is blocked from moving from {src} to {dest}, by {playerInfo[blockingID][0]} block {blockName(blockingID, dest)}")

            # move block back to initial location
            stdPath[src] = [pID, size, direct]
            return 3


def tokenChoice(pID, tID, diceValue):
    # + Returns +
    # -1 if move is not possible
    # 0 if turn played out normally
    # 1 if player awarded bonus roll
    # 2 if a piece reached home

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

    # retrieve token data
    currPos = tokens[pID][tID].cellNum
    tName = tokens[pID][tID].tokenName
    tDir = tokens[pID][tID].direction
    tCapt = tokens[pID][tID].captured
    tAppP = tokens[pID][tID].approachPass
    tBhaMul = tokens[pID][tID].bhavanaMultiplier

    if currPos == -1:
        # token is in base
        m = moveToken(-1, pStart, pID, tID, 1)
        if m == 3: return -1

        print("Flipping Coin to Pick Direction")
        coinVal = flipCoin()
        if coinVal:
            print(f"\tHeads, {tName} will move Clockwise")
        else:
            print(f"\tTails, {tName} will move Anti-Clockwise")
            tokens[pID][tID].direction = -1

        # update inBase / onBoard counters
        playerInfo[pID][3] -= 1
        playerInfo[pID][4] += 1

        print(f"{pName} Player now has {playerInfo[pID][4]}/4 Pieces on the Board, and {playerInfo[pID][3]}/4 Pieces in the Base", end="")
        if playerInfo[pID][5]:
            # if any tokens in Home
            print(f", and {playerInfo[pID][5]} Pieces in Home")
        print()

        if m == 2: return 1
        return 0

    # token is in stdPath
    if 0 <= currPos < 52:
        # find next position
        nextPos = cellAtMove(currPos, diceValue, tDir)

        # check if path to next position is clear
        allowedPos = checkPath(currPos, diceValue, pID, tDir)
        if allowedPos == -1:
            # not allowed to move due to block
            blocker = stdPath[nextPos][0]   
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker][0]} block {blockName(blocker, nextPos)}")
            return -1
        
        if allowedPos == currPos:
            # block in immediate cell
            blockLocation = cellAtMove(currPos, 1, tDir)
            blocker = stdPath[blockLocation][0]
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker][0]} block {blockName(blocker, blockLocation)}")
            return -1

        if allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            blockLocation = cellAtMove(allowedPos, 1, tDir)
            blocker = stdPath[blockLocation][0]
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker][0]} block {blockName(blocker, blockLocation)} at square {blockLocation}")
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
                    nextPos += diceValue - distanceTo(currPos, pApproach, tDir) - 1

                    print(f"{pName} piece {tName} is moving to Home Straight")
                    print(f"\t{tName} is {pHome - nextPos} squares away from Home")

                    # update flags
                    tokens[pID][tID].cellNum = nextPos
                    stdPath[currPos][1] -= 1
                    if stdPath[currPos][1] == 0:
                        stdPath[currPos] = [-1, -1, 0]

                    if nextPos == pHome:
                        tokens[pID][tID].cellNum = pHome

                        # update onBoard / inHome counters
                        playerInfo[pID][4] -= 1
                        playerInfo[pID][5] += 1

                        print(f"{pName} piece {tName} has reached Home")
                        print(f"{pName} Player now has {playerInfo[pID][4]}/4 Pieces on the Board, and {playerInfo[pID][3]}/4 Pieces in the Base", end="")
                        print(f", and {playerInfo[pID][5]}/4 Pieces in Home")
                        return 2

                    if not -1 <= stdPath[currPos][1] <= 4:
                        print("\n\n\n\n\n\n\DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD\n\n\n\n\n\n\n")
                        print(stdPath)
                        time.sleep(5)
                    return 0

                else:
                    # aint captured nun
                    print(f"{pName} piece {tName} hasn't captured any tokens, Cannot enter Home-Straight")

            m = moveToken(currPos, nextPos, pID, tID, tDir)
            if m == 3: return -1

            # approachPass counter for anticlockwise tokens
            tokens[pID][tID].approachPass += 1
            if m == 2: return 1

        else:
            # regular stdPath move without passing approach
            m = moveToken(currPos, nextPos, pID, tID, tDir)
            if m == 3: return -1
            if m == 2: return 1
        return 0

    # token is in home straight
    if pHomeStrt <= currPos <= pHome:
        spacesLeft = pHome - currPos

        if diceValue < spacesLeft:
            # moving up home straight
            nextPos = currPos + diceValue
            tokens[pID][tID].cellNum = nextPos

            print(f"{pName} piece {tName} is moving up the Home Straight")
            print(f"\t{tName} is {pHome - nextPos} squares away from Home")
            return 0

        elif diceValue == spacesLeft or spacesLeft == 0:
            # going home
            tokens[pID][tID].cellNum = pHome

            # update onBoard / inHome counters
            playerInfo[pID][4] -= 1
            playerInfo[pID][5] += 1

            print(f"{pName} piece {tName} has reached Home")
            print(f"{pName} Player now has {playerInfo[pID][4]}/4 Pieces on the Board, and {playerInfo[pID][3]}/4 Pieces in the Base", end="")
            print(f", and {playerInfo[pID][5]}/4 Pieces in Home")
            return 2

        else:
            # overshot home
            print(f"{pName} piece {tName} over-shoots home; Rolled {diceValue} while {spacesLeft} from Home")
            return -1


def blockChoice(pID, bID, diceValue):
    # + Returns +
    # -1 if move is not possible
    # 0 if turn played out normally
    # 1 if player awarded bonus roll
    # 2 if a piece reached home

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

    currPos = tokens[pID][bID - 5].cellNum
    members = blockMembers(pID, currPos)
    bDir = stdPath[currPos][2]
    bCount = stdPath[currPos][1]
    bName = blockName(pID, currPos)

    if 0 <= currPos <= 52:
        # block is in stdPath

        nextPos = cellAtMove(currPos, diceValue // bCount, bDir)
        # check if path to next position is clear
        allowedPos = checkPath(currPos, diceValue // bCount, pID, bDir)
        if allowedPos == -1:
            # landing on a block
            if stdPath[nextPos][1] != bCount:
                # not same size, so cant capture
                blocker = stdPath[nextPos][0]
                print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker][0]} block {blockName(blocker, nextPos)}")
                return -1
            
        elif allowedPos == currPos:
            # block in immediate cell
            blockLocation = cellAtMove(currPos, 1, bDir)
            blocker = stdPath[blockLocation][0]
            print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker][0][0]} block {blockName(blocker, blockLocation)}")
            return -1

        elif allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            blockLocation = cellAtMove(allowedPos, 1, bDir)
            blocker = stdPath[blockLocation][0]
            print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker][0]} block {blockName(blocker, blockLocation)} at square {blockLocation}")
            print(f"\tMoving block {bName} to square {allowedPos} which is the cell before the block")
        nextPos = allowedPos

        # check if passing approach
        distToApproach = distanceTo(currPos, pApproach, bDir)
        distToNextPos = distanceTo(currPos, nextPos, bDir)

        # if distToApproach < distToNextPos:
        #     # block is passing approach cell
        #     pass
        # else:
        # regular stdPath move without passing approach cell
        m = moveBlock(currPos, nextPos, pID, bDir, bCount)
        if m == 3: return -1
        if m == 2: return 1
        return 0


def playTurn(pID, roundNum):
    # + Returns +
    # no options
    # token selected
    # block selected

    pName = playerInfo[pID][0]
    diceValue = rollDice()
    print(f"\n{pName}'s Turn (Round {roundNum})")
    print(f"{pName} rolled {diceValue}")

    # find possible moves for player with dice roll
    options = [] # 0-3 tokens, 5-8 block of that token
    for index, token in enumerate(tokens[pID]):
        if token.cellNum == -1:
            # token in base
            if diceValue == 6:
                # only an option if 6 rolled
                options.append(index)

        elif 0 <= token.cellNum < 52:
            # token in stdPath
            options.append(index)

            if stdPath[token.cellNum][1] > 1:
                # token is part of a block
                options.append(index + 5)

        elif token.cellNum != 70 + 10*pID:
            # token in home straight
            options.append(index)


    if not options:
        # no options possible
        print(f"{pName} has no possible moves, Ignoring the throw and moving on to the next player")
        return 0

    # TEMPORARY RANDOM AI
    playerChoice = tempPlayerAI(options)

    if playerChoice < 4:
        # picked a token
        choiceRes = tokenChoice(pID, playerChoice, diceValue)
    else:
        # picked a block
        choiceRes = blockChoice(pID, playerChoice, diceValue)

    if choiceRes == -1:
        options.remove(playerChoice)
        while options and choiceRes == -1:
            print(f"{pName} is picking a different move")
            playerChoice = tempPlayerAI(options)

            if playerChoice < 4:
                # picked a token
                choiceRes = tokenChoice(pID, playerChoice, diceValue)
            else:
                # picked a block
                choiceRes = blockChoice(pID, playerChoice, diceValue)
            options.remove(playerChoice)

        if choiceRes == -1:
            print(f"{pName} has no possible moves, Ignoring the throw and moving to the next player")
            choiceRes = 0

    return choiceRes


def tempPlayerAI(options):
    return random.choice(options)

##################################################################################################

# data about players
playerInfo = [
    # name / color, starting cell, approach cell, inBase count, onBoard count, inHome count
    [GREEN + "Green" + RESET, 41, 39, 4, 0, 0],
    [YELLOW + "Yellow" + RESET, 2, 0, 4, 0, 0],
    [BLUE + "Blue" + RESET, 15, 13, 4, 0, 0],
    [RED + "Red" + RESET, 28, 26, 4, 0, 0],
]

# tokens array
# array index == playerID
# subarray index == tokenID
tokens = [
    [
        Piece(-1, GREEN + "G1" + RESET, 1, 0, 0, 0),
        Piece(-1, GREEN + "G2" + RESET, 1, 0, 0, 0),
        Piece(-1, GREEN + "G3" + RESET, 1, 0, 0, 0),
        Piece(-1, GREEN + "G4" + RESET, 1, 0, 0, 0)
    ],
    [
        Piece(-1, YELLOW + "Y1" + RESET, 1, 0, 0, 0),
        Piece(-1, YELLOW + "Y2" + RESET, 1, 0, 0, 0),
        Piece(-1, YELLOW + "Y3" + RESET, 1, 0, 0, 0),
        Piece(-1, YELLOW + "Y4" + RESET, 1, 0, 0, 0)
    ],
    [
        Piece(-1, BLUE + "B1" + RESET, 1, 0, 0, 0),
        Piece(-1, BLUE + "B2" + RESET, 1, 0, 0, 0),
        Piece(-1, BLUE + "B3" + RESET, 1, 0, 0, 0),
        Piece(-1, BLUE + "B4" + RESET, 1, 0, 0, 0)
    ],
    [
        Piece(-1, RED + "R1" + RESET, 1, 0, 0, 0),
        Piece(-1, RED + "R2" + RESET, 1, 0, 0, 0),
        Piece(-1, RED + "R3" + RESET, 1, 0, 0, 0),
        Piece(-1, RED + "R4" + RESET, 1, 0, 0, 0)
    ]
]

# array to represent stdPath
# player ID, number of tokens in cell, direction of token / block
stdPath = [[-1, -1, 0]] * 52

###################################################################################################

def endOfRound(roundNum):
    print("\n==========================")
    print(f"End of Round {roundNum}")
    print("==========================")

    for p in range(4):
        # time.sleep(0.5)
        print(f"{playerInfo[p][0]} player now has {playerInfo[p][4]}/4 Pieces on the Board, {playerInfo[p][3]}/4 Pieces in the Base\nand {playerInfo[p][5]}/4 Pieces in their Home")
        print("==========================")
        print(f"Location of {playerInfo[p][0]} Pieces")
        print("==========================")
        for t in tokens[p]:
            print(f"Piece {t.tokenName} -> ", end="")
            if t.cellNum == -1:
                print("Base")
            elif t.cellNum == 70 + 10*p:
                print("Home")
            elif t.cellNum < 52:
                print(f"Cell {t.cellNum}")
            else:
                print(f"{playerInfo[p][0]}|HomePath|{t.cellNum - (65 + 10*p)}")
        print("==========================\n")


def gameLoop(firstPlayer):
    roundNum = 1
    currPlayer = firstPlayer
    while True:
        print("\n==========================")
        print(f"Start of Round {roundNum}")
        print("==========================")
        for _ in range(4):
            # time.sleep(0.5)
            # Note### NEED LOGIC FOR REPLAYING TURNS AND SKIPPED TURNS
            turnRes = playTurn(currPlayer, roundNum)
            if turnRes == 2:
                # player reached home

                if playerInfo[currPlayer][5] == 4:
                    # win condition
                    endOfRound(roundNum)
                    print("#####################################")
                    print(f"{playerInfo[currPlayer][0]} Player has all 4 Pieces in Home")
                    print(f"{playerInfo[currPlayer][0]} Player Wins!!!")
                    print("#####################################")
                    for i in range(52):
                        print(stdPath[i])
                    return

            # move on to next player, wrap around if needed
            currPlayer += 1
            currPlayer %= 4

        roundNum += 1
        # time.sleep(1)
        print(stdPath)
        endOfRound(roundNum)
        # time.sleep(1)


def main():
    for i in range(4):
        # iterate over all players and display tokens
        print(f"\nThe {playerInfo[i][0]} player has 4 Pieces named", end=" ")
        for pToken in tokens[i]:
            print(pToken.tokenName, end=" ")
    print("\n")
    time.sleep(0.5)

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

    time.sleep(0.5)
    print(f"\n{playerInfo[firstPlayer][0]} has the highest roll and will begin the game")
    print(f"The order of a single round will be {playerInfo[firstPlayer][0]}, {playerInfo[(firstPlayer+1) % 4][0]}, {playerInfo[(firstPlayer+2) % 4][0]}, {playerInfo[(firstPlayer+3) % 4][0]}")
    time.sleep(1)
    # start actual game loop
    gameLoop(firstPlayer)


main()
