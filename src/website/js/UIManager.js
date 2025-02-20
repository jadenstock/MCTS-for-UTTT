class UIManager {
    constructor(gameState) {
        this.gameState = gameState;
        this.initializeElements();

        // Add debug log
        console.log("UIManager constructor complete");

        // Wait for DOM to be ready before initializing dropdown
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                console.log("DOMContentLoaded event fired");
                this.updateSavedGamesDropdown();
            });
        } else {
            // DOM is already ready
            console.log("DOM already loaded, updating dropdown immediately");
            this.updateSavedGamesDropdown();
        }
    }

    initializeElements() {
        console.log("Initializing UI elements");
        this.boardContainer = document.querySelector(".game-board");
        this.winnerElement = document.getElementById("winner");
        this.lastMoveElement = document.getElementById("last-move");
        this.computeTimeValue = document.getElementById("compute-time-value");
        this.movesElement = document.getElementById("metadata-moves");
        this.thinkingMessage = document.getElementById("thinking-message");
        this.savedGamesSelect = document.getElementById("saved-games");
        this.gameNameInput = document.getElementById("game-name");
        console.log("Saved games select element:", this.savedGamesSelect);
    }

    async updateSavedGamesDropdown() {
        console.log("Attempting to update saved games dropdown");
        try {
            const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.LIST_GAMES);
            console.log("API response received:", response);
            const games = await response.json();
            console.log("Games data:", games);

            if (!this.savedGamesSelect) {
                console.error("savedGamesSelect element not found!");
                return;
            }

            // Clear existing options except the first placeholder
            this.savedGamesSelect.innerHTML = '<option value="">Select a game...</option>';

            // Add an option for each saved game
            games.forEach(game => {
                const option = document.createElement('option');
                option.value = game.game_id;
                option.textContent = game.name || `Game ${game.game_id.slice(0, 8)}...`;
                this.savedGamesSelect.appendChild(option);
            });

            console.log("Dropdown updated successfully");
        } catch (error) {
            console.error('Failed to load games list:', error);
        }
    }

    updateGameName(name) {
        if (this.gameNameInput) {
            this.gameNameInput.value = name;
        }
    }

    async loadGame(gameId) {
        try {
            const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.LOAD_GAME(gameId));
            const gameData = await response.json();

            // Update the game state
            this.gameState.board = gameData.current_state.board;
            this.gameState.gameId = gameData.game_id;
            this.gameState.moveNumber = gameData.moves.length + 1;

            // Update game name if it exists
            if (gameData.name) {
                this.updateGameName(gameData.name);
            }

            // Update last move tracking
            const lastMove = gameData.current_state.last_move;
            this.lastMoveElement.dataset.lastBoard = lastMove[0];
            this.lastMoveElement.dataset.lastCell = lastMove[1];
            this.lastMoveElement.innerHTML = `Last move: B${lastMove[0] + 1}C${lastMove[1] + 1}`;

            // Force game state recalculation
            this.gameState.checkBoardStatus();

            // Render the board and ensure all cells are properly marked
            this.renderBoard();
            this.forceUpdateCellStates();
            this.updateGameStatus();

            // If it's computer's turn (O), trigger a move
            if (gameData.current_state.next_to_move === "o") {
                const computerMove = await window.game.computerPlayer.makeMove();
                if (computerMove) {
                    this.gameState.checkBoardStatus();
                    this.renderBoard();
                    this.updateGameStatus();
                }
            }

        } catch (error) {
            console.error('Failed to load game:', error);
        }
    }

    forceUpdateCellStates() {
        // Mark all existing moves as occupied
        this.gameState.board.forEach((miniBoard, boardIndex) => {
            miniBoard.forEach((cell, cellIndex) => {
                if (cell) {  // If cell has any value (X or O)
                    const cellElement = document.querySelector(`#cell_${boardIndex}${cellIndex}`);
                    if (cellElement) {
                        cellElement.classList.add("occupied");
                    }
                }
            });
        });

        // Re-check and mark won boards
        this.gameState.board.forEach((miniBoard, boardIndex) => {
            const winner = this.gameState.checkBoardWinner(miniBoard);
            if (winner) {
                // Mark all cells in won boards as occupied
                miniBoard.forEach((_, cellIndex) => {
                    const cellElement = document.querySelector(`#cell_${boardIndex}${cellIndex}`);
                    if (cellElement) {
                        cellElement.classList.add("occupied");
                    }
                });
            }
        });

        // Update legal moves based on last move
        this.updateLegalMoves();
    }

    renderBoard() {
        this.boardContainer.innerHTML = "";
        this.gameState.board.forEach((miniBoard, i) => {
            this.boardContainer.innerHTML += `
                <div id="mini-board_${i}" class="mini-board">
                    ${this.renderMiniBoard(miniBoard, i)}
                </div>`;
        });
        this.updateLegalMoves();
        this.updateComputeTime();
    }

    renderMiniBoard(miniBoard, boardIndex) {
        const winner = this.gameState.checkBoardWinner(miniBoard);
        const cells = miniBoard.map((cell, cellIndex) => `
            <div id="cell_${boardIndex}${cellIndex}"
                 class="cell"
                 onclick="game.handleCellClick(${boardIndex}, ${cellIndex})">
                ${cell}
            </div>`
        ).join('');

        return `
            ${cells}
            ${winner ? `<div class="board-winner-overlay">${winner}</div>` : ''}
        `;
    }

    updateLegalMoves() {
        // First clear all occupied markers
        this.gameState.board.forEach((miniBoard, i) => {
            miniBoard.forEach((_, j) => {
                const cell = document.querySelector(`#cell_${i}${j}`);
                if (cell) {
                    cell.classList.remove("occupied");
                    cell.style.color = '';

                    if (this.gameState.checkBoardWinner(this.gameState.board[i]) !== "") {
                        cell.classList.add("occupied");
                    }
                }
            });
        });

        // If no moves made yet, only mark occupied cells
        if (this.lastMoveElement.dataset.lastCell === "-1") {
            this.gameState.board.forEach((miniBoard, i) => {
                miniBoard.forEach((cell, j) => {
                    if (cell === GAME_CONSTANTS.PLAYERS.HUMAN ||
                        cell === GAME_CONSTANTS.PLAYERS.COMPUTER) {
                        document.querySelector(`#cell_${i}${j}`).classList.add("occupied");
                    }
                });
            });
            return;
        }

        // Process each cell
        this.gameState.board.forEach((miniBoard, i) => {
            miniBoard.forEach((cell, j) => {
                // Highlight last move in red
                if (this.lastMoveElement.dataset.lastBoard == i &&
                    this.lastMoveElement.dataset.lastCell == j) {
                    document.querySelector(`#cell_${i}${j}`).style.color = "red";
                }

                // Mark occupied cells
                if (cell === GAME_CONSTANTS.PLAYERS.HUMAN ||
                    cell === GAME_CONSTANTS.PLAYERS.COMPUTER) {
                    document.querySelector(`#cell_${i}${j}`).classList.add("occupied");
                }

                // Handle target board logic
                const targetBoard = parseInt(this.lastMoveElement.dataset.lastCell);
                const targetBoardWon = this.gameState.checkBoardWinner(this.gameState.board[targetBoard]) !== "";
                const targetBoardFull = !this.gameState.board[targetBoard].includes("");

                if (!targetBoardWon && !targetBoardFull) {
                    // If target board is not won/full, mark all cells in other boards as occupied
                    if (i !== targetBoard) {
                        document.querySelector(`#cell_${i}${j}`).classList.add("occupied");
                    }
                }
            });
        });
    }

    updateLastMove(board, cell) {
        this.lastMoveElement.innerHTML = `Last move: B${board + 1}C${cell + 1}`;
        this.lastMoveElement.dataset.lastBoard = board;
        this.lastMoveElement.dataset.lastCell = cell;
    }

    updateComputeTime() {
        const time = document.getElementById("computeTime").value;
        this.computeTimeValue.innerHTML = `${time} seconds`;
    }

    updateMetadata(metadata) {
        document.getElementById("metadata-nodes-evaluated").innerHTML =
            `<u>Gamestates Evaluated:</u> ${metadata.num_gamestates}`;
        document.getElementById("metadata-depth-evaluated").innerHTML =
            `<u>Gametree Depth:</u> ${metadata.depth_explored}`;
        document.getElementById("actual-think-time").innerHTML =
            `Actual thinking time: ${metadata.thinking_time.toFixed(2)} seconds`;
        this.updateMovesConsidered(metadata.moves);
    }

    updateMovesConsidered(moves) {
        this.movesElement.innerHTML = '<br><u>Moves Considered:</u><br>';
        moves.slice(0, 9).forEach(move => {
            this.movesElement.innerHTML +=
                `B${parseInt(move[0][0]) + 1}C${parseInt(move[0][1]) + 1}\t\t` +
                `score: ${parseFloat(move[1]).toFixed(5)}<br>`;
        });
    }

    updateGameStatus() {
        this.winnerElement.className = "";
        if (this.gameState.winner === GAME_CONSTANTS.PLAYERS.HUMAN) {
            this.winnerElement.innerText = "Winner is player!!";
            this.winnerElement.classList.add("playerWin");
        } else if (this.gameState.winner === GAME_CONSTANTS.PLAYERS.COMPUTER) {
            this.winnerElement.innerText = "Winner is computer";
            this.winnerElement.classList.add("computerWin");
        } else if (this.gameState.boardFull) {
            this.winnerElement.innerText = "Draw!";
            this.winnerElement.classList.add("draw");
        }
    }

    showThinkingMessage() {
        this.thinkingMessage.innerHTML = "Computer Thinking...";
    }

    hideThinkingMessage() {
        this.thinkingMessage.innerHTML = "";
    }

    reset() {
        this.winnerElement.className = "";
        this.winnerElement.innerText = "";
        this.lastMoveElement.innerHTML = "";
        this.lastMoveElement.dataset.lastBoard = -1;
        this.lastMoveElement.dataset.lastCell = -1;
        this.gameNameInput.value = "";  // Reset game name input

        // Reset metadata displays
        document.getElementById("metadata-nodes-evaluated").innerHTML =
            "<u>Gamestates Evaluated:</u> ...";
        document.getElementById("metadata-depth-evaluated").innerHTML =
            "<u>Gametree Depth:</u> ...";
        document.getElementById("metadata-moves").innerHTML =
            "<u>Moves Considered:</u> ...";

        // Update the games dropdown
        this.updateSavedGamesDropdown();
    }
}