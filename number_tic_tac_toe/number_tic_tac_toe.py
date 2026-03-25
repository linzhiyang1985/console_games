# 数字华容道
import msvcrt
import random
import time
import os

# 颜色代码
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# 数字点阵
NUMBER_DOT_ARRAY = [
    # ['■■ ■■ ■■ ■■', '■■       ■■', '■■       ■■', '■■       ■■', '■■       ■■', '■■       ■■', '■■ ■■ ■■ ■■'], #0
    ['           ', '           ', '           ', '           ', '           ', '           ', '           '], #empty cell
    ['    ■■     ', ' ■■ ■■     ', '    ■■     ', '    ■■     ', '    ■■     ', '    ■■     ', '■■ ■■ ■■ ■■'], #1
    ['■■ ■■ ■■ ■■', '         ■■', '         ■■', '■■ ■■ ■■ ■■', '■■         ', '■■         ', '■■ ■■ ■■ ■■'], #2
    ['■■ ■■ ■■ ■■', '         ■■', '         ■■', '■■ ■■ ■■ ■■', '         ■■', '         ■■', '■■ ■■ ■■ ■■'], #3
    ['■■       ■■', '■■       ■■', '■■       ■■', '■■ ■■ ■■ ■■', '         ■■', '         ■■', '         ■■'], #4
    ['■■ ■■ ■■ ■■', '■■         ', '■■         ', '■■ ■■ ■■ ■■', '         ■■', '         ■■', '■■ ■■ ■■ ■■'], #5
    ['■■ ■■ ■■ ■■', '■■         ', '■■         ', '■■ ■■ ■■ ■■', '■■       ■■', '■■       ■■', '■■ ■■ ■■ ■■'], #6
    ['■■ ■■ ■■ ■■', '         ■■', '         ■■', '         ■■', '         ■■', '         ■■', '         ■■'], #7
    ['■■ ■■ ■■ ■■', '■■       ■■', '■■       ■■', '■■ ■■ ■■ ■■', '■■       ■■', '■■       ■■', '■■ ■■ ■■ ■■'], #8
    ['■■ ■■ ■■ ■■', '■■       ■■', '■■       ■■', '■■ ■■ ■■ ■■', '         ■■', '         ■■', '■■ ■■ ■■ ■■'], #9
]

# num_idx = 0
# for number in NUMBER_DOT_ARRAY:
#     print(f'Number {num_idx}:')
#     for index, line in enumerate(number):
#         print(line)
#     print()
#     num_idx += 1

class Game:
    def __init__(self):
        self.board = self.generate_board()
        self.space_row, self.space_col = self.find_space()
    
    def generate_board(self):
        # 生成一个3x3的棋盘，数字1-8随机分布，0表示空格
        board = [0] * 9
        for i in range(8):
            board[i] = i + 1
        board[-1] = 0
        random.shuffle(board)
        board_2d = [board[i * 3:(i + 1) * 3] for i in range(3)]
        return board_2d
    
    def find_space(self):
        # 找到空格的位置
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == 0:
                    return row, col

    # def print_board(self):
    #     os.system('cls' if os.name == 'nt' else 'clear')
    #     print('=== 数字华容道 ===')
    #     print("Controls: W(Up), S(Down), A(Left), D(Right) or Arrow Keys; Q(Quit)")
    #     for row in range(3):
    #         for col in range(3):
    #             print(self.board[row][col], end=' ')
    #         print()
    
    def print_board_2d(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(GREEN + '    === 数字华容道 ===' + RESET)
        print(GREEN + "Controls: W(Up), S(Down), A(Left), D(Right) or Arrow Keys; Q(Quit)" + RESET)
        print()
        print()
        # upper border
        print(GREEN + '#' * 47 + RESET)
        print(GREEN + '#' * 47 + RESET)
        for row in range(3):
            dot_array = self.combine_numbers(self.board[row])
            for dot in dot_array:
                print(dot)
            # lower border
            print(GREEN + '#' * 47 + RESET)    
        print(GREEN + '#' * 47 + RESET)
    
    def combine_numbers(self, numbers_in_row):
        # 合并数字
        combined_dot_array = []
        for row_index in range(7):
            combined_row = GREEN + '## ' + RESET
            for num in numbers_in_row:
                number_dots = NUMBER_DOT_ARRAY[num][row_index]
                combined_row += BLUE + number_dots + GREEN + ' ## ' + RESET
            combined_dot_array.append(combined_row)
        return combined_dot_array

    
    def move(self, direction):
        # 移动空格所在的行或列
        if direction == 'w':
            # 把空格下方的数字往上移, 空格变成该数字
            num_row = self.space_row + 1
            num_col = self.space_col
        elif direction == 's':
            # 把空格上方的数字往下移, 空格变成该数字
            num_row = self.space_row - 1
            num_col = self.space_col 
        elif direction == 'a':
            # 把空格右边的数字往左移, 空格变成该数字
            num_row = self.space_row
            num_col = self.space_col + 1
        elif direction == 'd':
            # 把空格左边的数字往右移, 空格变成该数字
            num_row = self.space_row
            num_col = self.space_col - 1
        else:
            print('Invalid direction')
            return
        # 检查移动是否合法
        if num_row < 0 or num_row >= 3 or num_col < 0 or num_col >= 3:
            print('Invalid move')
            return
        # 执行移动
        self.board[self.space_row][self.space_col], self.board[num_row][num_col] = self.board[num_row][num_col], self.board[self.space_row][self.space_col]
        self.space_row, self.space_col = num_row, num_col
    
    def check_win(self):
        # 检查是否胜利
        for row in range(3):
            for col in range(3):
                if self.board[row][col] != row * 3 + col + 1:
                    if row == 2 and col == 2 and self.board[row][col] == 0:
                        return True
                    else:
                        return False
        return True
    
    def play(self):
        # Print board
        self.print_board_2d()
        # 游戏主循环
        while True:
            # Get user input
            key = None
            accepted_keys_and_map = {
                b'w': 'w', b's': 's', b'a': 'a', b'd': 'd', b'q': 'q',
                b'W': 'w', b'S': 's', b'A': 'a', b'D': 'd', b'Q': 'q',
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
            direction = key
            if direction == 'q':
                print('Game quit')
                break
            self.move(direction)
            # Print board
            self.print_board_2d()
            if self.check_win():
                print('You win!')
                break

if __name__ == '__main__':
    game = Game()
    game.play()