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
        this.uiManager.addToPastMoves(board, cell, GAME_CONSTANTS.PLAYERS.HUMAN);
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

    reset() {
        this.gameState.reset();
        this.uiManager.reset();
        this.uiManager.renderBoard();
    }
}

// Initialize the game
window.addEventListener('DOMContentLoaded', () => {
    window.game = new Game();
    // Bind the reset function to window for global access
    window.reset_board = () => window.game.reset();
});