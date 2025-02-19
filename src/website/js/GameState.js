class GameState {
    constructor() {
        this.gameId = crypto.randomUUID();  // Add just this one line
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
        this.isComputerThinking = false;
        this.winner = null;
        this.boardFull = false;
        this.targetBoard = -1;  // -1 means can play anywhere
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
        this.isComputerThinking = false;
        this.winner = null;
        this.boardFull = false;
        this.targetBoard = -1;
    }
}