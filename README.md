# Execution
```shell
gcc logic.c main.c
./a.out
```


# Notes

-   "Pieces" are commonly referred to as "Tokens" throughout the program. This is done to prevent confusion between a Player’s pID, and a Piece’s pID, thereby having a Piece’s ID be a tID.

# Structures

### Piece

Used to represent a single piece of any player. It contains the following attributes;

-   **tokenName** - Holds the actual name of the piece, used for output messages. (eg: Y1, B3, R2... etc)
-   **clockwise** - A boolean variable to store a piece’s direction referred to in movement functions.
-   **captured** - A boolean variable to store whether a piece has made a capture. The precise number of captures a piece has made isn’t required for any functionality specified, therefore a boolean value will suffice.
-   **approachPass** - A boolean variable to store whether a piece has passed its relevant approach cell, which is a requirement for an anti-clockwise piece, to enter its home straight.
-   **cellNum** - Stores the actual location of the piece. Can hold values: 0-51 to indicate the piece is on the standard path, 55-59 to indicate the piece is on its home straight, and 60 to indicate the piece has reached home.
-   **bhawanaMultiplier** - Stores the status of effects from the piece having been teleported to Bhawana via a mystery cell. Values range from -4 to +4. Value 0 indicates that the piece is not sick or energized and its roll values are to be unaffected. A positive value indicates that the piece is energized and its roll value will be doubled. A negative value indicates that the piece is sick and its roll value will be halved. The actual value is brought towards zero at the end of each round, and the value is set to +4 or -4, upon teleporting to Bhawana.
-   **kotuwaBrief** - Stores the status of effects from the piece having been teleported to Kotuwa, via a mystery cell or Pita-Kotuwa. Values range from 0 to 4. Value 0 indicates that the piece is not attending a briefing, and can move freely. A positive value indicates that the piece is in a briefing and cannot be moved. The value is decremented every round and the value is set to 4 upon teleporting to Kotuwa.

### Player

Used to hold data about a single player. It contains the following attributes;

-   **name** - Stores the actual color of a player as a string. Used for displaying output messages.
-   **starting** - Stores the cell location of the player’s starting cell.
-   **approach** - Stores the cell location of the player’s approach cell.
-   **inBase** - Stores the number of pieces the player has in their base.
-   **onBoard** - Stores the number of pieces the player has on the board.
-   **inHome** - Stores the number of pieces the player has in their home. Used to check win condition.
-   **restricted** - Stores the number of movement-restricted pieces the player has. Used to manage penalties for rolling threes consecutively, while having pieces in a briefing at Kotuwa.
-   **prevThree** - Stores a boolean value to mark if the previous roll was of value 3. Used to manage penalties for rolling threes consecutively, while having pieces in a briefing at Kotuwa.
-   **prevPiece** - Stores the index of the piece moved on the previous round by the player. Only relevant to the blue player, and their behavior of cyclic movement.
-   **choiceWeights** - Stores an array of size 8, which contains a number value that represents the player’s preference on each choice of movement. The array indexes of 0-3, indicate the preference to move pieces of the respective index, and indexes of 4-7 indicate the preference to move the block, that the piece at the respective index - 4, is a member of. This array will be updated after rolling the dice for each player, and values will be assigned, with higher values being set for favorable choices, and lower values being set for unfavorable choices. The value -1 will be set to any choice that is deemed impossible at the time of deciding preferences. The *playTurn* function will attempt the choices the player’s behavior has set in descending order until a choice is successful.

### StdCell

Used to hold data about a single cell in the Standard Path. It contains the following attributes;
-   **playerID** - Stores the index of the player currently occupying the cell. Will hold value -1 if no player is occupying the cell,
-   **count** - Stores the number of pieces currently occupying the cell. Used to identify and handle block logic
-   **clockwise** - Stores a boolean value to mark if the occupants of the cell are to move clockwise or anti-clockwise. Used to identify and handle block direction logic.

### HomeStrtCell

Used to hold data about a single cell in a player’s Home Straight. It contains the following attributes;
-   **count** - Stores the number of pieces occupying the cell. Used to     handle block logic within home straight.

# Data Arrays

### players

An array of size 4 containing ’Player’ structures for all 4 players. Indexes of this array, are as follows; 0 - Green Player, 1 - Yellow Player, 2 - Blue Player, 3 - Red Player. This allocation of indexes to players is consistent throughout the program. This data array is referenced throughout the program by various functions, for cell values, choice priorities, win conditions, and much more; Therefore the **players** array is defined globally.

### tokens

A 2D array of size 4x4 containing ’Piece’ structures for all 4 pieces of all 4 players. The same indexing as defined above applies to map row indexes with players. The column indexes map to the respective pieces as follows; 0 - X1, 1 - X2, 2 - X3, 3 - X4. The **tokens** array is defined globally as it is referenced throughout the program.

### stdPath

An array of size 52 containing ’StdCell’ structures for all 52 cells in the standard path. Cell numbers are 0 indexed. The data array is not primarily used for any functionality, and only acts as a quick reference or as a ’memo’ of where pieces and blocks reside, allowing efficiency boosts by not having to loop over all 16 pieces in the game every action.

### homeStraights

A 2D array of size 4x5 containing ’HomeStrtCell’ structures for all 5 home straight cells for all 4 players. The same indexing as defined above applies to map row indexes with players. The column indexes map to the relevant home straight cell, with the zeroth index being the home straight cell being the cell furthest from home. This data array is not primarily used for any functionality and only acts as a quick reference to handle block logic within home straights, allowing for efficiency boosts by avoiding looping over pieces.

# Helper Functions

Functions that provide reused functionality required by other functions.

### rollDice

Returns a number between 1 and 6 to simulate rolling a dice.

### flipCoin

Returns a boolean value to simulate flipping a coin. True for heads and False for tails.

### blockName

Prints the symbolic representation of a block at a specified cell. Does not return anything.

### playerSummary

Prints a specified player’s onBoard, inBase, and inHome values as a summary of their piece locations.

### distanceTo

Returns the absolute distance in the number of spaces, a specified destination cell is from a specified source cell, in a specified direction.

### cellAtMove

Returns the cell number/index to be reached after moving a specified number of spaces in a specified direction from a specified source cell.

### checkPath

Returns the furthest cell number/index a piece can go to when trying to move a specified number of spaces in a specified direction. Will check for blocks along the path, which will inhibit a piece’s movement. Will return the cell preceding a block if the piece is to surpass a block and be prevented from passing it. Will return the value -1 if the piece is to land directly on a block, therefore the move being disallowed. Will return the *cellAtMove* cell after the specified movement, if there are no blocks in the path specified.

### blockDirection

Returns a boolean value to represent if a specified player’s pieces at a specified cell, are in a block that is to travel clockwise or anti-clockwise according to the following rules; A block created by multiple pieces of the same direction, will travel in that direction. A block created by pieces of both directions, the block will travel in the direction of the piece with the longest distance from home.

### resetPiece

Resets a specified player’s specified piece to take on initial values, of when the piece was starting in the base. Will also update a player’s inBase and onBoard counters to reflect a piece going back to base.

### setStdCell

Sets a specified index of the *stdPath* data array to be a specified set of values for *playerID, count*, and *clockwise*.

### resetStdCell

Resets a specified index of the stdPath data array to take on the initial values, of when the standard path cell was deemed to be empty.

### capture

Resets opponent pieces at a specified capturing cell and prints messages about capture.

# Movement Functions

Functions that handle movement of pieces between cells on the standard path, and the consequential actions of those movements.

### moveToken

Moves a specified player’s piece, from a source cell to a destination cell. The function also handles updating the *stdPath* array, capturing, the formation of blocks, as well as printing messages about movement. Returns values ranging from 0-3 as follows;
Value 0 - movement ended successfully, with the piece moving to a free cell.
Value 1 - movement ended successfully with the piece moving to a cell occupied by the same player, forming a block.
Value 2 - movement ended successfully with the piece moving to a cell occupied by a different player, and capturing the opponent piece.
Value 3 - movement failed with the piece being prevented from moving to the destination due to an opposing block’s presence.

### moveBlock

Moves a specified player’s pieces of a block, from a source cell to a destination cell. The function also handles updating the *stdPath* array, capturing, the formation of larger blocks, as well as printing messages about movement. Returns values ranging from 0-3 as follows;
Value 0 - movement ended successfully, with the block moving to a free cell.
Value 1 - movement ended successfully with the block moving to a cell occupied by the same player, forming a larger block.
Value 2 - movement ended successfully with the block moving to a cell occupied by a different player, and capturing the opponent piece/block.
Value 3 - movement failed with the block being prevented from moving to the destination due to a larger, opposing block’s presence.

### teleport

Teleports a specified player’s piece/block, from a source cell to a destination cell. The function also handles updating the *stdPath* array, capturing, the formation of blocks, as well as printing messages about teleportation. Returns values ranging from 0-3 as follows;
Value 0 - teleportation ended successfully, with the piece/block teleporting to a free cell.
Value 1 - teleportation ended successfully with the piece/block teleporting to a cell occupied by the same player, forming a block.
Value 2 - teleportation ended successfully with the piece/block teleporting to a cell occupied by a different player, and capturing the opponent piece.
Value 3 - teleportation failed with the piece/block being prevented from teleporting to the destination due to a larger, opposing block’s presence.

# Mystery Handlers

Functions that handle mystery cells, apply random mystery effects and handle any directly related follow-up activities.

### landMystery

Randomly picks a mystery cell effect, and applies it to a specified player’s piece/block at the current mystery cell. Will also check for the legality of teleportation before applying and handing over to a mystery effect function.

### bhawana

Flips a coin to decide an effect, applies the effect to each piece that landed in the mystery cell, and teleports them to cell 9. Effect application is done by setting the *bhawanaMultiplier* attribute within the affected pieces. Application of effect before teleportation is done so that any same color pieces that already reside in Bhawana and form a block with teleported pieces aren’t also affected by Bhawana.

### kotuwa

Applies the effect to each piece that landed in the mystery cell, and teleports them to cell 27. Effect application is done by setting the *kotuwaBrief* attribute within the affected pieces. Application of effect before teleportation is done so that any same color pieces that already reside in Kotuwa and form a block with teleported pieces aren’t also affected by Kotuwa.

### kotuwaBreak

Handles the penalty for a player with pieces in a briefing at Kotuwa, rolling threes consecutively. Will the pieces in Kotuwa (in a briefing), to base, and reset all piece attributes.

### pitaKotuwa

If the Piece/Block is moving clockwise, set the direction of each piece that landed in the mystery cell to anti-clockwise, and teleport them to cell 46. If the Piece/Block is moving anti-clockwise, teleport the Piece/Block to Kotuwa. Application of effect before teleportation is done so that any same color pieces that already reside in Pita-Kotuwa and form a block with teleported pieces aren’t also affected by Pita-Kotuwa.

### mysteryToBase

Handles sending pieces in the mystery cell to the base. Will reset piece attributes and display relevant messages.

# Main Piece/Block Handlers

### tokenTurn

Responsible for the following;
-   Moving a piece out of the base
-   Checking if the piece is in a Kotuwa briefing
-   Applying Bhawana effects onto roll value
-   Checking if the movement takes a piece past the Approach cell
-   Checking if a piece is eligible to enter Home Straight
-   Moving a piece to Home Straight
-   Moving a piece along Standard Path
-   Checking if the piece landed on the Mystery cell
-   Moving a piece up the Home Straight
-   Moving a piece to Home
-   Mark bonus rolls for capture
-   Displaying relevant messages

Will return a value between -1 and 2 to represent various outcomes to be
handled at the place of the function call, as follows;
Value -1 - the move failed, as the move was not possible
Value 0 - the move ended successfully, no further action is required
Value 1 - the move ended successfully and the player is awarded a bonus roll
Value 2 - the move ended successfully and the player’s piece reached home, thereby needing to check the win condition at the *gameLoop* function

### blockTurn

Responsible for the following;
-   Checking if the movement takes a block past the Approach cell
-   Checking if a block is eligible to enter Home Straight
-   Moving a block to Home Straight
-   Moving a block along Standard Path
-   Checking if the block landed on the Mystery cell
-   Moving a block up the Home Straight
-   Moving a block to Home
-   Mark bonus rolls for capture
-   Displaying relevant messages

Will return a value between -1 and 2 to represent various outcomes to be
handled at the place of the function call, as follows;
Value -1 - the move failed, as the move was not possible
Value 0 - the move ended successfully, no further action is required
Value 1 - the move ended successfully and the player is awarded a bonus roll
Value 2 - the move ended successfully and the player’s block reached home, thereby needing to check the win condition at the *gameLoop* function

### breakPlayerBlocks

Handles penalty for a player rolling 6 three times consecutively. Attempts to break all blocks belonging to the specified player, by moving all pieces, except one, from each block by 6 units/spaces cumulatively. Handles identification of blocks and calling necessary helper functions depending on the situation.

### breakBlockHelperI

Handles breakage of player blocks when player blocks consist of a single block of size 2.

### breakBlockHelperII

Handles breakage of player blocks when player blocks consist of a single block of size 3.

### breakBlockHelperIII

Handles breakage of player blocks when player blocks consist of a single block of size 4.

### breakBlockHelperIV

Handles breakage of player blocks when player blocks consist of a pair of blocks of size 2.

# Turn Simulation

### playTurn

Handles a single turn for a specified player for a single round. Will call *rollDice* and *updateChoiceWeights* functions to simulate a player rolling a die and picking a move. Afterward, it will pick the option with the highest preference and call *tokenTurn* or *blockTurn* as required. If either of the aforementioned functions returns value -1, the preference of that move will be reset, and the next highest preference option will be attempted until an option works or the player runs out of possible options. Will return the following values to represent various outcomes to be handled by the *gameLoop* function, as follows;
Value 0 - player turn ended successfully, no further action required.
Value 1 - player turn ended successfully, player is awarded a bonus roll for capture.
Value 2 - player turn ended successfully, the player’s piece reached home and the win condition needs to be checked.
Value 6 - player turn ended successfully, the player is awarded a bonus roll for rolling 6.
Value 7 - player turn ended successfully, the player is awarded a bonus roll for rolling 6, and the player’s piece reached home and the win condition needs to be checked.
Value -1 - player turn ended unsuccessfully, with no moves being made.

### updateChoiceWeights

Handles calling a specified player’s behaviour function, after resetting all weights for all options. Also handles resetting choice weights which are repeated on multiple members of the same block.

### greenBehaviour

Checks and applies preference values to all possible options available to the green player, according to the following behaviour description.
-   Prioritises winning by blocking.
-   Will not look to capture opponent pieces more than what is required to enter the home straight.
-   Likes to keep an empty base. Any pieces in the base will be moved to Starting whenever a six is thrown if there are any pieces in the base unless moving six cells enables green to create a block.
-   Prioritizes moving its other pieces home before breaking a block. Green always attempts to move forward using the block move explained in Rule CS-4.
-   Will only break a block, when other pieces are in front of it, if and only if the value of the roll cannot be performed by green using the pieces in front of the block.

### yellowBehaviour

Checks and applies preference values to all possible options available to the yellow player, according to the following behaviour description.
-   Prioritises winning.
-   Will not look to capture opponent pieces more than what is required
    to enter the home straight.
-   Likes to keep an empty Base. Whenever a six is thrown, if there are
    any pieces in the Base, they will be moved to Starting.
-   If no pieces are in the base or rolled a value that cannot transfer a piece from Base to Starting, prioritise the pieces that need captures first to see whether any opponent piece is within range. If such a piece is within range then the capture will take place.
-   If no captures could be done, move the piece closest to its home by the number specified in the roll.

### blueBehaviour

Checks and applies preference values to all possible options available to the blue player, according to the following behaviour description.

-   Prioritises mystery cells.
-   Moves in a cyclic manner. That is, if B1 is moved in the current round, B2 is considered in the next and so on.
-   If the piece to be moved is movable;
    -   prioritize landing on the mystery cell if it is moving
        counterclockwise.
    -   avoid landing on the mystery cell if it is moving clockwise.

### redBehaviour
Checks and applies preference values to all possible options available to the red player, according to the following behaviour description.
-   Aggressive player who prioritises capturing opponent pieces rather than winning the game.

-   If any opponent piece can be captured by moving the specified number of cells in the dice, prioritize capturing the opponent piece.

-   If more than one piece can be captured by moving different red pieces, prioritize capturing the opponent piece closest to its home.

-   Will always keep one piece in the standard path and will not take another piece to the path from the base unless it cannot capture any piece by moving six cells. In such a case, a piece would be transferred to Starting.

-   Will always avoid creating blocks unless it is unavoidable.

# Round/Game Loop

### gameLoop

Handles the main loop of the game. Looping infinitely until a winner is found, passing turns between players. Uses the return values from *playTurn* function to handle win conditions, mystery cell initialization, draw condition checking, and bonus roll awarding.

### endOfRound

Displays a summary of all players and locations of their pieces. Will also handle updating flags for Bhawana effects and Kotuwa briefing timers.

### spawnMysteryCell

Selects a random unoccupied cell in the standard path to be the next mystery cell. Will ensure new mystery cell, isn’t in the same location as the previous mystery cell.

### checkEndCondition

Checks if locations of pieces, correspond to a situation where the game is at a locked state, where no piece can move due to others. Used in *gameLoop* function to identify a draw/partial-win.

### gameOver

Displays the winner of the game.

# Initialization

### gameStart

Identifies first player to play, Initializes all data arrays, and starts the *gameLoop.*

### findStarting

Rolls dice for all players, possibly repeatedly, until a player has a maximum roll total, and is chosen to go first.

### playerIntroductions

Displays a summary of players and their pieces, before the game starts.

### initializePlayers

Sets all data in the **players** data array to take on the initial values.

### initializeTokens

Sets all data in the **tokens** data array to take on the initial values.

### initializeStdPath

Sets all data in the **stdPath** data array to take on the initial values.

### initializeHomeStraights

Sets all data in the **homeStraights** data array to take on the initial values.
