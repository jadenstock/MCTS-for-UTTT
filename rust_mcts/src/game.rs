pub const WIN_LINES: [[usize; 3]; 8] = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
];

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub enum Cell {
    Empty,
    X,
    O,
}

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub enum Player {
    X,
    O,
}

impl Player {
    #[inline]
    pub fn to_cell(self) -> Cell {
        match self {
            Player::X => Cell::X,
            Player::O => Cell::O,
        }
    }
    #[inline]
    pub fn opponent(self) -> Player {
        match self {
            Player::X => Player::O,
            Player::O => Player::X,
        }
    }
    #[inline]
    pub fn to_winner(self) -> Winner {
        match self {
            Player::X => Winner::X,
            Player::O => Winner::O,
        }
    }
}

/// Winner::Draw is only used for the global board, never for mini boards.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub enum Winner {
    None,
    X,
    O,
    Draw,
}

impl Winner {
    #[inline]
    pub fn is_terminal(self) -> bool {
        !matches!(self, Winner::None)
    }
}

pub type Move = (u8, u8);

#[derive(Clone, Debug)]
pub struct MiniBoard {
    pub cells: [Cell; 9],
    pub winner: Winner,
}

impl MiniBoard {
    pub fn new() -> Self {
        MiniBoard {
            cells: [Cell::Empty; 9],
            winner: Winner::None,
        }
    }

    pub fn evaluate_winner(&self) -> Winner {
        for &[a, b, c] in &WIN_LINES {
            let ca = self.cells[a];
            if ca != Cell::Empty && ca == self.cells[b] && ca == self.cells[c] {
                return match ca {
                    Cell::X => Winner::X,
                    Cell::O => Winner::O,
                    Cell::Empty => unreachable!(),
                };
            }
        }
        Winner::None
    }
}

#[derive(Clone, Debug)]
pub struct Board {
    pub mini_boards: [MiniBoard; 9],
    pub winner: Winner,
}

impl Board {
    pub fn new() -> Self {
        Board {
            mini_boards: std::array::from_fn(|_| MiniBoard::new()),
            winner: Winner::None,
        }
    }

    /// Returns (is_open, winner) for a mini board's global status.
    /// open = has winner==None AND has empty cells.
    fn global_cell_open(mini: &MiniBoard) -> bool {
        mini.winner == Winner::None && mini.cells.iter().any(|&c| c == Cell::Empty)
    }

    pub fn has_viable_big_board_line(&self) -> bool {
        for &player in &[Winner::X, Winner::O] {
            'line: for &[a, b, c] in &WIN_LINES {
                for &idx in &[a, b, c] {
                    let mini = &self.mini_boards[idx];
                    // Drawn (full, no winner) mini-board blocks this line for both players
                    if mini.winner == Winner::None && !Self::global_cell_open(mini) {
                        continue 'line;
                    }
                    // Opponent-owned cell blocks this line for `player`
                    if mini.winner != Winner::None
                        && mini.winner != player
                        && mini.winner != Winner::Draw
                    {
                        continue 'line;
                    }
                }
                return true;
            }
        }
        false
    }

    pub fn evaluate_winner(&self) -> Winner {
        for &[a, b, c] in &WIN_LINES {
            let wa = self.mini_boards[a].winner;
            if (wa == Winner::X || wa == Winner::O)
                && wa == self.mini_boards[b].winner
                && wa == self.mini_boards[c].winner
            {
                return wa;
            }
        }
        if !self.has_viable_big_board_line() {
            return Winner::Draw;
        }
        let has_playable = self.mini_boards.iter().any(|m| {
            m.winner == Winner::None && m.cells.iter().any(|&c| c == Cell::Empty)
        });
        if !has_playable {
            return Winner::Draw;
        }
        Winner::None
    }
}

#[derive(Clone, Debug)]
pub struct Game {
    pub board: Board,
    /// (board_idx, cell_idx, player_who_moved)
    pub move_stack: Vec<(u8, u8, Player)>,
    pub next_to_move: Player,
}

impl Game {
    pub fn new() -> Self {
        Game {
            board: Board::new(),
            move_stack: Vec::new(),
            next_to_move: Player::X,
        }
    }

    pub fn legal_moves(&self) -> Vec<Move> {
        if self.board.winner.is_terminal() {
            return vec![];
        }
        // If there's a last move, try to constrain to the target board
        if let Some(&(_, last_cell, _)) = self.move_stack.last() {
            let tb = last_cell as usize;
            let mini = &self.board.mini_boards[tb];
            if mini.winner == Winner::None {
                let cells: Vec<Move> = (0..9usize)
                    .filter(|&j| mini.cells[j] == Cell::Empty)
                    .map(|j| (tb as u8, j as u8))
                    .collect();
                if !cells.is_empty() {
                    return cells;
                }
            }
        }
        // Free move: play anywhere open
        let mut moves = Vec::new();
        for i in 0..9usize {
            let mini = &self.board.mini_boards[i];
            if mini.winner == Winner::None {
                for j in 0..9usize {
                    if mini.cells[j] == Cell::Empty {
                        moves.push((i as u8, j as u8));
                    }
                }
            }
        }
        moves
    }

    /// Unconditional make_move — caller must pass a legal move.
    pub fn make_move(&mut self, board_idx: u8, cell_idx: u8) {
        let bi = board_idx as usize;
        let ci = cell_idx as usize;
        let player = self.next_to_move;
        self.board.mini_boards[bi].cells[ci] = player.to_cell();
        self.move_stack.push((board_idx, cell_idx, player));
        self.board.mini_boards[bi].winner = self.board.mini_boards[bi].evaluate_winner();
        self.board.winner = self.board.evaluate_winner();
        self.next_to_move = player.opponent();
    }

    pub fn undo_last_move(&mut self) {
        if let Some((board_idx, cell_idx, player)) = self.move_stack.pop() {
            let bi = board_idx as usize;
            let ci = cell_idx as usize;
            self.board.mini_boards[bi].cells[ci] = Cell::Empty;
            self.board.mini_boards[bi].winner = self.board.mini_boards[bi].evaluate_winner();
            self.board.winner = self.board.evaluate_winner();
            self.next_to_move = player;
        }
    }

    pub fn state_key(&self) -> StateKey {
        let mut cells = [0u8; 81];
        let mut mini_winners = [0u8; 9];
        for (i, mini) in self.board.mini_boards.iter().enumerate() {
            for (j, &c) in mini.cells.iter().enumerate() {
                cells[i * 9 + j] = match c {
                    Cell::Empty => 0,
                    Cell::X => 1,
                    Cell::O => 2,
                };
            }
            mini_winners[i] = winner_to_u8(mini.winner);
        }
        StateKey {
            cells,
            mini_winners,
            global_winner: winner_to_u8(self.board.winner),
            next_to_move: match self.next_to_move {
                Player::X => 0,
                Player::O => 1,
            },
            last_cell: self.move_stack.last().map(|m| m.1).unwrap_or(255),
        }
    }
}

fn winner_to_u8(w: Winner) -> u8 {
    match w {
        Winner::None => 0,
        Winner::X => 1,
        Winner::O => 2,
        Winner::Draw => 3,
    }
}

/// Compact key for transposition tables (exact endgame + graph PUCT).
#[derive(Hash, PartialEq, Eq, Clone, Debug)]
pub struct StateKey {
    pub cells: [u8; 81],
    pub mini_winners: [u8; 9],
    pub global_winner: u8,
    pub next_to_move: u8,
    pub last_cell: u8,
}

// ---------------------------------------------------------------------------
// Parsing helpers — convert Python string representations to Rust types
// ---------------------------------------------------------------------------

pub fn parse_cell(s: &str) -> Cell {
    match s {
        "x" | "X" => Cell::X,
        "o" | "O" => Cell::O,
        _ => Cell::Empty,
    }
}

pub fn parse_player(s: &str) -> Player {
    match s {
        "o" | "O" => Player::O,
        _ => Player::X,
    }
}

pub fn parse_winner(s: &str) -> Winner {
    match s {
        "x" | "X" => Winner::X,
        "o" | "O" => Winner::O,
        "draw" => Winner::Draw,
        _ => Winner::None,
    }
}

/// Build a Game from the serialized state passed over the Python boundary.
/// `boards[i][j]` = cell string for mini board i, cell j.
/// `mini_winners[i]` = winner string for mini board i.
/// `last_cell` = cell index of the last move (-1 if none).
pub fn game_from_state(
    boards: &[Vec<String>],
    mini_winners: &[String],
    global_winner: &str,
    next_to_move: &str,
    last_cell: i32,
) -> Game {
    let mut game = Game::new();
    game.next_to_move = parse_player(next_to_move);

    for i in 0..9 {
        for j in 0..9 {
            game.board.mini_boards[i].cells[j] = parse_cell(&boards[i][j]);
        }
        game.board.mini_boards[i].winner = parse_winner(&mini_winners[i]);
    }
    game.board.winner = parse_winner(global_winner);

    // Insert a sentinel move-stack entry so legal_moves() routes correctly.
    // The player field is a dummy; the search never undoes past the root.
    if last_cell >= 0 {
        let dummy_player = game.next_to_move.opponent();
        game.move_stack.push((0, last_cell as u8, dummy_player));
    }

    game
}
