class Game {
    constructor() {
        this.gameState = new GameState();
        this.apiClient = new ApiClient(GAME_CONSTANTS.API_ENDPOINTS);
        this.uiManager = new UIManager(this.gameState, this.apiClient);
        this.computerPlayer = new ComputerPlayer(this.gameState, this.uiManager, this.apiClient);
        this.initialize();
    }

    initialize() {
        this.uiManager.renderBoard();
        // Bind the slider update function to window for global access
        window.updateSlider = (slideAmount) => {
            this.uiManager.updateComputeTime();
        };
        this.ensureDescriptiveGameId();
        this.uiManager.updateGameIdLabel(this.gameState.gameId);
    }

    isUuidLike(value) {
        if (!value) return false;
        return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
    }

    sanitizeIdPart(value) {
        return String(value || "unknown").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
    }

    makeDescriptiveGameId() {
        const xController = this.uiManager?.xControllerSelect?.value || "player";
        const oController = this.uiManager?.oControllerSelect?.value || "player";
        const now = new Date();
        const ts = [
            now.getFullYear(),
            String(now.getMonth() + 1).padStart(2, "0"),
            String(now.getDate()).padStart(2, "0"),
            String(now.getHours()).padStart(2, "0"),
            String(now.getMinutes()).padStart(2, "0"),
            String(now.getSeconds()).padStart(2, "0"),
        ].join("");
        const rand = Math.random().toString(36).slice(2, 6);
        return `${this.sanitizeIdPart(xController)}_vs_${this.sanitizeIdPart(oController)}_${ts}_${rand}`;
    }

    ensureDescriptiveGameId(force = false) {
        if (force || !this.gameState.gameId || this.isUuidLike(this.gameState.gameId)) {
            this.gameState.gameId = this.makeDescriptiveGameId();
            this.uiManager.updateGameIdLabel(this.gameState.gameId);
        }
    }

    getCurrentController() {
        return this.uiManager.getControllerForSide(this.gameState.next_to_move);
    }

    applyAuthoritativeState(data) {
        if (!data.current_state) {
            return;
        }
        this.gameState.board = this.uiManager.normalizeBoard(data.current_state.board);
        this.gameState.next_to_move = this.uiManager.normalizeToken(data.current_state.next_to_move);
        this.gameState.winner = data.current_state.winner ? this.uiManager.normalizeToken(data.current_state.winner) : null;
        this.gameState.boardFull = !!data.current_state.winner;

        if (typeof data.move_count === "number") {
            this.gameState.totalMoves = data.move_count;
            this.gameState.moveNumber = data.move_count + 1;
        }

        const lastMove = data.current_state.last_move;
        if (lastMove) {
            this.gameState.targetBoard = lastMove[1];
            this.uiManager.updateLastMove(lastMove[0], lastMove[1]);
        } else {
            this.gameState.targetBoard = -1;
        }
    }

    async runBotTurnsUntilPlayerOrEnd(maxPlies = 81) {
        let plies = 0;
        while (plies < maxPlies && !this.gameState.winner && !this.gameState.boardFull) {
            const controller = this.getCurrentController();
            if (controller === "player") {
                break;
            }
            const { ok, data } = await this.apiClient.requestNextBotMove({
                game_id: this.gameState.gameId,
                node_limit: document.getElementById("nodeLimit").value,
                ai_agent_id: controller,
            });
            if (!ok) {
                console.error("Bot turn request failed:", data.error || data);
                break;
            }
            this.applyAuthoritativeState(data);
            this.gameState.checkBoardStatus();
            this.uiManager.renderBoard();
            this.uiManager.forceUpdateCellStates();
            this.uiManager.updateGameStatus();
            this.uiManager.updateMoveHistoryDisplay();
            if (data.metadata) {
                this.uiManager.updateMetadata(data.metadata);
            }
            plies += 1;
        }
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

        // Only allow interaction when current side is configured as Player.
        if (this.getCurrentController() !== "player") {
            console.log("Move rejected: Not human turn");
            return;
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
        this.ensureDescriptiveGameId();
        if (this.gameState.gameId) {
            try {
                console.log("Sending move to server:", {
                    game_id: this.gameState.gameId,
                    game_board: this.gameState.board,
                    last_move: [board, cell, GAME_CONSTANTS.PLAYERS.HUMAN],
                    node_limit: document.getElementById("nodeLimit").value
                });
                
                const { ok, data } = await this.apiClient.requestComputerTurn({
                    game_id: this.gameState.gameId,
                    game_board: this.gameState.board,
                    last_move: [board, cell, GAME_CONSTANTS.PLAYERS.HUMAN],
                    node_limit: document.getElementById("nodeLimit").value,
                    ai_agent_id: this.uiManager.getControllerForSide(this.gameState.next_to_move),
                });
                console.log("Server response:", data);

                if (!ok) {
                    console.error("Server rejected move:", data.error || data);
                    return;
                }

                // Apply computer move if one exists.
                if (data.board !== null && data.cell !== null && data.board !== undefined && data.cell !== undefined) {
                    const computerBoard = data.board;
                    const computerCell = data.cell;
                    console.log("Computer move from server:", computerBoard, computerCell);

                    const computerMoveSuccess = this.gameState.makeMove(
                        computerBoard,
                        computerCell,
                        GAME_CONSTANTS.PLAYERS.COMPUTER
                    );
                    if (!computerMoveSuccess) {
                        console.error("Failed to apply computer move to local state");
                        return;
                    }
                }

                // Reconcile local state with authoritative server state.
                this.applyAuthoritativeState(data);

                // Update UI after computer move
                this.gameState.checkBoardStatus();
                this.uiManager.renderBoard();
                this.uiManager.forceUpdateCellStates();
                this.uiManager.updateGameStatus();
                this.uiManager.updateMoveHistoryDisplay();
                
                // Update metadata if available
                if (data.metadata) {
                    this.uiManager.updateMetadata(data.metadata);
                }
                await this.runBotTurnsUntilPlayerOrEnd();
                
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
            this.uiManager.followLiveGame(null);
            this.uiManager.loadGame(selectedId, { autoComputerMove: false, source: "user" });
        }
    }

    loadSelectedInProgressGame() {
        // Deprecated: in-progress bot games are now loaded from the Bot Games tab list.
    }

    reset() {
        this.gameState.reset();
        this.ensureDescriptiveGameId(true);
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
        this.apiClient.renameGame(this.gameState.gameId, newName)
        .then(({ ok, data }) => {
            if (ok && data.success) {
                this.uiManager.updateGameName(newName);
                this.uiManager.updateSavedGamesDropdown();
                return;
            }
            alert(data.error || 'Failed to update game name');
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
