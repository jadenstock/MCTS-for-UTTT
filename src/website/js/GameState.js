class GameState {
    constructor() {
        this.gameId = crypto.randomUUID();
        this.board = [
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""]
        ];
        this.moveNumber = 1;
        this.totalMoves = 0;  // Track total moves for history navigation
        this.moves = [];      // Store move history
        this.isComputerThinking = false;
        this.winner = null;
        this.boardFull = false;
        this.targetBoard = -1;  // -1 means can play anywhere
        this.next_to_move = GAME_CONSTANTS.PLAYERS.HUMAN;  // Human goes first by default
    }

    makeMove(board, cell, player) {
        console.log(`Attempting move: board ${board}, cell ${cell}, player ${player}`);
        console.log(`Current target board: ${this.targetBoard}`);

        if (this.isComputerThinking || this.winner) {
            console.log('Move rejected: Computer thinking or game over');
            return false;
        }
        if (this.board[board][cell] !== "") {
            console.log('Move rejected: Cell already occupied');
            return false;
        }

        // Check if move is in correct board
        if (this.targetBoard !== -1) {
            const targetBoardWon = this.checkBoardWinner(this.board[this.targetBoard]) !== "";
            const targetBoardFull = !this.board[this.targetBoard].includes("");

            console.log(`Target board ${this.targetBoard} status:`);
            console.log(`- Won: ${targetBoardWon}`);
            console.log(`- Full: ${targetBoardFull}`);

            if (!targetBoardWon && !targetBoardFull && board !== this.targetBoard) {
                console.log('Move rejected: Wrong board');
                return false;
            }
        }

        console.log('Move accepted');
        this.board[board][cell] = player;
        this.moveNumber++;
        this.totalMoves = this.moveNumber - 1;  // Update total moves
        
        // Add move to history
        if (this.moves.length >= this.totalMoves) {
            // If we're not at the end of history (e.g., after navigating back),
            // truncate the move history to current position
            this.moves = this.moves.slice(0, this.moveNumber - 2);
        }
        
        // Add the new move to history
        this.moves.push({
            board: board,
            cell: cell,
            player: player,
            timestamp: new Date().toISOString()
        });
        
        // Update next player to move
        this.next_to_move = player === GAME_CONSTANTS.PLAYERS.HUMAN ? 
            GAME_CONSTANTS.PLAYERS.COMPUTER : GAME_CONSTANTS.PLAYERS.HUMAN;
        console.log("Next to move updated to:", this.next_to_move);
            
        this.targetBoard = cell;
        this.checkBoardStatus();
        return true;
    }

    checkBoardWinner(board) {
        const lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
            [0, 4, 8], [2, 4, 6]             // Diagonals
        ];

        for (const [a, b, c] of lines) {
            if (board[a] && board[a] === board[b] && board[a] === board[c]) {
                return board[a];
            }
        }
        return "";
    }

    checkGameWinner() {
        const bigBoard = this.board.map(miniBoard => this.checkBoardWinner(miniBoard));
        return this.checkBoardWinner(bigBoard);
    }

    checkBoardStatus() {
        // First check for a winner
        const gameWinner = this.checkGameWinner();
        if (gameWinner) {
            this.winner = gameWinner;
            this.boardFull = true;
            return;
        }

        // Check if all boards are either won or full
        const allBoardsWonOrFull = this.board.every((miniBoard, index) => {
            const boardWon = this.checkBoardWinner(miniBoard) !== "";
            const boardFull = !miniBoard.includes("");
            return boardWon || boardFull;
        });

        if (allBoardsWonOrFull) {
            this.winner = "draw";
            this.boardFull = true;
        }
    }

    reset() {
        this.gameId = crypto.randomUUID();
        this.board = Array(9).fill().map(() => Array(9).fill(""));
        this.moveNumber = 1;
        this.totalMoves = 0;
        this.moves = [];
        this.isComputerThinking = false;
        this.winner = null;
        this.boardFull = false;
        this.targetBoard = -1;
        this.next_to_move = GAME_CONSTANTS.PLAYERS.HUMAN;  // Reset to human's turn
    }
}
