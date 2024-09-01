# ToDo;
# Convert PlayerInfo array to a class
# Mystery Cells
# Bhavana
# Kotuwa
# Pita-Kotuwa
# Player Block breakage

# Toggle time.sleep()'s between lines
# True to watch execution line by line
# False to play out rounds asap
sleepTimer = False

#######################################################################################################

import random
import time

# random.seed(635435)

# stdOut color codes
RED = '\033[1;31m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[1;34m'
RESET = '\033[0m'

class Piece:
    def __init__(self, cellNum, tokenName, direction, captured, approachPass, bhavanaMultiplier):
        self.cellNum = cellNum
        self.tokenName = tokenName
        self.direction = direction
        self.captured = captured
        self.approachPass = approachPass
        self.bhavanaMultiplier = bhavanaMultiplier

class Player:
    def __init__(self, name, starting, approach, inBase, onBoard, inHome):
        self.name = name
        self.startingCell = starting
        self.approachCell = approach
        self.inBase = inBase
        self.onBoard = onBoard
        self.inHome = inHome

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

    if len(name) == 1:
        print("\t\t\t\t\tblockName error: called for block name from cell which has no block")
        print(f"\t\t\t\t\t\t{pID} {blockCell}")
        time.sleep(10)

    if len(name) <= 4:
        print("\t\t\t\t\tblockName error: called for block name from cell which ONE token")
        print(f"\t\t\t\t\t\t{pID} {blockCell}")
        time.sleep(10)
                
    return name


def playerSummary(pID):
    # displays summary of player pieces given a player id

    print(f"{playerInfo[pID].name} Player now has {playerInfo[pID].onBoard}/4 Pieces on the Board, and {playerInfo[pID].inBase}/4 Pieces in the Base", end="")
    if playerInfo[pID].inHome:
        # if any tokens in Home
        print(f", and {playerInfo[pID].inHome} Pieces in Home")
    print()

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
    # will return -1, if token is to land directly on opposing block
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
    pApproach = playerInfo[pID].approachCell
    clockwiseDist = distanceTo(cell, pApproach, 1)
    anticwDist = distanceTo(cell, pApproach, -1)

    clockwise = False
    anticw = False
    for token in tokens[pID]:
        if token.cellNum == cell:
            if token.direction == 1:
                clockwise = True
            else:
                anticw = True

    if clockwise and anticw:
        if clockwiseDist >= anticwDist:
            return 1
        else: 
            return -1
    elif clockwise:
        return 1
    else:
        return -1


def capture(cell, capturerID, capturingName, capturedID, block):
    # no returns
    # updates tokens captured
    # DOES NOT change stdPath array

    capturerName = playerInfo[capturerID].name
    capturedName = playerInfo[capturedID].name

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
            capturedToken.bhavanaMultiplier = 0

            # update inBase / onBoard counters for captured player
            playerInfo[capturedID].inBase += 1
            playerInfo[capturedID].onBoard -= 1

            if not block:
                print(f"\t{capturerName} piece {capturingName} lands on square {cell}, captures {capturedName} piece {capturedToken.tokenName}, and returns it to Base")
                break

    playerSummary(capturedID)


def moveToken(src, dest, pID, tID, direct):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming block
    # 2 - moved successfully to cell occupied by opposing color, capturing opponent
    # 3 - failed to move to cell due to opposing block

    if 0 <= src < 52:
        # prev position was in stdPath
        stdPath[src][1] -= 1

        if stdPath[src][1] == 0:
            # previous postition is now empty
            stdPath[src] = [-1, -1, 0]
        else:
            # update block direction for prev position
            prevBDir = stdPath[src][2]
            stdPath[src][2] = blockDirection(src, pID)

        # data for std out messages
        dist = distanceTo(src, dest, direct)
        directionStr = "clockwise" if direct == 1 else "anti-clockwise"

    # moving player / token data
    pName = playerInfo[pID].name
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

        print("\tMerging with", blockName(pID, dest), end="")

        # updating new stdPath and token data
        stdPath[dest][1] += 1
        tokens[pID][tID].cellNum = dest
        stdPath[dest][2] = blockDirection(dest, pID)

        print(" to form block", blockName(pID, dest))
        print(f"\tUpdating Block {blockName(pID, dest)} Direction: {stdPath[dest][2]}")
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
            capture(dest, pID, tName, stdPath[dest][0], False)

            # update new stdPath and token data
            stdPath[dest] = [pID, 1, direct]
            tokens[pID][tID].captured += 1
            tokens[pID][tID].cellNum = dest
            return 2

        else:
            # can't capture
            blockingID = stdPath[dest][0]

            if src != -1:
                # move token back to previous location in stdPath
                if stdPath[src][0] == -1:
                    # re-occupy previous cell
                    stdPath[src] = [pID, 1, direct]
                else:
                    # add back to block
                    stdPath[src][1] += 1
                    stdPath[src][2] = prevBDir

                print(f"{pName} piece {tName} is blocked from moving from {src} to {dest}, by {playerInfo[blockingID].name} block {blockName(blockingID, dest)}")
            else:
                print(f"{pName} piece {tName} is blocked from moving from the Base to {dest}, by {playerInfo[blockingID].name} block {blockName(blockingID, dest)}")
            return 3


def moveBlock(src, dest, pID, direct):
    # + RETURNS +
    # 0 - moved successfully to a free cell
    # 1 - moved successfully to cell occupied by same color, forming larger block
    # 2 - moved successfully to cell occupied by opposing block of same size, capturing opponent
    # 3 - failed to move to cell due to opposing block
    
    size = stdPath[src][1]
    stdPath[src] = [-1, -1, 0]

    # data for std out messages
    dist = distanceTo(src, dest, direct)
    directionStr = "clockwise" if direct == 1 else "anti-clockwise"

    # moving player / token data
    pName = playerInfo[pID].name
    bName = blockName(pID, src)

    if stdPath[dest][0] == -1:
        # moving to free cell
        print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")

        stdPath[dest] = [pID, size, direct]
        for token in tokens[pID]:
            if token.cellNum == src:
                token.cellNum = dest
        return 0

    elif stdPath[dest][0] == pID:
        # moving to cell occupied by same color
        print(f"{pName} moves piece {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")
        print(f"\tMerging with", blockName(pID, dest), end="")

        stdPath[dest][1] += size
        stdPath[dest][2] = blockDirection(dest, pID)

        for token in tokens[pID]:
            if token.cellNum == src:
                token.cellNum = dest

        print(" to form block ", blockName(pID, dest))        
        print(f"\tUpdating Block {blockName(pID, dest)} Direction: {stdPath[dest][2]}")
        return 1
    
    else:
        # occupied by opposing color
        if stdPath[dest][1] == size:
            # can capture
            print(f"{pName} moves block {bName} from location {src} to {dest} by {dist} units in {directionStr} direction")

            # capture opposing block
            capture(dest, pID, bName, stdPath[dest][0], True)

            # update new stdPath and token data
            stdPath[dest] = [pID, size, direct]
            for pToken in tokens[pID]:
                if pToken.cellNum == src:
                    pToken.cellNum = dest
                    pToken.captured += 1
            return 2
        else:

            # can't capture
            blockingID = stdPath[dest][0]
            print(f"{pName} block {bName} is blocked from moving from {src} to {dest}, by {playerInfo[blockingID].name} block {blockName(blockingID, dest)}")

            # move block back to initial location
            stdPath[src] = [pID, size, direct]
            return 3


def tokenTurn(pID, tID, diceValue):
    # + Returns +
    # -1 if move is not possible
    # 0 if turn played out normally
    # 1 if player awarded bonus roll
    # 2 if a piece reached home

    # retrieve player data
    pName = playerInfo[pID].name
    pStart = playerInfo[pID].startingCell
    pApproach = playerInfo[pID].approachCell

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
        if m == 3:
            return -1

        print("Flipping Coin to Pick Direction")
        coinVal = flipCoin()
        if coinVal:
            print(f"\tHeads, {tName} will move Clockwise")
        else:
            print(f"\tTails, {tName} will move Anti-Clockwise")
            tokens[pID][tID].direction = -1

        ###Note### block direction updated after coin flip, stdOut for direction came at move function
        stdPath[pStart][2] = blockDirection(pStart, pID)
        ################################################

        # update inBase / onBoard counters
        playerInfo[pID].inBase -= 1
        playerInfo[pID].onBoard += 1

        playerSummary(pID)

        # award bonus roll for capture
        if m == 2:
            return 1
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
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker].name} block {blockName(blocker, nextPos)}")
            return -1
        
        if allowedPos == currPos:
            # block in immediate cell
            blockLocation = cellAtMove(currPos, 1, tDir)
            blocker = stdPath[blockLocation][0]
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker].name} ", end="")
            if stdPath[blockLocation][1] == 1:
                for token in tokens[blocker]:
                    if token.cellNum == blockLocation:
                        print(f"piece {token.name}")
            else:  
                print(f"block {blockName(blocker, blockLocation)}")
            return -1

        if allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            blockLocation = cellAtMove(allowedPos, 1, tDir)
            blocker = stdPath[blockLocation][0]
            print(f"{pName} piece {tName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker].name} block {blockName(blocker, blockLocation)} at square {blockLocation}")
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

                    # update flags
                    tokens[pID][tID].cellNum = nextPos
                    stdPath[currPos][1] -= 1
                    if stdPath[currPos][1] == 0:
                        stdPath[currPos] = [-1, -1, 0]
                    else:
                        print(f"\tUpdating Block {blockName(pID, currPos)} Direction: {stdPath[currPos][2]}")
                        stdPath[currPos][2] = blockDirection(currPos, pID)

                    if nextPos == pHome:
                        # going directly home
                        tokens[pID][tID].cellNum = pHome

                        # update onBoard / inHome counters
                        playerInfo[pID].onBoard -= 1
                        playerInfo[pID].inBase += 1

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
            playerInfo[pID].onBoard -= 1
            playerInfo[pID].inHome += 1

            print(f"{pName} piece {tName} has reached Home")
            playerSummary(pID)
            return 2

        else:
            # overshot home
            print(f"{pName} piece {tName} over-shoots home; Rolled {diceValue} while {spacesLeft} from Home")
            return -1


def blockTurn(pID, bID, diceValue):
    # + Returns +
    # -1 if move is not possible
    # 0 if turn played out normally
    # 1 if player awarded bonus roll
    # 2 if a piece reached home

    # retrieve player data
    pName = playerInfo[pID].name
    pStart = playerInfo[pID].startingCell
    pApproach = playerInfo[pID].approachCell

    # player's home straight
    # home straights and homes are;
    #       green: 65-69, 70
    #       yellow: 75-79, 80
    #       blue: 85-89, 90
    #       red: 95-99, 100
    pHome = 70 + 10*pID
    pHomeStrt = 65 + 10*pID

    currPos = tokens[pID][bID - 5].cellNum
    bDir = stdPath[currPos][2]
    bCount = stdPath[currPos][1]
    bName = blockName(pID, currPos)

    diceValue = max(diceValue // bCount, 1)

    if currPos < 52:
        # block is in stdPath
        nextPos = cellAtMove(currPos, diceValue, bDir)
        allowedPos = checkPath(currPos, diceValue, pID, bDir)

        if allowedPos == -1:
            # landing on block
            if stdPath[nextPos][1] != bCount:
                blocker = stdPath[nextPos][0]
                
                print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker].name}", end="")
                if stdPath[nextPos][1] == 1:
                    for token in tokens[blocker]:
                        if token.cellNum == nextPos:
                            print(f" piece {token.name}")
                else:  
                    print(f" block {blockName(blocker, nextPos)}")
                
                return -1
        
        elif allowedPos == currPos:
            # block in immediate cell
            blockLocation = cellAtMove(currPos, 1, bDir)
            blocker = stdPath[blockLocation][0]
            
            print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker].name} ", end="")
            if stdPath[blockLocation][1] == 1:
                for token in tokens[blocker]:
                    if token.cellNum == blockLocation:
                        print(f"piece {token.name}")
            else:  
                print(f"block {blockName(blocker, blockLocation)}")
            
            return -1
        
        elif allowedPos != nextPos:
            # moving to an adjacent cell coz of block
            blockLocation = cellAtMove(allowedPos, 1, bDir)
            blocker = stdPath[blockLocation][0]

            print(f"{pName} block {bName} is blocked from moving from {currPos} to {nextPos} by {playerInfo[blocker].name} block {blockName(blocker, blockLocation)} at square {blockLocation}")
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
                            stdPath[currPos][1] -= 1
                            print(f"\tBlock member {token.tokenName} is moving to Home Straight")
                            print(f"\t\t{token.tokenName} is {pHome - nextMemberPos} squares away from Home")
                        else:
                            # aint captured nun
                            print(f"\tBlock member {token.tokenName} hasn't captured any tokens, Cannot enter Home-Straight")

                # reset prev pos, if all tokens move out
                if stdPath[currPos][1] == 0:
                    stdPath[currPos] = [-1, -1, 0]
                    return 0
                else:
                    stdPath[currPos][2] = blockDirection(currPos, pID)
                    print(f"\tUpdating Block {blockName(pID, currPos)} Direction: {stdPath[currPos][2]}")
        #############################################################################################################
        m = moveBlock(currPos, nextPos, pID, bDir)
        if m == 3: return -1
        if m == 2: return 1
        return 0
    else:
        # shouldn't be able to come here anyway
        print("\n\n\n\n\n\n\t\t\t\t\t\tBLOCK IN HOME STRAIGHT???????")
        time.sleep(10)


def breakPlayerBlocks(pID):
    return # INCOMPLETE
    # possibilities
    # 1 block of 2
    # 2 blocks of 2
    # 1 block of 3
    # 1 block of 4
    
    blocks = [
        [-1,0,0,0],
        [-1,0,0,0]
    ] # location, count, clockwise, anticw

    for token in tokens[pID]:
        if stdPath[token.cellNum][1] > 1:
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


def playTurn(pID, roundNum, sixRepeats):
    # Returns
    # 0 - turn over
    # 1 - bonus roll for capture
    # 2 - player reached home
    # 6 - bonus roll for 6

    # retrieve player data
    pName = playerInfo[pID].name
    pHome = 70 + 10*pID

    diceValue = rollDice()
    print(f"\n{pName}'s Turn (Round {roundNum})")
    print(f"{pName} rolled {diceValue}")

    if diceValue == 6 and sixRepeats == 2:
        breakPlayerBlocks(pID)
        print(f"{pName} Player rolled three 6's in a row, Ignoring throw and moving on to the next player")
        return 0

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

            # else: # TEMPORARY FORCING PLAYERS TO FAVOR BLOCKS
            #     options.append(index)

        elif token.cellNum != 70 + 10*pID:
            # token in home straight
            options.append(index)

    if not options:
        # no options possible
        print(f"{pName} has no possible moves, Ignoring the throw and moving on to the next player")
        return 0

    playerChoice = tempPlayerAI(options)

    if playerChoice < 4:
        # picked a token
        choiceRes = tokenTurn(pID, playerChoice, diceValue)
    else:
        # picked a block
        choiceRes = blockTurn(pID, playerChoice, diceValue)

    if choiceRes == -1:
        options.remove(playerChoice)
        while options and choiceRes == -1:
            print(f"{pName} is picking a different move")
            playerChoice = tempPlayerAI(options)

            if playerChoice < 4:
                # picked a token
                choiceRes = tokenTurn(pID, playerChoice, diceValue)
            else:
                # picked a block
                choiceRes = blockTurn(pID, playerChoice, diceValue)
            options.remove(playerChoice)

        if choiceRes == -1:
            print(f"{pName} has no possible moves, Ignoring the throw and moving to the next player")
            choiceRes = 0

    if diceValue == 6 and choiceRes != -1:
        # bonus roll for 6
        return 6
    if choiceRes == 1:
        # bonus roll for capture
        return 1
    if choiceRes == 2:
        # check win condition
        return 2
    return 0


def tempPlayerAI(options):
    return random.choice(options)

##################################################################################################

# data about players
playerInfo = [
    # name / color, starting cell, approach cell, inBase count, onBoard count, inHome count
    Player(GREEN + "Green" + RESET, 41, 39, 4, 0, 0),
    Player(YELLOW + "Yellow" + RESET, 2, 0, 4, 0, 0),
    Player(BLUE + "Blue" + RESET, 15, 13, 4, 0, 0),
    Player(RED + "Red" + RESET, 28, 26, 4, 0, 0),
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


def debugging():
    for i in range(52):
        if stdPath[i][1] == -1:
            continue
        if not (0 <= stdPath[i][1] <= 4):
            print("\n\n\nDEBUGGING: stdPath count out of range\n\n\n")
            stdPathView()
            time.sleep(25)


def stdPathView():
    print("\nStandard Path:")
    for i in range(52):
        if stdPath[i][2] == 1:
            ddd = '+'
        elif stdPath[i][2] == -1:
            ddd = '-'
        else:
            ddd = ' '
        print(f"{str(i + 1).zfill(2)} P:{stdPath[i][0] if stdPath[i][0] != -1 else ' '} | C:{stdPath[i][1] if stdPath[i][1] != -1 else ' '} | D:{ddd} \t", end="")

        if i != 0 and ((i + 1) % 4 == 0):
            print()
    return

def endOfRound(roundNum):
    print("\n==========================")
    print(f"End of Round {roundNum}")
    print("==========================")

    for p in range(4):
        if sleepTimer: time.sleep(0.3)
        print(f"{playerInfo[p].name} player now has {playerInfo[p].onBoard}/4 Pieces on the Board, {playerInfo[p].inBase}/4 Pieces in the Base\nand {playerInfo[p].inHome}/4 Pieces in their Home")
        print("==========================")
        print(f"Location of {playerInfo[p].name} Pieces")
        print("==========================")
        for t in tokens[p]:
            print(f"Piece {t.tokenName} [capt: {t.captured}, appr: {t.approachPass}, dir: {t.direction}] -> ", end="")
            if t.cellNum == -1:
                print("Base")
            elif t.cellNum == 70 + 10*p:
                print("Home")
            elif t.cellNum < 52:
                print(f"Cell {t.cellNum}")
            else:
                print(f"{playerInfo[p].name}|HomePath|{t.cellNum - (65 + 10*p)}")
        print("==========================\n")


def gameLoop(firstPlayer):
    roundNum = 1
    currPlayer = firstPlayer
    while True:
        print("\n==========================")
        print(f"Start of Round {roundNum}")
        print("==========================")
        for _ in range(4):
            sixRepeats = 0
            while True:
                if sleepTimer: time.sleep(0.5)
                turnRes = playTurn(currPlayer, roundNum, sixRepeats)

                if turnRes == 2:
                    # player reached home
                    if playerInfo[currPlayer].inHome == 4:
                        # win condition
                        endOfRound(roundNum)

                        print("#####################################")
                        print(f"{playerInfo[currPlayer].name} Player has all 4 Pieces in Home")
                        print(f"{playerInfo[currPlayer].name} Player Wins!!! Round: {roundNum}")
                        print("#####################################")

                        stdPathView()
                        return
                    else:
                        break
                
                if turnRes == 0:
                    # turn ended
                    break

                # keep track of consecutive sixes
                if turnRes == 6:
                    print(f"\n{playerInfo[currPlayer].name} Player is awarded a bonus roll for rolling 6")
                    sixRepeats += 1
                else:
                    print(f"\n{playerInfo[currPlayer].name} Player is awarded a bonus roll for capturing an opponent")
                    sixRepeats = 0

            # move on to next player, wrap around if needed
            currPlayer += 1
            currPlayer %= 4

        roundNum += 1
        if sleepTimer: time.sleep(0.75)
        endOfRound(roundNum)
        debugging()
        if sleepTimer: time.sleep(0.2)

def findStarting():
    first = -1
    maxVal = 0
    rolls = [0]*4
    print("Deciding who plays first\n")
    while first == -1:
        for i in range(4):
            roll = rollDice()
            print(f"{playerInfo[i].name} rolls {roll}")
            time.sleep(0.15)
            rolls[i] += roll
            if rolls[i] > maxVal:
                maxVal = rolls[i]
                first = i
            elif rolls[i] == maxVal:
                first = -1
        
        if first == -1:
            print("\nMultiple players rolled the same highest value, rerolling\n")
            time.sleep(0.5)

    time.sleep(0.5)
    print(f"\n{playerInfo[first].name} has the highest roll and will begin the game")
    print(f"The order of a single round will be {playerInfo[first].name}, {playerInfo[(first+1) % 4].name}, {playerInfo[(first+2) % 4].name}, {playerInfo[(first+3) % 4].name}")
    time.sleep(0.5)
    return first


def main():
    for i in range(4):
        # iterate over all players and display tokens
        print(f"\nThe {playerInfo[i].name} player has 4 Pieces named", end=" ")
        for pToken in tokens[i]:
            print(pToken.tokenName, end=" ")
    print("\n")
    time.sleep(0.4)

    firstPlayer = findStarting()
    # start actual game loop
    gameLoop(firstPlayer)


main()