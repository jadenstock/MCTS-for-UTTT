const GAME_CONSTANTS = {
    PLAYERS: {
        HUMAN: 'X',
        COMPUTER: 'O'
    },
    BOARD_SIZE: 9,
    API_BASE_URL: 'http://127.0.0.1:5000',
    API_ENDPOINTS: {
        MAKE_MOVE: 'http://127.0.0.1:5000/api/makemove/',
        LIST_GAMES: 'http://127.0.0.1:5000/api/games',
        LOAD_GAME: (gameId) => `http://127.0.0.1:5000/api/games/${gameId}`,
        UPDATE_GAME_NAME: (gameId) => `http://127.0.0.1:5000/api/games/rename/${gameId}`,
        RESTORE_TO_MOVE: (gameId, moveNumber) => `http://127.0.0.1:5000/api/games/${gameId}/restore/${moveNumber}`,
        LIST_SNAPSHOTS: (gameId) => `http://127.0.0.1:5000/api/games/${gameId}/snapshots`,
        CREATE_SNAPSHOT: (gameId) => `http://127.0.0.1:5000/api/games/${gameId}/snapshots`,
        RESTORE_SNAPSHOT: (gameId, snapshotId) => `http://127.0.0.1:5000/api/games/${gameId}/snapshots/${snapshotId}/restore`,
    },
    WINNING_COMBINATIONS: [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
        [0, 4, 8], [2, 4, 6]             // Diagonals
    ]
};
