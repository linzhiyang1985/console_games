import random
import os
import msvcrt
import ctypes
import time
from copy import deepcopy
from playsound3 import playsound
import subprocess

GEM_TYPES = ['💎', '🧊', '💜', '🌸', '🌕', '🍀', '🚀'] ## 🏀🔴 🔶 '🟩',❄ '💠'  🔷 '💛'   #'🟥', '🟢', '🔵', '🟡', '🟣'
EXPLOSED_GEM = '💥'
SPECIAL_GEMS = {
    'lightning_h': '⚡', #⚡
    'lightning_v': '⬡', #❄
    'bomb': '💣',
    'rainbow': '🌈'
}
BOARD_SIZE = 8 # 8*8
MIN_MATCH = 3

HIGHLIGHT_BG = '\033[47m'
RESET = '\033[0m'

class BejeweledGame:
    def __init__(self):
        self.board = []
        self.score = 0
        self.game_over = False
        self.cursor_pos = (0, 0)
        self.need_help = True
        self.init_board()
    
    def init_board(self):
        self.board = []
        for _ in range(BOARD_SIZE):
            row = []
            for _ in range(BOARD_SIZE):
                row.append(random.choice(GEM_TYPES))
            self.board.append(row)
        while self.has_matches(self.board):
            self.clear_matches(is_mute=True)
            self.fill_empty(is_mute=True)
    
    def clear(self):
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

    def print_title(self):
        print("=== 宝石迷阵 ===")

    def print_rules(self):
        if self.need_help:
            print("游戏规则: 交换相邻宝石，使至少3颗相同颜色的宝石连成一线")
            print("方向键移动光标, Shift+方向键交换宝石, 't'提示, 'q'退出游戏")
            self.need_help = False
    
    def print_score(self):
        print(f"得分: {self.score}\n")

    def print_board(self, matched_cells=[]):
        self.clear()
        self.print_title()
        self.print_rules()
        
        self.print_score()

        for i, row in enumerate(self.board):
            for j, cell in enumerate(row):
                cell_display = f"{cell}" if cell != ' ' else EXPLOSED_GEM
                if (i, j) == self.cursor_pos:
                    cell_display = f"[{cell_display}]"
                else:
                    cell_display = f" {cell_display} "
                print(cell_display, end=' ')
            print()
    
    def has_matches(self, board):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE - MIN_MATCH + 1):
                if board[i][j] == board[i][j+1] == board[i][j+2]: # 检查水平匹配
                    return True
                if board[j][i] == board[j+1][i] == board[j+2][i]: # 检查垂直匹配
                    return True
        return False
    
    def swap_gems(self, row1, col1, row2, col2):
        self.board[row1][col1], self.board[row2][col2] = self.board[row2][col2], self.board[row1][col1]
    
    def is_valid_move(self, row, col, direction):
        new_row, new_col = row, col
        if direction == 'up':
            new_row = row - 1
        elif direction == 'down':
            new_row = row + 1
        elif direction == 'left':
            new_col = col - 1
        elif direction == 'right':
            new_col = col + 1
        
        return 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE
    
    def get_swap_pos(self, row, col, direction):
        if direction == 'up':
            return row - 1, col
        elif direction == 'down':
            return row + 1, col
        elif direction == 'left':
            return row, col - 1
        elif direction == 'right':
            return row, col + 1
    
    def find_matches(self):
        matches = []
        for i in range(BOARD_SIZE):
            j = 0
            while j < BOARD_SIZE:
                gem = self.board[i][j] # 起始宝石
                if gem in SPECIAL_GEMS.values():
                    matches.append([(i, j)]) # 特殊宝石独立消除
                    j += 1
                    continue
                k = j + 1
                while k < BOARD_SIZE and self.board[i][k] == gem: # 检查水平匹配
                    k += 1
                if k - j >= MIN_MATCH:
                    matches.append(sorted([(i, x) for x in range(j, k)]))
                j = k
        
        for j in range(BOARD_SIZE):
            i = 0
            while i < BOARD_SIZE:
                gem = self.board[i][j]
                if gem in SPECIAL_GEMS.values():
                    matches.append([(i, j)]) # 特殊宝石独立消除
                    i += 1
                    continue
                k = i + 1
                while k < BOARD_SIZE and self.board[k][j] == gem: # 检查垂直匹配
                    k += 1
                if k - i >= MIN_MATCH:
                    matches.append(sorted([(x, j) for x in range(i, k)]))
                i = k
        
        return matches
    
    def is_horizontal_match(self, match):
        return len(set([r for r, c in match])) == 1

    def clear_matches(self, is_mute=False):
        matches = self.find_matches()
        if not matches:
            return False
        
        for match in matches:
            match_count = len(match)
            self.score += match_count * 10
            for row, col in match:
                # 清除普通宝石
                gem = self.board[row][col]
                self.board[row][col] = ' '
                # 生成特殊宝石
                if match_count >= 4:
                    is_horizontal = self.is_horizontal_match(match)
                    special_gem_row, special_gem_col = (match[0] if is_horizontal else match[-1])
                    self.board[special_gem_row][special_gem_col] = self.create_special_gem(match_count, is_horizontal)
            if not is_mute:
                self.print_board(match)
                self.play_clear()
                time.sleep(0.5)
        for match in matches:
            for row, col in match:
                # 处理特殊宝石
                gem = self.board[row][col]
                exploded = False
                exploded_cells = []
                if gem == SPECIAL_GEMS['lightning_h']:
                    # 整行清除
                    for c in range(BOARD_SIZE):
                        if self.board[row][c] != ' ':
                            self.board[row][c] = ' '
                            exploded_cells.append((row, c))
                            self.score += 5
                    exploded = True
                elif gem == SPECIAL_GEMS['lightning_v']:
                    # 整列清除
                    for r in range(BOARD_SIZE):
                        if self.board[r][col] != ' ':
                            self.board[r][col] = ' '
                            exploded_cells.append((r, col))
                            self.score += 5
                    exploded = True
                elif gem == SPECIAL_GEMS['bomb']:
                    # 九宫格清除
                    for r in range(max(0, row-1), min(BOARD_SIZE, row+2)):
                        for c in range(max(0, col-1), min(BOARD_SIZE, col+2)):
                            if self.board[r][c] != ' ':
                                self.board[r][c] = ' '
                                exploded_cells.append((r, c))
                                self.score += 5
                    exploded = True
                elif gem == SPECIAL_GEMS['rainbow']:
                    # 随机选择一种宝石, 清除全屏幕所有该种宝石
                    target_gem = random.choice(GEM_TYPES)
                    for r in range(BOARD_SIZE):
                        for c in range(BOARD_SIZE):
                            if self.board[r][c] == target_gem:
                                self.board[r][c] = ' '
                                exploded_cells.append((r, c))
                                self.score += 5
                    exploded = True
                if exploded:
                    if not is_mute:
                        self.play_explode()
                        self.print_board(exploded_cells)
                        time.sleep(0.5)
        return True
    
    def fill_empty(self, is_mute=False):
        play_fill_count = 0
        falling_played = False
        for col in range(BOARD_SIZE):
            empty_row = BOARD_SIZE - 1
            for row in range(BOARD_SIZE - 1, -1, -1):
                if self.board[row][col] != ' ':
                    if row != empty_row:
                        self.board[empty_row][col] = self.board[row][col]
                        self.board[row][col] = ' '
                        if not is_mute:
                            play_fill_count += 1
                    empty_row -= 1
            if not is_mute and play_fill_count > 0 and not falling_played:
                self.play_fill()
                self.print_board()
                time.sleep(0.2)
                falling_played = True

            play_fill_count = 0
            new_gen_played = False
            for row in range(empty_row, -1, -1):
                self.board[row][col] = random.choice(GEM_TYPES)
                if not is_mute:
                    play_fill_count += 1

            if not is_mute and play_fill_count > 0 and not new_gen_played:
                self.play_fill()
                self.print_board()
                time.sleep(0.1)
                new_gen_played = True
    
    def create_special_gem(self, match_length, is_horizontal):
        if match_length == 4:
            if is_horizontal:
                return SPECIAL_GEMS['lightning_h']
            else:
                return SPECIAL_GEMS['lightning_v']
        elif match_length >= 5:
            return SPECIAL_GEMS['rainbow']
        return ' '
    
    def process_matches(self, is_mute=False):
        while self.clear_matches(is_mute):
            self.fill_empty(is_mute)
    
    def play_move(self):
        playsound('sound/move.wav', block=False)
    
    def play_invalid(self):
        playsound('sound/invalid.wav', block=False)
    
    def play_clear(self):
        playsound('sound/clear.wav', block=False)
    
    def play_explode(self):
        playsound('sound/explode.wav', block=False)
    
    def play_fill(self):
        playsound('sound/fill.wav', block=False)
    
    def get_user_input(self):
        accepted_keys_and_map = {
            b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right',
            b'q': 'quit', b'Q': 'quit',
            b't': 'tip',
            b'h': 'help',
            b'\r': 'enter',
        }
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':
                    key = msvcrt.getch()
                if key in accepted_keys_and_map:
                    cmd = accepted_keys_and_map[key]
                    if (ctypes.windll.user32.GetKeyState(0x10) & 0x8000) != 0:
                        cmd += ' swap'
                    return cmd
            time.sleep(0.1)

    def handle_input(self):
        while True:
            # user_input = input("\n请输入移动: ").strip().lower()
            cmd = self.get_user_input()
            if 'swap' in cmd:
                is_swap = True
                cmd = cmd.split(' ')[0]
            else:
                is_swap = False
            
            if cmd == 'quit':
                self.game_over = True
                return False
            elif cmd == 'help':
                self.need_help = True
                return True
            elif cmd == 'tip':
                is_no_more_moves, hint_pos = self.check_no_more_moves()
                if not is_no_more_moves:
                    self.cursor_pos = hint_pos
                return True
            elif cmd in ('up', 'down', 'left', 'right'):
                row, col = self.cursor_pos
                direction = cmd
                if self.is_valid_move(row, col, direction):
                    new_row, new_col = self.get_swap_pos(row, col, direction)
                    if is_swap:
                        self.swap_gems(row, col, new_row, new_col) # 交换宝石
                        if not self.has_matches(self.board):
                            self.swap_gems(row, col, new_row, new_col) # 恢复交换
                            self.play_invalid()
                        else:
                            self.cursor_pos = (new_row, new_col)
                            self.play_move()
                    else:
                        self.cursor_pos = (new_row, new_col)
                        self.play_move()
                return True
    
    def check_no_more_moves(self):
        # 尝试交换任意两个位置，检查是否有匹配
        temp_board = deepcopy(self.board)
        # 检查水平匹配
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE - 2):
                # swap
                temp_board[row][col], temp_board[row][col+1] = temp_board[row][col+1], temp_board[row][col]
                if self.has_matches(temp_board):
                    return False, (row, col)
                # swap back
                temp_board[row][col], temp_board[row][col+1] = temp_board[row][col+1], temp_board[row][col]
        # 检查垂直匹配
        for col in range(BOARD_SIZE):
            for row in range(BOARD_SIZE - 2):
                # swap
                temp_board[row][col], temp_board[row+1][col] = temp_board[row+1][col], temp_board[row][col]
                if self.has_matches(temp_board):
                    return False, (row, col)
                # swap back
                temp_board[row][col], temp_board[row+1][col] = temp_board[row+1][col], temp_board[row][col]
        return True, None

    def play(self):
        self.print_title()
        self.print_rules()
        
        while not self.game_over:
            self.print_board()
            if not self.handle_input():
                break
            self.process_matches()
            if self.check_no_more_moves()[0]:
                self.game_over = True
                print("没办法再移动了！")
        
        print(f"\n游戏结束! 最终得分: {self.score}")

if __name__ == "__main__":
    game = BejeweledGame()
    game.process_matches(is_mute=True)
    game.score = 0
    game.play()
