# Ultimate Tic-Tac-Toe Frontend Documentation

## Project Overview

Ultimate Tic-Tac-Toe is a complex variant of the classic game, implemented with a web frontend and Flask backend. The frontend is built with vanilla JavaScript using a component-based architecture.

## Project Structure

```
/ultimate-tictactoe
  ├── index.html           # Main HTML file with game interface
  ├── css/
  │   └── styles.css      # Game styling
  └── js/
      ├── constants.js    # Game constants and API endpoints
      ├── GameState.js    # Core game logic and state management
      ├── UIManager.js    # DOM manipulation and UI updates
      ├── ComputerPlayer.js # AI interaction and move computation
      └── Game.js        # Main game coordination
```

## Core Components

### GameState Class

Manages the core game logic and state:

```javascript
{
    gameId: string,          // Unique UUID for game persistence
    board: Array[9][9],      // 9x9 array representing the complete game board
    moveNumber: number,      // Current move number
    isComputerThinking: boolean,
    winner: string|null,     // Current winner (if any)
    boardFull: boolean,      // Whether the board is full
    targetBoard: number      // Which board must be played in (-1 for any)
}
```

Key Methods:
- `makeMove(board, cell, player)`: Validates and executes moves
- `checkBoardWinner(board)`: Determines if a mini-board is won
- `checkGameWinner()`: Checks for game completion
- `checkBoardStatus()`: Updates game state after moves
- `reset()`: Resets game to initial state

### UIManager Class

Handles all DOM interactions and rendering:

```javascript
{
    gameState: GameState,    // Reference to game state
    boardContainer: Element, // Main game board container
    winnerElement: Element,  // Winner display element
    lastMoveElement: Element, // Last move tracking
    savedGamesSelect: Element // Game loading dropdown
}
```

Key Methods:
- `renderBoard()`: Renders complete game board
- `updateLegalMoves()`: Highlights legal moves and last move
- `updateGameStatus()`: Updates winner display
- `loadGame(gameId)`: Loads saved game state
- `updateSavedGamesDropdown()`: Updates game selection dropdown

### ComputerPlayer Class

Manages AI interaction:

```javascript
{
    gameState: GameState,
    uiManager: UIManager
}
```

Key Methods:
- `makeMove()`: Coordinates computer move execution
- `requestMove()`: Makes API call for computer move

### Game Class

Coordinates game components:

```javascript
{
    gameState: GameState,
    uiManager: UIManager,
    computerPlayer: ComputerPlayer
}
```

Key Methods:
- `handleCellClick(board, cell)`: Processes player moves
- `loadSelectedGame()`: Loads selected game state
- `reset()`: Resets game state

## State Management

### Game State

Game state is managed through two mechanisms:
1. The `GameState` class for core game logic
2. DOM data attributes for move tracking

Critical State Elements:
```html
<h2 id="last-move" data-last-board="-1" data-last-cell="-1"></h2>
```

These dataset attributes are used for:
- Move validation
- AI communication
- Legal move determination

### Game Persistence

Games are automatically persisted with:
- Unique game IDs (UUID)
- Automatic saving after each move
- Load functionality via dropdown

## Move Processing

### Move Validation

Moves are validated by checking:
1. Cell availability
2. Computer thinking status
3. Target board requirements
4. Game completion status

Special Cases:
- First move: Any cell is legal
- Won/full target board: Can play anywhere

### Move Execution Flow

1. Player Move:
   ```javascript
   handleCellClick(board, cell)
   ↓
   gameState.makeMove()
   ↓
   uiManager.updateLastMove()
   ↓
   uiManager.renderBoard()
   ```

2. Computer Move:
   ```javascript
   computerPlayer.makeMove()
   ↓
   requestMove() API call
   ↓
   Process response
   ↓
   Update UI
   ```

## API Integration

### Computer Move Request
```javascript
{
    game_id: string,
    last_move: [boardIndex, cellIndex, "X"],
    game_board: Array[9][9],
    compute_time: number,
    force_full_time: boolean
}
```

### Computer Move Response
```javascript
{
    board: number,
    cell: number,
    metadata: {
        num_gamestates: number,
        depth_explored: number,
        thinking_time: number,
        moves: Array
    }
}
```

## UI Features

### Game Controls
- Compute time slider (5-60 seconds)
- Force full compute time option
- Game loading dropdown
- Reset button

### Game Information
- Last move indicator
- Winner display
- Computer thinking indicator
- Move metadata display

## Best Practices

### Error Handling
- API call error catching
- Move validation checks
- State consistency verification

### State Updates
1. Validate move
2. Update game state
3. Update UI
4. Process computer response
5. Update UI again

### Performance Considerations
- Efficient DOM updates
- Minimal state duplication
- Proper async/await usage

## Debug Guidance

Common Issues:
1. Move validation failures
2. API communication errors
3. State synchronization problems
4. UI update timing

Debug Steps:
1. Check console logs
2. Verify state consistency
3. Confirm API request/response format
4. Validate UI update sequence

## Future Improvements

1. State Management
   - Move to pure JavaScript state
   - Remove DOM data dependencies
   - Implement proper state machine

2. Code Quality
   - Add TypeScript
   - Implement unit tests
   - Add error boundaries

3. Features
   - Undo/redo functionality
   - Game replay
   - Move analysis
   - Local multiplayer