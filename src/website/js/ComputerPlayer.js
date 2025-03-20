class ComputerPlayer {
    constructor(gameState, uiManager) {
        this.gameState = gameState;
        this.uiManager = uiManager;
    }

    async makeMove() {
        if (this.gameState.winner || this.gameState.isComputerThinking) return;

        this.gameState.isComputerThinking = true;
        this.uiManager.showThinkingMessage();

        try {
            const response = await this.requestMove();
            const moveData = await response.json();

            // Process the move
            const board = parseInt(moveData.board);
            const cell = parseInt(moveData.cell);

            // Update game state using the makeMove method
            const moveSuccess = this.gameState.makeMove(board, cell, GAME_CONSTANTS.PLAYERS.COMPUTER);
            console.log(`Computer move to board ${board}, cell ${cell}, success: ${moveSuccess}`);
            
            // Debug the board state
            console.log("Board state after computer move:", JSON.stringify(this.gameState.board));

            // Update last move element's dataset
            this.uiManager.updateLastMove(board, cell);

            // Update metadata
            this.uiManager.updateMetadata(moveData.metadata);

            // Return the move for the game class to handle
            return { board, cell };

        } catch (error) {
            console.error('Error making computer move:', error);
            return null;
        } finally {
            this.gameState.isComputerThinking = false;
            this.uiManager.hideThinkingMessage();
        }
    }

    async requestMove() {
        // Determine the last move player based on whose turn it is now
        // If it's computer's turn now, the last move must have been by the human
        // If we're at the start of the game, use a default last move
        const lastBoard = parseInt(document.getElementById("last-move").dataset.lastBoard);
        const lastCell = parseInt(document.getElementById("last-move").dataset.lastCell);
        
        // Default to human as the last player if we have a valid last move
        let lastPlayer = GAME_CONSTANTS.PLAYERS.HUMAN;
        
        // If we're at the beginning of the game with no moves yet
        if (lastBoard === -1 || lastCell === -1) {
            console.log("No last move found, using default values");
        }
        
        console.log(`Last move: board ${lastBoard}, cell ${lastCell}, player ${lastPlayer}`);
        
        const requestData = {
            game_id: this.gameState.gameId,
            last_move: [lastBoard, lastCell, lastPlayer],
            game_board: this.gameState.board,
            compute_time: document.getElementById("computeTime").value,
            force_full_time: document.getElementById("forceFullTime").checked
        };

        console.log("Sending move request to server:", requestData);

        return fetch(GAME_CONSTANTS.API_ENDPOINTS.MAKE_MOVE, {
            method: "POST",
            mode: 'cors',
            body: JSON.stringify(requestData),
            headers: {
                'Content-Type': 'application/json',
                'Accept-Charset': 'UTF-8'
            },
            credentials: "same-origin"
        });
    }
}
