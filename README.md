# Ultimate Tic-Tac-Toe with MCTS AI

A sophisticated implementation of Ultimate Tic-Tac-Toe featuring a Monte Carlo Tree Search (MCTS) AI player, persistent game storage, and an interactive web interface.

## Features

- 🎮 Full Ultimate Tic-Tac-Toe gameplay
- 🤖 Advanced MCTS-based AI opponent
- 💾 Game persistence with save/load functionality
- 📊 Real-time AI analysis and move statistics
- ⚙️ Configurable AI computation time
- 🌐 Clean, responsive web interface

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+ (for frontend development)
- Modern web browser

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ultimate-tictactoe.git
cd ultimate-tictactoe
```

2. Set up development environment:
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

### Running the Game

1. Start the backend server:
```bash
invoke run-server
# Or specify a custom port:
invoke run-server --port 8000
```

2. Open `index.html` in your web browser

## Game Rules

Ultimate Tic-Tac-Toe is played on nine small tic-tac-toe boards arranged in a 3×3 grid. To win, you must win three small boards in a row. The twist: your opponent's move determines which board you must play in next.

For detailed rules, see the [Wikipedia page](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe).

## Technical Implementation

### Frontend Architecture
- Vanilla JavaScript with component-based structure
- Real-time game state management
- Responsive UI with move highlighting
- Game persistence interface

Key components:
- `GameState`: Core game logic
- `UIManager`: DOM and rendering
- `ComputerPlayer`: AI interface

### Backend Architecture
- Flask-based RESTful API
- MCTS AI implementation
- Persistent game storage
- Move analysis system

### AI Implementation

The AI uses Monte Carlo Tree Search with several enhancements:
- UCB1 for node selection
- Russell-Norvig scoring function
- Adaptive computation time
- Early stopping optimization
- Move confidence metrics

#### AI Performance
The AI performs well against:
- Beginner to intermediate players
- Tactical play styles
- Time-pressured situations

For optimal AI performance:
- Use 15-20 seconds computation time
- Enable "Force full thinking time" for critical positions
- Review move metadata for insights

## API Endpoints

### Make Move
```http
POST /api/makemove/
```

### List Games
```http
GET /api/games
```

### Load Game
```http
GET /api/games/{game_id}
```

## Development

### Project Structure
```
/ultimate-tictactoe
├── frontend/           # Web interface
│   ├── js/            # JavaScript components
│   └── css/           # Styling
├── src/               # Backend
│   ├── core/          # Game engine
│   ├── ai/            # MCTS implementation
│   └── utils/         # Utilities
└── docs/              # Documentation
```

### Documentation
- [Frontend Documentation](docs/Frontend.md)
- [Backend Documentation](docs/Backend.md)
- [API Documentation](docs/API.md)

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Roadmap

See our [detailed roadmap](ROADMAP.md) for planned features and improvements.

## Known Issues

- Game state issues in drawn games
- End-game AI search depth concerns

## Acknowledgments

- MCTS implementation inspired by the survey paper: "A Survey of Monte Carlo Tree Search Methods"
- Board evaluation based on Russell-Norvig's game theory principles