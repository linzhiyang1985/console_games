import random
import os
import msvcrt
import time

class Game2048:
    def __init__(self):
        self.size = 4
        self.board = [[0] * self.size for _ in range(self.size)]
        self.score = 0
        self.target_num = 2048
        self.is_target_locked = False
        self.game_over = False
        self.won = False
        self.init_board()
    
    def init_board(self):
        self.add_random_tile()
        self.add_random_tile()
    
    def add_random_tile(self):
        empty_cells = [(i, j) for i in range(self.size) for j in range(self.size) if self.board[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.board[i][j] = 2 if random.random() < 0.9 else 4
    
    def print_board(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        # print title and score
        print('\033[41m' + "-- 2048 Dynamic --" + '\033[0m')
        print('\033[42m' + f"Target{' (Locked)' if self.is_target_locked else ''}: {self.target_num}" + '\033[0m')
        print('\033[44m' + f"Score: {self.score}" + '\033[0m')
        # print board
        print('\033[32m' + "-" * (1 + 6 * self.size) + '\033[0m') # upper bound
        for row in self.board:
            print('\033[32m' + "|" + '\033[0m', end="") # left most cell border
            for cell in row:
                if cell == 0:
                    print(" " * 5, end="") # empty cell, enough space for 5-digit number
                else:
                    print(f"{cell:5}", end="") # number, enough space up to 5 digits
                
                print('\033[32m' + "|" + '\033[0m', end="") # right border of the cell
            print()
            print('\033[32m' + "-" * (1 + 6 * self.size) + '\033[0m') # lower bound of each row
        # print control tips
        print("Controls: W(Up), S(Down), A(Left), D(Right) or Arrow Keys; X(Expand), L(Lock Target); Q(Quit)")
        # print game over tips
        if self.won:
            print('\033[43m' + "Congratulations! You won!" + '\033[0m')
        if self.game_over:
            print('\033[41m' + "Game Over!" + '\033[0m')
    
    def compress(self, row):
        new_row = [num for num in row if num != 0]
        new_row += [0] * (self.size - len(new_row))
        return new_row
    
    def merge(self, row):
        for i in range(self.size - 1):
            if row[i] == row[i+1] and row[i] != 0:
                row[i] *= 2
                self.score += row[i]
                row[i+1] = 0
                if row[i] == self.target_num:
                    self.won = True
        return row
    
    def move_left(self):
        moved = False
        for i in range(self.size):
            original_row = self.board[i].copy()
            self.board[i] = self.compress(self.board[i])
            self.board[i] = self.merge(self.board[i])
            self.board[i] = self.compress(self.board[i])
            if self.board[i] != original_row:
                moved = True
        return moved
    
    def move_right(self):
        moved = False
        for i in range(self.size):
            original_row = self.board[i].copy()
            self.board[i] = self.compress(self.board[i])[::-1]
            self.board[i] = self.merge(self.board[i])
            self.board[i] = self.compress(self.board[i])[::-1]
            if self.board[i] != original_row:
                moved = True
        return moved
    
    def move_up(self):
        moved = False
        for j in range(self.size):
            column = [self.board[i][j] for i in range(self.size)]
            original_column = column.copy()
            column = self.compress(column)
            column = self.merge(column)
            column = self.compress(column)
            for i in range(self.size):
                self.board[i][j] = column[i]
            if column != original_column:
                moved = True
        return moved
    
    def move_down(self):
        moved = False
        for j in range(self.size):
            column = [self.board[i][j] for i in range(self.size)][::-1]
            original_column = column.copy()
            column = self.compress(column)
            column = self.merge(column)
            column = self.compress(column)
            column = column[::-1]
            for i in range(self.size):
                self.board[i][j] = column[i]
            if column != original_column:
                moved = True
        return moved
    
    '''
    在2048游戏中,move_***方法的操作顺序(compress → merge → compress)是游戏逻辑的关键部分,这个顺序确保了游戏规则的正确实现。让我详细解释一下每一步的作用:

    ### 1. 第一次 compress(压缩)
    - 作用 :将行或列中的所有非零数字向目标方向(上、下、左、右)移动,将零值挤到相反方向
    - 目的 :为后续的合并操作做准备,确保相同的数字能够相邻
    ### 2. merge(合并)
    - 作用 :将相邻的相同数字合并为一个新的数字(值为两者之和)
    - 结果 :合并后,右侧(或下方)的数字会变为零值
    - 注意 :合并只会发生一次,不会连续合并(例如 2-2-2 只会合并前两个为 4,不会再合并 4-2)
    ### 3. 第二次 compress(压缩)
    - 作用 :处理合并后产生的零值,将非零数字再次向目标方向移动
    - 目的 :确保棋盘保持整洁,非零数字都聚集在一起,为下一次移动做准备
    ### 示例说明
    以向左移动为例:

    1. 初始状态 :[2, 0, 2, 4]
    2. 第一次 compress :[2, 2, 4, 0](将非零数字向左移动)
    3. merge :[4, 0, 4, 0](合并相邻的两个2)
    4. 第二次 compress :[4, 4, 0, 0](将合并后产生的零值向右移动)
    这样的操作顺序确保了游戏规则的正确执行,使玩家能够通过方向键控制方块的移动和合并。
    '''
    
    def expand_board(self):
        old_size = self.size
        self.size += 2 # expand the board by 2 cells in each direction, i.e. add a empty row/column around the original board
        new_board = [[0] * self.size for _ in range(self.size)]
        for i in range(old_size):
            for j in range(old_size):
                new_board[i+1][j+1] = self.board[i][j]
        self.board = new_board
        if not self.is_target_locked:
            self.target_num *= 2
            self.won = False
            self.game_over = False
        self.print_board()

    def check_game_over(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    return False
                if j < self.size - 1 and self.board[i][j] == self.board[i][j+1]:
                    return False
                if i < self.size - 1 and self.board[i][j] == self.board[i+1][j]:
                    return False
        return True
    
    def play(self):
        while not self.game_over:
            self.print_board()
            # Get user input
            key = None
            accepted_keys_and_map = {
                b'w': 'w', b's': 's', b'a': 'a', b'd': 'd',
                b'q': 'q', b'x': 'x', b'l': 'l',
                b'W': 'w', b'S': 's', b'A': 'a', b'D': 'd',
                b'Q': 'q', b'X': 'x', b'L': 'l',
                b'H': 'w', b'P': 's', b'K': 'a', b'M': 'd',
            }
            while key is None:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in (b'\xe0', b'\x00'):
                        key = msvcrt.getch()
                    if key in accepted_keys_and_map:
                        key = accepted_keys_and_map[key]
                    else:
                        key = None
                time.sleep(0.1)
            # Process user input
            moved = False
            if key == 'w':
                moved = self.move_up()
            elif key == 's':
                moved = self.move_down()
            elif key == 'a':
                moved = self.move_left()
            elif key == 'd':
                moved = self.move_right()
            elif key == 'x':
                self.expand_board()
            elif key == 'l':
                self.is_target_locked = not self.is_target_locked
            elif key == 'q':
                break
            # Check if the move was valid
            if moved:
                self.add_random_tile()
                self.game_over = self.check_game_over()
                if self.game_over and not self.won:
                    print('\033[41m' + "No more move" + '\033[0m')
                    x_or_other_keys = input("Press [X] to expand board and continue...any other keys to quit:")
                    if x_or_other_keys.strip() and x_or_other_keys[0].upper() == 'X':
                        self.expand_board()
                        self.game_over = False
        
        self.print_board()
        print("Thank you for playing!")

if __name__ == "__main__":
    game = Game2048()
    game.play()