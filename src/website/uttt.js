const player = "X";
const computer = "O";

let board_full = false;
let play_board = [
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""]];
let move_number = 1;
let isComputerThinking = false;

const board_container = document.querySelector(".game-board");
const winner = document.getElementById("winner");
const last_move = document.getElementById("last-move");
const compute_time_value = document.getElementById("compute-time-value");
const moves_element = document.getElementById("metadata-moves");
const predicted_moves_element = document.getElementById("metadata-predicted-line");
const past_moves = document.getElementById("past-moves");

// check if board if full. why is this needed?
check_board_complete = () => {
  let flag = true;
  play_board.forEach(element => {
    element.forEach(c => {
      if (c != player && c != computer) {
        flag = false;
      }
    });
  });
  board_full = flag;
};

// check that a,b,c are either all "x" or all "o"
const check_line = (a, b, c) => {
  return (a == b) && (b == c) && (a == player || a == computer)
};

// take an array of lenth 9, check for a winner, return winner
const check_board = (board) => {
  for (i = 0; i < 9; i += 3) {
    if (check_line(board[i], board[i + 1], board[i + 2])) {
      return board[i];
    }
  }
  for (i = 0; i < 3; i++) {
    if (check_line(board[i], board[i + 3], board[i + 6])) {
      return board[i];
    }
  }
  if (check_line(board[0], board[4], board[8])) {
    return board[0];
  }
  if (check_line(board[2], board[4], board[6])) {
    return board[2];
  }
  return "";
}

const check_UTTT_winner = () => {
  let big_board = [check_board(play_board[0]), check_board(play_board[1]), check_board(play_board[2]), check_board(play_board[3]), check_board(play_board[4]), check_board(play_board[5]), check_board(play_board[6]), check_board(play_board[7]), check_board(play_board[8])];
  return check_board(big_board);
}

// potentially declair a winner
const check_for_winner = () => {
  let res = check_UTTT_winner()
  if (res == player) {
    winner.innerText = "Winner is player!!";
    winner.classList.add("playerWin");
    board_full = true
  } else if (res == computer) {
    winner.innerText = "Winner is computer";
    winner.classList.add("computerWin");
    board_full = true
  } else if (board_full) {
    winner.innerText = "Draw!";
    winner.classList.add("draw");
  }
};

mini_board_html = (mini_board, i) => {
  var s = ""
  mini_board.forEach((c, j) => {
      s += `<div id="cell_${i}${j}" class="cell" onclick="addPlayerMove(${i},${j})">${c}</div>`
    });
  return s
}

const findLegalMoves = () => {
  play_board.forEach((mini_board, i) => {
      mini_board.forEach((c, j) => {
        document.querySelector(`#cell_${i}${j}`).classList.remove("occupied")
      });
    });

  if (last_move.dataset.lastCell != -1) {
    play_board.forEach((mini_board, i) => {
      mini_board.forEach((c, j) => {

        // highlight the last played move
        if ((last_move.dataset.lastBoard == i) && (last_move.dataset.lastCell == j)) {
          document.querySelector(`#cell_${i}${j}`).style.color = "red";
        }

        // if a cell is occupied then it's illegal
        if (c == player || c == computer) {
          document.querySelector(`#cell_${i}${j}`).classList.add("occupied");
        }
        // otherwise every cell is legal unless the target board isn't won and isn't fill (if )
        if (!((check_board(play_board[last_move.dataset.lastCell]) != "") || (!play_board[last_move.dataset.lastCell].includes("")))) {
          if (i != last_move.dataset.lastCell) {
            document.querySelector(`#cell_${i}${j}`).classList.add("occupied");
          }
        }
      });
    });
  }
};

const add_to_past_moves = (i, j, p) => {
  past_moves.innerHTML += `<option value="", data-move-number=${move_number} selected>${move_number}) ${p}-B${i+1}C${j+1}</option>`;
  move_number += 1;
}

const addPlayerMove = (i,j) => {
  if (isComputerThinking) {
    console.log("Move blocked - computer thinking");
    return;
  }

  if (!document.querySelector(`#cell_${i}${j}`).classList.contains("occupied")) {
    play_board[i][j] = player;
    add_to_past_moves(i, j, player);

    last_move.innerHTML = "";
    last_move.innerHTML += `Last move: B${i+1}C${j+1}`;
    last_move.dataset.lastBoard = i;
    last_move.dataset.lastCell = j;   

    game_loop();
    addComputerMove(); 
  }
};

//just play randomly
const addComputerMove = async() => {
  findLegalMoves();
  
  if (winner.dataset.winner == "") {
    isComputerThinking = true;
    let message = document.getElementById("thinking-message");
    message.innerHTML = "Computer Thinking..."

    let last_move_arr = [last_move.dataset.lastBoard, last_move.dataset.lastCell, player];
    let big_board = [play_board[0], play_board[1], play_board[2], play_board[3], play_board[4], play_board[5], play_board[6], play_board[7], play_board[8]];
    let forceFullTime = document.getElementById("forceFullTime").checked;
    let request_data = JSON.stringify({
      "last_move": last_move_arr,
      "game_board": big_board,
      "compute_time": document.getElementById("computeTime").value,
      "force_full_time": forceFullTime
    });

    fetch('http://127.0.0.1:5000/api/makemove/', {
      method: "POST",
      mode: 'cors',
      body: JSON.stringify(request_data),
      headers: {
        'Content-Type': 'application/json',
        'Accept-Charset': 'UTF-8'
      },
      credentials: "same-origin"
    }).then((response) => response.json())
    .then(function(response) {
      // Update actual think time display
      document.getElementById("actual-think-time").innerHTML =
        `Actual thinking time: ${response.metadata.thinking_time.toFixed(2)} seconds`;

      let b = parseInt(response.board)
      let c = parseInt(response.cell)
      add_to_past_moves(b, c, computer);
      
      document.getElementById("metadata-nodes-evaluated").innerHTML = `<u>Gamestates Evaluated:</u> ${response.metadata.num_gamestates}`
      document.getElementById("metadata-depth-evaluated").innerHTML = `<u>Gametree Depth:</u> ${response.metadata.depth_explored}`
      
      predicted_moves_element.innerHTML = `<u>Predicted Line:</u><br>`
      response.metadata.predicted_line.forEach((m, i) => {
        if (i>0) {
          predicted_moves_element.innerHTML += `${parseInt(m[0])+1}`  
          if (i < response.metadata.predicted_line.length -1) {
            predicted_moves_element.innerHTML += ", "
          }
          predicted_moves_element.innerHTML += "<br>"      
        }
        predicted_moves_element.innerHTML += `${m[2].toUpperCase()}-B${parseInt(m[0])+1}C${parseInt(m[1])+1}, `
        if (i < response.metadata.predicted_line.length -1) {
          predicted_moves_element.innerHTML += `${player}-B${parseInt(m[1])+1}C`
        }
      });

      moves_element.innerHTML = `<br><u>Moves Considered:</u><br>`
      response.metadata.moves.forEach((m, i)=>{
        if (i <= 8){
          moves_element.innerHTML += `B${parseInt(m[0][0])+1}C${parseInt(m[0][1])+1}\t\tscore: ${parseFloat(m[1]).toFixed(5)}<br>`
        };
      });
      
      play_board[b][c] = computer;

      last_move.innerHTML = "";
      last_move.innerHTML += `Last move: B${b+1}C${c+1}`;
      last_move.dataset.lastBoard = b;
      last_move.dataset.lastCell = c;

      message.innerHTML = ""
      isComputerThinking = false;
      game_loop();
    })
  }
};

//render move, check for completion on sub-boards and board, check for winner.
const game_loop = () => {
  render_board();
  findLegalMoves();
  check_for_winner();
}

const render_board = () => {
  compute_time_value.innerHTML = ""
  compute_time_value.innerHTML += `${document.getElementById("computeTime").value} seconds`

  board_container.innerHTML = "";
  play_board.forEach((mini_board, i) => {
    board_container.innerHTML += `<div id="mini-board_${i}" class="mini-board">${mini_board_html(mini_board, i)}</div>`;
  });
};

const updateSlider = (slideAmount) => {
  var sliderDiv = document.getElementById("sliderAmount");
  compute_time_value.innerHTML = `${document.getElementById("computeTime").value} seconds`
  compute_time_value.dataset.value = parseInt(slideAmount)
}

const reset_board = () => {
  play_board = [
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""],
["", "", "", "", "", "", "", "", ""]];
  board_full = false;
  winner.classList.remove("playerWin");
  winner.classList.remove("computerWin");
  winner.classList.remove("draw");
  
  play_board.forEach((mini_board, i) => {
      mini_board.forEach((c, j) => {
        document.querySelector(`#cell_${i}${j}`).classList.remove("occupied")
      });
    });

  last_move.innerHTML = "";
  last_move.dataset.lastBoard = -1;
  last_move.dataset.lastCell = -1;  

  winner.innerText = "";

  document.getElementById("metadata-nodes-evaluated").innerHTML = `<u>Gamestates Evaluated:</u> ...`
  document.getElementById("metadata-depth-evaluated").innerHTML = `<u>Gametree Depth:</u> ...`
  document.getElementById("metadata-predicted-line").innerHTML = `<u>Predicted Line:</u> ...` 
  document.getElementById("metadata-moves").innerHTML = `<u>Moves Considered:</u> ...`
  
  past_moves.innerHTML = "";
  move_number = 1;

  render_board();
};

//initial render
render_board();