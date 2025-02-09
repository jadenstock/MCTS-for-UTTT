# Ultimate Tic-Tac-Toe Frontend Documentation

## Project Structure
```
/ultimate-tictactoe
  ├── index.html                    # Main HTML file
  └── css/
      ├── styles.css                # Styles
  └── js/
      ├── constants.js              # Game constants and configuration
      ├── GameState.js              # Core game state management
      ├── UIManager.js              # DOM manipulation and rendering
      ├── ComputerPlayer.js         # AI move computation and API interaction
      └── Game.js                   # Main game coordination
```

## Key Components

### GameState Class
Manages the core game state including:
- 9x9 board representation
- Move tracking
- Winner detection
- Game status (computer thinking, game over, etc.)

```javascript
this.board = [["", "", "", ...], ...];  // 9x9 array of moves
this.moveNumber = 1;
this.isComputerThinking = false;
this.winner = null;
this.boardFull = false;
```

### UIManager Class
Handles all DOM interactions and rendering:
- Board rendering
- Move highlighting
- Legal move validation
- Metadata updates (nodes evaluated, depth, etc.)
- Past moves tracking

Key method: `updateLegalMoves()`
- Clears all cell states
- Highlights last move in red
- Marks occupied cells
- Implements UTTT rules about which board can be played in

### ComputerPlayer Class
Manages AI interaction:
- Makes API calls to Flask backend
- Processes AI responses
- Updates game state with computer moves
- Handles metadata display

Important detail: Uses double JSON.stringify for API calls:
```javascript
body: JSON.stringify(JSON.stringify(requestData))
```
This is required for compatibility with the Flask backend.

### Game Class
Coordinates between components:
- Initializes game state
- Handles player moves
- Coordinates between UI updates and computer moves
- Manages game reset functionality

## Critical Game State Management

### Last Move Tracking
The game heavily relies on the last-move element's dataset attributes:
```html
<h2 id="last-move" data-last-board="-1" data-last-cell="-1"></h2>
```
These dataset attributes are crucial for:
- Determining legal moves
- Communicating with the AI
- Tracking game progression

### Move Validation
Legal moves are determined by:
1. Checking if cell is empty
2. Checking if it's the computer's turn
3. Checking if the move is in the correct board (based on last move)
4. Special cases:
   - First move (all cells legal)
   - Target board is won/full (can play anywhere)

### Board State Updates
The board updates follow this sequence:
1. Human makes move:
   - Update game state
   - Update UI
   - Update last move tracking
2. Computer responds:
   - API call made
   - Response processed
   - Board updated
   - UI refreshed
   - Last move tracking updated

## API Integration

### Request Format
```javascript
{
    last_move: [boardIndex, cellIndex, "X"],
    game_board: [9x9 array],
    compute_time: seconds,
    force_full_time: boolean
}
```

### Response Format
```javascript
{
    board: number,
    cell: number,
    metadata: {
        num_gamestates: number,
        depth_explored: number,
        thinking_time: number,
        predicted_line: array,
        moves: array
    }
}
```

## Important Implementation Details

### Move Validation Sequence
1. Click handler activated
2. Move validation checked
3. If valid:
   - Update board state
   - Update UI
   - Trigger computer move
   - Update UI again after computer move

### UI Update Sequence
1. Clear board
2. Render current state
3. Update legal moves
4. Update metadata
5. Check for winner

### State Management Notes
- Game state is tracked both in JavaScript (GameState class) and DOM (dataset attributes)
- This dual tracking is intentional for compatibility with the original implementation
- The last-move dataset attributes are the source of truth for move validation

## Known Quirks
1. Double JSON stringification in API calls is required
2. Last move tracking relies on DOM dataset attributes rather than pure JS state
3. Move validation combines both GameState and DOM checks

## Debug Tips
1. Check console for API call errors
2. Verify last-move dataset attributes after moves
3. Monitor board state in GameState.board
4. Verify UI updates after both human and computer moves

## Future Improvements
1. Move state management entirely to GameState class
2. Implement proper TypeScript interfaces
3. Add comprehensive error handling
4. Add unit tests
5. Improve documentation with JSDoc