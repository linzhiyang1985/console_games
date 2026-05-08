import random
import os
import msvcrt
import ctypes
import time
from copy import deepcopy
from playsound3 import playsound
import subprocess
import re
import threading


CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fa5]{1}')  # 中文字符的Unicode范围
WIDECHAR_PATTERN = re.compile(r'[^\u0001-\u4e00]{1}')  # 任意宽字符, 如Emoji

GEM_TYPES = ['💎', '🧊', '💜', '🌸', '🌕', '🍀', '🚀'] ## 🏀🔴 🔶 '🟩',❄ '💠'  🔷 '💛'   #'🟥', '🟢', '🔵', '🟡', '🟣'
EXPLOSED_GEM = '💥'
SPECIAL_GEMS = {
    'lightning_h': '⚡',
    'lightning_v': '❄',
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
        self.prev_frame_rows = []
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

    def output_title(self):
        return ["=== 宝石迷阵 ==="]

    def output_rules(self):
        rules = []
        if self.need_help:
            rules.append("游戏规则:")
            rules.append("交换相邻宝石, 使至少3颗相同颜色的宝石连成一线")
            rules.append("方向键移动光标, Shift+方向键交换宝石")
            rules.append("'t'提示, 'q'退出游戏")
            self.need_help = False
        return rules
    
    def output_score(self):
        return [f"得分: {self.score}"]

    def output_board(self):
        board_rows = []

        for i, row in enumerate(self.board):
            row_str = ''
            for j, cell in enumerate(row):
                cell_display = f"{cell}" if cell != ' ' else EXPLOSED_GEM # 爆炸后的宝石显示为💥
                if (i, j) == self.cursor_pos:
                    cell_display = f"[{cell_display}]"
                else:
                    cell_display = f" {cell_display} "
                row_str += cell_display
            board_rows.append(row_str)
        return board_rows

    def move_console_cursor(self, row: int, column: int):
        # 移动光标到指定位置, 左上角坐标为(1,1)
        if os.name == 'nt':
            msvcrt.putch(b'\x1b')
            msvcrt.putch(b'[')
            for r in f"{row}":
                msvcrt.putch(r.encode())
            msvcrt.putch(b';')
            for c in f"{column}":
                msvcrt.putch(c.encode())
            msvcrt.putch(b'H')
        else:
            curses.move(row, column)

    def calculate_delta_frame_row(self, new_frame_rows):
        delta_frame_rows = []
        for i, new_row in enumerate(new_frame_rows):
            new_row_len = len(new_row) + len(WIDECHAR_PATTERN.findall(new_row)) # 每个中文字符/Emoji占两位宽度

            old_row = self.prev_frame_rows[i] if i < len(self.prev_frame_rows) else ''
            old_row_len = len(old_row) + len(WIDECHAR_PATTERN.findall(old_row)) # 每个中文字符/Emoji占两位宽度

            if new_row != old_row:
                new_row = new_row.ljust(max(old_row_len, new_row_len))
                delta_frame_rows.append((i+1, new_row))
        extra_rows_to_clean = len(self.prev_frame_rows) - len(new_frame_rows)
        if extra_rows_to_clean > 0:
            for i in range(len(new_frame_rows), len(self.prev_frame_rows), 1):
                old_row_len = len(old_row) + len(WIDECHAR_PATTERN.findall(self.prev_frame_rows[i])) # 每个中文字符占两位宽度
                delta_frame_rows.append((i+1, ' ' * old_row_len)) # 打印空格以覆盖旧行
        return delta_frame_rows

    def print_frame(self, extra_rows=[], insert_at=-1):
        title_row = self.output_title()
        rule_rows = self.output_rules()
        score_row = self.output_score()
        board_rows = self.output_board()

        frame_rows = title_row + rule_rows + score_row + board_rows
        for row in extra_rows:
            if insert_at == -1:
                frame_rows.append(row)
            else:
                frame_rows.insert(insert_at, row)
        
        delta_frame_rows = self.calculate_delta_frame_row(frame_rows)
        self.prev_frame_rows = frame_rows

        for i, row in delta_frame_rows:
            self.move_console_cursor(i+1, 1)
            print(row)
    
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
                self.print_frame()
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
                        self.print_frame()
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
                self.print_frame()
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
                self.print_frame()
                time.sleep(0.1)
                new_gen_played = True
    
    def create_special_gem(self, match_length, is_horizontal):
        if match_length == 4:
            if is_horizontal:
                return SPECIAL_GEMS['lightning_h']
            else:
                return SPECIAL_GEMS['lightning_v']
        elif match_length >= 5:
            return random.choice([SPECIAL_GEMS['bomb'], SPECIAL_GEMS['rainbow']])
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
        messages = []
        while not self.game_over:
            self.print_frame()
            if not self.handle_input():
                break
            self.process_matches()
            if self.check_no_more_moves()[0]:
                self.game_over = True
                messages.extend(["没办法再移动了！"])
        
        messages.extend(["", f"游戏结束! 最终得分: {self.score}"])
        self.print_frame(messages)

class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.sound_file_path = 'sound/background.mp3'
        self.track_length = 157
        self.sound_handle = None
        self.is_stop = False
        
    def run(self):
        start_time = time.time()
        self.sound_handle = playsound(self.sound_file_path, block=False)
        while not self.is_stop:
            if time.time() - start_time >= self.track_length: # whole sound duration
                # play random sound
                self.sound_handle.stop()
                self.sound_handle = playsound(self.sound_file_path, block=False)
            time.sleep(1)
        self.sound_handle.stop()
    
    def stop(self):
        self.is_stop = True

if __name__ == "__main__":
    try:
        background_player = LoopPlayer()
        background_player.start()

        game = BejeweledGame()
        game.process_matches(is_mute=True)
        game.score = 0
        game.clear()
        game.play()

    except Exception as e:
        pass
    finally:
        background_player.stop()
