class UIManager {
    constructor(gameState) {
        this.gameState = gameState;
        this.initializeElements();
    }

    initializeElements() {
        this.boardContainer = document.querySelector(".game-board");
        this.winnerElement = document.getElementById("winner");
        this.lastMoveElement = document.getElementById("last-move");
        this.computeTimeValue = document.getElementById("compute-time-value");
        this.movesElement = document.getElementById("metadata-moves");
        this.pastMovesElement = document.getElementById("past-moves");
        this.thinkingMessage = document.getElementById("thinking-message");
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

    addToPastMoves(board, cell, player) {
        this.pastMovesElement.innerHTML += `
            <option value="" data-move-number=${this.gameState.moveNumber}>
                ${this.gameState.moveNumber}) ${player}-B${board + 1}C${cell + 1}
            </option>`;
    }

    updateMetadata(metadata) {
        // Update nodes evaluated
        document.getElementById("metadata-nodes-evaluated").innerHTML =
            `<u>Gamestates Evaluated:</u> ${metadata.num_gamestates}`;

        // Update depth explored
        document.getElementById("metadata-depth-evaluated").innerHTML =
            `<u>Gametree Depth:</u> ${metadata.depth_explored}`;

        // Update actual think time
        document.getElementById("actual-think-time").innerHTML =
            `Actual thinking time: ${metadata.thinking_time.toFixed(2)} seconds`;

        // Update moves considered
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
        this.pastMovesElement.innerHTML = "";

        // Reset metadata displays
        document.getElementById("metadata-nodes-evaluated").innerHTML =
            "<u>Gamestates Evaluated:</u> ...";
        document.getElementById("metadata-depth-evaluated").innerHTML =
            "<u>Gametree Depth:</u> ...";
        document.getElementById("metadata-moves").innerHTML =
            "<u>Moves Considered:</u> ...";
    }
}