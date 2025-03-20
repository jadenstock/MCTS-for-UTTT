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
        
        // Move history elements
        this.currentMoveDisplay = document.getElementById("current-move-display");
        this.firstMoveBtn = document.getElementById("first-move-btn");
        this.prevMoveBtn = document.getElementById("prev-move-btn");
        this.nextMoveBtn = document.getElementById("next-move-btn");
        this.lastMoveBtn = document.getElementById("last-move-btn");
        
        // Computer move control elements
        this.turnIndicator = document.getElementById("turn-indicator");
        this.triggerComputerMoveBtn = document.getElementById("trigger-computer-move-btn");
        
        // Snapshot elements
        this.snapshotNameInput = document.getElementById("snapshot-name");
        this.snapshotsSelect = document.getElementById("snapshots-select");
        this.createSnapshotBtn = document.getElementById("create-snapshot-btn");
        this.restoreSnapshotBtn = document.getElementById("restore-snapshot-btn");
        
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
            this.gameState.totalMoves = gameData.moves.length;
            this.gameState.moves = gameData.moves;
            
            // Critical: Update next_to_move from the server response
            this.gameState.next_to_move = gameData.current_state.next_to_move;
            console.log("Next to move after loading game:", this.gameState.next_to_move);
            
            // Reset winner and boardFull to allow continued play
            this.gameState.winner = gameData.current_state.winner || null;
            this.gameState.boardFull = !!gameData.current_state.winner;

            // Update game name if it exists
            if (gameData.name) {
                this.updateGameName(gameData.name);
            }

            // Update target board from last move
            const lastMove = gameData.current_state.last_move;
            if (lastMove) {
                this.gameState.targetBoard = lastMove[1]; // Set target board to the cell of the last move
                
                // Update last move tracking
                this.lastMoveElement.dataset.lastBoard = lastMove[0];
                this.lastMoveElement.dataset.lastCell = lastMove[1];
                this.lastMoveElement.innerHTML = `Last move: B${lastMove[0] + 1}C${lastMove[1] + 1}`;
            } else {
                this.gameState.targetBoard = -1; // No moves yet, can play anywhere
                this.lastMoveElement.dataset.lastBoard = -1;
                this.lastMoveElement.dataset.lastCell = -1;
                this.lastMoveElement.innerHTML = '';
            }

            // Force game state recalculation
            this.gameState.checkBoardStatus();

            // Render the board and ensure all cells are properly marked
            this.renderBoard();
            this.forceUpdateCellStates();
            this.updateGameStatus();
            
            // Update move history display
            this.updateMoveHistoryDisplay();
            
            // Update snapshots dropdown
            this.updateSnapshotsDropdown();

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
        
        // Update turn indicator
        this.updateTurnIndicator();
    }
    
    updateTurnIndicator() {
        if (this.gameState.winner || this.gameState.boardFull) {
            this.turnIndicator.textContent = "Game Over";
            this.turnIndicator.style.color = "black";
            this.triggerComputerMoveBtn.disabled = true;
            return;
        }
        
        if (this.gameState.next_to_move === GAME_CONSTANTS.PLAYERS.HUMAN) {
            this.turnIndicator.textContent = "Your Turn (X)";
            this.turnIndicator.style.color = "blue";
            this.triggerComputerMoveBtn.disabled = true;
        } else {
            this.turnIndicator.textContent = "Computer's Turn (O)";
            this.turnIndicator.style.color = "red";
            this.triggerComputerMoveBtn.disabled = false;
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
        this.snapshotNameInput.value = ""; // Reset snapshot name input
        
        // Reset move history display
        this.currentMoveDisplay.textContent = "Move: 0/0";
        
        // Clear snapshots dropdown
        this.snapshotsSelect.innerHTML = '<option value="">Select a snapshot...</option>';

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
    
    // Move History Navigation Methods
    
    updateMoveHistoryDisplay() {
        const currentMove = this.gameState.moveNumber - 1;
        const totalMoves = this.gameState.totalMoves || 0;
        this.currentMoveDisplay.textContent = `Move: ${currentMove}/${totalMoves}`;
        
        // Enable/disable navigation buttons based on current position
        this.firstMoveBtn.disabled = currentMove <= 0;
        this.prevMoveBtn.disabled = currentMove <= 0;
        this.nextMoveBtn.disabled = currentMove >= totalMoves;
        this.lastMoveBtn.disabled = currentMove >= totalMoves;
    }
    
    async navigateToMove(moveNumber) {
        if (!this.gameState.gameId) {
            alert('No active game to navigate');
            return;
        }
        
        try {
            this.showThinkingMessage();
            const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.RESTORE_TO_MOVE(this.gameState.gameId, moveNumber), {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.success) {
                // Update game state with restored data
                const gameData = data.game;
                
                // Update the board state to the current move
                this.gameState.board = gameData.current_state.board;
                
                // Set the current move number based on the current_move_index
                const currentMoveIndex = gameData.current_move_index || moveNumber;
                this.gameState.moveNumber = currentMoveIndex + 1;
                
                // Store all moves in history and set totalMoves to the total number of moves
                this.gameState.moves = gameData.moves;
                this.gameState.totalMoves = gameData.moves.length;
                
                console.log(`Move navigation: ${this.gameState.moveNumber - 1}/${this.gameState.totalMoves}`);
                
                // Critical: Update next_to_move from the server response
                this.gameState.next_to_move = gameData.current_state.next_to_move;
                console.log("Next to move after navigation:", this.gameState.next_to_move);
                
                // Reset winner and boardFull to allow continued play
                this.gameState.winner = null;
                this.gameState.boardFull = false;
                
                // Update target board from last move
                const lastMove = gameData.current_state.last_move;
                if (lastMove) {
                    this.gameState.targetBoard = lastMove[1]; // Set target board to the cell of the last move
                    
                    // Update last move tracking
                    this.lastMoveElement.dataset.lastBoard = lastMove[0];
                    this.lastMoveElement.dataset.lastCell = lastMove[1];
                    this.lastMoveElement.innerHTML = `Last move: B${lastMove[0] + 1}C${lastMove[1] + 1}`;
                } else {
                    this.gameState.targetBoard = -1; // No moves yet, can play anywhere
                    this.lastMoveElement.dataset.lastBoard = -1;
                    this.lastMoveElement.dataset.lastCell = -1;
                    this.lastMoveElement.innerHTML = '';
                }
                
                // Force game state recalculation
                this.gameState.checkBoardStatus();
                
                // Update UI
                this.renderBoard();
                this.forceUpdateCellStates();
                this.updateGameStatus(); // This calls updateTurnIndicator()
                this.updateMoveHistoryDisplay();
                
                // Debug the current state
                console.log("Game state after navigation:");
                console.log("- Next to move:", this.gameState.next_to_move);
                console.log("- Move number:", this.gameState.moveNumber);
                console.log("- Total moves:", this.gameState.totalMoves);
                console.log("- Target board:", this.gameState.targetBoard);
            } else {
                alert('Failed to navigate to move: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error navigating to move:', error);
            alert('Failed to navigate to move: ' + error.message);
        } finally {
            this.hideThinkingMessage();
        }
    }
    
    navigateToPreviousMove() {
        const currentMove = this.gameState.moveNumber - 1;
        if (currentMove > 0) {
            this.navigateToMove(currentMove - 1);
        }
    }
    
    navigateToNextMove() {
        const currentMove = this.gameState.moveNumber - 1;
        const totalMoves = this.gameState.totalMoves || 0;
        if (currentMove < totalMoves) {
            this.navigateToMove(currentMove + 1);
        }
    }
    
    navigateToLastMove() {
        const totalMoves = this.gameState.totalMoves || 0;
        if (totalMoves > 0) {
            this.navigateToMove(totalMoves);
        }
    }
    
    // Snapshot Management Methods
    
    async updateSnapshotsDropdown() {
        if (!this.gameState.gameId) {
            return;
        }
        
        try {
            const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.LIST_SNAPSHOTS(this.gameState.gameId));
            const snapshots = await response.json();
            
            // Clear existing options except the first placeholder
            this.snapshotsSelect.innerHTML = '<option value="">Select a snapshot...</option>';
            
            // Add an option for each snapshot
            snapshots.forEach(snapshot => {
                const option = document.createElement('option');
                option.value = snapshot.id;
                option.textContent = snapshot.label || `Snapshot at move ${snapshot.move_number}`;
                this.snapshotsSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load snapshots:', error);
        }
    }
    
    async createSnapshot() {
        if (!this.gameState.gameId) {
            alert('No active game to snapshot');
            return;
        }
        
        const label = this.snapshotNameInput.value.trim() || `Snapshot at move ${this.gameState.moveNumber - 1}`;
        
        try {
            this.showThinkingMessage();
            const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.CREATE_SNAPSHOT(this.gameState.gameId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ label })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Snapshot created successfully');
                this.snapshotNameInput.value = ''; // Clear the input
                this.updateSnapshotsDropdown(); // Refresh the dropdown
            } else {
                alert('Failed to create snapshot: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error creating snapshot:', error);
            alert('Failed to create snapshot: ' + error.message);
        } finally {
            this.hideThinkingMessage();
        }
    }
    
    async restoreSelectedSnapshot() {
        if (!this.gameState.gameId) {
            alert('No active game to restore');
            return;
        }
        
        const snapshotId = this.snapshotsSelect.value;
        if (!snapshotId) {
            alert('Please select a snapshot to restore');
            return;
        }
        
        try {
            this.showThinkingMessage();
            const response = await fetch(GAME_CONSTANTS.API_ENDPOINTS.RESTORE_SNAPSHOT(this.gameState.gameId, snapshotId), {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.success) {
                // Update game state with restored data
                const gameData = data.game;
                
                // Update the board state to the current move
                this.gameState.board = gameData.current_state.board;
                
                // Set the current move number based on the current_move_index
                const currentMoveIndex = gameData.current_move_index || gameData.moves.length;
                this.gameState.moveNumber = currentMoveIndex + 1;
                
                // Store all moves in history and set totalMoves to the total number of moves
                this.gameState.moves = gameData.moves;
                this.gameState.totalMoves = gameData.moves.length;
                
                console.log(`Snapshot restore: ${this.gameState.moveNumber - 1}/${this.gameState.totalMoves}`);
                
                // Critical: Update next_to_move from the server response
                this.gameState.next_to_move = gameData.current_state.next_to_move;
                console.log("Next to move after snapshot restore:", this.gameState.next_to_move);
                
                // Reset winner and boardFull to allow continued play
                this.gameState.winner = null;
                this.gameState.boardFull = false;
                
                // Update target board from last move
                const lastMove = gameData.current_state.last_move;
                if (lastMove) {
                    this.gameState.targetBoard = lastMove[1]; // Set target board to the cell of the last move
                    
                    // Update last move tracking
                    this.lastMoveElement.dataset.lastBoard = lastMove[0];
                    this.lastMoveElement.dataset.lastCell = lastMove[1];
                    this.lastMoveElement.innerHTML = `Last move: B${lastMove[0] + 1}C${lastMove[1] + 1}`;
                } else {
                    this.gameState.targetBoard = -1; // No moves yet, can play anywhere
                    this.lastMoveElement.dataset.lastBoard = -1;
                    this.lastMoveElement.dataset.lastCell = -1;
                    this.lastMoveElement.innerHTML = '';
                }
                
                // Force game state recalculation
                this.gameState.checkBoardStatus();
                
                // Update UI
                this.renderBoard();
                this.forceUpdateCellStates();
                this.updateGameStatus(); // This calls updateTurnIndicator()
                this.updateMoveHistoryDisplay();
                
                // Debug the current state
                console.log("Game state after snapshot restore:");
                console.log("- Next to move:", this.gameState.next_to_move);
                console.log("- Move number:", this.gameState.moveNumber);
                console.log("- Total moves:", this.gameState.totalMoves);
                console.log("- Target board:", this.gameState.targetBoard);
                
                this.updateSnapshotsDropdown(); // Refresh snapshots list
                
                alert('Snapshot restored successfully');
            } else {
                alert('Failed to restore snapshot: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error restoring snapshot:', error);
            alert('Failed to restore snapshot: ' + error.message);
        } finally {
            this.hideThinkingMessage();
        }
    }
}
