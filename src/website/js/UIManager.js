class UIManager {
    constructor(gameState, apiClient) {
        this.gameState = gameState;
        this.apiClient = apiClient;
        this.liveFollowGameId = null;
        this.activeGameSource = "user";
        this.initializeElements();
        this.initializeTabs();
        this.startArchivePolling();

        // Add debug log
        console.log("UIManager constructor complete");

        // Wait for DOM to be ready before initializing dropdown
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                console.log("DOMContentLoaded event fired");
                this.updateSavedGamesDropdown();
                this.updateBotGamesList();
                this.initializeBotSelectors();
            });
        } else {
            // DOM is already ready
            console.log("DOM already loaded, updating dropdown immediately");
            this.updateSavedGamesDropdown();
            this.updateBotGamesList();
            this.initializeBotSelectors();
        }
    }

    initializeElements() {
        console.log("Initializing UI elements");
        this.boardContainer = document.querySelector(".game-board");
        this.winnerElement = document.getElementById("winner");
        this.lastMoveElement = document.getElementById("last-move");
        this.gameIdLabel = document.getElementById("game-id-label");
        this.computeTimeValue = document.getElementById("compute-time-value");
        this.movesElement = document.getElementById("metadata-moves");
        this.thinkingMessage = document.getElementById("thinking-message");
        this.savedGamesSelect = document.getElementById("saved-games");
        this.botGamesListElement = document.getElementById("bot-games-list");
        this.gamesFilterSelect = document.getElementById("games-filter");
        this.xControllerSelect = document.getElementById("x-controller");
        this.oControllerSelect = document.getElementById("o-controller");
        this.botsSelect = document.getElementById("bots-select");
        this.botDetailsElement = document.getElementById("bot-details");
        this.gameNameInput = document.getElementById("game-name");
        this.playTabButton = document.getElementById("tab-play");
        this.archiveTabButton = document.getElementById("tab-archive");
        this.botsTabButton = document.getElementById("tab-bots");
        this.playView = document.getElementById("play-view");
        this.archiveView = document.getElementById("archive-view");
        this.botsView = document.getElementById("bots-view");
        
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

    async initializeBotSelectors() {
        try {
            const { ok, data } = await this.apiClient.listBots();
            if (!ok || !Array.isArray(data)) {
                return;
            }
            const options = [{ bot_id: "player", family: "human", notes: "Human player" }, ...data];
            const fill = (select, withHuman = true) => {
                if (!select) return;
                select.innerHTML = "";
                if (withHuman) {
                    const human = document.createElement("option");
                    human.value = "player";
                    human.textContent = "player (human)";
                    select.appendChild(human);
                }
                const families = {};
                options.forEach(opt => {
                    if (opt.bot_id === "player") return;
                    const fam = opt.family || "unknown";
                    if (!families[fam]) families[fam] = [];
                    families[fam].push(opt);
                });
                Object.keys(families).sort().forEach(fam => {
                    const group = document.createElement("optgroup");
                    group.label = `${fam} family`;
                    families[fam].sort((a, b) => a.bot_id.localeCompare(b.bot_id)).forEach(opt => {
                        const option = document.createElement("option");
                        option.value = opt.bot_id;
                        option.textContent = `${opt.bot_id} (preset)`;
                        group.appendChild(option);
                    });
                    select.appendChild(group);
                });
            };
            fill(this.xControllerSelect, true);
            fill(this.oControllerSelect, true);
            fill(this.botsSelect, false);
            if (this.xControllerSelect) this.xControllerSelect.value = "player";
            if (this.oControllerSelect) this.oControllerSelect.value = "pragmatic_v1";
            if (this.botsSelect && data.length > 0) {
                this.botsSelect.value = data[0].bot_id;
                this.renderBotDetails(data[0]);
            }
            if (this.botsSelect) {
                this.botsSelect.addEventListener("change", () => {
                    const selected = data.find(x => x.bot_id === this.botsSelect.value);
                    this.renderBotDetails(selected || null);
                });
            }
        } catch (e) {
            console.error("Failed to initialize bot selectors:", e);
        }
    }

    renderBotDetails(bot) {
        if (!this.botDetailsElement) return;
        if (!bot) {
            this.botDetailsElement.textContent = "";
            return;
        }
        this.botDetailsElement.textContent = [
            `family: ${bot.family}`,
            `preset_id: ${bot.bot_id}`,
            `ucb_constant: ${bot.ucb_constant}`,
            `rollout_depth: ${bot.rollout_depth}`,
            `notes: ${bot.notes || ""}`,
        ].join("\n");
    }

    getControllerForSide(sideToken) {
        const side = this.normalizeToken(sideToken);
        if (side === "X" && this.xControllerSelect) {
            return this.xControllerSelect.value || "player";
        }
        if (side === "O" && this.oControllerSelect) {
            return this.oControllerSelect.value || "player";
        }
        return "player";
    }

    normalizeToken(token) {
        return token ? token.toString().toUpperCase() : "";
    }

    normalizeBoard(board) {
        return board.map(miniBoard => miniBoard.map(cell => this.normalizeToken(cell)));
    }

    async updateSavedGamesDropdown() {
        console.log("Attempting to update saved games dropdown");
        try {
            const { ok, data: games } = await this.apiClient.listGames(false);
            console.log("API response received:", ok);
            console.log("Games data:", games);
            if (!ok) {
                throw new Error(games.error || "Failed to list games");
            }

            if (!this.savedGamesSelect) {
                console.error("savedGamesSelect element not found!");
                return;
            }

            // Clear existing options except the first placeholder
            this.savedGamesSelect.innerHTML = '<option value="">Select a game...</option>';

            // Add only non-bot games to the user dropdown.
            games.forEach(game => {
                if (game.is_bot_game) {
                    return;
                }
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

    async updateBotGamesList() {
        if (!this.botGamesListElement) {
            return;
        }
        try {
            const [{ ok: okUser, data: userGames }, { ok: okBot, data: botGames }] = await Promise.all([
                this.apiClient.listGames(false),
                this.apiClient.listBotGames(false),
            ]);
            if (!okUser || !okBot) {
                throw new Error("Failed to load games list");
            }
            const merged = [
                ...userGames.filter(g => !g.is_bot_game).map(g => ({ ...g, source: "user" })),
                ...botGames.map(g => ({ ...g, source: "bot", is_bot_game: true })),
            ];
            const filter = this.gamesFilterSelect ? this.gamesFilterSelect.value : "all";
            const filtered = merged.filter(game => {
                if (filter === "user") return game.source === "user";
                if (filter === "bot") return game.source === "bot";
                if (filter === "in_progress") return game.in_progress;
                return true;
            }).sort((a, b) => {
                const ta = a.last_updated || "";
                const tb = b.last_updated || "";
                return tb.localeCompare(ta);
            });
            if (!filtered.length) {
                this.botGamesListElement.innerHTML = "<p class='panel-subtitle'>No games for selected filter.</p>";
                return;
            }
            this.botGamesListElement.innerHTML = "";
            filtered.forEach(game => {
                const row = document.createElement("div");
                row.className = "bot-game-row";
                const status = game.in_progress ? "in_progress" : (game.winner || "draw");
                row.innerHTML = `
                    <div>${game.game_id}</div>
                    <div>${game.source} | x=${game.agent_x || "?"} o=${game.agent_o || "?"}</div>
                    <div>status=${status}</div>
                    <div>nodes=${game.node_limit ?? "n/a"}</div>
                    <button type="button">View</button>
                `;
                row.querySelector("button").addEventListener("click", async () => {
                    this.followLiveGame(game.in_progress ? game.game_id : null);
                    this.activeGameSource = game.source;
                    await this.loadGame(game.game_id, { autoComputerMove: false, source: game.source });
                    this.switchTab("play");
                });
                this.botGamesListElement.appendChild(row);
            });
        } catch (error) {
            console.error("Failed to load bot games list:", error);
            this.botGamesListElement.innerHTML = "<p class='panel-subtitle'>Failed to load bot games.</p>";
        }
    }

    updateGameName(name) {
        if (this.gameNameInput) {
            this.gameNameInput.value = name;
        }
    }

    updateGameIdLabel(gameId) {
        if (!this.gameIdLabel) {
            return;
        }
        this.gameIdLabel.textContent = gameId ? `Game ID: ${gameId}` : "";
    }

    initializeTabs() {
        if (!this.playTabButton || !this.archiveTabButton || !this.playView || !this.archiveView) {
            return;
        }
        this.playTabButton.addEventListener("click", () => this.switchTab("play"));
        this.archiveTabButton.addEventListener("click", () => this.switchTab("archive"));
        if (this.botsTabButton) {
            this.botsTabButton.addEventListener("click", () => this.switchTab("bots"));
        }
        if (this.gamesFilterSelect) {
            this.gamesFilterSelect.addEventListener("change", () => this.updateBotGamesList());
        }
    }

    switchTab(tabName) {
        const playActive = tabName === "play";
        const archiveActive = tabName === "archive";
        const botsActive = tabName === "bots";
        this.playTabButton.classList.toggle("active", playActive);
        this.archiveTabButton.classList.toggle("active", archiveActive);
        if (this.botsTabButton) {
            this.botsTabButton.classList.toggle("active", botsActive);
        }
        this.playView.classList.toggle("active", playActive);
        this.archiveView.classList.toggle("active", archiveActive);
        if (this.botsView) {
            this.botsView.classList.toggle("active", botsActive);
        }
        if (archiveActive) {
            this.updateBotGamesList();
        }
    }

    startArchivePolling() {
        setInterval(async () => {
            await this.updateSavedGamesDropdown();
            await this.updateBotGamesList();

            if (!this.liveFollowGameId) {
                return;
            }
            try {
                const liveLoader = this.activeGameSource === "bot"
                    ? this.apiClient.loadBotGame.bind(this.apiClient)
                    : this.apiClient.loadGame.bind(this.apiClient);
                const { ok, data } = await liveLoader(this.liveFollowGameId);
                if (!ok) {
                    return;
                }
                if (data.current_state && !data.current_state.winner) {
                    await this.loadGame(this.liveFollowGameId, {
                        autoComputerMove: false,
                        source: this.activeGameSource,
                    });
                } else {
                    this.liveFollowGameId = null;
                }
            } catch (err) {
                console.error("Archive polling error:", err);
            }
        }, 2500);
    }

    followLiveGame(gameId) {
        this.liveFollowGameId = gameId || null;
    }

    async loadGame(gameId, options = {}) {
        try {
            const autoComputerMove = !!options.autoComputerMove;
            const source = options.source || this.activeGameSource || "user";
            const loader = source === "bot"
                ? this.apiClient.loadBotGame.bind(this.apiClient)
                : this.apiClient.loadGame.bind(this.apiClient);
            const { ok, data: gameData } = await loader(gameId);
            if (!ok) {
                throw new Error(gameData.error || "Failed to load game");
            }
            this.activeGameSource = source;

            // Update the game state
            this.gameState.board = this.normalizeBoard(gameData.current_state.board);
            this.gameState.gameId = gameData.game_id;
            this.updateGameIdLabel(this.gameState.gameId);
            this.gameState.moveNumber = gameData.moves.length + 1;
            this.gameState.totalMoves = gameData.moves.length;
            this.gameState.moves = gameData.moves;
            
            // Critical: Update next_to_move from the server response
            this.gameState.next_to_move = this.normalizeToken(gameData.current_state.next_to_move);
            console.log("Next to move after loading game:", this.gameState.next_to_move);
            
            // Reset winner and boardFull to allow continued play
            this.gameState.winner = gameData.current_state.winner ? this.normalizeToken(gameData.current_state.winner) : null;
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
            if (autoComputerMove && gameData.current_state.next_to_move === "o" && this.playView && this.playView.classList.contains("active")) {
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
                    if (cell) {
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
                if (cell) {
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
        const nodeLimitEl = document.getElementById("nodeLimit");
        if (!nodeLimitEl) {
            return;
        }
        const nodes = nodeLimitEl.value;
        this.computeTimeValue.innerHTML = `${nodes} nodes`;
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
            const board = parseInt(move[0][0]);
            const cell = parseInt(move[0][1]);
            const score = parseFloat(move[1]);
            const rollouts = move.length > 2 ? parseInt(move[2]) : null;
            this.movesElement.innerHTML +=
                `B${board + 1}C${cell + 1}\t\t` +
                `score: ${score.toFixed(5)}` +
                `${Number.isInteger(rollouts) ? ` | rollouts: ${rollouts}` : ''}<br>`;
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
            if (this.triggerComputerMoveBtn) {
                this.triggerComputerMoveBtn.disabled = true;
            }
            return;
        }
        
        if (this.gameState.next_to_move === GAME_CONSTANTS.PLAYERS.HUMAN) {
            this.turnIndicator.textContent = "Your Turn (X)";
            this.turnIndicator.style.color = "blue";
            if (this.triggerComputerMoveBtn) {
                this.triggerComputerMoveBtn.disabled = true;
            }
        } else {
            this.turnIndicator.textContent = "Computer's Turn (O)";
            this.turnIndicator.style.color = "red";
            if (this.triggerComputerMoveBtn) {
                this.triggerComputerMoveBtn.disabled = false;
            }
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
        this.updateGameIdLabel(this.gameState.gameId);

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
            const restorer = this.activeGameSource === "bot"
                ? this.apiClient.restoreBotToMove.bind(this.apiClient)
                : this.apiClient.restoreToMove.bind(this.apiClient);
            const { ok, data } = await restorer(this.gameState.gameId, moveNumber);
            if (!ok) {
                throw new Error(data.error || "Failed to restore move");
            }
            if (data.success) {
                // Update game state with restored data
                const gameData = data.game;
                
                // Update the board state to the current move
                this.gameState.board = this.normalizeBoard(gameData.current_state.board);
                
                // Set the current move number based on the current_move_index
                const currentMoveIndex = gameData.current_move_index || moveNumber;
                this.gameState.moveNumber = currentMoveIndex + 1;
                
                // Store all moves in history and set totalMoves to the total number of moves
                this.gameState.moves = gameData.moves;
                this.gameState.totalMoves = gameData.moves.length;
                
                console.log(`Move navigation: ${this.gameState.moveNumber - 1}/${this.gameState.totalMoves}`);
                
                // Critical: Update next_to_move from the server response
                this.gameState.next_to_move = this.normalizeToken(gameData.current_state.next_to_move);
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
            const { ok, data: snapshots } = await this.apiClient.listSnapshots(this.gameState.gameId);
            if (!ok) {
                throw new Error(snapshots.error || "Failed to list snapshots");
            }
            
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
            const { ok, data } = await this.apiClient.createSnapshot(this.gameState.gameId, label);
            if (!ok) {
                throw new Error(data.error || "Failed to create snapshot");
            }
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
            const { ok, data } = await this.apiClient.restoreSnapshot(this.gameState.gameId, snapshotId);
            if (!ok) {
                throw new Error(data.error || "Failed to restore snapshot");
            }
            if (data.success) {
                // Update game state with restored data
                const gameData = data.game;
                
                // Update the board state to the current move
                this.gameState.board = this.normalizeBoard(gameData.current_state.board);
                
                // Set the current move number based on the current_move_index
                const currentMoveIndex = gameData.current_move_index || gameData.moves.length;
                this.gameState.moveNumber = currentMoveIndex + 1;
                
                // Store all moves in history and set totalMoves to the total number of moves
                this.gameState.moves = gameData.moves;
                this.gameState.totalMoves = gameData.moves.length;
                
                console.log(`Snapshot restore: ${this.gameState.moveNumber - 1}/${this.gameState.totalMoves}`);
                
                // Critical: Update next_to_move from the server response
                this.gameState.next_to_move = this.normalizeToken(gameData.current_state.next_to_move);
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
