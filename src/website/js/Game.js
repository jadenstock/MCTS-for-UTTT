class Game {
    constructor() {
        this.gameState = new GameState();
        this.uiManager = new UIManager(this.gameState);
        this.computerPlayer = new ComputerPlayer(this.gameState, this.uiManager);
        this.initialize();
    }

    initialize() {
        this.uiManager.renderBoard();
        // Bind the slider update function to window for global access
        window.updateSlider = (slideAmount) => {
            this.uiManager.updateComputeTime();
        };
    }

    async handleCellClick(board, cell) {
        console.log("Cell clicked:", board, cell);
        
        // Check if cell is occupied or if it's not the player's turn
        const cellElement = document.querySelector(`#cell_${board}${cell}`);
        if (cellElement.classList.contains("occupied") ||
            this.gameState.isComputerThinking) {
            console.log("Move rejected: Cell is occupied or computer is thinking");
            return;
        }
        
        // Debug the current state
        console.log("Game state before move:");
        console.log("- Next to move:", this.gameState.next_to_move);
        console.log("- Move number:", this.gameState.moveNumber);
        console.log("- Total moves:", this.gameState.totalMoves);
        console.log("- Target board:", this.gameState.targetBoard);
        
        // Force next_to_move to be HUMAN if we're making a move after navigation
        if (this.gameState.next_to_move !== GAME_CONSTANTS.PLAYERS.HUMAN) {
            console.log("Forcing next_to_move to HUMAN");
            this.gameState.next_to_move = GAME_CONSTANTS.PLAYERS.HUMAN;
        }

        // Make the move if valid
        const moveSuccess = this.gameState.makeMove(board, cell, GAME_CONSTANTS.PLAYERS.HUMAN);
        console.log("Human move success:", moveSuccess);
        if (!moveSuccess) {
            return;
        }
        
        // If we're making a move after navigating to a previous move,
        // update the totalMoves to match the current move number
        if (this.gameState.moveNumber - 1 < this.gameState.totalMoves) {
            console.log(`Truncating move history: ${this.gameState.moveNumber - 1} < ${this.gameState.totalMoves}`);
            this.gameState.totalMoves = this.gameState.moveNumber - 1;
        }

        // Update UI after human move
        this.uiManager.updateLastMove(board, cell);
        this.uiManager.renderBoard();
        this.uiManager.updateGameStatus();
        this.uiManager.updateMoveHistoryDisplay();

        // Save the game state if we have a game ID
        if (this.gameState.gameId) {
            try {
                console.log("Sending move to server:", {
                    game_id: this.gameState.gameId,
                    game_board: this.gameState.board,
                    last_move: [board, cell, GAME_CONSTANTS.PLAYERS.HUMAN],
                    compute_time: document.getElementById("computeTime").value
                });
                
                const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.MAKE_MOVE, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        game_id: this.gameState.gameId,
                        game_board: this.gameState.board,
                        last_move: [board, cell, GAME_CONSTANTS.PLAYERS.HUMAN],
                        compute_time: document.getElementById("computeTime").value
                    })
                });
                
                const data = await response.json();
                console.log("Server response:", data);
                
                // Directly update the board with the computer's move from the server
                const computerBoard = data.board;
                const computerCell = data.cell;
                
                console.log("Computer move from server:", computerBoard, computerCell);
                
                // Update the game state with the computer's move
                this.gameState.board[computerBoard][computerCell] = GAME_CONSTANTS.PLAYERS.COMPUTER;
                this.gameState.targetBoard = computerCell;
                this.gameState.moveNumber++;
                this.gameState.totalMoves = this.gameState.moveNumber - 1;
                
                // Add the move to history
                this.gameState.moves.push({
                    board: computerBoard,
                    cell: computerCell,
                    player: GAME_CONSTANTS.PLAYERS.COMPUTER,
                    timestamp: new Date().toISOString()
                });
                
                // Update next_to_move to be the player's turn again
                this.gameState.next_to_move = GAME_CONSTANTS.PLAYERS.HUMAN;
                console.log("Next to move after computer move:", this.gameState.next_to_move);
                
                // Update UI after computer move
                this.uiManager.updateLastMove(computerBoard, computerCell);
                this.gameState.checkBoardStatus();
                this.uiManager.renderBoard();
                this.uiManager.forceUpdateCellStates();
                this.uiManager.updateGameStatus();
                this.uiManager.updateMoveHistoryDisplay();
                
                // Update metadata if available
                if (data.metadata) {
                    this.uiManager.updateMetadata(data.metadata);
                }
                
            } catch (error) {
                console.error('Error with server communication:', error);
            }
        } else {
            // If no game ID, make a local computer move
            const computerMove = await this.computerPlayer.makeMove();
            if (computerMove) {
                console.log("Local computer move:", computerMove);
                // Ensure the board is updated with the computer's move
                this.gameState.checkBoardStatus();
                this.uiManager.renderBoard();
                this.uiManager.forceUpdateCellStates();
                this.uiManager.updateGameStatus();
                this.uiManager.updateMoveHistoryDisplay();
            }
        }
    }

    loadSelectedGame() {
        console.log("Load game called");
        const selectedId = this.uiManager.savedGamesSelect.value;
        console.log("Selected game:", selectedId);
        if (selectedId) {
            this.uiManager.loadGame(selectedId);
        }
    }

    reset() {
        this.gameState.reset();
        this.uiManager.reset();
        this.uiManager.renderBoard();
    }

    // Add to the Game class
    updateGameName() {
        const nameInput = document.getElementById('game-name');
        const newName = nameInput.value.trim();

        if (!newName) {
            alert('Please enter a valid game name');
            return;
        }

        if (!this.gameState.gameId) {
            alert('No active game to rename');
            return;
        }

        // Call the API to update the name
        fetch(GAME_CONSTANTS.API_ENDPOINTS.UPDATE_GAME_NAME(this.gameState.gameId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: newName
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.uiManager.updateGameName(newName);
                this.uiManager.updateSavedGamesDropdown();
            } else {
                alert('Failed to update game name');
            }
        })
        .catch(error => {
            console.error('Error updating game name:', error);
            alert('Failed to update game name');
        });
    }
    
    // Trigger a computer move manually
    // This is useful when navigating to a point in history where it's the computer's turn
    async triggerComputerMove() {
        console.log("Manually triggering computer move");
        
        // Debug the current state
        console.log("Game state before computer move:");
        console.log("- Next to move:", this.gameState.next_to_move);
        console.log("- Move number:", this.gameState.moveNumber);
        console.log("- Total moves:", this.gameState.totalMoves);
        console.log("- Target board:", this.gameState.targetBoard);
        
        // Check if it's the computer's turn
        if (this.gameState.next_to_move !== GAME_CONSTANTS.PLAYERS.COMPUTER) {
            console.log("Not computer's turn, current turn:", this.gameState.next_to_move);
            alert("It's not the computer's turn to move");
            return;
        }
        
        // If we're in a state where the game is over, don't allow moves
        if (this.gameState.winner || this.gameState.boardFull) {
            console.log("Game is over, can't make more moves");
            alert("The game is already over");
            return;
        }
        
        // If we're making a move after navigating to a previous move,
        // update the totalMoves to match the current move number
        if (this.gameState.moveNumber - 1 < this.gameState.totalMoves) {
            console.log(`Truncating move history: ${this.gameState.moveNumber - 1} < ${this.gameState.totalMoves}`);
            this.gameState.totalMoves = this.gameState.moveNumber - 1;
        }
        
        // Trigger the computer move
        const computerMove = await this.computerPlayer.makeMove();
        if (computerMove) {
            console.log("Computer move triggered:", computerMove);
            
            // If we have a game ID, update the totalMoves
            if (this.gameState.gameId) {
                this.gameState.totalMoves = this.gameState.moveNumber - 1;
            }
            
            // Ensure the board is updated with the computer's move
            this.gameState.checkBoardStatus();
            this.uiManager.renderBoard();
            this.uiManager.forceUpdateCellStates();
            this.uiManager.updateGameStatus();
            this.uiManager.updateMoveHistoryDisplay();
            
            // Debug the state after the move
            console.log("Game state after computer move:");
            console.log("- Next to move:", this.gameState.next_to_move);
            console.log("- Move number:", this.gameState.moveNumber);
            console.log("- Total moves:", this.gameState.totalMoves);
            console.log("- Target board:", this.gameState.targetBoard);
        } else {
            console.error("Failed to trigger computer move");
            alert("Failed to trigger computer move");
        }
    }
}

// Initialize the game
window.addEventListener('DOMContentLoaded', () => {
    window.game = new Game();
    // Bind the reset function to window for global access
    window.reset_board = () => window.game.reset();
});
