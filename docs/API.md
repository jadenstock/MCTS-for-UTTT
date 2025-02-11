# Ultimate Tic-Tac-Toe API Documentation

## Overview

The Ultimate Tic-Tac-Toe API provides endpoints for game state management, AI move computation, and game persistence. All endpoints support CORS and use JSON for data transfer.

## Base URL

By default: `http://localhost:5000`

## Endpoints

### Make Computer Move

Computes and executes the AI's next move.

```http
POST /api/makemove/
```

#### Request Body

```json
{
    "game_id": "string",           // UUID for game persistence
    "last_move": [                 // Last move made
        number,                    // Board index (0-8)
        number,                    // Cell index (0-8)
        string                     // Player marker ("X" or "O")
    ],
    "game_board": [               // 9x9 array representing the game board
        [string, ...],            // Each sub-array represents a mini-board
        ...                       // Empty cells are ""
    ],
    "compute_time": number,       // AI thinking time in seconds
    "force_full_time": boolean    // Whether to use full compute time
}
```

#### Example Request

```json
{
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "last_move": [4, 7, "X"],
    "game_board": [
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "X", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""]
    ],
    "compute_time": 20,
    "force_full_time": false
}
```

#### Response

```json
{
    "board": number,          // Board index of AI's move
    "cell": number,          // Cell index of AI's move
    "metadata": {
        "num_gamestates": number,     // States evaluated
        "depth_explored": number,      // Search depth reached
        "thinking_time": number,       // Actual computation time
        "moves": [                     // Top moves considered
            [
                [number, number],      // [board, cell]
                number                 // Move score
            ],
            ...
        ],
        "early_stop": boolean         // Whether search stopped early
    }
}
```

#### Example Response

```json
{
    "board": 7,
    "cell": 4,
    "metadata": {
        "num_gamestates": 15783,
        "depth_explored": 12,
        "thinking_time": 18.45,
        "moves": [
            [[7, 4], 0.685],
            [[7, 3], 0.642],
            [[7, 5], 0.621]
        ],
        "early_stop": true
    }
}
```

### List Games

Retrieves a list of saved games.

```http
GET /api/games
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| in_progress | boolean | If true, only returns games that haven't finished (default: true) |

#### Response

```json
[
    {
        "game_id": string,        // Game UUID
        "moves": number,          // Number of moves made
        "winner": string,         // Winner ("X", "O", or "")
        "next_to_move": string,   // Next player ("X" or "O")
        "in_progress": boolean    // Whether game is ongoing
    },
    ...
]
```

#### Example Response

```json
[
    {
        "game_id": "550e8400-e29b-41d4-a716-446655440000",
        "moves": 12,
        "winner": "",
        "next_to_move": "O",
        "in_progress": true
    },
    {
        "game_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "moves": 47,
        "winner": "X",
        "next_to_move": "O",
        "in_progress": false
    }
]
```

### Load Game

Retrieves the complete state of a specific game.

```http
GET /api/games/{game_id}
```

#### Path Parameters

| Parameter | Description |
|-----------|-------------|
| game_id | UUID of the game to load |

#### Response

```json
{
    "game_id": string,
    "moves": [                    // Complete move history
        {
            "move_number": number,
            "board": number,
            "cell": number,
            "player": string,
            "metadata": object    // AI metadata if computer move
        },
        ...
    ],
    "current_state": {
        "board": [[string]],     // Current 9x9 board state
        "last_move": [           // Last move made
            number,              // Board index
            number,              // Cell index
            string              // Player marker
        ],
        "next_to_move": string,  // Next player
        "winner": string         // Current winner
    }
}
```

#### Example Response

```json
{
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "moves": [
        {
            "move_number": 1,
            "board": 4,
            "cell": 7,
            "player": "X",
            "metadata": null
        },
        {
            "move_number": 2,
            "board": 7,
            "cell": 4,
            "player": "O",
            "metadata": {
                "num_gamestates": 15783,
                "depth_explored": 12,
                "thinking_time": 18.45,
                "moves": [[7, 4, 0.685]],
                "early_stop": true
            }
        }
    ],
    "current_state": {
        "board": [
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "X", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "O", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""]
        ],
        "last_move": [7, 4, "O"],
        "next_to_move": "X",
        "winner": ""
    }
}
```

## Error Responses

All endpoints may return the following errors:

### 404 Not Found

```json
{
    "error": "Game not found"
}
```

### 400 Bad Request

```json
{
    "error": "Invalid request format"
}
```

### 500 Internal Server Error

```json
{
    "error": "Internal server error"
}
```

## Cross-Origin Resource Sharing

All endpoints support CORS with the following headers:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

## Rate Limiting

Currently, there are no rate limits implemented on any endpoints.