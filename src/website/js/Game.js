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
        // Check if cell is occupied using UI state
        const cellElement = document.querySelector(`#cell_${board}${cell}`);
        if (cellElement.classList.contains("occupied") ||
            this.gameState.isComputerThinking) {
            return;
        }

        // Make the move if valid
        this.gameState.board[board][cell] = GAME_CONSTANTS.PLAYERS.HUMAN;
        this.gameState.moveNumber++;

        // Update UI after human move
        this.uiManager.updateLastMove(board, cell);
        this.uiManager.renderBoard();
        this.uiManager.updateGameStatus();

        // Make computer move
        const computerMove = await this.computerPlayer.makeMove();
        if (computerMove) {
            this.gameState.checkBoardStatus();
            this.uiManager.renderBoard();
            this.uiManager.updateGameStatus();
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
}

// Initialize the game
window.addEventListener('DOMContentLoaded', () => {
    window.game = new Game();
    // Bind the reset function to window for global access
    window.reset_board = () => window.game.reset();
});