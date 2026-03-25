const readline = require('readline');

const WIDTH = 60;
const HEIGHT = 60;
const INITIAL_LENGTH = 3;
const SPEED_INCREMENT = 7;
const WIN_LENGTH = 60;

const COLORS_BG = ['\u001b[41m', '\u001b[42m', '\u001b[43m', '\u001b[44m', '\u001b[45m', '\u001b[46m'];
const COLOR_RESET = '\u001b[0m';

class SnakeGame {
  constructor() {
    this.snake = [];
    this.can_cross_wall = true;
    this.oldSnakeTail = null;
    this.direction = 'right';
    this.movingDirection = this.direction;
    this.food = {};
    this.score = 0;
    this.speed = 160;
    this.gameOver = false;
    this.won = false;
    this.snake_poisoned_time = 0; // future healed time, i.e. 10 seconds later
    this.poisoned_speed = 0;
    this.initGame();
  }

  initGame() {
    const startX = Math.floor(WIDTH / 2);
    const startY = Math.floor(HEIGHT / 2);
    
    for (let i = 0; i < INITIAL_LENGTH; i++) {
      this.snake.push({ x: startX - i, y: startY });
    }
    
    this.generateFood();
  }

  generateFood() {
    do {
      this.food.x = Math.floor(Math.random() * WIDTH);
      this.food.y = Math.floor(Math.random() * HEIGHT);
      this.food.poisoned = Math.random() < 0.3;
    } while (this.food.x ===0 || this.food.y ===0 || this.food.x >= WIDTH - 1 || this.food.y >= HEIGHT - 1 || this.snake.some(segment => segment.x === this.food.x && segment.y === this.food.y));
  }

  changeDirection(newDirection) {
    const oppositeDirections = {
      up: 'down',
      down: 'up',
      left: 'right',
      right: 'left'
    };
    
    if (newDirection !== oppositeDirections[this.movingDirection]) {
      this.direction = newDirection;
    }
  }

  move() {
    const head = { ...this.snake[0] };
    
    switch (this.direction) {
      case 'up':
        head.y--;
        break;
      case 'down':
        head.y++;
        break;
      case 'left':
        head.x--;
        break;
      case 'right':
        head.x++;
        break;
    }
    this.movingDirection = this.direction;
    
    if (head.x <= 0 || head.x >= WIDTH - 1 || head.y <= 0 || head.y >= HEIGHT - 1) {
      // head hits border
      if(!this.can_cross_wall){
        this.gameOver = true;
        return;
      }else{
        if(head.x <= 0 && this.direction == 'left'){head.x = WIDTH - 2;}
        if(head.x >= WIDTH - 1 && this.direction == 'right'){head.x = 1;}
        if(head.y <= 0 && this.direction == 'up'){head.y = HEIGHT - 2;}
        if(head.y >= HEIGHT - 1 && this.direction == 'down'){head.y = 1;}
      }
    }
    
    if (this.snake.some(segment => segment.x === head.x && segment.y === head.y)) {
      // head hits any of the snake body part
      this.gameOver = true;
      return;
    }
    
    this.snake.unshift(head);//add the new head to the beginning of the array
    
    if (head.x === this.food.x && head.y === this.food.y) {
      //snake body increase by one, i.e. the food node become the new head, keep it
      this.score += (this.poisoned_speed > 0? 200: 100); // hit food with high speed get more points
      if (this.food.poisoned) {
        this.snake_poisoned_time = Date.now() + 10000; // 10 seconds
        this.poisoned_speed = Math.floor(this.speed / 2); // smaller faster
      }

      this.generateFood();
      
      if ( (this.snake.length - INITIAL_LENGTH) % SPEED_INCREMENT === 0) {
        this.speed = Math.max(30, this.speed - 10);
      }
      
      if (this.snake.length >= WIN_LENGTH) {
        this.won = true;
        this.gameOver = true;
      }
    } else {
      // otherwise, remove the old tail node
      this.oldSnakeTail = this.snake.pop();
    }
  }

  drawBorder(){
    console.clear();
    for (let y = 0; y < HEIGHT; y++) {
      let row = '';
      if (y===0||y === HEIGHT - 1){
        for (let x = 0; x < WIDTH; x++) {
            row += '#';
        }
      } else{
        row += '#';
        for (let x = 1; x < WIDTH - 1; x++) {
            row += ' ';
        }
        row += '#';
      }
      row = '\u001b[32m'+ row + '\u001b[0m';
      console.log(row);
    }
  }

  drawFood(){
    readline.cursorTo(process.stdout, this.food.x, this.food.y);
    process.stdout.write('\u001b[41m*\u001b[0m');
  }

  drawSnake(){
    let isHead = true;

    if(this.snake_poisoned_time && Date.now() > this.snake_poisoned_time){ // healed
      this.poisoned_speed = 0;
      this.snake_poisoned_time = 0;
    }
    
    this.snake.forEach(segment => {
        readline.cursorTo(process.stdout, segment.x, segment.y);
        if(isHead){
            process.stdout.write('\u001b[44mO\u001b[0m');
            isHead = false;
        }else{
          if(this.poisoned_speed > 0){
            process.stdout.write(COLORS_BG[Math.floor(Math.random() * COLORS_BG.length)] + 'O' + COLOR_RESET);
          }else{
            process.stdout.write('\u001b[43mO\u001b[0m');
          }
        }
    });
    if(this.oldSnakeTail){
        readline.cursorTo(process.stdout, this.oldSnakeTail.x, this.oldSnakeTail.y);
        process.stdout.write(' ');
    }
  }

  drawStat(){
    readline.cursorTo(process.stdout, 0, HEIGHT + 1);

    console.log(`Food position: (${this.food.x}, ${this.food.y})`);
    console.log(`Snake head position: (${this.snake[0].x}, ${this.snake[0].y})` + (this.snake_poisoned_time > 0 ? '\u001b[31m (Poisoned)\u001b[0m' : '            '));
    console.log(`Score: ${this.score} | Length: ${this.snake.length} | Speed: ${Math.round(1000/ (this.snake_poisoned_time > 0 ? this.poisoned_speed:this.speed))}    `);
    console.log('Use arrow keys to control the snake, Ctrl+C to quit the game');
  }

  update() {
    this.drawFood();
    this.drawSnake();
    this.drawStat();
  }

  start() {
    this.drawBorder(); // only draw one time

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    readline.emitKeypressEvents(process.stdin);
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(true);
    }
    
    process.stdin.on('keypress', (str, key) => {
      if (key.ctrl && key.name === 'c') {
        rl.close();
        process.exit();
      }
      
      switch (key.name) {
        case 'up':
          this.changeDirection('up');
          break;
        case 'down':
          this.changeDirection('down');
          break;
        case 'left':
          this.changeDirection('left');
          break;
        case 'right':
          this.changeDirection('right');
          break;
      }
    });
    
    const gameLoop = () => {
      if (!this.gameOver) {
        this.move();
        this.update();
        setTimeout(gameLoop, this.poisoned_speed || this.speed);
      } else {
        if (this.won) {
          console.log('Congratulations! You won!');
        } else {
          console.log('Game Over!');
        }
        rl.close();
        process.exit();
      }
    };
    
    this.update();
    setTimeout(gameLoop, this.poisoned_speed || this.speed);
  }
}

const game = new SnakeGame();
game.start();