## MCTS for Ultimate Tic Tac Toe
This is a project to create an Ultimate tic tac toe AI agent using MCTS. For the rules of UTTT see the [wikipedia](https://en.wikipedia.org/wiki/Ultimate_tic-tac-toe) page


### Theory and Implementation
Here I will not go into a full description of MCTS. For that, see this [survey](http://www.incompleteideas.net/609%20dropbox/other%20readings%20and%20resources/MCTS-survey.pdf). I will instead describe my specific program.

This is a MCTS agent using UBC1 scores for move selection. MCTS faces two key challenges. Once challenge is that it usually requires a board heuristic function (the same problem faced by min-max approaches). For this I use the Russell-Norvig Tic-Tac-Toe board score function (see [here](https://john.cs.olemiss.edu/~dwilkins/CSCI531/fall12/slides/AI_09_games.pdf)) applied recursively to mini-boards. 

The second challenge is how you simulate opponent behavior. Obviously if we just applied the same MCTS algorithm we'd have a recursive loop. If instead we do something very basic and simple then it might not be a good predictor of their moves (however this is a common strategy and can work in conjunction with massive amounts of compute.) Here I take a hybrid approach. for opponent moves I use a smaller MCTS and for that MCTS I simulate opponent behavior using a simple greedy strategy. So there is essentially only one level or recursion. 

Overall the bot performs reasonably well. It can usually beat new or weak opponents. It can sometimes draw with even strong opponents. However a player with a firm grasp of the game can usually beat it. for best results use at least 15-20 or more seconds of compute per computer move. I have not tested it but I suspect that it is better than simple min-max strategies.

### Web interface usage
To run from the web interface (preferred) run python flask_server.py Then in your preferred web browser open up uttt.html. From there it should be very intuitive. you can select how many seconds to allow for each computer move and after each move some metadata (how many states considered, which moves it considered along with their scores etc.) will be displayed. It should look like this:
<img src="/docs/uttt_game_Example.png" alt="UTTT game example"/>

### Command line usage
To run this program from the command line simply run python runner.py, and the game will start. Edit the runner file to change how many seconds the computer gets to think on each move. Specifically edit the run_game method.
