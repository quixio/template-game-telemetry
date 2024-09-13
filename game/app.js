function generateGUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  const session_id = generateGUID();
  
  var canvas = document.getElementById('game');
  var context = canvas.getContext('2d');
  
  var grid = 16;
  var count = 0;
  var gameOver = false;
  var autopilot = false; // Autopilot flag
  
  var snake = {
    x: 160,
    y: 160,
    dx: grid,
    dy: 0,
    cells: [],
    maxCells: 4
  };
  
  var apple = {
    x: 320,
    y: 320
  };
  
  
  function getWebSocketURL(httpURL) {
    try {
        const url = new URL(httpURL);

        // Replace the protocol from 'http' or 'https' to 'ws' or 'wss' for WebSocket connection
        const wsProtocol = url.protocol === 'https:' ? 'wss:' : 'ws:';

        // Replace the hostname with the WebSocket hostname
        const wsHost = url.hostname.replace('game-', 'gametelemetry-');

        // Form the WebSocket URL
        const wsURL = `${wsProtocol}//${wsHost}${url.pathname}`;
        
        return wsURL;
    } catch (e) {
        console.error('Invalid URL:', e);
        return null;
    }
}

  // Set up WebSocket connection
  var socket = new WebSocket(getWebSocketURL(document.location) + session_id);
  
  socket.onopen = function(event) {
    console.log('Connected to WebSocket');
  };
  
  // Send telemetry data through WebSocket
  function sendTelemetry(data) {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    }
  }
  
  // Send game over event through WebSocket
  function sendGameOverEvent() {
    sendTelemetry({
      type: 'gameOver',
      snakeLength: snake.cells.length,
      session_id: session_id,
      reason: gameOver ? 'collision' : 'other'
    });
  }
  
  function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min)) + min;
  }
  
  // End game when snake hits the wall
  function checkWallCollision() {
    if (snake.x < 0 || snake.x >= canvas.width || snake.y < 0 || snake.y >= canvas.height) {
      gameOver = true;
      sendGameOverEvent();
    }
  }
  
  function resetGame() {
    snake.x = 160;
    snake.y = 160;
    snake.cells = [];
    snake.maxCells = 4;
    snake.dx = grid;
    snake.dy = 0;
    apple.x = getRandomInt(0, canvas.width / grid) * grid;
    apple.y = getRandomInt(0, canvas.width / grid) * grid;
    gameOver = false;
  }
  
  // Check if the next position will collide with the snake's body
  function willCollideWithSelf(nextX, nextY) {
    return snake.cells.some(cell => cell.x === nextX && cell.y === nextY);
  }
  
  // Directly change snake direction and send telemetry (simulate keypress in autopilot)
  function changeDirection(keyCode) {
    if (keyCode === 37 && snake.dx === 0) { // Left arrow key
      snake.dx = -grid;
      snake.dy = 0;
    } else if (keyCode === 38 && snake.dy === 0) { // Up arrow key
      snake.dx = 0;
      snake.dy = -grid;
    } else if (keyCode === 39 && snake.dx === 0) { // Right arrow key
      snake.dx = grid;
      snake.dy = 0;
    } else if (keyCode === 40 && snake.dy === 0) { // Down arrow key
      snake.dx = 0;
      snake.dy = grid;
    }
  
    // Send telemetry to simulate the key press
    sendTelemetry({
      type: 'keypress',
      key: keyCode,
      snakeLength: snake.cells.length,
      session_id: session_id
    });
  }
  
  // Autopilot logic to determine direction and avoid collisions
  function autopilotMove() {
    let nextX, nextY;
  
    // Try moving toward the apple
    if (apple.x < snake.x && snake.dx === 0) {
      nextX = snake.x - grid;
      nextY = snake.y;
      if (!willCollideWithSelf(nextX, nextY)) {
        changeDirection(37); // Move left
        return;
      }
    }
    if (apple.x > snake.x && snake.dx === 0) {
      nextX = snake.x + grid;
      nextY = snake.y;
      if (!willCollideWithSelf(nextX, nextY)) {
        changeDirection(39); // Move right
        return;
      }
    }
    if (apple.y < snake.y && snake.dy === 0) {
      nextX = snake.x;
      nextY = snake.y - grid;
      if (!willCollideWithSelf(nextX, nextY)) {
        changeDirection(38); // Move up
        return;
      }
    }
    if (apple.y > snake.y && snake.dy === 0) {
      nextX = snake.x;
      nextY = snake.y + grid;
      if (!willCollideWithSelf(nextX, nextY)) {
        changeDirection(40); // Move down
        return;
      }
    }
  
    // If no ideal move is possible, choose a safe direction
    let directions = [
      { dx: grid, dy: 0, keyCode: 39 },  // Right
      { dx: -grid, dy: 0, keyCode: 37 }, // Left
      { dx: 0, dy: grid, keyCode: 40 },  // Down
      { dx: 0, dy: -grid, keyCode: 38 }  // Up
    ];
  
    for (let dir of directions) {
      nextX = snake.x + dir.dx;
      nextY = snake.y + dir.dy;
      if (!willCollideWithSelf(nextX, nextY)) {
        changeDirection(dir.keyCode);
        break;
      }
    }
  }
  
  // Game loop
  function loop() {
    if (gameOver) {
      context.fillStyle = 'white';
      context.font = '40px Arial';
      context.fillText('Game Over', 120, 200);
      return;
    }
  
    requestAnimationFrame(loop);
  
    if (++count < 20 - snake.cells.length) {  // Slower by skipping more frames
      return;
    }
  
    count = 0;
    context.clearRect(0, 0, canvas.width, canvas.height);
  
    // Autopilot mode, emit key presses based on the apple's location
    if (autopilot) {
      autopilotMove();
    }
  
    // Move snake
    snake.x += snake.dx;
    snake.y += snake.dy;
  
    // Check if the snake hits the wall
    checkWallCollision();
  
    if (gameOver) {
      sendGameOverEvent();  // Send game over event when the game ends
      return;
    }
  
    // Send snake position telemetry (normalized to grid)
    sendTelemetry({
      type: 'movement',
      x: snake.x / grid,
      y: snake.y / grid,
      snakeLength: snake.cells.length,
      session_id: session_id
    });
  
    // Keep track of where the snake has been
    snake.cells.unshift({x: snake.x, y: snake.y});
  
    if (snake.cells.length > snake.maxCells) {
      snake.cells.pop();
    }
  
    // Draw apple
    context.fillStyle = 'red';
    context.fillRect(apple.x, apple.y, grid - 1, grid - 1);
  
    // Draw snake one cell at a time
    context.fillStyle = 'green';
    snake.cells.forEach(function(cell, index) {
      context.fillRect(cell.x, cell.y, grid - 1, grid - 1);
  
      // Snake eats the apple
      if (cell.x === apple.x && cell.y === apple.y) {
        snake.maxCells++;
        apple.x = getRandomInt(0, canvas.width / grid) * grid;
        apple.y = getRandomInt(0, canvas.width / grid) * grid;
        sendTelemetry({
            type: 'apple-eaten',
            x: snake.x / grid,
            y: snake.y / grid,
            snakeLength: snake.cells.length,
            session_id: session_id
          });
      }
  
      // Check for collision with itself
      for (var i = index + 1; i < snake.cells.length; i++) {
        if (cell.x === snake.cells[i].x && cell.y === snake.cells[i].y) {
          gameOver = true;
          sendGameOverEvent(); // Send game over event when the snake collides with itself
          break;
        }
      }
    });
  }
  
  // Listen to keyboard events to move the snake and toggle autopilot
  document.addEventListener('keydown', function(e) {
    // 'C' key for autopilot toggle
    if (e.which === 67) {  // 'C' key
      autopilot = !autopilot;
      console.log('Autopilot mode:', autopilot);
    }
  
    if (!autopilot) {
      // Prevent snake from backtracking on itself
      changeDirection(e.which);
    }
  });
  
  // Start the game
  resetGame();
  requestAnimationFrame(loop);