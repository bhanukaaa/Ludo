#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "types.h"

// Dev Tools============================================

#include <unistd.h>

    // Use ANSI escape codes to colorize StdOut: 1 = True; 0 = False
    #define USE_COLOR_CODES 1

    // Use Sleep function to display StdOut messages line by line,
    // allowing game play to take a natural, readable pace
    // 1 = True; 0 = False
    #define SLEEP_TIMER 0

    // Display additional info for development purposes;
    // Check certain values for out of bounds errors
    #define DEV_MODE 0

void customSleep(float seconds) {
    if (SLEEP_TIMER) usleep(seconds * 1000000 * 0.5);
}

unsigned int seed;

// Data Arrays===========================================

Player players[4];   // player data
Piece tokens[4][4];  // 2D array of piece data
StdCell stdPath[52]; // data about stdPath cells for quick reference
HomeStrtCell homeStraights[4][5]; // data about home straights for quick reference

#define pHome 60
#define pHomeStrt 55

// Helper Functions======================================

short rollDice() {
    // simulates dice roll, returns num; 1-6
    return (rand() % 6) + 1;
}

bool flipCoin() {
    // simulates coin flip, returns bool/num; 1 or 0
    return (rand() % 2) + 1;
}

void blockName(short pID, short blockCell) {
    // displays the symbolic name of a block

    printf("|");
    for (int i = 0; i < 4; i++) {
        // iterate over all player pieces
        if (tokens[pID][i].cellNum != blockCell) continue;
        printf("%s|", tokens[pID][i].tokenName);
    }
}

void playerSummary(short pID) {
    // displays a summary of a given player's pieces

    Player player = players[pID];
    printf("%s Player now has %d/4 Pieces on the Board, and %d/4 Pieces in the Base", player.name, player.onBoard, player.inBase);
    if (player.inHome) {
        // any pieces in home
        printf(", and %d/4 Pieces in Home", player.inHome);
    }
    printf("\n");
}

short distanceTo(short src, short dest, bool clockwise) {
    // Returns;
    // absolute distance in spaces from source cell

    short dist = 0;
    if (src < dest) {
        // src is numerically lower / equal to dest
        // could also be wrap around when going anticlockwise
        //   eg; src 37, dest 41, clockwise = 4
        //   eg; src 2, dest 50, anticlockwise = 48(will adjust before return)
        dist = dest - src;
    } else {
        // src is greater than dest
        // could also be wrap around when going clockwise
        //   eg; src 41, dest 37, anticlockwise = 52 - 41 + 37 = 48(will adjust before return)
        //   eg; src 50, dest 2, clockwise = 52 - 50 + 2 = 4
        dist = (52 - src) + (dest);
    }

    if (clockwise) return dist; // clockwise distance
    else {
        // anticlockwise distance, adjusted
        // i.e; dist from 50->2 in clockwise, is 4 spaces
        //    ; dist from 2->50 in clockwise, is 48 spaces
        //    ; dist from 2->50 in anticlockwise, is 4 spaces
        //    ; therefore, dist from a->b(anti - cw) == b->a(clockwise)
        return 52 - dist;
    }
}

short cellAtMove(short src, short spaces, bool clockwise) {
    // Returns;
    // cell index after stdPath traversal of spaces

    if (clockwise) {
        src += spaces;
        // normalize to fit array index range
        src %= 52;
    } else {
        src -= spaces;
        if (src < 0) {
            // normalize to wrap around back from 52
            src = 52 + src;
        }
    }
    return src;
}

short checkPath(short src, short moves, short pID, bool clockwise) {
    // Returns;
    // furthest cell a token can go to in a path specified, checks for blocks
    // will return cell preceding block, IF dice roll takes token PAST the block
    // will return -1, if token is to land directly on opposing block
    // will return cellAtMove cell if no opposing block encountered
    
    short furthest = src;
    for (int m = 1; m <= moves; m++) {
        // iterate from 1 space to 'moves' spaces ahead
        short movedCell = cellAtMove(src, m, clockwise);

        if ((stdPath[movedCell].playerID == -1) || (stdPath[movedCell].playerID == pID)) {
            // cell is free or cell occupied by same color
            furthest = movedCell;

        } else if (stdPath[movedCell].count > 1) {
            // opposing block in checking cell
            if (m == moves) {
                // landing directly on block
                return -1;
            } else {
                // overshooting block, move to adjacent
                return furthest;
            }

        } else {
            // opposing piece capturable
            furthest = movedCell;
        }
    }
    return furthest;
}

bool blockDirection(short cell, short pID) {
    // Returns;
    // true or false, based on rule CS-4

    bool clockwise = false, anticw = false;

    for (int i = 0; i < 4; i++) {
        if (tokens[pID][i].cellNum != cell) continue;

        // find block member directions
        if (tokens[pID][i].clockwise) clockwise = true;
        else {
            if (!tokens[pID][i].approachPass) {
                // anticlockwise piece, that hasn't passed approach;
                // is always further away than clockwise
                return false;
            }
            anticw = true;
        }
    }

    short clockwiseDist, anticwDist;
    if (clockwise) clockwiseDist = distanceTo(cell, players[pID].approach, true);
    if (anticw) anticwDist = distanceTo(cell, players[pID].approach, false);

    if (clockwise && anticw) {
        // members of both directions exist
        if (clockwiseDist > anticwDist) return true;
        else return false;

    } else if (clockwise) {
        // only clockwise members exist
        return true;

    } else {
        // only anti-clockwise members exist
        return false;
    }
}

void resetPiece(short pID, short tID) {
    // reset piece attributes
    tokens[pID][tID].cellNum = -1;
    tokens[pID][tID].clockwise = true;
    tokens[pID][tID].captured = false;
    tokens[pID][tID].approachPass = false;
    tokens[pID][tID].bhawanaMultiplier = 0;
    tokens[pID][tID].kotuwaBrief = 0;

    // update inBase/onBoard counters
    players[pID].inBase += 1;
    players[pID].onBoard -= 1;
}

void setStdCell(short cell, short pID, short count, bool clockwise) {
    // sets stdPath cell data to values specified
    stdPath[cell].playerID = pID;
    stdPath[cell].count = count;
    stdPath[cell].clockwise = clockwise;
}

void resetStdCell(short cell) {
    // sets stdPath cell to default / "empty" state
    stdPath[cell].playerID = -1;
    stdPath[cell].count = 0;
    stdPath[cell].clockwise = true;
}

void capture(short cell, short capturerID, short tokenIDblockCell, short capturedID, bool block) {
    // updates tokens captured
    // DOES NOT change stdPath array

    char *capturerColor = players[capturerID].name;
    char *capturedColor = players[capturedID].name;

    if (block) {
        printf("\t%s block ", capturerColor);
        blockName(capturerID, tokenIDblockCell);
        printf(" lands on square %hd, captures %s block ", cell, capturedColor);
        blockName(capturedID, cell);
        printf(" and returns it to Base\n");
    }

    for (int i = 0; i < 4; i++) {
        if (tokens[capturedID][i].cellNum != cell) continue;

        // in capturing cell
        resetPiece(capturedID, i);

        if (!block) {
            printf("\t%s piece %s lands on square %hd, captures %s piece %s, and returns it to Base\n", capturerColor, tokens[capturerID][tokenIDblockCell].tokenName, cell, capturedColor, tokens[capturedID][i].tokenName);
            break;
        }
    }

    playerSummary(capturedID);
}

// Movement Functions====================================

short moveToken(short src, short dest, short pID, short tID, bool clockwise) {
    // Returns;
    // 0 - moved successfully to a free cell
    // 1 - moved successfully to cell occupied by same color, forming block
    // 2 - moved successfully to cell occupied by opposing color, capturing opponent
    // 3 - failed to move to cell due to opposing block

    // data for stdOut
    short dist;
    char *directionStr = clockwise ? "clockwise" : "anti-clockwise";
    
    bool prevBDir; // in case piece moves back to src

    if (0 <= src && src < 52) {
        // prev position in stdPath
        stdPath[src].count -= 1;

        if (stdPath[src].count == 0) {
            // prev position now empty
            resetStdCell(src);
        } else {
            // update block direction for prev position
            bool prevBDir = stdPath[src].clockwise;
            stdPath[src].clockwise = blockDirection(src, pID);
        }

        // data for stdOut
        dist = distanceTo(src, dest, clockwise);
    }

    // moving player / token data
    char *pName = players[pID].name;
    char *tName = tokens[pID][tID].tokenName;

    if (stdPath[dest].playerID == -1) {
        // moving to free cell
        if (src == -1) {
            // moving from stdPath
            printf("%s moves piece %s from the Base to the Starting Point (%hd)\n", pName, tName, dest);
        } else {
            // moving from base
            printf("%s moves piece %s from location %hd to %hd by %hd units in %s direction\n", pName, tName, src, dest, dist, directionStr);
        }

        // update new stdPath and token data
        setStdCell(dest, pID, 1, clockwise);
        tokens[pID][tID].cellNum = dest;
        return 0;
    }

    if (stdPath[dest].playerID == pID) {
        // occupied by same color
        if (src == -1) {
            // moving from stdPath
            printf("%s moves piece %s from the Base to the Starting Point (%hd)\n", pName, tName, dest);
        } else {
            // moving from base
            printf("%s moves piece %s from location %hd to %hd by %hd units in %s direction\n", pName, tName, src, dest, dist, directionStr);
        }

        printf("\tMerging with ");
        blockName(pID, dest);

        // update new stdPath and token data
        stdPath[dest].count += 1;
        tokens[pID][tID].cellNum = dest;
        stdPath[dest].clockwise = blockDirection(dest, pID);

        printf(" to form block ");
        blockName(pID, dest);
        printf("\n");
        return 1;
    }

    // occupied by opposing color
    if (stdPath[dest].count == 1) {
        // can capture
        if (src == -1) {
            // moving from stdPath
            printf("%s moves piece %s from the Base to the Starting Point (%hd)\n", pName, tName, dest);
        } else {
            // moving from base
            printf("%s moves piece %s from location %hd to %hd by %hd units in %s direction\n", pName, tName, src, dest, dist, directionStr);
        }

        // capture opposing token
        capture(dest, pID, tID, stdPath[dest].playerID, false);

        // update new stdPath and token data
        setStdCell(dest, pID, 1, clockwise);
        tokens[pID][tID].captured = true;
        tokens[pID][tID].cellNum = dest;
        return 2;
    }

    // cant capture
    short blockingID = stdPath[dest].playerID;
    if (src != -1) {
        if (stdPath[src].playerID == -1) {
            // re-occupy prev pos
            setStdCell(src, pID, 1, clockwise);
        } else {
            // add back to block
            stdPath[src].count += 1;
            stdPath[src].clockwise = prevBDir;
        }
        printf("%s piece %s is blocked from moving from %hd to %hd, by %s block ", pName, tName, src, dest, players[blockingID].name);
        blockName(blockingID, dest);
        printf("\n");

    } else {
        printf("%s piece %s is blocked from moving from the Base to Starting Point (%hd), by %s block ", pName, tName, dest, players[blockingID].name);
        blockName(blockingID, dest);
        printf("\n");
    }
    return 3;
}

short moveBlock(short src, short dest, short pID, bool clockwise) {
    // Returns;
    // 0 - moved successfully to a free cell
    // 1 - moved successfully to cell occupied by same color, forming larger block
    // 2 - moved successfully to cell occupied by opposing color, capturing opponent
    // 3 - failed to move to cell due to opposing block

    // moving player data / block data
    char *pName = players[pID].name;
    short size = stdPath[src].count;

    // data for stdOut
    short dist = distanceTo(src, dest, clockwise);
    char *directionStr = clockwise ? "clockwise" : "anti-clockwise";

    // update prev position
    resetStdCell(src);

    // moving to free cell
    if (stdPath[dest].playerID == -1) {
        printf("%s moves block ", pName);
        blockName(pID, src);
        printf(" from location %hd to %hd by %hd units in %s direction\n", src, dest, dist, directionStr);

        // update new stdPath and token data
        setStdCell(dest, pID, size, clockwise);
        for (int i = 0; i < 4; i++) {
            if (tokens[pID][i].cellNum != src) continue;
            tokens[pID][i].cellNum = dest;
        }
        return 0;
    }

    // occupied by same color
    if (stdPath[dest].playerID == pID)
    {
        printf("%s moves block ", pName);
        blockName(pID, src);
        printf(" from location %hd to %hd by %hd units in %s direction\n", src, dest, dist, directionStr);

        printf("\tMerging with ");
        blockName(pID, dest);

        // update new stdPath and token data
        stdPath[dest].count += size;
        for (int i = 0; i < 4; i++) {
            if (tokens[pID][i].cellNum != src) continue;
            tokens[pID][i].cellNum = dest;
        }
        stdPath[dest].clockwise = blockDirection(dest, pID);

        printf(" to form block ");
        blockName(pID, dest);
        printf("\n");
        return 1;
    }

    // occupied by opposing color
    if (stdPath[dest].count == size || stdPath[dest].count == 1) {
        // can capture

        printf("%s moves block ", pName);
        blockName(pID, src);
        printf(" from location %hd to %hd by %hd units in %s direction\n", src, dest, dist, directionStr);

        // capture opposing token
        capture(dest, pID, src, stdPath[dest].playerID, true);

        // update new stdPath and token data
        setStdCell(dest, pID, size, clockwise);
        for (int i = 0; i < 4; i++) {
            if (tokens[pID][i].cellNum != src) continue;

            if (stdPath[dest].count != 1) {
                // block capturing single piece;
                // does not count as capture for members
                tokens[pID][i].captured = true;
            } 
            tokens[pID][i].cellNum = dest;
        }
        return 2;
    }

    // cant capture
    short blockingID = stdPath[dest].playerID;

    // re-occupy prev pos
    setStdCell(src, pID, size, clockwise);

    printf("%s block ", pName);
    blockName(pID, src);
    printf(" is blocked from moving from %hd to %hd, by %s block ", src, dest, players[blockingID].name);
    blockName(blockingID, dest);
    printf("\n");
    return 3;
}

short teleport(short src, short dest, short pID, short mID, char *srcName, char *destName) {
    // Returns;
    // 0 - moved successfully to a free cell
    // 1 - moved successfully to cell occupied by same color, forming larger block
    // 2 - moved successfully to cell occupied by opposing color, capturing opponent
    // 3 - failed to move to cell due to opposing block

    // teleporting player data / block data
    char *pName = players[pID].name;
    short size = stdPath[src].count;
    bool clockwise = stdPath[src].clockwise;

    // update prev position
    resetStdCell(src);

    // moving to free cell
    if (stdPath[dest].playerID == -1) {
        printf("\t%s teleports ", pName);
        blockName(pID, src);
        printf(" from location %s (%hd) to %s (%hd)\n", srcName, src, destName, dest);

        // update new stdPath and token data
        setStdCell(dest, pID, size, clockwise);
        for (int i = 0; i < 4; i++) {
            if (tokens[pID][i].cellNum != src) continue;
            tokens[pID][i].cellNum = dest;
        }
        return 0;
    }

    // occupied by same color
    if (stdPath[dest].playerID == pID) {
        printf("\t%s teleports ", pName);
        blockName(pID, src);
        printf(" from location %s (%hd) to %s (%hd)\n", srcName, src, destName, dest);

        printf("\tMerging with ");
        blockName(pID, dest);

        // update new stdPath and token data
        stdPath[dest].count += size;
        for (int i = 0; i < 4; i++) {
            if (tokens[pID][i].cellNum != src) continue;
            tokens[pID][i].cellNum = dest;
        }
        stdPath[dest].clockwise = blockDirection(dest, pID);

        printf(" to form block ");
        blockName(pID, dest);
        printf("\n");
        return 1;
    }

    // occupied by opposing color
    if (stdPath[dest].count == size || stdPath[dest].count == 1) {
        // can capture

        printf("\t%s teleports ", pName);
        blockName(pID, src);
        printf(" from location %s (%hd) to %s (%hd)\n", srcName, src, destName, dest);

        // capture opposing token
        capture(dest, pID, src, stdPath[dest].playerID, true);

        // update new stdPath and token data
        setStdCell(dest, pID, size, clockwise);
        for (int i = 0; i < 4; i++) {
            if (tokens[pID][i].cellNum != src) continue;

            if (stdPath[dest].count != 1) {
                // block capturing single piece;
                // does not count as capture for members
                tokens[pID][i].captured = true;
            }
            tokens[pID][i].cellNum = dest;
        }
        return 2;
    }

    // cant capture
    short blockingID = stdPath[dest].playerID;

    // re-occupy prev pos
    setStdCell(src, pID, size, clockwise);

    printf("\t%s is blocked from teleporting from %s (%hd) to %s (%hd), by %s block ", players[pID].name, srcName, src, destName, dest, players[blockingID].name);
    blockName(blockingID, dest);
    printf("\n");
    return 3;
}

// Mystery Handlers======================================

void bhawana(short pID, short mID, short mCell) {
    // applies bhawana effect to pieces at mystery cell and teleports them to cell 9

    bool bhawanaEffect = flipCoin();
    for (int i = 0; i < 4; i++) {
        // iterate over all player pieces
        Piece *token = &tokens[pID][i];
        if (token->cellNum != mCell) continue;

        // apply effect if piece is in mystery cell
        printf("\t%s piece %s teleported to Bhawana\n", players[pID].name, token->tokenName);
        if (bhawanaEffect) {
            printf("\t%s piece %s feels energized, and movement speed doubles\n", players[pID].name, token->tokenName);
            token->bhawanaMultiplier = 4;
        } else {
            printf("\t%s piece %s feels sick, and movement speed halves\n", players[pID].name, token->tokenName);
            token->bhawanaMultiplier = -4;
        }
    }
    // teleport after applying effects, so that any pieces already at dest don't get any effects
    teleport(mCell, 9, pID, mID, "Mystery Cell", "Bhawana");
}

void kotuwa(short pID, short mID, short mCell, bool fromPitaKotuwa) {
    // applies kotuwa effects to pieces at mystery cell and then teleports them to cell 27

    for (int i = 0; i < 4; i++) {
        // iterate over all player pieces
        Piece *token = &tokens[pID][i];
        if (token->cellNum != mCell) continue;

            // apply effect if piece is in mystery cell
            printf("\t%s piece %s teleported to Kotuwa\n", players[pID].name, token->tokenName);
            token->kotuwaBrief = 4;
            players[pID].restricted += 1;

            printf("\t%s piece %s attends briefing and cannot move for four rounds\n", players[pID].name, token->tokenName);
    }

    // teleport after applying effects, so that any pieces already at dest don't get any effects
    if (fromPitaKotuwa)  teleport(mCell, 27, pID, mID, "Pita-Kotuwa", "Kotuwa");
    else teleport(mCell, 27, pID, mID, "Mystery Cell", "Kotuwa");
}

void kotuwaBreak(short pID) {
    // sends pieces in briefing, in kotuwa to base

    for (int i = 0; i < 4; i++) {
        // iterate over all player pieces
        Piece *token = &tokens[pID][i];
        if (token->cellNum != 27 || token->kotuwaBrief == 0) continue;

        // send to base if piece is movement restricted and in kotuwa
        stdPath[27].count -= 1;
        resetPiece(pID, i);
        players[pID].restricted -= 1;

        printf("\n\t%s piece %s is movement-restricted and has rolled three consecutively\n", players[pID].name, token->tokenName);
        printf("\tTeleporting piece %s to Base\n", token->tokenName);
    }

    // reset stdPath cell if now empty
    if (stdPath[27].count == 0) resetStdCell(27);

    playerSummary(pID);
}

void pitaKotuwa(short pID, short mID, short mCell) {
    // applies pitakotuwa effects to pieces in mystery cell, and teleports them to cell 46

    if (mID > 3) {
        // special handling for blocks
        bool blockCW = stdPath[mCell].clockwise;
        printf("\tThe %s block ", players[pID].name);
        blockName(pID, mCell);

        if (blockCW) {
            // reverse block direction
            printf(", which was moving clockwise, has changed to moving counter-clockwise\n");
            printf("\tTeleporting to Kotuwa from Pita-Kotuwa");

            teleport(mCell, 46, pID, mID, "Mystery Cell", "Pita-Kotuwa");
            stdPath[mCell].clockwise = false;
        } else {
            // send block to kotuwa
            printf(" is moving in a counter-clockwise direction\n");
            printf("\tTeleporting to Kotuwa from Pita-Kotuwa");

            kotuwa(pID, mID, mCell, true);
        }
        return;
    }

    for (int i = 0; i < 4; i++) {
        // iterate over all player pieces
        Piece *token = &tokens[pID][i];
        if (token->cellNum != mCell) continue;

        // apply effect if piece is in mystery cell
        printf("\t%s piece %s teleported to Pita-Kotuwa\n", players[pID].name, token->tokenName);

        if (token->clockwise) {
            // clockwise pieces, turn anticlockwise
            token->clockwise = false;
            printf("\tThe %s piece %s, which was moving clockwise, has changed to moving counter-clockwise\n", players[pID].name, token->tokenName);
        } else {
            // anticlockwise pieces, go to kotuwa
            printf("\tThe %s piece %s is moving in a counter-clockwise direction\n", players[pID].name, token->tokenName);
            printf("\tTeleporting to Kotuwa from Pita-Kotuwa");
            kotuwa(pID, mID, mCell, true);
            return;
        }
    }
    // teleport after applying effects, so that any pieces already at dest don't get any effects
    teleport(mCell, 46, pID, mID, "Mystery Cell", "Pita-Kotuwa");
}

void mysteryToBase(short pID, short mID, short mCell) {
    // send pieces in mystery cell to base

    for (int i = 0; i < 4; i++) {
        // iterate over all player pieces
        Piece *token = &tokens[pID][i];
        if (token->cellNum != mCell) continue;

        // send to base if piece is in mystery cell
        printf("\t%s piece %s teleported to Base\n", players[pID].name, token->tokenName);
        resetPiece(pID, i);
    }

    resetStdCell(mCell);
    playerSummary(pID);
}

void landMystery(short pID, short mID, short mCell) {
    // applies mystery effect to piece/block and teleports to respective destination

    short size = stdPath[mCell].count; // to check for collisions
    short mystery = rollDice(); 

    printf("%s player lands on a mystery cell and is teleported to ", players[pID].name);
    switch (mystery) {
        case 1:
            // teleport to Bhawana
            printf("Bhawana\n");
            if (stdPath[9].count <= 1 || (size != 1 && stdPath[9].count == size)) bhawana(pID, mID, mCell);
            else {
                // error message outside function to prevent effect application
                printf("%s is blocked from teleporting to Bhawana by %s block ", players[pID].name, players[stdPath[9].playerID].name);
                blockName(stdPath[9].playerID, 9);
            }
            break;

        case 2:
            // teleport to Kotuwa
            printf("Kotuwa\n");
            if (stdPath[27].count <= 1 || (size != 1 && stdPath[27].count == size)) kotuwa(pID, mID, mCell, false);
            else {
                // error message outside function to prevent effect application
                printf("%s is blocked from teleporting to Kotuwa by %s block ", players[pID].name, players[stdPath[27].playerID].name);
                blockName(stdPath[27].playerID, 9);
            }
            break;

        case 3:
            // teleport to Pita-Kotuwa
            printf("Pita-Kotuwa\n");
            if (stdPath[46].count <= 1 || (size != 1 && stdPath[46].count == size)) pitaKotuwa(pID, mID, mCell);
            else {
                // error message outside function to prevent effect application
                printf("%s is blocked from teleporting to Bhawana by %s block ", players[pID].name, players[stdPath[46].playerID].name);
                blockName(stdPath[46].playerID, 9);
            }
            break;

        case 4:
            // teleport to Base
            printf("Base\n");
            mysteryToBase(pID, mID, mCell);
            break;

        case 5:
            // teleport to Starting
            printf("X\n");
            teleport(mCell, players[pID].starting, pID, mID, "Mystery Cell", "Starting Cell");
            break;

        case 6:
            // teleport to Approach
            printf("Approach\n");
            teleport(mCell, players[pID].approach, pID, mID, "Mystery Cell", "Approach Cell");
    }
}

// Piece/Block Handlers==================================

short tokenTurn(short pID, short tID, short diceValue, short mysteryCell) {
    // Returns;
    // -1 if move is not possible
    // 0 if turn played out normally
    // 1 if player awarded bonus roll
    // 2 if a piece reached home

    // player data
    char *pName = players[pID].name;
    short pStart = players[pID].starting;
    short pApproach = players[pID].approach;

    // player's home straight
    // home straights and homes are; 95-99, 100

    // token data
    short currPos = tokens[pID][tID].cellNum;
    char *tName = tokens[pID][tID].tokenName;
    bool tDir = tokens[pID][tID].clockwise;
    bool tCapt = tokens[pID][tID].captured;
    bool tAppP = tokens[pID][tID].approachPass;
    short tBhawMul = tokens[pID][tID].bhawanaMultiplier;
    short tKotuBr = tokens[pID][tID].kotuwaBrief;

    // token in home
    if (currPos == pHome) return -1;

    if (tKotuBr > 0) {
        // kotuwa effects
        printf("%s piece %s is attending a briefing and cannot move for the next %hd rounds\n", pName, tName, tKotuBr);
        return -1;
    }

    short m; // return value for move functions

    // token is in base
    if (currPos == -1 && diceValue == 6) {
        m = moveToken(-1, pStart, pID, tID, true);

        if (m == 3) return -1;

        // prev piece memo for blue player
        if (pID == 2) players[2].prevPiece = tID;

        printf("\tFlipping Coin to Pick Direction\n");
        bool coinVal = flipCoin();

        if (coinVal) printf("\tHeads, %s will move Clockwise\n", tName);
        else {
            printf("\tTails, %s will move Anti-Clockwise\n", tName);
            tokens[pID][tID].clockwise = false;
        }

        // update block direction, is block was formed
        if (m == 1) stdPath[pStart].clockwise = blockDirection(pStart, pID);

        // update inbase/onBoard counters
        players[pID].inBase -= 1;
        players[pID].onBoard += 1;

        playerSummary(pID);

        // check mystery cell collision
        if (pStart == mysteryCell) landMystery(pID, tID, mysteryCell);

        // award bonus roll for capture
        if (m == 2) return 1;
        return 0;
    }

    // bhawana effects
    if (tBhawMul > 0) {
        printf("%s piece %s is feeling energized, and movement speed doubles\n", pName, tName);
        diceValue *= 2;
    } else if (tBhawMul < 0) {
        printf("%s piece %s is feeling sick, and movement speed halves\n", pName, tName);
        diceValue /= 2;
    }

    // piece is in stdPath
    if (0 <= currPos && currPos < 52) {
        // find next position
        short nextPos = cellAtMove(currPos, diceValue, tDir);

        // check if path to next position is clear
        short allowedPos = checkPath(currPos, diceValue, pID, tDir);
        if (allowedPos == -1) {
            // not allowed to move due to landing on block
            short blocker = stdPath[nextPos].playerID;
            printf("%s piece %s is blocked from moving from %hd to %hd by %s block ", pName, tName, currPos, nextPos, players[blocker].name);
            blockName(blocker, nextPos);
            printf(" at square %hd\n", nextPos);
            return -1;
        }

        if (allowedPos == currPos) {
            // block in immediate cell
            short blockLocation = cellAtMove(currPos, 1, tDir);
            short blocker = stdPath[blockLocation].playerID;
            printf("%s piece %s is blocked from moving from %hd to %hd by %s block ", pName, tName, currPos, nextPos, players[blocker].name);
            blockName(blocker, blockLocation);
            printf(" at square %hd\n", blockLocation);
            return -1;
        }

        if (allowedPos != nextPos) {
            // moving to an adjacent cell coz of block
            short blockLocation = cellAtMove(allowedPos, 1, tDir);
            short blocker = stdPath[blockLocation].playerID;
            printf("%s piece %s is blocked from moving from %hd to %hd by %s block ", pName, tName, currPos, nextPos, players[blocker].name);
            blockName(blocker, blockLocation);
            printf(" at square %hd\n", blockLocation);
            printf("\tMoving piece %s to square %hd which is the cell before the block\n", tName, allowedPos);
        }

        nextPos = allowedPos;

        // check if passing approach
        short distToApproach = distanceTo(currPos, pApproach, tDir);
        short distToNextPos = distanceTo(currPos, nextPos, tDir);

        if (distToApproach < distToNextPos) {
            // roll takes us past approach cell

            if (tDir || tAppP > 0) {
                // travelling clockwise or passed approach when anticw

                if (tCapt > 0) {
                    // captured at least 1 piece
                    nextPos = pHomeStrt;
                    nextPos += diceValue - distToApproach - 1; // -1 coz going from approach to home straight

                    if (nextPos > pHome) {
                        // over shoots home
                        printf("%s piece %s over-shoots home\n", pName, tName);
                        return -1;
                    }

                    // prev piece memo for blue player
                    if (pID == 2) players[2].prevPiece = tID;

                    // update stdPath data
                    stdPath[currPos].count -= 1;
                    if (stdPath[currPos].count == 0) resetStdCell(currPos);
                    else stdPath[currPos].clockwise = blockDirection(currPos, pID);

                    if (nextPos == pHome) {
                        // going home directly
                        tokens[pID][tID].cellNum = pHome;

                        // update onBoard/inHome counters
                        players[pID].onBoard -= 1;
                        players[pID].inHome += 1;

                        printf("%s piece %s has reached Home\n", pName, tName);
                        playerSummary(pID);
                        return 2;
                    }

                    // update token data
                    tokens[pID][tID].cellNum = nextPos;

                    // update home straight data
                    homeStraights[pID][nextPos - pHomeStrt].count += 1;

                    printf("%s piece %s is moving to Home Straight\n", pName, tName);
                    printf("\t%s is %hd squares away from Home\n", tName, pHome - nextPos);
                    return 0;
                }
                // no captures
                printf("%s piece %s hasn't captured any pieces, Cannot enter Home-Straight\n", pName, tName);
            }

            // move straight on past approach
            m = moveToken(currPos, nextPos, pID, tID, tDir);
            if (m == 3) return -1;

            // approach pass counter for anti clockwise pieces
            tokens[pID][tID].approachPass = true;

            // prev piece memo for blue player
            if (pID == 2) players[2].prevPiece = tID;

            // check mystery cell collision
            if (nextPos == mysteryCell) landMystery(pID, tID, mysteryCell);

            if (m == 2) return 1;
        } else {
            // regular stdPath move without passing approach
            m = moveToken(currPos, nextPos, pID, tID, tDir);
            if (m == 3) return -1;

            // prev piece memo for blue player
            if (pID == 2) players[2].prevPiece = tID;

            // check mystery cell collision
            if (nextPos == mysteryCell) landMystery(pID, tID, mysteryCell);

            if (m == 2) return 1;
        }
        return 0;
    }

    // token is in home straight
    short spacesLeft = pHome - currPos;

    if (diceValue < spacesLeft) {
        // moving up home straight
        short nextPos = currPos + diceValue;
        tokens[pID][tID].cellNum = nextPos;

        // update home straight data
        homeStraights[pID][currPos - pHomeStrt].count -= 1;
        homeStraights[pID][nextPos - pHomeStrt].count += 1;

        printf("%s piece %s is moving up the Home Straight\n", pName, tName);
        printf("\t%s is %hd squares away from Home\n", tName, pHome - nextPos);

        // prev piece memo for blue player
        if (pID == 2) players[2].prevPiece = tID;
        return 0;

    } else if (diceValue == spacesLeft || spacesLeft == 0) {
        // going home
        tokens[pID][tID].cellNum = pHome;

        // update onBoard/inHome counters
        players[pID].onBoard -= 1;
        players[pID].inHome += 1;

        // update home straight data
        homeStraights[pID][currPos - pHomeStrt].count -= 1;

        printf("%s piece %s has reached Home\n", pName, tName);
        playerSummary(pID);

        // prev piece memo for blue player
        if (pID == 2) players[2].prevPiece = tID;

        return 2;
    }

    // over shoots home
    printf("%s piece %s over-shoots home; Rolled %hd while %hd from Home\n", pName, tName, diceValue, spacesLeft);
    return -1;
}

short blockTurn(short pID, short bID, short diceValue, short mysteryCell) {
    // Returns;
    // -1 if move is not possible
    // 0 if turn played out normally
    // 1 if player awarded bonus roll
    // 2 if a piece reached home

    // player data
    char *pName = players[pID].name;
    short pStart = players[pID].starting;
    short pApproach = players[pID].approach;

    // player's home straight
    // home straights and homes are; 95-99, 100

    // block data
    short currPos = tokens[pID][bID - 4].cellNum;
    short bSize;
    
    if (currPos < 52) bSize = stdPath[currPos].count;
    else bSize = homeStraights[pID][currPos - pHomeStrt].count;

    if (diceValue < bSize) {
        printf("%s tries to move block ", pName);
        blockName(pID, currPos);
        printf("\n\tDice roll of %hd is not sufficient to move block of size %hd\n", diceValue, bSize);
        return -1;
    }

    diceValue /= bSize; // block movement division
    short m; // return value for move function

    if (currPos < 52) {
        // block is in stdPath
        bool bClockwise = stdPath[currPos].clockwise;

        // find next position
        short nextPos = cellAtMove(currPos, diceValue, bClockwise);

        // check if path to next position is clear
        short allowedPos = checkPath(currPos, diceValue, pID, bClockwise);

        if (allowedPos == -1) {
            // not allowed to move due to landing on block
            short blocker = stdPath[nextPos].playerID;

            printf("%s block ", pName);
            blockName(pID, currPos);
            printf(" is blocked from moving from %hd to %hd by %s block ", currPos, nextPos, players[blocker].name);
            blockName(blocker, nextPos);
            printf(" at square %hd\n", nextPos);
            return -1;
        }

        if (allowedPos == currPos) {
            // block in immediate cell
            short blockLocation = cellAtMove(currPos, 1, bClockwise);
            short blocker = stdPath[blockLocation].playerID;
            printf("%s block ", pName);
            blockName(pID, currPos);
            printf(" is blocked from moving from %hd to %hd by %s block ", currPos, nextPos, players[blocker].name);
            blockName(blocker, blockLocation);
            printf(" at square %hd\n", blockLocation);
            return -1;
        }

        if (allowedPos != nextPos) {
            // moving to an adjacent cell coz of block
            short blockLocation = cellAtMove(allowedPos, 1, bClockwise);
            short blocker = stdPath[blockLocation].playerID;
            printf("%s block ", pName);
            blockName(pID, currPos);
            printf(" is blocked from moving from %hd to %hd by %s block ", currPos, nextPos, players[blocker].name);
            blockName(blocker, blockLocation);
            printf(" at square %hd\n", blockLocation);
            printf("\tMoving block ");
            blockName(pID, currPos);
            printf(" to square %hd which is the cell before the block\n", allowedPos);
        }

        nextPos = allowedPos;

        // check if passing approach
        short distToApproach = distanceTo(currPos, pApproach, bClockwise);
        short distToNextPos = distanceTo(currPos, nextPos, bClockwise);

        if (distToApproach < distToNextPos) {
            // block can only move to approach if ALL members are eligible
            bool eligible = true;

            for (int i = 0; i < 4; i++) {
                // iterate over all player pieces
                if (tokens[pID][i].cellNum != currPos) continue;

                if (!tokens[pID][i].captured) {
                    // no captures
                    eligible = false;
                    break;
                }

                if (!tokens[pID][i].clockwise && !tokens[pID][i].approachPass) {
                    // anticlockwise piece, w/o approach passes
                    eligible = false;
                    break;
                }
            }

            if (eligible) {
                // block moving to home straight
                nextPos = pHomeStrt;
                nextPos += diceValue - distToApproach - 1;

                // update token data
                for (int i = 0; i < 4; i++) {
                    if (tokens[pID][i].cellNum != currPos) continue;
                    tokens[pID][i].cellNum = nextPos;
                }

                // update home straight data
                homeStraights[pID][nextPos - pHomeStrt].count += bSize;

                // reset prev position on stdPath
                resetStdCell(currPos);

                printf("%s block ", pName);
                blockName(pID, nextPos);
                printf(" is moving to Home-Straight\n\t");
                blockName(pID, nextPos);
                printf(" is %hd squares away from Home\n", pHome - nextPos);

                return 0;
            }
            else {
                // block moving past home straight
                printf("%s block ", pName);
                blockName(pID, currPos);
                printf(" is not eligible to enter Home-Straight\n\tMoving straight on past Approach Cell\n");

                // update approach pass for all members
                for (int i = 0; i < 4; i++) {
                    if (tokens[pID][i].cellNum != currPos) continue;
                    tokens[pID][i].approachPass = true;
                }
            }
        }
        m = moveBlock(currPos, nextPos, pID, bClockwise);
        if (m == 3) return -1;

        // prev piece memo for blue player;
        // marking "leader" of block as piece moved
        if (pID == 2) players[2].prevPiece = bID - 4;

        // check mystery cell collision
        if (nextPos == mysteryCell) landMystery(pID, bID, mysteryCell);

        if (m == 2) return 1;
        return 0;
    }

    // block is in home straight
    short spacesLeft = pHome - currPos;

    if (diceValue < spacesLeft) {
        // moving up home straight

        short nextPos = currPos + diceValue;
        for (int i = 0; i < 4; i++) {
            // update block members
            if (tokens[pID][i].cellNum != currPos) continue;
            tokens[pID][i].cellNum = nextPos;
        }

        // update home straight data
        homeStraights[pID][currPos - pHomeStrt].count -= bSize;
        homeStraights[pID][nextPos - pHomeStrt].count += bSize;

        printf("%s block ", pName);
        blockName(pID, nextPos);
        printf(" is moving up the Home Straight\n\t");
        blockName(pID, nextPos);
        printf(" is %hd squares away from Home\n", pHome - nextPos);

        // prev piece memo for blue player
        if (pID == 2) players[2].prevPiece = bID - 4;
        return 0;

    } else if (diceValue == spacesLeft || spacesLeft == 0) {
        // going home
        printf("%s block ", pName);
        blockName(pID, currPos);
        printf(" has reached Home\n");

        for (int i = 0; i < 4; i++) {
            // update block members
            if (tokens[pID][i].cellNum != currPos) continue;
            tokens[pID][i].cellNum = pHome;
        }

        // update onBoard/inHome counters
        players[pID].onBoard -= bSize;
        players[pID].inHome += bSize;

        // update home straight data
        homeStraights[pID][currPos - pHomeStrt].count -= bSize;

        playerSummary(pID);

        // prev piece memo for blue player
        if (pID == 2) players[2].prevPiece = bID - 4;
        return 2;
    }

    // over shoots home
    printf("%s block ", pName);
    blockName(pID, currPos);
    printf(" over-shoots home; Tried to move %hd units while %hd from Home\n", diceValue, spacesLeft);
    return -1;
}

bool breakBlockHelperI(short blockA[6], short pID) {
    // Situation I: Single block of size 2

    if (blockA[4] > 0 && blockA[4] > blockA[5]) {
        // clockwise piece can move further
        for (int t = 0; t < 4; t++) {
            if (tokens[pID][t].cellNum != blockA[0]) continue;
            if (!tokens[pID][t].clockwise) continue;

            moveToken(blockA[0], cellAtMove(blockA[0], blockA[4], true), pID, t, true);
            return true;
        }
    } else if (blockA[5] > 0) {
        // anticlockwise piece can move further
        for (int t = 0; t < 4; t++) {
            if (tokens[pID][t].cellNum != blockA[0]) continue;
            if (tokens[pID][t].clockwise) continue;

            moveToken(blockA[0], cellAtMove(blockA[0], blockA[5], false), pID, t, false);
            return true;
        }
    }

    // no moves possible
    return false;
}

bool breakBlockHelperII(short blockA[6], short pID) {
    // Situation II: Single block of size 3

    // spread of moves; adding up to 6
    short moveOptions[3][2] = {
        {1, 5},
        {2, 4},
        {3, 3}
    };
    short moveIndex;

    for (int o = 0; o < 3; o++) {
        // iterate over all move spreads

        if (blockA[2] >= 2) {
            // move two clockwise pieces
            // check if move option is legal
            if (blockA[4] >= moveOptions[o][1]) {
                // flag to mark choice taken;
                // order does not matter if same direction
                moveIndex = 0;
                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;
                    if (!tokens[pID][t].clockwise) continue;

                    moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][moveIndex], true), pID, t, true);
                    moveIndex++; // next piece moves by other value in spread

                    // breakage complete if two pieces moved
                    if (moveIndex == 2) return true;
                }
            }
        }

        if (blockA[3] >= 2) {
            // move two anticlockwise pieces
            // check if move option is legal
            if (blockA[5] >= moveOptions[o][1]) {
                // flag to mark choice taken;
                // order does not matter if same direction
                moveIndex = 0;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;
                    if (tokens[pID][t].clockwise) continue;

                    moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][moveIndex], false), pID, t, false);
                    moveIndex++; // next piece moves by other value in spread

                    // breakage complete if two pieces moved
                    if (moveIndex == 2) return true;
                }
            }
        }

        if (blockA[2] >= 1 && blockA[3] >= 1) {
            // move one piece of each direction
            // check if move option is legal (clockwise first, anticw second)
            if (blockA[4] >= moveOptions[o][0] && blockA[5] >= moveOptions[o][1]) {
                // flags to mark if piece of direction was moved
                bool cwMoved = false, anticwMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;

                    if (!cwMoved && tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][0], true), pID, t, true);
                        cwMoved = true;
                    }
                    else if (!anticwMoved && !tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][1], false), pID, t, false);
                        anticwMoved = true;
                    }

                    // breakage complete if two pieces are moved
                    if (cwMoved && anticwMoved) return true;
                }
            }

            // check if move option is legal (anticw first, clockwise second)
            if (blockA[4] >= moveOptions[o][1] && blockA[5] >= moveOptions[o][0]) {
                // flags to mark if piece of direction was moved
                bool cwMoved = false, anticwMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;

                    if (!cwMoved && tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][1], true), pID, t, true);
                        cwMoved = true;
                    }
                    else if (!anticwMoved && !tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][0], false), pID, t, false);
                        anticwMoved = true;
                    }

                    // breakage complete if two pieces moved
                    if (cwMoved && anticwMoved) return true;
                }
            }
        }
    }
    return false;
}

bool breakBlockHelperIII(short blockA[6], short pID) {
    // Situation III: Single block of size 4

    short moveOptions[10][3] = {
        {1, 2, 3},
        {1, 3, 2},
        {2, 1, 3},
        {2, 3, 1},
        {3, 1, 2},
        {3, 2, 1},
        {1, 1, 4},
        {1, 4, 1},
        {4, 1, 1},
        {2, 2, 2}
    };
    short moveIndex;

    for (int o = 0; o < 10; o++) {
        if (blockA[2] >= 3) {
            // move 3 clockwise pieces
            // check if move is legal
            if (blockA[4] >= moveOptions[o][0] && blockA[4] >= moveOptions[o][1] && blockA[4] >= moveOptions[o][2]) {
                // flag to mark choice taken;
                // order does not matter if same direction
                moveIndex = 0;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;
                    if (!tokens[pID][t].clockwise) continue;

                    moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][moveIndex], true), pID, t, true);
                    moveIndex++; // next piece moves by other value in spread

                    // breakage complete if three pieces moved
                    if (moveIndex == 3) return true;
                }
            }
        }

        if (blockA[3] >= 3) {
            // move 3 anticlockwise pieces
            // check if move is legal
            if (blockA[5] >= moveOptions[o][0] && blockA[5] >= moveOptions[o][1] && blockA[5] >= moveOptions[o][2]) {
                // flag to mark choice taken;
                // order does not matter if same direction
                moveIndex = 0;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;
                    if (tokens[pID][t].clockwise) continue;

                    moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][moveIndex], false), pID, t, false);
                    moveIndex++; // next piece moves by other value in spread

                    // breakage complete if three pieces moved
                    if (moveIndex == 3) return true;
                }
            }
        }

        if (blockA[2] >= 2 && blockA[3] >= 1) {
            // move 2 clockwise & 1 anticlockwise pieces
            // check if move legal (2 clockwise first, 1 anticw third)
            if (blockA[4] >= moveOptions[o][0] && blockA[4] >= moveOptions[o][1] && blockA[5] >= moveOptions[o][2]) {
                // counter for number of clockwise pieces moved
                // also acts as index to pick move from spread
                short cwMove = 0;
                // flag to mark anticlockwise piece moved
                bool anticwMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;

                    if (cwMove < 2 && tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][cwMove], true), pID, t, true);
                        cwMove++;
                    }
                    else if (!anticwMoved && !tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][2], false), pID, t, false);
                        anticwMoved = true;
                    }

                    // breakage complete if three pieces moved
                    if (cwMove == 2 && anticwMoved) return true;
                }
            }
        }

        if (blockA[2] >= 1 && blockA[3] >= 2) {
            // move 1 clockwise & 2 anticlockwise pieces
            // check if move legal (2 anticw first, 1 clockwise third)
            if (blockA[5] >= moveOptions[o][0] && blockA[5] >= moveOptions[o][1] && blockA[4] >= moveOptions[o][2]) {
                // counter for number of anti-clockwise pieces moved
                // also acts as index to pick move from spread
                short anticwMove = 0;
                // flag to mark clockwise piece moved
                bool cwMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum != blockA[0]) continue;

                    if (!cwMoved && tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][2], true), pID, t, true);
                        cwMoved = true;
                    }
                    else if (anticwMove < 2 && !tokens[pID][t].clockwise) {
                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][anticwMove], false), pID, t, false);
                        anticwMove++;
                    }

                    // breakage complete if three pieces moved
                    if (cwMoved && anticwMove == 2) return true;
                }
            }
        }
    }
    return false;
}

bool breakBlockHelperIV(short blockA[6], short blockB[6], short pID) {
    // Situation IV: Two blocks of size 2

    // spread of moves; adding up to 6
    short moveOptions[5][2] = {
        {1, 5},
        {2, 4},
        {3, 3},
        {4, 2},
        {5, 1}
    };

    for (int o = 0; o < 5; o++) {
        if (blockA[2] >= 1 && blockB[2] >= 1) {
            // move clockwise piece of both blocks
            // check if move legal
            if (blockA[4] >= moveOptions[o][0] && blockB[4] >= moveOptions[o][1]) {
                // flags to mark piece moved for each block
                bool aMoved = false, bMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum == blockA[0]) {
                        if (aMoved) continue;
                        if (!tokens[pID][t].clockwise) continue;

                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][0], true), pID, t, true);
                        aMoved = true;
                    }
                    if (tokens[pID][t].cellNum == blockB[0]) {
                        if (bMoved) continue;
                        if (!tokens[pID][t].clockwise) continue;

                        moveToken(blockB[0], cellAtMove(blockB[0], moveOptions[o][1], true), pID, t, true);
                        bMoved = true;
                    }

                    // breakage complete if two pieces moved
                    if (aMoved && bMoved) return true;
                }
            }
        }

        if (blockA[3] >= 1 && blockB[3] >= 1) {
            // move anticw piece of both blocks
            // check if move legal
            if (blockA[5] >= moveOptions[o][0] && blockB[5] >= moveOptions[o][1]) {
                // flags to mark piece moved for each block
                bool aMoved = false, bMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum == blockA[0]) {
                        if (aMoved) continue;
                        if (tokens[pID][t].clockwise) continue;

                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][0], false), pID, t, false);
                        aMoved = true;
                    }
                    if (tokens[pID][t].cellNum == blockB[0]) {
                        if (bMoved) continue;
                        if (tokens[pID][t].clockwise) continue;

                        moveToken(blockB[0], cellAtMove(blockB[0], moveOptions[o][1], false), pID, t, false);
                        bMoved = true;
                    }

                    // breakage complete if two pieces moved
                    if (aMoved && bMoved) return true;
                }
            }
        }

        if (blockA[2] >= 1 && blockB[3] >= 1) {
            // move cw piece of block A & anticw piece of block B
            // check if move legal
            if (blockA[4] >= moveOptions[o][0] && blockB[5] >= moveOptions[o][1]) {
                // flags to mark piece moved for each block
                bool aMoved = false, bMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum == blockA[0]) {
                        if (aMoved) continue;
                        if (!tokens[pID][t].clockwise) continue;

                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][0], true), pID, t, true);
                        aMoved = true;
                    }
                    if (tokens[pID][t].cellNum == blockB[0]) {
                        if (bMoved) continue;
                        if (tokens[pID][t].clockwise) continue;

                        moveToken(blockB[0], cellAtMove(blockB[0], moveOptions[o][1], false), pID, t, false);
                        bMoved = true;
                    }

                    // breakage complete if two pieces moved
                    if (aMoved && bMoved) return true;
                }
            }
        }

        if (blockA[3] >= 1 && blockB[2] >= 1) {
            // move anticw piece of block A & cw piece of block B
            // check if move legal
            if (blockA[5] >= moveOptions[o][0] && blockB[4] >= moveOptions[o][1]) {
                // flags to mark piece moved for each block
                bool aMoved = false, bMoved = false;

                for (int t = 0; t < 4; t++) {
                    // iterate over player pieces
                    if (tokens[pID][t].cellNum == blockA[0]) {
                        if (aMoved) continue;
                        if (tokens[pID][t].clockwise) continue;

                        moveToken(blockA[0], cellAtMove(blockA[0], moveOptions[o][0], false), pID, t, false);
                        aMoved = true;
                    }
                    if (tokens[pID][t].cellNum == blockB[0]) {
                        if (bMoved) continue;
                        if (!tokens[pID][t].clockwise) continue;

                        moveToken(blockB[0], cellAtMove(blockB[0], moveOptions[o][1], true), pID, t, true);
                        bMoved = true;
                    }

                    // breakage complete if two pieces moved
                    if (aMoved && bMoved) return true;
                }
            }
        }
    }
    return false;
}

void breakPlayerBlocks(short pID) {
    // attempts to break all blocks of a player
    // by moving necessary pieces by 6 units cumulatively

    // location, count, clockwise, anticlockwise, maxCW, maxAntiCW
    short blockA[6] = {-1,0,0,0,0,0};
    short blockB[6] = {-1,0,0,0,0,0};

    // identify player blocks
    for (int i = 0; i < 4; i++) {
        Piece token = tokens[pID][i];
        if (token.cellNum >= 52 || token.cellNum < 0) continue;
        if (stdPath[token.cellNum].count < 2) continue;

        if (blockA[0] == -1 || blockA[0] == token.cellNum) {
            blockA[0] = token.cellNum;
            blockA[1] += 1;
            if (token.clockwise) blockA[2] += 1;
            else blockA[3] += 1;
        } else {
            blockB[0] = token.cellNum;
            blockB[1] += 1;
            if (token.clockwise) blockB[2] += 1;
            else blockB[3] += 1;
        }
    }

    if (blockA[0] == -1) {
        // no blocks found
        return;
    }

    // find max distances pieces can move
    if (blockA[2]) {
        // clockwise piece exists in block 1
        blockA[4] = checkPath(blockA[0], 6, pID, true);
        if (blockA[4] != blockA[0] && blockA[4] != -1) {
            blockA[4] = distanceTo(blockA[0], blockA[4], true);
        }
        else if (blockA[4] == -1) blockA[4] = 5; // block in cell 6 spaces ahead
        else blockA[4] = 0; // block in immediate cell
    }
    if (blockA[3]) {
        // anticlockwise piece exists in block 1
        blockA[5] = checkPath(blockA[0], 6, pID, false);
        if (blockA[5] != blockA[0] && blockA[5] != -1) {
            blockA[5] = distanceTo(blockA[0], blockA[5], false);
        }
        else if (blockA[5] == -1) blockA[5] = 5; // block in cell 6 spaces ahead
        else blockA[5] = 0; // block in immediate cell
    }

    if (blockB[0] != -1) { // second block exists
        if (blockB[2]) {
            // clockwise piece exists in block 2
            blockB[4] = checkPath(blockB[0], 6, pID, true);
            if (blockB[4] != blockB[0] && blockB[4] != -1) {
                blockB[4] = distanceTo(blockB[0], blockB[4], true);
            }
            else if (blockB[4] == -1) blockB[4] = 5; // block in cell 6 spaces ahead
            else blockB[4] = 0; // block in immediate cell
        }
        if (blockB[3]) {
            // anticlockwise piece exists in block 2
            blockB[5] = checkPath(blockB[0], 6, pID, false);
            if (blockB[5] != blockB[0] && blockB[5] != -1) {
                blockB[5] = distanceTo(blockB[0], blockB[5], false);
            }
            else if (blockB[5] == -1) blockB[5] = 5; // block in cell 6 spaces ahead
            else blockB[5] = 0; // block in immediate cell
        }
    }

    if (DEV_MODE) printf(">>Block A>> loc: %d, c: %d, cw: %d, acw: %d, mcw: %d, macw: %d\n", blockA[0], blockA[1], blockA[2], blockA[3], blockA[4], blockA[5]);
    if (DEV_MODE && blockB[0] != -1) printf(">>Block B>> loc: %d, c: %d, cw: %d, acw: %d, mcw: %d, macw: %d\n", blockB[0], blockB[1], blockB[2], blockB[3], blockB[4], blockB[5]);

    printf("\t%s Player rolled three 6's in a row\n", players[pID].name);
    printf("\tAttempting to break all %s blocks; ", players[pID].name);
    blockName(pID, blockA[0]);
    if (blockB[0] != -1) {
        printf(" and ");
        blockName(pID, blockB[0]);
    }
    printf(", by 6 units cumulatively\n");

    bool success = false;
    if (blockB[0] == -1 && blockA[1] == 2) {
        // I: Single block of size 2
        success = breakBlockHelperI(blockA, pID);
    }
    else if (blockA[1] == 3) {
        // II: Single block of size 3
        success = breakBlockHelperII(blockA, pID);
    }
    else if (blockA[1] == 4) {
        // III: Single block of size 4
        success = breakBlockHelperIII(blockA, pID);
    }
    else {
        // IV: Two blocks of size 2
        success = breakBlockHelperIV(blockA, blockB, pID);
    }

    if (success) printf("\t%s Player blocks broken successfully\n", players[pID].name);
    else printf("\tUnable to break %s Player blocks, as no moves were possible\n", players[pID].name);
}

// Turn Simulation=======================================

short playTurn(short pID, short roundNum, short sixRepeats, short mysteryCell) {
    // Returns;
    // 0 - turn over
    // 1 - bonus roll for capture
    // 2 - player reached home
    // 6 - bonus roll for 6
    // 7 - bonus roll for 6 AND player reached home
    // -1 - no moves made

    // player data
    char *pName = players[pID].name;
    printf("\n%s's Turn (Round %hd)\n", pName, roundNum);

    short diceValue = rollDice();
    printf("%s rolled %hd\n", pName, diceValue);
    customSleep(0.2);

    if (diceValue == 6 && sixRepeats == 2) {
        breakPlayerBlocks(pID);
        printf("\n\t%s Player rolled three 6's in a row, Ignoring throw and moving on to the next player\n", pName);
        return 0;
    }

    if (diceValue == 3) {
        if (players[pID].restricted > 0 && players[pID].prevThree) {
            // kotuwa briefing tokens to base
            kotuwaBreak(pID);
        }
        players[pID].prevThree = true;

    } else players[pID].prevThree = false;

    updateChoiceWeights(pID, diceValue, mysteryCell);

    short moveRes;
    while (1) {
        short highIndex = -1;
        short highWeight = -1;

        for (int i = 0; i < 8; i++) {
            // iterate over all 8 options
            short w = players[pID].choiceWeights[i];
            if (w > highWeight) {
                // pick move with highest weight/player-preference
                highIndex = i;
                highWeight = w;
            }
        }

        if (highIndex == -1) {
            printf("\t%s has no possible moves, Ignoring the throw and moving to the next player\n", pName);
            customSleep(0.2);
            return -1;
        }

        // indexes 0-3: piece, indexes 4-7: block
        if (highIndex < 4) moveRes = tokenTurn(pID, highIndex, diceValue, mysteryCell);
        else moveRes = blockTurn(pID, highIndex, diceValue, mysteryCell);

        if (moveRes != -1) break; // break out of loop if move made successfully

        printf("\t%s is picking a different move\n\n", pName);
        players[pID].choiceWeights[highIndex] = -1;
        customSleep(0.3);
    }

    if (moveRes == 2) {
        // piece reached home, check win condition
        if (diceValue == 6) return 7;
        return 2;
    }
    if (moveRes == 1) return 1; // bonus roll for capture
    if (diceValue == 6) return 6; // bonus roll for rolling 6
    return 0;
}

// Player Behaviours=====================================

void greenBehaviour(short diceV) {
    // sets green player preferences according to following rules;
        // create block +++++
        // move out of base +++
        // move pieces home >>>> breaking block
        // break block with other options ahead; only if all other options not possible

    short pApproach = players[0].approach;
    for (int i = 0; i < 4; i++) {
        // iterate over all green pieces
        Piece token = tokens[0][i];

        if (token.cellNum == pHome) continue; // in home

        if (token.cellNum == -1) {
            // in base
            if (diceV == 6) players[0].choiceWeights[i] = 98;
            continue;
        }

        if (52 < token.cellNum && token.cellNum < pHome) {
            // home straight
            players[0].choiceWeights[i] = token.cellNum;
            if (homeStraights[0][token.cellNum - pHomeStrt].count == 1) continue;

            // piece is part of block
            // green prefers moving block, over breaking so higher priority
            players[0].choiceWeights[i + 4] = token.cellNum + 1;
            continue;
        }

        // stdPath
        if (stdPath[token.cellNum].count > 1) {
            // piece is part of a block

            // break block, low priority
            players[0].choiceWeights[i] = 0;

            // moving block, higher priority
            players[0].choiceWeights[i + 4] = 1;
            continue;
        }
        // non block piece priority inv proportional to dist to home
        else players[0].choiceWeights[i] = 60 - distanceTo(token.cellNum, pApproach, token.clockwise);

        short nextCell = cellAtMove(token.cellNum, diceV, token.clockwise);
        if (stdPath[nextCell].playerID == 0) {
            // high priority to create blocks
            players[0].choiceWeights[i] = 99;
        }

        // NOTE: MIGHT WANT TO ADD OPPONENT CAPTURE PRIORITY
    }
}

void yellowBehaviour(short diceV) {
    // sets yellow player preferences according to following rules;
        // move out of base ++++
        // capture w/ piece that needs capture +++
        // above criteria not met; move piece closest to home

    short pApproach = players[1].approach;
    for (int i = 0; i < 4; i++) {
        // iterate over all yellow pieces
        Piece token = tokens[1][i];

        if (token.cellNum == pHome) continue; // in home

        if (token.cellNum == -1) {
            // in base, highest priority if rolled 6
            if (diceV == 6) players[1].choiceWeights[i] = 100;
            continue;
        }

        if (52 < token.cellNum && token.cellNum < pHome) {
            // home straight, cellNum is already high to represent preference
            players[1].choiceWeights[i] = token.cellNum;
            if (homeStraights[1][token.cellNum - pHomeStrt].count == 1) continue;
            
            // piece is part of block
            players[1].choiceWeights[i + 4] = token.cellNum - 1;
            continue;
        }

        // stdPath
        if (stdPath[token.cellNum].count > 1) {
            // piece is part of a block
            // mark block move as possible
            players[1].choiceWeights[i + 4] = 0;
        }

        if (token.captured == 0) {
            // piece needs captures

            short nextCell = cellAtMove(token.cellNum, diceV, token.clockwise);
            short targetPlayer = stdPath[nextCell].playerID;

            if (targetPlayer != 1 && targetPlayer != -1 && stdPath[nextCell].count == 1) {
                // high priority for pieces with no captures and opponent in range
                players[1].choiceWeights[i] = 99;
                continue;
            }
        }

        // piece priority inv proportional to dist to home 
        players[1].choiceWeights[i] = 60 - distanceTo(token.cellNum, pApproach, token.clockwise);

        if (token.clockwise == -1 && token.approachPass < 1) {
            // anticlockwise piece not passed approach is further behind
            // decrease priority to reflect above
            players[1].choiceWeights[i] -= 52;
        }
    }
}

void blueBehaviour(short diceV, short mysteryCell) {
    // sets blue player preferences according to following rules;
        // B(x+1) +++++, when prev move was Bx (cyclic manner)
        // clockwise -> mystery cell - - - - -
        // anticw -> mystery cell ++++

    // piece moved prev turn
    short prevPiece = players[2].prevPiece;

    // priority multipliers based on prev move
    // assigned preference weight, multiplied by following values
    short cyclicMultiplier[4] = {1, 1, 1, 1};
    cyclicMultiplier[(prevPiece + 1) % 4] = 4;
    cyclicMultiplier[(prevPiece + 2) % 4] = 3;
    cyclicMultiplier[(prevPiece + 3) % 4] = 2;

    for (int i = 0; i < 4; i++) {
        // iterate over all blue pieces
        Piece token = tokens[2][i];

        if (token.cellNum == pHome) continue; // in home

        if (token.cellNum == -1) {
            // in base, undefined preference with cyclic multiplier
            if (diceV == 6) players[2].choiceWeights[i] = 1 * cyclicMultiplier[i];
            continue;
        }

        if (52 < token.cellNum && token.cellNum < pHome) {
            // home straight, undefined preference with cyclic multiplier
            players[2].choiceWeights[i] = 1 * cyclicMultiplier[i];
            if (homeStraights[2][token.cellNum - pHomeStrt].count == 1) continue;

            // piece is part of block, mark block move as possible
            players[2].choiceWeights[i + 4] = 1;
            continue;
        }

        // stdPath
        if (stdPath[token.cellNum].count > 1) {
            // piece is part of a block

            // mark block move as possible
            // undefined preference
            players[2].choiceWeights[i + 4] = 0;
        }

        // cell roll will move piece to
        short nextCell = cellAtMove(token.cellNum, diceV, token.clockwise);
        if (mysteryCell == nextCell) {
            // landing on mystery cell

            // clockwise piece, tries to avoid mystery cell
            if (token.clockwise) players[2].choiceWeights[i] = 0;

            // anticlockwise piece, targets mystery cell
            else players[2].choiceWeights[i] = 100 * cyclicMultiplier[i];
            continue;
        }

        // other pieces; undefined preference, cyclic multiplier
        players[2].choiceWeights[i] = 1 * cyclicMultiplier[i];
    }
}

void redBehaviour(short diceV) {
    // sets red player preferences according to following rules;
        // capturing opponent closer to home +++++++
        // capturing opponent ++++
        // break blocks +++
        // move out of base - - - - -
        // create blocks - - - - - - - - -

    short pStart = players[3].starting;
    for (int i = 0; i < 4; i++) {
        // iterate over all red pieces
        Piece token = tokens[3][i];

        if (token.cellNum == pHome) continue; // in home

        if (token.cellNum == -1) {
            // in base
            if (diceV == 6) {
                // occupancy status of red starting cell
                short startingCellStatus = stdPath[pStart].playerID;

                // free cell
                if (startingCellStatus == -1) players[3].choiceWeights[i] = 1;

                // forming block unfavored
                else if (startingCellStatus == 3) players[3].choiceWeights[i] = 0;

                // opponent piece in starting cell
                else if (stdPath[pStart].count == 1) {
                    // opponent pID
                    short targetPlayer = stdPath[pStart].playerID;
                    for (int j = 0; j < 4; j++) {
                        // iterate over all opponent pieces
                        if (tokens[targetPlayer][j].cellNum != pStart) continue;

                        // set piece preference inv proportional to opponent dist from home
                        players[3].choiceWeights[i] = 55 - distanceTo(pStart, players[targetPlayer].approach, tokens[targetPlayer][j].clockwise);
                        
                        if (!tokens[targetPlayer][j].clockwise && !tokens[targetPlayer][j].approachPass) {
                            // anticlockwise opponent, who hasn't passed approach is further from home
                            players[3].choiceWeights[i] -= 52;
                        }
                    }
                }
            }
            continue;
        }

        if (52 < token.cellNum && token.cellNum < pHome) {
            // home straight, undefined preference
            players[3].choiceWeights[i] = 2;
            if (homeStraights[3][token.cellNum - pHomeStrt].count == 1) continue;

            // piece is part of block
            // low priority, as red dislikes blocks
            players[3].choiceWeights[i + 4] = 0;
            continue;
        }

        // stdPath
        if (stdPath[token.cellNum].count > 1) {
            // piece is part of a block

            // breaking block, high preference
            players[3].choiceWeights[i] = 3;
            // mark block move as possible
            players[3].choiceWeights[i + 4] = 0;
        }

        // cell roll will take piece to
        short nextCell = cellAtMove(token.cellNum, diceV, token.clockwise);

        // occupancy 
        short targetPlayer = stdPath[nextCell].playerID;
        if (targetPlayer == 3) {
            // forming block, unfavored
            players[3].choiceWeights[i] = 0;
            continue;
        }

        if (targetPlayer == -1) {
            // free cell, lower preference
            players[3].choiceWeights[i] = 1;
            continue;
        }

        // cant capture
        if (stdPath[nextCell].count > 1) continue;

        players[3].choiceWeights[i] = 2;
        for (int j = 0; j < 4; j++) {
            // iterate over opponent pieces
            if (tokens[targetPlayer][j].cellNum != nextCell) continue;

            // set piece preference inv proportional to opponent dist from home
            players[3].choiceWeights[i] = 55 - distanceTo(nextCell, players[targetPlayer].approach, tokens[targetPlayer][j].clockwise);

            if (!tokens[targetPlayer][j].clockwise && !tokens[targetPlayer][j].approachPass) {
                // anticlockwise opponent, who hasn't passed approach is further from home
                players[3].choiceWeights[i] -= 52;
            }
        }
    }
}

void updateChoiceWeights(short pID, short diceV, short mysteryCell) {
    // calls player behaviour functions and updates move choice preference weights
    
    for (int i = 0; i < 8; i++) {
        // reset all weights to -1: impossible
        players[pID].choiceWeights[i] = -1;
    }

    // call respective behaviour function
    switch (pID) {
        case 0:
            greenBehaviour(diceV);
            break;
        case 1:
            yellowBehaviour(diceV);
            break;
        case 2:
            blueBehaviour(diceV, mysteryCell);
            break;
        case 3:
            redBehaviour(diceV);
    }

    // reset repeated weights for block members
    // to avoid trying same impossible block move, with different access piece
    short blockCellA = -1;
    short blockCellB = -1;
    for (int i = 0; i < 4; i++) {
        Piece token = tokens[pID][i];

        if (stdPath[token.cellNum].count > 1) {
            // reset weight; if block member location already appears
            // mark unseen block locations
            if (blockCellA == token.cellNum) players[pID].choiceWeights[i + 4] = -1;
            else if (blockCellA == -1) blockCellA = token.cellNum;
            else if (blockCellB == -1) blockCellB = token.cellNum;
            else players[pID].choiceWeights[i + 4] = -1;
        }
    }
}

// Round/Game Loop=======================================

void stdPathView() {
    // only for development purposes
    printf("\nStandard Path:\n");
    for (int i = 0; i < 52; i++) {
        char ddd = (stdPath[i].clockwise) ? '+' : '-';
        printf("%02d P:%c | C:%c | D:%c \t", i, (stdPath[i].playerID != -1) ? stdPath[i].playerID + '0' : ' ', (stdPath[i].count != -1) ? stdPath[i].count + '0' : ' ', ddd);
        if (i != 0 && ((i + 1) % 4 == 0)) printf("\n");
    }
}

void playersView() {
    // only for development purposes
    for (int i = 0; i < 4; i++) {
        printf("%s : base %hd, board %hd, home %hd\n", players[i].name, players[i].inBase, players[i].onBoard, players[i].inHome);
    }
}

void endOfRound(short roundNum, short mysteryRound, short currMystery) {
    printf("\n====================\n");
    printf("End of Round %hd\n", roundNum);
    printf("====================\n");

    for (int p = 0; p < 4; p++) {
        // iterate over all players
        customSleep(0.3);
        playerSummary(p);

        printf("====================\n");
        printf("Location of %s Pieces\n", players[p].name);
        printf("====================\n");

        for (int t = 0; t < 4; t++) {
            // iterate over all pieces
            customSleep(0.1);
            printf("Piece %s --> ", tokens[p][t].tokenName);
            if (DEV_MODE) printf("{cw: %hd; capt: %hd;} ", tokens[p][t].clockwise, tokens[p][t].captured);

            if (tokens[p][t].cellNum == -1) printf("Base\n");
            else if (tokens[p][t].cellNum == pHome) printf("Home\n");
            else if (tokens[p][t].cellNum < 52) printf("Cell %hd\n", tokens[p][t].cellNum);
            else printf("%s|HomePath|%hd\n", players[p].name, tokens[p][t].cellNum - (pHomeStrt) + 1);

            // update flags for pieces with bhawana effects
            if (tokens[p][t].bhawanaMultiplier > 0) tokens[p][t].bhawanaMultiplier -= 1;
            if (tokens[p][t].bhawanaMultiplier < 0) tokens[p][t].bhawanaMultiplier += 1;

            // update flags for pieces with kotuwa effects
            if (tokens[p][t].kotuwaBrief > 0) {
                tokens[p][t].kotuwaBrief -= 1;
                // update player flag when piece freed of kotuwa effect
                if (tokens[p][t].kotuwaBrief == 0) players[p].restricted -= 1;
            }
        }
        printf("====================\n\n");
    }
    if (DEV_MODE) stdPathView();

    // mystery cell info
    if (currMystery != -1 && (mysteryRound - roundNum - 1) > 0) {
        printf("The Mystery Cell is at cell %hd and will be at that location for the next %hd rounds\n", currMystery, mysteryRound - roundNum - 1);
    }
}

void debugging() {
    // only for development purposes
    for (int i = 0; i < 52; i++) {
        if (stdPath[i].count == 0) continue;
        if (!(1 <= stdPath[i].count && stdPath[i].count <= 4)) {
            printf("\n\n\nDEBUGGING: stdPath count out of range\n\n\n");
            stdPathView();
            sleep(25);
        }
        if (!(0 <= stdPath[i].playerID && stdPath[i].playerID <= 3)) {
            printf("\n\n\nDEBUGGING: stdPath playerID out of range\n\n\n");
            stdPathView();
            sleep(25);
        }
        if (!(-1 <= stdPath[i].clockwise && stdPath[i].clockwise <= 1)) {
            printf("\n\n\nDEBUGGING: stdPath direction out of range\n\n\n");
            stdPathView();
            sleep(25);
        }
    }

    for (int i = 0; i < 4; i++) {
        if (!(0 <= players[i].inBase && players[i].inBase <= 4)) {
            printf("\n\n\nDEBUGGING: player in base out of range\n\n\n");
            printf("%s %hd %hd %hd\n", players[i].name, players[i].inBase, players[i].onBoard, players[i].inHome);
            sleep(25);
        }
        if (!(0 <= players[i].onBoard && players[i].onBoard <= 4)) {
            printf("\n\n\nDEBUGGING: player on board out of range\n\n\n");
            printf("%s %hd %hd %hd\n", players[i].name, players[i].inBase, players[i].onBoard, players[i].inHome);
            sleep(25);
        }
        if (!(0 <= players[i].inHome && players[i].inHome <= 4)) {
            printf("\n\n\nDEBUGGING: player in home out of range\n\n\n");
            printf("%s %hd %hd %hd\n", players[i].name, players[i].inBase, players[i].onBoard, players[i].inHome);
            sleep(25);
        }
    }
}

short spawnMysteryCell(short currMystery) {
    // spawns mystery cell at random unoccupied location; won't be previous mystery cell location

    short new;
    while (1) {
        // loop until valid cell found
        new = rand() % 52;
        if (new != currMystery && stdPath[new].count == 0) break; // allowed mystery location
    }

    printf("\nA Mystery Cell has spawned in location %hd and will be at this location for the next four rounds\n", new);
    customSleep(0.4);
    return new;
}

bool checkEndCondition() {
    // checks if game is unable to continue, given that players had no possible moves

    // if any pieces are in the base, game can still continue
    // if no pieces are in base and players had no possible moves for 10 rounds in a row
    // game is like to have reached a stalemate
    // if the starting cell of a piece in base, is blocked, it is also a draw
    
    for (int p = 0; p < 4; p++) {
        for (int t = 0; t < 4; t++) {
            if (tokens[p][t].cellNum != -1) continue;

            // free starting cell
            if (stdPath[players[p].starting].playerID == -1) return false;
            // same color in starting cell
            if (stdPath[players[p].starting].playerID == p) return false;
            // opponent in starting cell, can capture
            if (stdPath[players[p].starting].count == 1) return false;
        }
    }
    return true;
}

void gameOver(short winnerID, short roundNum) {
    printf("\n\n\n\t====================\n");
    printf("\t     Game Over\n");
    printf("\t Rounds Played: %d\n", roundNum);
    printf("\t====================\n");
    if (winnerID != -1) printf("\t %s Player Wins!\n", players[winnerID].name);
}

void gameLoop(short starter) {
    // loops infinitely until winner is found
    // handles bonus rolls
    // handles win condition

    // round data
    short roundNum = 1;
    short currPlayer = starter;
    short mysteryRound = -1;
    short currMystery = -1;
    short emptyTurns = 0;

    // player turn data
    short turnRes;
    short sixRepeats;

    while (1) {
        // infinite game loop

        if (emptyTurns >= 40) {
            // 10 rounds, with all players not making any moves in a row
            // game might not be able to carry on, due to impossible moves for all
            // check if game should be ended
            if (checkEndCondition()) {
                printf("\n\n\n\tGame cannot continue, as all players have no possible moves left\n");

                // check for winner
                short maxHome = 0;
                short winner = -1;
                for (int i = 0; i < 4; i++) {
                    if (players[i].inHome > maxHome) {
                        // player with more pieces in home
                        maxHome = players[i].inHome;
                        winner = i;
                    } else if (players[i].inHome == maxHome) {
                        // no single winner
                        winner = -1;
                    }
                }

                endOfRound(roundNum, mysteryRound, currMystery);

                if (winner == -1) {
                    printf("\tGame ends in a Draw\n");
                    gameOver(-1, roundNum);
                } else {
                    printf("\t%s Player has the highest number of pieces in Home\n", players[winner].name);
                    gameOver(winner, roundNum);
                }
                return;
            }
            // reset counter
            emptyTurns = 0;
        }

        printf("\n====================\n");
        printf("Start of Round %hd\n", roundNum);
        printf("====================\n");

        // srand seed for development purposes, TEMPORARY
        printf("\t>>>>> Current SRand Seed: %d\n", seed);

        if (roundNum == mysteryRound) {
            // mystery cell due to spawn

            // set new mystery cell
            currMystery = spawnMysteryCell(currMystery);
            // set next round for mystery cell spawn
            mysteryRound += 4;
        }

        for (int i = 0; i < 4; i++) {
            // iterate 4 times for 4 players

            sixRepeats = 0; // counter for sixes rolled in a row
            while (1) {
                // infinite player turn loop, until turn ends

                customSleep(0.5);
                turnRes = playTurn(currPlayer, roundNum, sixRepeats, currMystery);

                if (turnRes == 2 || turnRes == 7) {
                    // piece reached home

                    // check win condition
                    if (players[currPlayer].inHome == 4) {
                        endOfRound(roundNum, mysteryRound, currMystery);
                        gameOver(currPlayer, roundNum);
                        if (DEV_MODE) printf("\n>>>>> Current SRand Seed: %d\n", seed);
                        return;
                    }
                }

                if (mysteryRound == -1 && turnRes != -1) {
                    // set next round a mystery cell would be due to spawn
                    // turnRes is -1 if no piece was moved
                    mysteryRound = roundNum + 2;
                }

                if (turnRes == -1) {
                    // turnRes -1, when no moves are made
                    // keep track of number of turns with no moves made, happen in a row
                    emptyTurns += 1;
                } else emptyTurns = 0;

                if (turnRes <= 0 || turnRes == 2) break; // turn ended

                if (turnRes == 6 || turnRes == 7) {
                    printf("\n\t%s Player is awarded a bonus roll for rolling 6\n", players[currPlayer].name);
                    customSleep(0.3);
                    sixRepeats += 1; // keep track of consecutive sixes
                } else {
                    printf("\n\t%s Player is awarded a bonus roll for capturing an opponent\n", players[currPlayer].name);
                    customSleep(0.3);
                    sixRepeats = 0; // reset counter for consecutive sixes
                }
            }

            // move on to next player
            currPlayer += 1;
            currPlayer %= 4; // wrap around from pID; 3 -> 0
        }

        customSleep(0.75);
        endOfRound(roundNum, mysteryRound, currMystery); // display end of round data
        roundNum += 1; // update round num
        customSleep(0.2);

        if (DEV_MODE) debugging();
        if (DEV_MODE) playersView();
    }
}

// Initialization========================================

short findStarting() {
    // simulates dice rolling for all players;
     // until single player rolls higher total

    short first = -1;
    short maxVal = 0;
    short rolls[] = {0, 0, 0, 0};

    printf("\nDeciding who plays first\n\n");
    customSleep(0.2);

    while (first == -1) {
        // iterate until single highest total is found
        for (int i = 0; i < 4; i++) {
            // roll dice for all players
            short roll = rollDice();
            printf("%s rolls %hd\n", players[i].name, roll);
            customSleep(0.15);

            rolls[i] += roll;
            if (rolls[i] > maxVal) {
                // set highest total and leader
                maxVal = rolls[i];
                first = i;
            }
            // reset leader if same total occurs
            else if (rolls[i] == maxVal) first = -1;
        }

        if (first == -1) {
            // no single leader was found
            printf("Multiple players rolled the same highest value; Re-rolling\n\n");
            customSleep(0.5);
        }
    }

    customSleep(0.2);
    printf("\n%s has the highest roll and will begin the game\n", players[first].name);
    printf("The order of a single round will be %s, %s, %s, %s \n", players[first].name, players[(first + 1) % 4].name, players[(first + 2) % 4].name, players[(first + 3) % 4].name);
    customSleep(0.5);
    return first;
}

void playerIntroduction() {
    // display all players and their pieces

    for (int i = 0; i < 4; i++) {
        // iterate over players
        printf("The %s Player has 4 pieces named ", players[i].name);
        // iterate over pieces
        for (int j = 0; j < 4; j++) printf("%s ", tokens[i][j].tokenName);
        customSleep(0.1);
        printf("\n");
    }
}

void initializePlayers() {
    // set initial values for 'players' data array

    for (int i = 0; i < 4; i++) {
        // set common initial attributes
        players[i].inBase = 4;
        players[i].onBoard = 0;
        players[i].inHome = 0;
        players[i].restricted = 0;
        players[i].prevThree = false;
        players[i].prevPiece = -1;
        for (int j = 0; j < 8; j++) players[i].choiceWeights[j] = -1;
    }

    // set unique attributes
        // green
    players[0].starting = 41;
    players[0].approach = 39;
        // yellow
    players[1].starting = 2;
    players[1].approach = 0;
        // blue
    players[2].starting = 15;
    players[2].approach = 13;
    players[2].prevPiece = 3; // makes blue cyclic seletion start at B1
        // red
    players[3].starting = 28;
    players[3].approach = 26;

    if (USE_COLOR_CODES) {
        // player names with ANSI escape codes for color formatting
        players[0].name = "\033[32mGreen\033[0m";
        players[1].name = "\033[33mYellow\033[0m";
        players[2].name = "\033[34mBlue\033[0m";
        players[3].name = "\033[31mRed\033[0m";
    } else {
        // player names without formatting
        players[0].name = "Green";
        players[1].name = "Yellow";
        players[2].name = "Blue";
        players[3].name = "Red";
    }
}

void initializeTokens() {
    // set initial values for 'tokens' data array

    // set common attributes
    for (int i = 0; i < 4; i++) {
        // iterate over al players
        for (int j = 0; j < 4; j++) {
            // iterate over all pieces
            tokens[i][j].cellNum = -1;
            tokens[i][j].clockwise = true;
            tokens[i][j].captured = false;
            tokens[i][j].approachPass = false;
            tokens[i][j].bhawanaMultiplier = 0;
            tokens[i][j].kotuwaBrief = 0;
        }
    }

    // set unique attributes
    if (USE_COLOR_CODES) {
        // piece names with ANSI escape codes for color formatting
            // green
        tokens[0][0].tokenName = "\033[32mG1\033[0m";
        tokens[0][1].tokenName = "\033[32mG2\033[0m";
        tokens[0][2].tokenName = "\033[32mG3\033[0m";
        tokens[0][3].tokenName = "\033[32mG4\033[0m";
            // yellow
        tokens[1][0].tokenName = "\033[33mY1\033[0m";
        tokens[1][1].tokenName = "\033[33mY2\033[0m";
        tokens[1][2].tokenName = "\033[33mY3\033[0m";
        tokens[1][3].tokenName = "\033[33mY4\033[0m";
            // blue
        tokens[2][0].tokenName = "\033[34mB1\033[0m";
        tokens[2][1].tokenName = "\033[34mB2\033[0m";
        tokens[2][2].tokenName = "\033[34mB3\033[0m";
        tokens[2][3].tokenName = "\033[34mB4\033[0m";
            // red
        tokens[3][0].tokenName = "\033[31mR1\033[0m";
        tokens[3][1].tokenName = "\033[31mR2\033[0m";
        tokens[3][2].tokenName = "\033[31mR3\033[0m";
        tokens[3][3].tokenName = "\033[31mR4\033[0m";
    } else {
        // piece names without formatting
            // green
        tokens[0][0].tokenName = "G1";
        tokens[0][1].tokenName = "G2";
        tokens[0][2].tokenName = "G3";
        tokens[0][3].tokenName = "G4";
            // yellow
        tokens[1][0].tokenName = "Y1";
        tokens[1][1].tokenName = "Y2";
        tokens[1][2].tokenName = "Y3";
        tokens[1][3].tokenName = "Y4";
            // blue
        tokens[2][0].tokenName = "B1";
        tokens[2][1].tokenName = "B2";
        tokens[2][2].tokenName = "B3";
        tokens[2][3].tokenName = "B4";
            // red
        tokens[3][0].tokenName = "R1";
        tokens[3][1].tokenName = "R2";
        tokens[3][2].tokenName = "R3";
        tokens[3][3].tokenName = "R4";
    }
}

void initializeStdPath() {
    // set initial values for 'stdPath' data array

    for (int i = 0; i < 52; i++) {
        // iterate over all 52 cells
        stdPath[i].playerID = -1;
        stdPath[i].count = 0;
        stdPath[i].clockwise = true;
    }
}

void initializeHomeStraights() {
    // set initial values for 'homeStraights' data array

    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 5; j++) {
            homeStraights[i][j].count = 0;
        }
    }
}

void gameStart() {
    // seed for srand function, can be set manually or initalized to curr time
    seed = time(NULL);
    // seed = 1724301215; // 1800 rounds to draw

    // seed = 1724739495; // two blocks of 2 breakage
    // seed = 1724725956; // blue weird breakage penalty
    // seed = 1724666206; // yellow block break
    // seed = 1724165246; // BLOCK MEETUP EDGE CASE - fixed
    // seed = 1724151279; // SOME WEIRD BLUE WINNING CASE - fixed
    // seed = 1724237593; // BLOCK MEETUP AND CANT MEET DRAW CONDITION - fixed
    // seed = 1724297448; // ZERO DIV ERROR - fixed

    srand(seed); // set srand seed

    // initialize data arrays
    initializePlayers();
    initializeTokens();
    initializeStdPath();

    // introduce players
    playerIntroduction();
    customSleep(0.4);

    // find starting player
    short starter = findStarting();

    // begin game loop
    gameLoop(starter);
}