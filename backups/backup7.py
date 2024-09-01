# ToDo;
# player block breakage penalty
# block to home straight
# block to home straight w antiCW
# green, red player AI touch ups
# block x mystery cell
# apply mysery effect only to pieces teleported and not already in dest

#######################################################################################################

# toggle time.sleep()'s between lines
# True to watch execution line by line
# False to play out rounds asap
sleepTimer = False
# sleepTimer = True

#######################################################################################################

import random
import time

seed = random.randint(1, 9999999999999)
# seed = 3116391339141
# seed = 2454717857304
# seed = 537717719515
# seed = 8908526615351 # UNRESOLVED INFINITE BLOCK MEETUP
random.seed(seed)

# stdOut color codes
BOLD = '\033[1m'
ITALICS = '\033[3m'
GRAY = '\033[90m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
RESET = '\033[0m'

#########################################################################################################

class Piece:
    def __init__(self, cellNum, tokenName, direction, captured, approachPass, bhawanaMultiplier, kotuwaBriefing):
        self.cellNum = cellNum
        self.tokenName = tokenName
        self.direction = direction
        self.captured = captured
        self.approachPass = approachPass
        self.bhawanaMultiplier = bhawanaMultiplier
        self.kotuwaBriefing = kotuwaBriefing

class Player:
    def __init__(self, name, starting, approach, inBase, onBoard, inHome, restricted, prevThree, choiceWeights, prevPiece):
        self.name = name
        self.startingCell = starting
        self.approachCell = approach
        self.inBase = inBase
        self.onBoard = onBoard
        self.inHome = inHome
        self.restricted = restricted
        self.prevThree = prevThree
        self.choiceWeights = choiceWeights
        self.prevPiece = prevPiece

class stdCell:
    def __init__(self, playerID, count, direction):
        self.playerID = playerID
        self.count = count
        self.direction = direction

##########################################################################################################

def rollDice():
    return random.randint(1, 6)


def flipCoin():
    return random.randint(0, 1)


def blockName(pID, blockCell):
    # + Returns +
    # symbolic name of a block
    name = "|"
    for token in tokens[pID]:
        if token.cellNum == blockCell:
            name += token.tokenName
            name += "|"
    return name


def playerSummary(pID):
    # displays summary of player pieces given a player id
    print(f"{players[pID].name} {GRAY}Player now has {RESET}{players[pID].onBoard}{GRAY}/4 Pieces on the Board, and {RESET}{players[pID].inBase}{GRAY}/4 Pieces in the Base", end="")
    if players[pID].inHome:
        # if any tokens in Home
        print(f", and {RESET}{players[pID].inHome}{GRAY}/4 Pieces in Home{RESET}")
    else:
        # new line
        print(RESET)


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
    # furthest cell a token can go to in a path specified
    # checks for blocks
    # will return cell preceding block, IF dice roll takes token PAST the block
    # will return -1, if token is to land directly on opposing block
    # will return cellAtMove cell if no opposing block encountered

    furthest = src
    for move in range(1, moves + 1):
        # iterate from 1 space to 'moves' spaces ahead
        # cell index
        movedCell = cellAtMove(src, move, direct)
        if stdPath[movedCell].playerID == -1 or stdPath[movedCell].playerID == pID:
            # if cell is free or cell occupied by same color
            furthest = movedCell

        elif stdPath[movedCell].count > 1:
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

    clockwise = False
    anticw = False
    for token in tokens[pID]:
        if token.cellNum == cell:
            if token.direction == 1:
                clockwise = True
            else:
                anticw = True

    pApproach = players[pID].approachCell
    clockwiseDist = distanceTo(cell, pApproach, 1)
    anticwDist = distanceTo(cell, pApproach, -1)

    if clockwise and anticw:
        if clockwiseDist >= anticwDist:
            return 1
        else: 
            return -1
    elif clockwise:
        # only clockwise members
        return 1
    else:
        # only anticlockwise members
        return -1


def capture(cell, capturerID, capturingName, capturedID, block):
    # no returns
    # updates tokens captured
    # DOES NOT change stdPath array

    capturerName = players[capturerID].name
    capturedName = players[capturedID].name

    if block:
        print(f"\t{capturerName} block {capturingName} lands on square {cell}, captures {capturedName} block {blockName(capturedID, cell)} and returns it to Base")

    for capturedToken in tokens[capturedID]:
        if capturedToken.cellNum == cell:
            # token in capturing cell
            # reset all attributes
            capturedToken.cellNum = -1
            capturedToken.direction = 1
            capturedToken.captured = 0
            capturedToken.approachPass = 0
            capturedToken.bhawanaMultiplier = 0
            capturedToken.kotuwaBriefing = 0

            # update inBase / onBoard counters for captured player
            players[capturedID].inBase += 1
            players[capturedID].onBoard -= 1

            if not block:
                # token can only capture single opponent
                print(f"\t{capturerName} piece {capturingName} lands on square {cell}, captures {capturedName} piece {capturedToken.tokenName}, and returns it to Base")
                break

    playerSummary(capturedID)

def move(src, dest, pID, mID, direct, block, teleport):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming block
    # 2 - moved successfully to cell occupied by opposing color, capturing opponent
    # 3 - failed to move to cell due to opposing block

    # prev position in std path
    if 0 <= src < 52:
        size = stdPath[src].count
        
        stdPath[src].count -= size
        
        if stdPath[src].count == 0:
            # previous postition is now empty
            stdPath[src] = stdCell(-1, -1, 0)
        else:
            # update direction for block left behind
            prevBDir = stdPath[src].direction
            stdPath[src].direction = blockDirection(src, pID)

    if stdPath[dest].playerID == -1:
        # dest is free cell
        stdPath[dest] = stdCell(pID, size, direct)

        if block:
            for token in tokens[pID]:
                if token.cellNum == src:
                    token.cellNum = dest
        else:
            tokens[pID][mID].cellNum = dest
        
        return 0

    elif stdPath[dest].playerID == pID:
        # occupied by same color
        stdPath[dest].count += size

        if block:
            for token in tokens[pID]:
                if token.cellNum == src:
                    token.cellNum = dest
        else:
            tokens[pID][mID].cellNum = dest
        
        stdPath[dest].direction = blockDirection(pID, dest)

        return 1
    
    else:
        # occupied by opposing color
        
        if stdPath[dest].count == size:
            # can capture
            capture(dest, pID,"", "", block)
            stdPath[dest] = stdCell(pID, size, direct)

            if block:
                for token in tokens[pID]:
                    if token.cellNum == src:
                        token.cellNum = dest
                        token.captured += 1
            else:
                tokens[pID][mID].cellNum = dest
                tokens[pID][mID].captured += 1
            
            return 2
        
        else:
            # cant capture

            if block:
                stdPath[src] = stdCell(pID, size, direct)
            else:
                if src != -1:
                    # move token back to previous location in stdPath
                    if stdPath[src].playerID == -1:
                        # re-occupy previous cell
                        stdPath[src] = stdCell(pID, 1, direct)
                    else:
                        # add back to block
                        stdPath[src].count += 1
                        stdPath[src].direction = prevBDir
            return 3



def moveToken(src, dest, pID, tID, direct):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming block
    # 2 - moved successfully to cell occupied by opposing color, capturing opponent
    # 3 - failed to move to cell due to opposing block

    if 0 <= src < 52:
        # prev position was in stdPath
        stdPath[src].count -= 1

        if stdPath[src].count == 0:
            # previous postition is now empty
            stdPath[src] = stdCell(-1, -1, 0)
        else:
            # update block direction for prev position
            prevBDir = stdPath[src].direction
            stdPath[src].direction = blockDirection(src, pID)

        # data for std out messages
        dist = distanceTo(src, dest, direct)
        directionStr = "clockwise" if direct == 1 else "anti-clockwise"

    # moving player / token data
    pName = players[pID].name
    tName = tokens[pID][tID].tokenName

    if stdPath[dest].playerID == -1:
        # moving to free cell

        if src != -1:
            # moving from stdPath
            print(f"{pName} moves piece {tName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        else:
            # moving from base
            print(f"{pName} moves piece {tName} from the Base to the Starting Point ({dest})")

        # update new stdPath and token data
        stdPath[dest] = stdCell(pID, 1, direct)
        tokens[pID][tID].cellNum = dest
        return 0

    elif stdPath[dest].playerID == pID:
        # occupied by same color

        if src != -1:
            # moving from stdPath
            print(f"{pName} moves piece {tName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        else:
            # moving from base
            print(f"{pName} moves piece {tName} from the Base to the Starting Point ({dest})")

        print("\tMerging with", blockName(pID, dest), end="")

        # updating new stdPath and token data
        stdPath[dest].count += 1
        tokens[pID][tID].cellNum = dest
        stdPath[dest].direction = blockDirection(dest, pID)

        print(" to form block", blockName(pID, dest))
        print(f"\tUpdating Block {blockName(pID, dest)} Direction: {stdPath[dest].direction}")
        return 1
    
    else:
        # occupied by opposing color
        if stdPath[dest].count == 1:
            # can capture
            if src != -1:
                # moving from stdPath
                print(f"{pName} moves piece {tName} from location {src} to {dest} by {dist} units in {directionStr} direction")
            else:
                # moving from base
                print(f"{pName} moves piece {tName} from the Base to the Starting Point ({dest})")

            # capture opposing token
            capture(dest, pID, tName, stdPath[dest].playerID, False)

            # update new stdPath and token data
            stdPath[dest] = stdCell(pID, 1, direct)
            tokens[pID][tID].captured += 1
            tokens[pID][tID].cellNum = dest
            return 2

        else:
            # can't capture
            blockingID = stdPath[dest].playerID

            if src != -1:
                # move token back to previous location in stdPath
                if stdPath[src].playerID == -1:
                    # re-occupy previous cell
                    stdPath[src] = stdCell(pID, 1, direct)
                else:
                    # add back to block
                    stdPath[src].count += 1
                    stdPath[src].direction = prevBDir

                print(f"{pName} piece {tName} is blocked from moving from {src} to {dest}, by {players[blockingID].name} block {blockName(blockingID, dest)}")
            else:
                print(f"{pName} piece {tName} is blocked from moving from the Base to {dest}, by {players[blockingID].name} block {blockName(blockingID, dest)}")
            return 3


def moveBlock(src, dest, pID, direct):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming larger block
    # 2 - moved successfully to cell occupied by opposing block of same size, capturing opponent
    # 3 - failed to move to cell due to opposing block
    
    size = stdPath[src].count
    stdPath[src] = stdCell(-1, -1, 0)

    # data for std out messages
    dist = distanceTo(src, dest, direct)
    directionStr = "clockwise" if direct == 1 else "anti-clockwise"

    # moving player / block data
    pName = players[pID].name
    bName = blockName(pID, src)

    if stdPath[dest].playerID == -1:
        # moving to free cell
        print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")

        stdPath[dest] = stdCell(pID, size, direct)
        for token in tokens[pID]:
            if token.cellNum == src:
                token.cellNum = dest
        return 0

    elif stdPath[dest].playerID == pID:
        # moving to cell occupied by same color
        print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        print(f"\tMerging with", blockName(pID, dest), end="")

        stdPath[dest].count += size
        stdPath[dest].direction = blockDirection(dest, pID)

        for token in tokens[pID]:
            if token.cellNum == src:
                token.cellNum = dest

        print(" to form block ", blockName(pID, dest))        
        print(f"\tUpdating Block {blockName(pID, dest)} Direction: {stdPath[dest].direction}")
        return 1
    
    else:
        # occupied by opposing color
        if stdPath[dest].count == size:
            # can capture
            print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")

            # capture opposing block
            capture(dest, pID, bName, stdPath[dest].playerID, True)

            # update new stdPath and token data
            stdPath[dest] = stdCell(pID, size, direct)
            for pToken in tokens[pID]:
                if pToken.cellNum == src:
                    pToken.cellNum = dest
                    pToken.captured += 1
            return 2
        else:

            # can't capture
            blockingID = stdPath[dest].playerID
            print(f"{pName} block {bName} is blocked from moving from {src} to {dest}, by {players[blockingID].name} block {blockName(blockingID, dest)}")

            # move block back to initial location
            stdPath[src] = stdCell(pID, size, direct)
            return 3


def teleport(src, dest, pID, mName, srcName, destName):
    direct = stdPath[src].direction
    size = stdPath[src].count
    stdPath[src] = stdCell(-1, -1, 0)

    # player data
    pName = players[pID].name

    if stdPath[dest].playerID == -1:
        # free cell
        stdPath[dest] = stdCell(pID, size, direct)
        for token in tokens[pID]:
            if token.cellNum == src:
                token.cellNum = dest
        return 0

    elif stdPath[dest].playerID == pID:
        # occupied by same color
        print(f"\tMerging with", blockName(pID, dest), end="")

        stdPath[dest].count += size
        stdPath[dest].direction = blockDirection(dest, pID)

        for token in tokens[pID]:
            if token.cellNum == src:
                token.cellNum = dest

        print(" to form block ", blockName(pID, dest))
        print(f"\tUpdating Block {blockName(pID, dest)} Direction: {stdPath[dest].direction}")
        return 1
    
    else:
        # occupied by opposing color
        if stdPath[dest].count == size:
            # can capture
            # capture opposing block
            capture(dest, pID, mName, stdPath[dest].playerID, True)

            # update new stdPath and token data
            stdPath[dest] = stdCell(pID, size, direct)
            for pToken in tokens[pID]:
                if pToken.cellNum == src:
                    pToken.cellNum = dest
                    pToken.captured += 1
            return 2
        else:

            # can't capture
            blockingID = stdPath[dest].playerID
            print(f"\t{pName} {mName} is blocked from teleporting from {srcName} ({src}) to {destName} ({dest}), by {players[blockingID].name} block {blockName(blockingID, dest)}")
            print(f"\t{mName} is teleporting back to {srcName}")
            # move block back to initial location
            stdPath[src] = stdCell(pID, size, direct)
            return 3


def bhawana(pID):
    bhawanaEffect = flipCoin()

    for token in tokens[pID]:
        if token.cellNum == 9:
            if bhawanaEffect == 1:
                print(f"\t{players[pID].name} piece {token.tokenName} feels energized, and movement speed doubles")
                token.bhawanaMultiplier = 4
            else:
                print(f"\t{players[pID].name} piece {token.tokenName} feels sick, and movement speed halves")
                token.bhawanaMultiplier = -4


def kotuwa(pID):
    for token in tokens[pID]:
        if token.cellNum == 27:
            print(f"\t{players[pID].name} piece {token.tokenName} attends briefing and cannot move for four rounds")
            token.kotuwaBriefing = 4
            players[pID].restricted += 1


def kotuwaBreak(pID):
    # player rolled two 3's in a row
    for token in tokens[pID]:
        if token.cellNum == 27 and token.kotuwaBriefing > 0:
            print(f"\n\t{players[pID].name} piece {token.tokenName} is movement-restricted and has rolled three consecutively")
            print(f"\tTeleporting piece {token.tokenName} to Base")

            token.cellNum = -1
            token.direction = 1
            token.captured = 0
            token.approachPass = 0
            token.bhawanaMultiplier = 0
            token.kotuwaBriefing = 0

            players[pID].inBase += 1
            players[pID].onBoard -= 1
            players[pID].restricted -= 1

            playerSummary(pID)


def pitaKotuwa(pID):
    for token in tokens[pID]:
        if token.cellNum == 46:
            if token.direction == 1:
                print(f"\tThe {players[pID].name} piece {token.tokenName}, which was moving clockwise, has changed to moving counter-clockwise")
                token.direction = -1
            else:
                print(f"\tThe {players[pID].name} piece {token.tokenName} is moving in a counter-clockwise direction")
                print(f"\tTeleporting to Kotuwa from Pita-Kotuwa")
                t = teleport(46, 27, pID, token.tokenName, "Pita-Kotuwa", "Kotuwa")
                if t != 3:
                    kotuwa(pID)


def landMystery(pID, mID, cell):
    if mID < 4:
        mName = "Token " + tokens[pID][mID].tokenName
    else:
        mName = "Block " + blockName(pID, tokens[pID][mID - 4].cellNum)
    print(f"\t{BOLD}{players[pID].name}{BOLD} lands on the Mystery Cell{RESET} ", end="")

    mystery = rollDice()
    match mystery: # use switch-case in C
        case 1:
            # teleport to Bhawana
            print(f"and is teleported to Bhawana")
            t = teleport(cell, 9, pID, mName, "Mystery Cell" , 'Bhawana')
            if t != 3:
                bhawana(pID)

        case 2:
            # teleport to Kotuwa
            print(f"and is teleported to Kotuwa")
            t = teleport(cell, 27, pID, mName, "Mystery Cell" , 'Kotuwa')
            if t != 3:
                kotuwa(pID)

        case 3:
            # teleport to Pita-Kotuwa
            print(f"and is teleported to Pita-Kotuwa")
            t = teleport(cell, 46, pID, mName, "Mystery Cell" , 'Pita-Kotuwa')
            if t != 3:
                pitaKotuwa(pID)

        case 4:
            # teleport to Base
            print(f"and is teleported to {players[pID].name} Base")
            stdPath[cell] = stdCell(-1, -1, 0)
            for token in tokens[pID]:
                if token.cellNum == cell:
                    token.cellNum = -1
                    token.direction = 1
                    token.captured = 0
                    token.approachPass = 0
                    token.bhawanaMultiplier = 0
                    token.kotuwaBriefing = 0

                    players[pID].inBase += 1
                    players[pID].onBoard -= 1
            playerSummary(pID)

        case 5:
            # teleport to Starting
            print(f"and is teleported to {players[pID].name} Starting Cell ({players[pID].startingCell})")
            t = teleport(cell, players[pID].startingCell, pID, mName, "Mystery Cell" , "Starting Cell")

        case 6:
            # teleport to Approach
            print(f"and is teleported to {players[pID].name} Approach Cell ({players[pID].approachCell})")
            t = teleport(cell, players[pID].approachCell, pID, mName, "Mystery Cell" , "Approach Cell")

    if sleepTimer:
        print('\a', end="")
        time.sleep(0.4)


def tokenTurn(pID, tID, diceValue, mysteryCell):
    # + Returns +
    # -1 if move is not possible
    # 0 if turn played out normally
    # 1 if player awarded bonus roll
    # 2 if a piece reached home

    # retrieve player data
    pName = players[pID].name
    pStart = players[pID].startingCell
    pApproach = players[pID].approachCell

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
    tBhawMul = tokens[pID][tID].bhawanaMultiplier
    tKotuBr = tokens[pID][tID].kotuwaBriefing

    # kotuwa effects
    if tKotuBr > 0:
        print(f"{pName} piece {tName} is attending a briefing and cannot move for the next {tKotuBr} rounds")
        return -1

    if currPos == -1 and diceValue == 6:
        # token is in base
        m = moveToken(-1, pStart, pID, tID, 1)
        if m == 3:
            return -1

        # prev piece memo for blue player
        if pID == 2:
            players[2].prevPiece = tID

        print("Flipping Coin to Pick Direction")
        coinVal = flipCoin()
        if coinVal:
            print(f"\tHeads, {tName} will move Clockwise")
        else:
            print(f"\tTails, {tName} will move Anti-Clockwise")
            tokens[pID][tID].direction = -1

        ###Note### block direction updated after coin flip, stdOut for direction came at move function
        stdPath[pStart].direction = blockDirection(pStart, pID)
        ################################################

        # update inBase / onBoard counters
        players[pID].inBase -= 1
        players[pID].onBoard += 1

        playerSummary(pID)

        # check mystery cell collision
        if pStart == mysteryCell:
            landMystery(pID, tID, mysteryCell)

        # award bonus roll for capture
        if m == 2:
            return 1
        return 0

    # bhawana Effects
    if tBhawMul > 0:
        print(f"{pName} piece {tName} is feeling energized, and movement speed doubles; {diceValue} -> {diceValue * 2}")
        diceValue *= 2
    elif tBhawMul < 0:
        print(f"{pName} piece {tName} is feeling sick, and movement speed halves; {diceValue} -> {diceValue // 2}")
        diceValue //= 2

    # token is in stdPath
    if 0 <= currPos < 52:
        # find next position
        nextPos = cellAtMove(currPos, diceValue, tDir)

        # check if path to next position is clear
        allowedPos = checkPath(currPos, diceValue, pID, tDir)
        if allowedPos == -1:
            # not allowed to move due to block
            blocker = stdPath[nextPos].playerID
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {players[blocker].name} block {blockName(blocker, nextPos)}")
            return -1
        
        if allowedPos == currPos:
            # block in immediate cell
            blockLocation = cellAtMove(currPos, 1, tDir)
            blocker = stdPath[blockLocation].playerID
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {players[blocker].name} ", end="")
            if stdPath[blockLocation].count == 1:
                for token in tokens[blocker]:
                    if token.cellNum == blockLocation:
                        print(f"piece {token.tokenName}")
            else:  
                print(f"block {blockName(blocker, blockLocation)}")
            return -1

        if allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            blockLocation = cellAtMove(allowedPos, 1, tDir)
            blocker = stdPath[blockLocation].playerID
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {players[blocker].name} block {blockName(blocker, blockLocation)} at square {blockLocation}")
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
                    nextPos += diceValue - distToApproach - 1

                    if nextPos > pHome:
                        # overshot home
                        print(f"{pName} piece {tName} over-shoots home")
                        return -1

                    # prev piece memo for blue player
                    if pID == 2:
                        players[2].prevPiece = tID

                    # update flags
                    tokens[pID][tID].cellNum = nextPos
                    stdPath[currPos].count -= 1
                    if stdPath[currPos].count == 0:
                        stdPath[currPos] = stdCell(-1, -1, 0)
                    else:
                        stdPath[currPos].direction = blockDirection(currPos, pID)
                        print(f"\tUpdating Block {blockName(pID, currPos)} Direction: {stdPath[currPos].direction}")

                    if nextPos == pHome:
                        # going directly home
                        tokens[pID][tID].cellNum = pHome

                        # update onBoard / inHome counters
                        players[pID].onBoard -= 1
                        players[pID].inHome += 1

                        print(f"{pName} piece {tName} has reached Home")
                        playerSummary(pID)
                        return 2

                    print(f"{pName} piece {tName} is moving to Home Straight")
                    print(f"\t{tName} is {pHome - nextPos} squares away from Home")
                    return 0

                else:
                    # aint captured nun
                    print(f"{pName} piece {tName} hasn't captured any tokens, Cannot enter Home-Straight")

            m = moveToken(currPos, nextPos, pID, tID, tDir)
            if m == 3: return -1

            # prev piece memo for blue player
            if pID == 2:
                players[2].prevPiece = tID

            # approachPass counter for anticlockwise tokens
            tokens[pID][tID].approachPass += 1

            # check mystery cell collision
            if nextPos == mysteryCell:
                landMystery(pID, tID, mysteryCell)

            if m == 2: return 1

        else:
            # regular stdPath move without passing approach
            m = moveToken(currPos, nextPos, pID, tID, tDir)
            if m == 3: return -1

            # check mystery cell collision
            if nextPos == mysteryCell:
                landMystery(pID, tID, mysteryCell)

            # prev piece memo for blue player
            if pID == 2:
                players[2].prevPiece = tID

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

            # prev piece memo for blue player
            if pID == 2:
                players[2].prevPiece = tID

            return 0

        elif diceValue == spacesLeft or spacesLeft == 0:
            # going home
            tokens[pID][tID].cellNum = pHome

            # update onBoard / inHome counters
            players[pID].onBoard -= 1
            players[pID].inHome += 1

            print(f"{pName} piece {tName} has reached Home")
            playerSummary(pID)

            # prev piece memo for blue player
            if pID == 2:
                players[2].prevPiece = tID

            return 2

        else:
            # overshot home
            print(f"{pName} piece {tName} over-shoots home; Rolled {diceValue} while {spacesLeft} from Home")
            return -1


def blockTurn(pID, bID, diceValue, mysteryCell):
    # + Returns +
    # -1 if move is not possible
    # 0 if turn played out normally
    # 1 if player awarded bonus roll
    # 2 if a piece reached home

    # retrieve player data
    pName = players[pID].name
    pStart = players[pID].startingCell
    pApproach = players[pID].approachCell

    # player's home straight
    # home straights and homes are;
    #       green: 65-69, 70
    #       yellow: 75-79, 80
    #       blue: 85-89, 90
    #       red: 95-99, 100
    pHome = 70 + 10*pID
    pHomeStrt = 65 + 10*pID

    currPos = tokens[pID][bID - 4].cellNum
    bDir = stdPath[currPos].direction
    bCount = stdPath[currPos].count
    bName = blockName(pID, currPos)

    if diceValue < bCount:
        print(f"{pName} tries to move block {bName}")
        print(f"\t{GRAY}Dice roll of {diceValue} is not sufficient to move block of size {bCount}{RESET}")
        return -1
    diceValue //= bCount

    if currPos < 52:
        # block in stdPath
        nextPos = cellAtMove(currPos, diceValue, bDir)
        allowedPos = checkPath(currPos, diceValue, pID, bDir)

        if allowedPos == -1:
            # landing on block
            if stdPath[nextPos].count != bCount:
                blocker = stdPath[nextPos].playerID
                
                print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {players[blocker].name}", end="")
                if stdPath[nextPos].count == 1:
                    for token in tokens[blocker]:
                        if token.cellNum == nextPos:
                            print(f" piece {token.name}")
                            return -1
                        
                print(f" block {blockName(blocker, nextPos)}")
                return -1
        
        elif allowedPos == currPos:
            # block in immediate cell
            blockLocation = cellAtMove(currPos, 1, bDir)
            blocker = stdPath[blockLocation].playerID
            
            print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {players[blocker].name} ", end="")
            if stdPath[blockLocation].count == 1:
                for token in tokens[blocker]:
                    if token.cellNum == blockLocation:
                        print(f"piece {token.name}")
                        return -1

            print(f"block {blockName(blocker, blockLocation)}")
            return -1
        
        elif allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            blockLocation = cellAtMove(allowedPos, 1, bDir)
            blocker = stdPath[blockLocation].playerID

            print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {players[blocker].name} block {blockName(blocker, blockLocation)} at square {blockLocation}")
            print(f"\tMoving block {bName} to square {allowedPos} which is the cell before the block")

            # update cell to move to
            nextPos = allowedPos

        distToApproach = distanceTo(currPos, pApproach, bDir)
        distToNextPos = distanceTo(currPos, nextPos, bDir)

        if distToApproach < distToNextPos:
            # passing approach

        ############################################################################################################
            # can only move to approach if going clockwise, or has passed approach at least once
            if bDir == 1: # TEMPORARY: DOESNT HANDLE ANTICLOCKWISE

                ##############################################################
                # TEMPORARY MOVING EACH TOKEN AS INDIVIDUAL INTO HOME STRAIGHT
                ##############################################################
                nextMemberPos = pHomeStrt + diceValue - distToApproach - 1
                print(f"{pName} block {bName} is passing the Approach Cell {pApproach}")
                for token in tokens[pID]:
                    if token.cellNum == currPos:
                        if token.captured > 0:
                            token.cellNum = nextMemberPos
                            stdPath[currPos].count -= 1
                            print(f"\tBlock member {token.tokenName} is moving to Home Straight")
                            print(f"\t\t{token.tokenName} is {pHome - nextMemberPos} squares away from Home")
                        else:
                            # aint captured nun
                            print(f"\tBlock member {token.tokenName} hasn't captured any tokens, Cannot enter Home-Straight")

                # reset prev pos, if all tokens move out
                if stdPath[currPos].count == 0:
                    stdPath[currPos] = stdCell(-1, -1, 0)
                    return 0
                else:
                    stdPath[currPos].direction = blockDirection(currPos, pID)
                    print(f"\tUpdating Block {blockName(pID, currPos)} Direction: {stdPath[currPos].direction}")
        #############################################################################################################
        m = moveBlock(currPos, nextPos, pID, bDir)
        if m == 3: return -1

        # check mystery cell collision
        if nextPos == mysteryCell:
            landMystery(pID, bID, mysteryCell)

        if m == 2: return 1
        return 0
    else:
        # shouldn't be able to come here anyway
        print("\n\n\n\n\n\n\t\t\t\t\t\tBLOCK IN HOME STRAIGHT???????")
        time.sleep(10)


def breakPlayerBlocks(pID):
    # return # INCOMPLETE
    # possibilities
    # 1 block of 2
    # 2 blocks of 2
    # 1 block of 3
    # 1 block of 4
    
    blocks = [
        [-1,0,0,0],
        [-1,0,0,0]
    ] # location, count, clockwise, anticw
    tokensInBlocks = 0
    for token in tokens[pID]:
        if not (0 <= token.cellNum < 52): continue
        if stdPath[token.cellNum].count > 1:
            tokensInBlocks += 1
            if blocks[0][0] == -1 or blocks[0][0] == token.cellNum:
                blocks[0][0] = token.cellNum
                blocks[0][1] += 1
                if token.direction == 1:
                    blocks[0][2] += 1
                else:
                    blocks[0][3] += 1
            else:
                blocks[1][0] = token.cellNum
                blocks[1][1] += 1
                if token.direction == 1:
                    blocks[1][2] += 1
                else:
                    blocks[1][3] += 1

    if not tokensInBlocks: return

    print(f"{players[pID].name} rolled '6' consecutively three times,\n\tBreaking all {players[pID].name} blocks")
    print(blocks[0])
    print(blocks[1])
    time.sleep(10)

    # if blocks[1][0] != -1:
    #     # 2 blocks of 2 special case
    #     for i in range(1, 5 + 1):
    #         if blocks[0][2] > 1:
    #             if stdPath[cellAtMove(blocks[0][0], i, 1)].count <= 1:



def playTurn(pID, roundNum, sixRepeats, mysteryCell):
    # Returns
    # 0 - turn over
    # 1 - bonus roll for capture
    # 2 - player reached home
    # 6 - bonus roll for 6
    # -1 - no moves made

    # retrieve player data
    pName = players[pID].name

    diceValue = rollDice()
    print(f"\n{pName}'s Turn (Round {roundNum})")

    print(f"{pName} rolled {diceValue}")

    if diceValue == 6 and sixRepeats == 2:
        # breakPlayerBlocks(pID)
        print(f"{pName} Player rolled three 6's in a row, Ignoring throw and moving on to the next player")
        return 0
    
    if diceValue == 3:
        if players[pID].prevThree and players[pID].restricted > 0:
            # send kotuwa briefing tokens to base if 3 rolled twice
            kotuwaBreak(pID)
    players[pID].prevThree = (diceValue == 3)

    updateChoiceWeights(pID, diceValue, mysteryCell)
    # print(pName, players[pID].choiceWeights)

    while True:
        highIndex = -1
        highWeight = -1

        for i in range(8):
            w = players[pID].choiceWeights[i]
            if w > highWeight:
                highIndex = i
                highWeight = w

        if highIndex == -1:
            print(f"{pName}{GRAY} has no possible moves, Ignoring the throw and moving to the next player{RESET}")
            return -1

        if highIndex < 4: moveRes = tokenTurn(pID, highIndex, diceValue, mysteryCell)
        else: moveRes = blockTurn(pID, highIndex, diceValue, mysteryCell)

        if moveRes != -1: break

        print(f"\n{pName} is picking a different move")
        players[pID].choiceWeights[highIndex] = -1

    if moveRes == 2:
        # check win condition
        if diceValue == 6:
            return 7
        return 2

    if moveRes == 1:
        # bonus roll for capture
        return 1
    if diceValue == 6 and moveRes != -1:
        # bonus roll for 6
        return 6
    return 0


def greenBehaviour(diceV):
    # empty base >>>>>>>
    # creating blocks >?>?>?>?>
    # breaking blocks <<<<<<<<<
    pApproach = players[0].approachCell

    for i in range(4):
        token = tokens[0][i]

        if token.cellNum == 70:
            # token in home
            continue

        if token.cellNum == -1:
            # in base
            if diceV == 6:
                players[0].choiceWeights[i] = 98
            continue
        
        if 52 < token.cellNum < 70:
            # home straight
            players[0].choiceWeights[i] = token.cellNum
            continue

        # stdPath
        if stdPath[token.cellNum].count > 1:
            # breaking block <<<<
            players[0].choiceWeights[i] = 0
            # moving block >>>>
            players[0].choiceWeights[i + 4] = 1
            continue
        else:
            players[0].choiceWeights[i] = 60 - distanceTo(token.cellNum, pApproach, token.direction)

        nextCell = cellAtMove(token.cellNum, diceV, token.direction)
        targetPlayer = stdPath[nextCell].playerID
        if targetPlayer == 0:
            # high priority to create blocks
            players[0].choiceWeights[i] = 99


def yellowBehaviour(diceV):
    # empty base >>>>>
    # 1 capture >>>>
    # closest to home >>>>>
    pApproach = players[1].approachCell

    for i in range(4):
        token = tokens[1][i]

        if token.cellNum == 80:
            # token in home
            continue

        if token.cellNum == -1:
            # in base
            if diceV == 6:
                players[1].choiceWeights[i] = 100
            continue
        
        if 52 < token.cellNum < 80:
            # home straight
            players[1].choiceWeights[i] = token.cellNum
            continue

        # stdPath
        if stdPath[token.cellNum].count > 1:
            # mark block move as possible
            players[1].choiceWeights[i + 4] = 0 

        if token.captured == 0:
            nextCell = cellAtMove(token.cellNum, diceV, token.direction)
            targetPlayer = stdPath[nextCell].playerID

            if targetPlayer != 1 and targetPlayer != -1 and stdPath[nextCell].count == 1:
                # high priority for pieces with no captures and opponent in range
                players[1].choiceWeights[i] = 99
                continue

        players[1].choiceWeights[i] = 60 - distanceTo(token.cellNum, pApproach, token.direction)

        if token.direction == -1 and token.approachPass < 1:
            # anticlockwise piece not passed approach is further behind
            players[1].choiceWeights[i] -= 52

def blueBehaviour(diceV, mysteryCell):
    # cyclic manner
    # target mystery if anticlockwise
    # avoid mystery if clockwise
    prevPiece = players[2].prevPiece
    cyclicMultiplier = [1, 1, 1, 1]
    cyclicMultiplier[(prevPiece + 1) % 4] = 4
    cyclicMultiplier[(prevPiece + 2) % 4] = 3
    cyclicMultiplier[(prevPiece + 3) % 4] = 2

    for i in range(4):
        token = tokens[2][i]

        if token.cellNum == 90: continue

        if token.cellNum == -1:
            # in base
            if diceV == 6:
                players[2].choiceWeights[i] = 1 * cyclicMultiplier[i]
            continue
        
        if 52 < token.cellNum < 90:
            # home straight
            players[2].choiceWeights[i] = 1 * cyclicMultiplier[i]
            continue

        # stdPath
        if stdPath[token.cellNum].count > 1:
            # mark block move as possible
            players[2].choiceWeights[i + 4] = 0

        nextCell = cellAtMove(token.cellNum, diceV, token.direction)
        if mysteryCell == nextCell:
            if token.direction == 1:
                players[2].choiceWeights[i] = 0
                continue
            else:
                players[2].choiceWeights[i] = 100 * cyclicMultiplier[i]
                continue

        players[2].choiceWeights[i] = 1 * cyclicMultiplier[i]

def redBehaviour(diceV):
    # capturing >>>
    # one piece on board when possible
    # blocks <<<
    pStart = players[3].startingCell

    for i in range(4):
        token = tokens[3][i]

        if token.cellNum == 100:
            # token in home
            continue

        if token.cellNum == -1:
            # in base
            if diceV == 6:
                startingCellStatus = stdPath[pStart].playerID
                if startingCellStatus == -1:
                    # free cell
                    players[3].choiceWeights[i] = 1
                elif startingCellStatus == 3:
                    # forming block, unfavored
                    players[3].choiceWeights[i] = 0
                elif stdPath[pStart].count == 1:
                    # capturing opponent
                    targetPlayer = stdPath[pStart].playerID
                    for oppToken in tokens[targetPlayer]:
                        if oppToken.cellNum != pStart:
                            # opponent closer to home, higher value
                            players[3].choiceWeights[i] = 55 - distanceTo(pStart, players[targetPlayer].approachCell, oppToken.direction)
            continue

        if 52 < token.cellNum < 100:
            # home straight
            players[3].choiceWeights[i] = 2
            continue

        if stdPath[token.cellNum].count > 1:
            # mark block move as possible
            players[3].choiceWeights[i + 4] = 0

        # stdPath
        nextCell = cellAtMove(token.cellNum, diceV, token.direction)
        targetPlayer = stdPath[nextCell].playerID
        if targetPlayer == 3:
            # forming block, unfavored
            players[3].choiceWeights[i] = 0
            continue
        if targetPlayer == -1:
            # free cell
            players[3].choiceWeights[i] = 2
            continue

        if stdPath[nextCell].count > 1: continue
        players[3].choiceWeights[i] = 2

        for oppToken in tokens[targetPlayer]:
            if oppToken.cellNum != nextCell: continue
            # opponent closer to home, higher value
            players[3].choiceWeights[i] = 55 - distanceTo(nextCell, players[targetPlayer].approachCell, oppToken.direction)


def updateChoiceWeights(pID, diceV, mysteryCell):
    # reset weights, -1 means impossible
    players[pID].choiceWeights = [-1,-1,-1,-1,-1,-1,-1,-1]

    match pID:
        case 0:
            # green player
            greenBehaviour(diceV)
        case 1:
            # yellow player
            yellowBehaviour(diceV)
        case 2:
            # blue player
            blueBehaviour(diceV, mysteryCell)
        case 3:
            # red player
            redBehaviour(diceV)
        # case _:
        #     for i in range(4):
        #         token = tokens[pID][i]
        #         if token.cellNum == -1:
        #             if diceV == 6:
        #                 players[pID].choiceWeights[i] = 1
        #         elif 0 <= token.cellNum < 52:
        #             players[pID].choiceWeights[i] = 1
        #             if stdPath[token.cellNum].count > 1:
        #                 players[pID].choiceWeights[i + 4] = 1
        #         elif token.cellNum != 70 + 10 * pID:
        #             players[pID].choiceWeights[i] = 1


##################################################################################################

# player data array
# array index == playerID
players = [
    Player(GREEN + "Green" + RESET, 41, 39, 4, 0, 0, 0, False, [-1,-1,-1,-1,-1,-1,-1,-1], -1),
    Player(YELLOW + "Yellow" + RESET, 2, 0, 4, 0, 0, 0, False, [-1,-1,-1,-1,-1,-1,-1,-1], -1),
    Player(BLUE + "Blue" + RESET, 15, 13, 4, 0, 0, 0, False, [-1,-1,-1,-1,-1,-1,-1,-1], 3),
    Player(RED + "Red" + RESET, 28, 26, 4, 0, 0, 0, False, [-1,-1,-1,-1,-1,-1,-1,-1], -1),
]


# token data array
# array index == playerID
# subarray index == tokenID
tokens = [
    [
        Piece(-1, GREEN + BOLD + "G1" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, GREEN + BOLD + "G2" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, GREEN + BOLD + "G3" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, GREEN + BOLD + "G4" + RESET, 1, 0, 0, 0, 0)
    ],
    [
        Piece(-1, YELLOW + BOLD + "Y1" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, YELLOW + BOLD + "Y2" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, YELLOW + BOLD + "Y3" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, YELLOW + BOLD + "Y4" + RESET, 1, 0, 0, 0, 0)
    ],
    [
        Piece(-1, BLUE + BOLD + "B1" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, BLUE + BOLD + "B2" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, BLUE + BOLD + "B3" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, BLUE + BOLD + "B4" + RESET, 1, 0, 0, 0, 0)
    ],
    [
        Piece(-1, RED + BOLD + "R1" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, RED + BOLD + "R2" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, RED + BOLD + "R3" + RESET, 1, 0, 0, 0, 0),
        Piece(-1, RED + BOLD + "R4" + RESET, 1, 0, 0, 0, 0)
    ]
]

# array to represent stdPath
# player ID, number of tokens in cell, direction of token / block
stdPath = [stdCell(-1, -1, 0)] * 52

###################################################################################################

def stdPathView():
    print(f"\n{BOLD}Standard Path:{RESET}")
    for i in range(52):
        if stdPath[i].direction == 1:
            ddd = '+'
        elif stdPath[i].direction == -1:
            ddd = '-'
        else:
            ddd = ' '
        print(f"{str(i).zfill(2)} P:{BOLD}{stdPath[i].playerID if stdPath[i].playerID != -1 else ' '}{RESET} | C:{BOLD}{stdPath[i].count if stdPath[i].count != -1 else ' '}{RESET} | D:{BOLD}{ddd}{RESET} \t", end="")

        if i != 0 and ((i + 1) % 4 == 0):
            print()
    return


def debugging():
    for i in range(52):
        if stdPath[i].count == -1:
            continue
        if not (1 <= stdPath[i].count <= 4):
            print("\n\n\nDEBUGGING: stdPath count out of range\n\n\n")
            stdPathView()
            time.sleep(25)
        if not (0 <= stdPath[i].playerID <= 3):
            print("\n\n\nDEBUGGING: stdPath playerID out of range\n\n\n")
            stdPathView()
            time.sleep(25)
        if not (-1 <= stdPath[i].direction <= 1):
            print("\n\n\nDEBUGGING: stdPath direction out of range\n\n\n")
            stdPathView()
            time.sleep(25)
    
    for i in range(4):
        if not (0 <= players[i].inBase <= 4):
            print("\n\n\nDEBUGGING: player in base out of range\n\n\n")
            stdPathView()
            time.sleep(25)
        if not (0 <= players[i].onBoard <= 4):
            print("\n\n\nDEBUGGING: player on board out of range\n\n\n")
            stdPathView()
            time.sleep(25)
        if not (0 <= players[i].inHome <= 4):
            print("\n\n\nDEBUGGING: player in home out of range\n\n\n")
            stdPathView()
            time.sleep(25)


def endOfRound(roundNum, mysteryRound, currMystery):
    print("\n==========================")
    print(f"End of Round {roundNum}")
    print("==========================\n")

    for p in range(4):
        if sleepTimer: time.sleep(0.3)
        playerSummary(p)
        print("==========================")
        print(f"Location of {players[p].name} Pieces")
        print("==========================")
        for t in tokens[p]:
            print(f"Piece {t.tokenName} [capt: {t.captured}, appr: {t.approachPass}, dir: {t.direction}] -> ", end="")
            if t.cellNum == -1:
                print(GRAY + ITALICS + "Base" + RESET)
            elif t.cellNum == 70 + 10*p:
                print(BOLD + ITALICS + "Home" + RESET)
            elif t.cellNum < 52:
                print(f"Cell {GRAY}{t.cellNum}{RESET}")
            else:
                print(f"{players[p].name}|{ITALICS}HomePath{RESET}|{GRAY}{t.cellNum - (65 + 10*p)}{RESET}")
        print("==========================\n")
    if currMystery != -1 and (mysteryRound - roundNum - 1) > 0:
        print(f"The Mystery Cell is at cell {currMystery} and will be at that location for the next {mysteryRound - roundNum - 1} rounds\n")


def spawnMysteryCell(currMystery):
    while True:
        # loop over stdPath cell values
        new = random.randint(0, 51)
        if new != currMystery and stdPath[new].count == -1:
            # cell not occupied and is not previous mystery cell
            break

    print(f"\n{BOLD}A Mystery Cell has spawned in location {new} and will be at this location for the next four rounds{RESET}")
    if sleepTimer: time.sleep(0.3)
    return new


def specialEffectUpdate():
    # move this to end of round function to not loop over all tokens twice every round later
    for i in range(4):
        for j in range(4):
            if tokens[i][j].bhawanaMultiplier > 0:
                tokens[i][j].bhawanaMultiplier -= 1
            elif tokens[i][j].bhawanaMultiplier < 0:
                tokens[i][j].bhawanaMultiplier += 1

            if tokens[i][j].kotuwaBriefing > 0:
                tokens[i][j].kotuwaBriefing -= 1
                if tokens[i][j].kotuwaBriefing == 0:
                    players[i].restricted -= 1


def gameLoop(starter):
    roundNum = 1
    currPlayer = starter
    mysteryRound = -1
    currMystery = -1

    while True:
        print("\n==========================")
        print(f"Start of Round {roundNum} {seed}")
        print("==========================")

        specialEffectUpdate()

        if roundNum == mysteryRound:
            # a mystery cell is due to spawn 
            currMystery = spawnMysteryCell(currMystery)
            mysteryRound += 4

        for _ in range(4):
            # counter to keep track of 6's rolled in a row
            sixRepeats = 0

            while True:
                if sleepTimer: time.sleep(0.5)
                turnRes = playTurn(currPlayer, roundNum, sixRepeats, currMystery)

                if turnRes == 2 or turnRes == 7:
                    # player reached home
                    if players[currPlayer].inHome == 4:
                        # win condition
                        endOfRound(roundNum, mysteryRound, currMystery)

                        print("#####################################")
                        print(f"{players[currPlayer].name} {BOLD}Player has all 4 Pieces in Home{RESET}")
                        print(f"{players[currPlayer].name} {BOLD}Player Wins!!!{RESET} Round: {roundNum}")
                        print("#####################################")

                        print(f"Random Seed: {seed}")
                        stdPathView()
                        return


                if mysteryRound == -1 and turnRes != -1:
                    # set next round a mystery cell is due to spawn
                    # turnRes is -1 if no piece was moved
                    mysteryRound = roundNum + 2
                
                if turnRes <= 0 or turnRes == 2:
                    # turn ended
                    break

                if turnRes == 6 or turnRes == 7:
                    # keep track of consecutive sixes
                    print(f"\n\t{ITALICS}{players[currPlayer].name} {ITALICS}Player is awarded a bonus roll for rolling 6 {RESET}")
                    sixRepeats += 1
                else:
                    print(f"\n\t{ITALICS}{players[currPlayer].name} {ITALICS}Player is awarded a bonus roll for capturing an opponent{RESET}")
                    sixRepeats = 0

            # move on to next player
            # wrap around if needed
            currPlayer += 1
            currPlayer %= 4

        if sleepTimer: time.sleep(0.75)
        endOfRound(roundNum, mysteryRound, currMystery)
        debugging()
        roundNum += 1
        if sleepTimer: time.sleep(0.2)

def findStarting():
    first = -1
    maxVal = 0
    rolls = [0] * 4
    print("Deciding who plays first\n")
    while first == -1:
        for i in range(4):
            roll = rollDice()
            print(f"{players[i].name} rolls {roll}")
            if sleepTimer: time.sleep(0.15)
            rolls[i] += roll
            if rolls[i] > maxVal:
                maxVal = rolls[i]
                first = i
            elif rolls[i] == maxVal:
                first = -1
        
        if first == -1:
            print(GRAY + ITALICS + "\nMultiple players rolled the same highest value, rerolling\n" + RESET)
            if sleepTimer: time.sleep(0.5)

    if sleepTimer: time.sleep(0.5)
    print(f"\n{players[first].name} has the highest roll and will begin the game")
    print(f"The order of a single round will be {players[first].name}, {players[(first+1) % 4].name}, {players[(first+2) % 4].name}, {players[(first+3) % 4].name}")
    if sleepTimer: time.sleep(0.5)
    return first


def main():
    for i in range(4):
        # iterate over all players and display tokens
        print(f"\nThe {players[i].name} player has 4 Pieces named", end=" ")
        for pToken in tokens[i]:
            print(pToken.tokenName, end=" ")
    print("\n")
    if sleepTimer: time.sleep(0.4)

    starter = findStarting()
    # start actual game loop
    gameLoop(starter)


main()