import os
import sys
import random
from dataclasses import dataclass
import msvcrt
import time
from playsound3 import playsound


@dataclass
class Color:
    BLACK_FG = '\033[30m'
    RED_FG = '\033[31m'
    GREEN_FG = '\033[32m'
    YELLOW_FG = '\033[33m'
    BLUE_FG = '\033[34m'
    MAGENTA_FG = '\033[35m'
    CYAN_FG = '\033[36m'
    DARK_WHITE_FG = '\033[37m'
    DARK_WHITE_BG = '\033[47m'

    BRIGHT_BLACK_FG = '\033[90m'
    BRIGHT_RED_FG = '\033[91m'
    BRIGHT_GREEN_FG = '\033[92m'
    BRIGHT_YELLOW_FG = '\033[93m'
    BRIGHT_BLUE_FG = '\033[94m'
    BRIGHT_MAGENTA_FG = '\033[95m'
    BRIGHT_CYAN_FG = '\033[96m'
    WHITE_FG = '\033[97m'

    RESET = '\033[0m'

class ConnectFour:
    def __init__(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]  # 6行7列
        self.init_player = 1
        self.game_over = False
        self.current_player = 1  # 1代表红色，2代表黄色
        self.game_mode = None  # 1: 双人对战, 2: 人机对战
        self.ai_color = None  # AI的颜色
        self.ai_difficulty = random.randint(1, 3)  # AI难度，1-3
        self.chess_position = 4
    
    def renew_game(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]  # 6行7列
        self.game_over = False
        self.current_player = self.init_player

    # def print_board(self):
    #     os.system('cls' if os.name == 'nt' else 'clear')
    #     print(" 1 2 3 4 5 6 7")
    #     print("-+-+-+-+-+-+-+-")
    #     for row in reversed(self.board):
    #         print("|", end="")
    #         for cell in row:
    #             if cell == 1:
    #                 print(Color.RED_FG + "R" + Color.RESET, end="|")  # 红色
    #             elif cell == 2:
    #                 print(Color.YELLOW_FG + "Y" + Color.RESET, end="|")  # 黄色
    #             else:
    #                 print(Color.DARK_WHITE_BG + " " + Color.RESET, end="|")
    #         print()
    #     print("-+-+-+-+-+-+-+-")

    CHESS = ('▗▟█▙▖', '█████', '▝▜█▛▘')

# """
# +-------+
# | ▗▟█▙▖ |
# | █████ |
# | ▝▜█▛▘ |
# +-------+
# """

    
    def play_move_sound(self):
        playsound('sound/move.wav', block=False)

    def play_drop_sound(self):
        playsound('sound/drop.wav', block=False)
        time.sleep(0.2)

    def play_win_sound(self):
        playsound('sound/win.wav', block=False)

    def print_board(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        # 打印标题
        print('=' * 22 + '  四子棋游戏  ' + '=' * 21)
        print()

        # 打印棋子
        for r in range(3):
            for i in range(1, 8):
                if i == self.chess_position:
                    print((Color.RED_FG if self.current_player == 1 else Color.YELLOW_FG) + (' ' * 2) + self.CHESS[r] + (' ' * 2) + Color.RESET, end="")
                else:
                    print(' ' * 8, end="")
            print()
        
        # 打印序号
        print(" ", end="")
        for i in range(1, 8):
            print(f'   {i}    ', end="")
        print()

        # 打印棋盘, 
        print("+-------" * 7 + "+")
        for row in reversed(self.board):
            row_content = ''
            for i in range(3):
                row_content += "|"
                for cell in row:
                    if cell == 1:
                        row_content += Color.RED_FG + ' ' + self.CHESS[i] + ' ' + Color.RESET + "|"
                    elif cell == 2:
                        row_content += Color.YELLOW_FG + ' ' + self.CHESS[i] + ' ' + Color.RESET + "|"
                    else:
                        row_content += " " * 7 + "|"
                if i < 2:
                    row_content += "\n"
            print(row_content)
            print("+-------" * 7 + "+")


    def is_valid_move(self, col):
        return 0 <= col < 7 and self.board[5][col] == 0

    def drop_piece(self, col, player):
        for row in range(6):
            if self.board[row][col] == 0:
                self.board[row][col] = player
                return row, col
        return None

    def check_win(self, player, row, col):
        # 检查横向
        count = 0
        for c in range(7):
            if self.board[row][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0

        # 检查纵向
        count = 0
        for r in range(6):
            if self.board[r][col] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0

        # 检查对角线（右上）
        count = 0
        r, c = row, col
        while r >= 0 and c < 7:
            if self.board[r][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
            r -= 1
            c += 1

        # 检查对角线（左上）
        count = 0
        r, c = row, col
        while r >= 0 and c >= 0:
            if self.board[r][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
            r -= 1
            c -= 1

        # 检查对角线（左下）
        count = 0
        r, c = row, col
        while r < 6 and c >= 0:
            if self.board[r][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
            r += 1
            c -= 1

        # 检查对角线（右下）
        count = 0
        r, c = row, col
        while r < 6 and c < 7:
            if self.board[r][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
            r += 1
            c += 1

        return False

    def is_board_full(self):
        return all(self.board[5][col] != 0 for col in range(7))

    def evaluate_window(self, window, player):
        score = 0
        opponent = 1 if player == 2 else 2

        if window.count(player) == 4:
            score += 100
        elif window.count(player) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(player) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opponent) == 3 and window.count(0) == 1:
            score -= 4

        return score

    def score_position(self, player):
        score = 0

        # 中心列优先
        center_array = [self.board[row][3] for row in range(6)]
        center_count = center_array.count(player)
        score += center_count * 3

        # 水平方向
        for r in range(6):
            row_array = self.board[r]
            for c in range(4):
                window = row_array[c:c+4]
                score += self.evaluate_window(window, player)

        # 垂直方向
        for c in range(7):
            col_array = [self.board[r][c] for r in range(6)]
            for r in range(3):
                window = col_array[r:r+4]
                score += self.evaluate_window(window, player)

        # 正对角线
        for r in range(3):
            for c in range(4):
                window = [self.board[r+i][c+i] for i in range(4)]
                score += self.evaluate_window(window, player)

        # 反对角线
        for r in range(3):
            for c in range(4):
                window = [self.board[r+i][c+3-i] for i in range(4)]
                score += self.evaluate_window(window, player)

        return score

    def minimax(self, depth, alpha, beta, maximizing_player):
        valid_moves = [col for col in range(7) if self.is_valid_move(col)]
        is_terminal = self.is_board_full() or any(self.check_win(1, r, c) for r in range(6) for c in range(7)) or any(self.check_win(2, r, c) for r in range(6) for c in range(7))

        if depth == 0 or is_terminal:
            if is_terminal:
                if any(self.check_win(self.ai_color, r, c) for r in range(6) for c in range(7)):
                    return (None, 100000000000000)
                elif any(self.check_win(1 if self.ai_color == 2 else 2, r, c) for r in range(6) for c in range(7)):
                    return (None, -100000000000000)
                else:
                    return (None, 0)
            else:
                return (None, self.score_position(self.ai_color))

        if maximizing_player:
            value = -float('inf')
            column = random.choice(valid_moves)
            for col in valid_moves:
                row = self.drop_piece(col, self.ai_color)[0]
                new_score = self.minimax(depth-1, alpha, beta, False)[1]
                self.board[row][col] = 0
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = float('inf')
            column = random.choice(valid_moves)
            opponent = 1 if self.ai_color == 2 else 2
            for col in valid_moves:
                row = self.drop_piece(col, opponent)[0]
                new_score = self.minimax(depth-1, alpha, beta, True)[1]
                self.board[row][col] = 0
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    def get_ai_move(self):
        depth = self.ai_difficulty
        if depth == 1:
            depth = 2
        elif depth == 2:
            depth = 3
        else:
            depth = 4
        col, _ = self.minimax(depth, -float('inf'), float('inf'), True)
        return col

    def get_user_input(self):
        key = None
        accepted_keys_and_map = {
            b'Q': 'q', b'q': 'q',
            b'K': 'left', b'M': 'right', b'P': 'down', b' ': 'down',
            b'1': '1', b'2': '2', b'3': '3', b'4': '4', b'5': '5', b'6': '6', b'7': '7',
        }
        while key is None:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':
                    key = msvcrt.getch()
                if key in accepted_keys_and_map:
                    key = accepted_keys_and_map[key]
                else:
                    key = None
            time.sleep(0.1)
        return key
    
    def play(self):
        print("===== 四子棋游戏 =====")
        print("游戏模式:")
        print("1. 人机对战")
        print("2. 双人对战")
        mode = input("请选择游戏模式(1/2,直接[回车]默认1), [Q]退出游戏:")
        if mode.lower() == 'q':
            print("游戏已退出")
            return
        if mode.strip() == "":
            mode = "1"
        self.game_mode = int(mode)

        if self.game_mode == 1:
            print("棋子颜色:")
            print("1. 红色")
            print("2. 黄色")
            color = input("请选择你的棋子颜色(1/2,直接[回车]默认1), [Q]退出游戏:")
            if color.lower() == 'q':
                print("游戏已退出")
                return
            if color.strip() == "":
                color = "1"
            player_color = int(color)
            self.ai_color = 2 if player_color == 1 else 1

            print("\n玩家先手/后手:")
            print("1. 先手")
            print("2. 后手")
            turn = input("请选择先手/后手(1/2,直接[回车]默认1), [Q]退出游戏:")
            if turn.lower() == 'q':
                print("游戏已退出")
                return
            if turn.strip() == "":
                turn = "1"
            if int(turn) == 2:
                self.current_player = self.ai_color
            else:
                self.current_player = player_color
            self.init_player = self.current_player # keep this setting through all game rounds

        while True:
            while not self.game_over:
                self.print_board()

                if self.game_mode == 2 or (self.game_mode == 1 and self.current_player != self.ai_color):
                    print(f"{Color.RED_FG + '红方' + Color.RESET if self.current_player == 1 else Color.YELLOW_FG + '黄方' + Color.RESET}玩家请下棋")
                    print("请用[左][右]移动棋子,[下]/[空格]落子")
                    print("或输入列号(1-7)直接落子")
                    print("[Q]退出")
                    move = self.get_user_input()
                    if move.lower() == 'q':
                        print("游戏已退出")
                        return
                    if move == 'left' and self.chess_position > 1:
                        self.chess_position -= 1
                        self.play_move_sound()
                        continue
                    elif move == 'right' and self.chess_position < 7:
                        self.chess_position += 1
                        self.play_move_sound()
                        continue
                    elif move == 'down':
                        move = self.chess_position
                    # do move
                    try:
                        col = int(move) - 1
                        if not self.is_valid_move(col):
                            print("无效的移动，请重新输入")
                            continue
                    except ValueError:
                        print("请输入有效的列号")
                        continue
                else:
                    print("AI正在思考...")
                    col = self.get_ai_move()
                    print(f"AI选择了列 {col + 1}")

                row, col = self.drop_piece(col, self.current_player)
                self.play_drop_sound()
                if self.check_win(self.current_player, row, col):
                    self.game_over = True
                    self.play_win_sound()
                    self.print_board()
                    print(f"{Color.RED_FG + '红方' + Color.RESET if self.current_player == 1 else Color.YELLOW_FG + '黄方' + Color.RESET}玩家获胜！")
                    break
                if self.is_board_full():
                    self.game_over = True
                    self.play_win_sound()
                    self.print_board()
                    print("平局！")
                    break

                self.current_player = 2 if self.current_player == 1 else 1

            again = input("再玩一局(Y/N, 直接[回车]再玩一局)? ").lower()
            if again.strip() == "":
                again = "y"
            if again == "y":
                self.renew_game()
            else:
                return

if __name__ == "__main__":
    game = ConnectFour()
    game.play()
