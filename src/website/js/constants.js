const GAME_CONSTANTS = {
    PLAYERS: {
        HUMAN: 'X',
        COMPUTER: 'O'
    },
    BOARD_SIZE: 9,
    API_ENDPOINT: 'http://127.0.0.1:5000/api/makemove/',
    WINNING_COMBINATIONS: [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
        [0, 4, 8], [2, 4, 6]             // Diagonals
    ]
};