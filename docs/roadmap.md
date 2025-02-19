# Ultimate Tic-Tac-Toe Development Roadmap

## Immediate Goals

### Game Management Improvements
- [ ] Enhanced game list dropdown
  - [ ] Add game metadata (date created, last played)
  - [ ] Display number of moves
  - [ ] Show current game status (in progress, won, drawn)
  - [ ] Add custom game naming
- [ ] Game management UI
  - [ ] Add ability to delete games
  - [ ] Implement game renaming
  - [ ] Add game filtering options (by status, date)
  - [ ] Add confirmation dialogs for destructive actions

### MCTS Algorithm Enhancements
- [ ] Implement informed rollout policies
  - [ ] Add heuristic-guided move selection
  - [ ] Prioritize tactical moves (wins, blocks)
  - [ ] Weight moves based on strategic patterns
  - [ ] Implement rollout policy caching
- [ ] Progressive History integration
  - [ ] Track global move success rates
  - [ ] Implement history-based UCT weights
  - [ ] Add decay factors for recent games
  - [ ] Store common board patterns
- [ ] Hybrid MCTS-Minimax implementation
  - [ ] Add alpha-beta pruning for endgame positions
  - [ ] Implement staged transition to exact solving
  - [ ] Develop position complexity evaluation
  - [ ] Cache solved sub-positions

### Performance Optimization
- [ ] Reduce deep copy usage
  - [ ] Implement state rollback instead of deep copying
  - [ ] Add efficient board state caching
  - [ ] Optimize memory usage in tree expansion
- [ ] Profile and optimize core MCTS operations
  - [ ] Benchmark current performance
  - [ ] Identify bottlenecks in tree traversal
  - [ ] Optimize node expansion strategy
- [ ] Improve early stopping mechanism
  - [ ] Implement variance-based confidence
  - [ ] Add dynamic exploration constants
  - [ ] Better handle endgame scenarios

## Mid-term Goals

### Advanced Search Techniques
- [ ] Implement RAVE (Rapid Action Value Estimation)
  - [ ] Add AMAF (All Moves As First) statistics
  - [ ] Implement RAVE parameter tuning
  - [ ] Test hybrid RAVE-UCT selection
- [ ] Position evaluation improvements
  - [ ] Develop pattern-based evaluation
  - [ ] Add strategic position scoring
  - [ ] Implement threat detection
- [ ] Search optimization
  - [ ] Add principal variation move ordering
  - [ ] Implement transposition tables
  - [ ] Test parallel tree search

### Game Analysis Features
- [ ] Move quality assessment
  - [ ] Calculate move strength metrics
  - [ ] Identify critical positions
  - [ ] Highlight potential blunders
- [ ] Game statistics tracking
  - [ ] Track win rates and patterns
  - [ ] Generate performance metrics
  - [ ] Create player profiles

## Future Considerations

### Advanced Features
- [ ] AI difficulty levels
  - [ ] Implement adjustable play strength
  - [ ] Add personality-based play styles
  - [ ] Create teaching mode
- [ ] Multi-player support
  - [ ] Local multiplayer
  - [ ] Game sharing via URLs
  - [ ] Optional move timer
- [ ] Learning capabilities
  - [ ] Add game database for learning
  - [ ] Implement basic position learning
  - [ ] Add pattern recognition training

### UI/UX Improvements
- [ ] Enhanced visualizations
  - [ ] Add move tree display
  - [ ] Show AI confidence visualization
  - [ ] Improve board highlighting
- [ ] Accessibility improvements
  - [ ] Add keyboard controls
  - [ ] Improve screen reader support
  - [ ] Add high contrast mode

## Known Issues

### Critical
- [ ] Fix drawn game handling
- [ ] Improve endgame search behavior
- [ ] Handle interrupted computer moves

### Performance
- [ ] Reduce memory usage during long games
- [ ] Optimize state management
- [ ] Improve loading times for game list

### UI
- [ ] Fix move placement during computer turns
- [ ] Improve mobile responsiveness
- [ ] Add better error messages

## Technical Debt
- [ ] Add comprehensive test suite
- [ ] Improve code documentation
- [ ] Refactor state management
- [ ] Clean up deprecated features


# Next steps
# add a 'go back' button to UI and have it impact the save state (makes end game testing work nice)
# show the game name in UI
# fix bug where winner isn't caluclated at end of game

# display on screen what computer thinks my next move will be (or top 3)
  # for debuggability

# find back-end improvements for efficiency
# Create config of most important params, create a tournament to test them
  # requires some sort of self play mechanism, Can happen entirly on backend but using the flask to make moves?


# Major bug, I can place on a board thats been won and the computer coutner moves. Issues in front end and back end?