#ifndef TYPES_H
#define TYPES_H

#include <stdbool.h>

typedef struct Piece
{
    char *tokenName; // 2B
    bool clockwise; // 1B
    bool captured; // 1B
    bool approachPass; // 1B
    short cellNum; // 2B
    short bhawanaMultiplier; // 2B
    short kotuwaBrief; // 2B
} Piece;

typedef struct Player
{
    char *name; // 7B (maximum: 'Yellow')
    bool prevThree; // 1B
    short starting; // 2B
    short approach; // 2B
    short inBase; // 2B
    short onBoard; // 2B
    short inHome; // 2B
    short restricted; // 2B
    short prevPiece; // 2B
    short choiceWeights[8]; // 16B
} Player;

typedef struct StdCell
{
    bool clockwise; // 1B
    short playerID; // 2B
    short count; // 2B
} StdCell;

typedef struct HomeStrtCell {
    short count; // 2B
} HomeStrtCell;

// Function Prototypes

short rollDice(void);
bool flipCoin(void);
void blockName(short, short);
void playerSummary(short);
short distanceTo(short, short, bool);
short cellAtMove(short, short, bool);
short checkPath(short, short, short, bool);
bool blockDirection(short, short);
void resetPiece(short, short);
void stdStdCell(short, short, short, bool);
void resetStdCell(short);
void capture(short, short, short, short, bool);

short moveToken(short, short, short, short, bool);
short moveBlock(short, short, short, bool);
short teleport(short, short, short, short, char *, char *);

void bhawana(short, short, short);
void kotuwa(short, short, short, bool);
void kotuwaBreak(short);
void pitaKotuwa(short, short, short);
void mysteryToBase(short, short, short);
void landMystery(short, short, short);

short tokenTurn(short, short, short, short);
short blockTurn(short, short, short, short);
bool breakBlockHelperI(short [], short);
bool breakBlockHelperII(short [], short);
bool breakBlockHelperIII(short [], short);
bool breakBlockHelperIV(short [], short [], short);
void breakPlayerBlocks(short);

short playTurn(short, short, short, short);
void greenBehaviour(short);
void yellowBehaviour(short);
void blueBehaviour(short, short);
void redBehaviour(short);
void updateChoiceWeights(short, short, short);

void endOfRound(short, short, short);
short spawnMysteryCell(short);
bool checkEndCondition(void);
void gameOver(short, short);
void gameLoop(short);

short findStarting(void);
void playerIntroduction(void);
void initializePlayers(void);
void initializeTokens(void);
void initializeStdPath(void);
void initializeHomeStraights(void);
void gameStart(void);

#endif