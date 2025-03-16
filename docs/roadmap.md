# Ultimate Tic-Tac-Toe Development Roadmap

This roadmap outlines the key action items for improving the UTTT codebase, focusing on three critical areas: AI improvement through deep learning, MCTS performance optimization, and game state management.

## 1. Game AI Improvement with Deep Learning

### Phase 1: Neural Network Foundation
- [ ] Create neural network module (`src/models/neural_net.py`)
- [ ] Design CNN architecture for board evaluation
- [ ] Implement board state encoding/decoding for network input/output
- [ ] Create initial model training pipeline

### Phase 2: Self-Play Data Generation
- [ ] Enhance `self_play.py` to generate training data at scale
- [ ] Implement efficient data storage format for game states and outcomes
- [ ] Create data augmentation for board symmetries/rotations
- [ ] Develop data collection pipeline that runs in background

### Phase 3: Neural Network Integration with MCTS
- [ ] Modify `SimulationTreeNode` to use neural network evaluation
- [ ] Replace heuristic scoring with neural network predictions
- [ ] Implement hybrid approach combining neural network with UCB1
- [ ] Add batch processing for neural network evaluations

### Phase 4: Progressive Training System
- [ ] Create pipeline for iterative neural network improvement
- [ ] Implement model versioning and evaluation
- [ ] Develop automated training cycle (self-play → training → evaluation)
- [ ] Add benchmarking against previous versions

## 2. MCTS Performance Optimization

### Phase 1: Parallelization Implementation
- [ ] Implement Root Parallelization
  - [ ] Create independent MCTS trees for each legal move
  - [ ] Run trees in parallel and combine results
  - [ ] Implement thread-safe result aggregation
- [ ] Implement Leaf Parallelization
  - [ ] Modify `expand_tree_by_one` to process multiple nodes in parallel
  - [ ] Use Python's `concurrent.futures` or `multiprocessing`
  - [ ] Implement thread-safe node updates for backpropagation

### Phase 2: Memory Optimization
- [ ] Create memory-efficient game state representation
- [ ] Implement bitboards or other compact representations
- [ ] Reduce deep copy usage with state rollback mechanism
- [ ] Add efficient board state caching

### Phase 3: Algorithm Enhancements
- [ ] Implement early stopping with confidence bounds
- [ ] Add dynamic exploration constant based on position
- [ ] Optimize node selection and expansion strategy
- [ ] Implement transposition tables for common positions

## 3. Game State Management Improvements

### Phase 1: Move History and Backtracking
- [ ] Enhance `GameStorage` class to store complete move history
- [ ] Add `restore_to_move` method to revert to previous states
- [ ] Implement transaction-like system for state consistency
- [ ] Add UI controls to navigate through move history

### Phase 2: Error Handling and Validation
- [ ] Add validation checks before and after state changes
- [ ] Implement state verification system to detect inconsistencies
- [ ] Add logging to track state changes and identify issues
- [ ] Create automated tests for game state integrity

### Phase 3: Game State Snapshots
- [ ] Create system for regular game state snapshots
- [ ] Allow restoring from snapshots if corruption is detected
- [ ] Implement efficient diff-based storage for snapshots
- [ ] Add UI for snapshot management

## Implementation Priority

1. **Game State Management Improvements**
   - Focus on fixing the immediate issues with game saving and state management
   - Implement move history and backtracking first to address the inability to undo moves
   - Add validation to prevent buggy states

2. **MCTS Performance Optimization**
   - Implement Root Parallelization as a quick win for performance
   - Optimize memory usage to allow deeper search
   - Add algorithm enhancements to improve search efficiency

3. **Game AI Improvement with Deep Learning**
   - Begin with self-play data generation to build training dataset
   - Develop neural network architecture and training pipeline
   - Integrate with MCTS for improved evaluation
   - Implement progressive training system

## Known Issues to Address

- [ ] Fix bug where winner isn't calculated correctly at end of game
- [ ] Fix bug where player can place on a board that's been won
- [ ] Address memory usage issues during long games
- [ ] Improve handling of interrupted computer moves
