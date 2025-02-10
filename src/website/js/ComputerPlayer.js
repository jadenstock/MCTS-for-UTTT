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

            // Update game state
            this.gameState.board[board][cell] = GAME_CONSTANTS.PLAYERS.COMPUTER;

            // Update UI and last move tracking
            this.uiManager.addToPastMoves(board, cell, GAME_CONSTANTS.PLAYERS.COMPUTER);

            // Critical: Update last move element's dataset
            const lastMoveElement = document.getElementById("last-move");
            lastMoveElement.innerHTML = `Last move: B${board+1}C${cell+1}`;
            lastMoveElement.dataset.lastBoard = board;
            lastMoveElement.dataset.lastCell = cell;

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
        const requestData = {
            game_id: this.gameState.gameId,
            last_move: [
                parseInt(document.getElementById("last-move").dataset.lastBoard),
                parseInt(document.getElementById("last-move").dataset.lastCell),
                GAME_CONSTANTS.PLAYERS.HUMAN
            ],
            game_board: this.gameState.board,
            compute_time: document.getElementById("computeTime").value,
            force_full_time: document.getElementById("forceFullTime").checked
        };

        return fetch(GAME_CONSTANTS.API_ENDPOINT, {
            method: "POST",
            mode: 'cors',
            body: JSON.stringify(JSON.stringify(requestData)),
            headers: {
                'Content-Type': 'application/json',
                'Accept-Charset': 'UTF-8'
            },
            credentials: "same-origin"
        });
    }
}