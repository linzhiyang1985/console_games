import random
import subprocess
import time
import ctypes
import re
import os
import threading
import msvcrt
import sys
from playsound3 import playsound


class Color:
    GRAY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

    BLACK = '\033[30m' # default background

    DARK_RED = '\033[31m'
    DARK_GREEN = '\033[32m'
    DARK_YELLOW = '\033[33m'
    DARK_BLUE = '\033[34m'
    DARK_MAGENTA = '\033[35m'
    DARK_CYAN = '\033[36m'
    DARK_WHITE = '\033[37m'
    
    WHITE = '\033[97m'  # default foreground
    RESET = '\033[0m'

    BG_DARK_WHITE = '\033[47m' #47--bg, XXXX--fg
    
class Gem:
    def __init__(self, emoji='  '):
        self.emoji = emoji
        self.selected = False
        self.moving = False
        self.highlight = False
        self.highlight_in_row_or_col = ''
        self.is_option = False
    
    def __repr__(self) -> str:
        return ('*' if self.selected or self.moving else '') + self.emoji
    
    def set_select(self, selected):
        self.selected = selected
    
    def set_moving(self, moving):
        self.moving = moving
    
    def set_highlight(self, highlight, in_row_or_col):
        self.highlight = highlight
        self.highlight_in_row_or_col = in_row_or_col
    
    def set_is_option(self, is_option):
        self.is_option = is_option

    def output_gem(self):
        # 3*3
        gem_matrix = [
            [' ', ' ', ' ', ' '],
            [' ', self.emoji, ' '],
            [' ', ' ', ' ', ' ']
        ]
        if self.selected or self.moving or self.is_option:
            gem_matrix[0][0] = '╭'
            gem_matrix[0][-1] = '╮'
            gem_matrix[-1][0] = '╰'
            gem_matrix[-1][-1] = '╯'
        if self.moving or self.is_option:
            gem_matrix[0][1] = '─'
            gem_matrix[0][2] = '─'
            gem_matrix[1][0] = '│'
            gem_matrix[1][-1] = '│'
            gem_matrix[2][1] = '─'
            gem_matrix[2][2] = '─'
        
        # render
        if self.highlight:
            bg_color = Color.BG_DARK_WHITE
        else:
            bg_color = Color.BLACK
        
        if self.is_option:
            if self.selected:
                fg_color = Color.DARK_MAGENTA
            else:
                fg_color = Color.MAGENTA
        elif self.selected or self.moving:
                fg_color = Color.YELLOW
        else:
                fg_color = Color.WHITE
        if bg_color:
            color = bg_color[:-1] + ';' + fg_color[fg_color.index('[')+1:]

        for i in range(len(gem_matrix)):
            for j in range(len(gem_matrix[i])):
                if self.highlight:
                    if self.highlight_in_row_or_col == 'r' and i == 1:
                        gem_matrix[i][j] = color + gem_matrix[i][j] + Color.RESET
                    elif self.highlight_in_row_or_col == 'c' and ((i==1 and j== 1) or (i!=1 and j in (1, 2))):
                        gem_matrix[i][j] = color + gem_matrix[i][j] + Color.RESET
                    elif self.highlight_in_row_or_col == 'rc' and ((i == 1) or (i!=1 and j in (1, 2))):
                        gem_matrix[i][j] = color + gem_matrix[i][j] + Color.RESET
                    else:
                        gem_matrix[i][j] = fg_color + gem_matrix[i][j] + Color.RESET
                else:
                    gem_matrix[i][j] = fg_color + gem_matrix[i][j] + Color.RESET
        return gem_matrix

class ScreenFramePrinter:
    COLOR_PATTERN = re.compile(r'\x1b\[\d+m')
    WIDECHAR_PATTERN = re.compile(r'[^\u0001-\u4dff]{1}')  # 任意宽字符, 如中文, Emoji等
    IS_WINDOWS = (os.name == 'nt')

    def __init__(self):
        self.prev_frame_rows = []
    
    @staticmethod
    def clear():
        subprocess.run('cls' if ScreenFramePrinter.IS_WINDOWS else 'clear', shell=True)

    @staticmethod
    def move_console_cursor(row: int, column: int):
        # 移动光标到指定位置, 左上角坐标为(1,1)
        if ScreenFramePrinter.IS_WINDOWS:
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
    
    @staticmethod
    def display_len(row):
        return len(ScreenFramePrinter.COLOR_PATTERN.sub('', row))
    
    @staticmethod
    def widechar_count(row):
        return len(ScreenFramePrinter.WIDECHAR_PATTERN.findall(row)) # 每个中文字符/Emoji占两位宽度
    
    def clear_cache(self):
        self.prev_frame_rows = []

    def calculate_delta_frame_row(self, new_frame_rows):
        delta_frame_rows = []
        for i, new_row in enumerate(new_frame_rows):
            new_row_len = self.display_len(new_row) + self.widechar_count(new_row)

            old_row = self.prev_frame_rows[i] if i < len(self.prev_frame_rows) else ''
            old_row_len = self.display_len(old_row) + self.widechar_count(old_row)

            if new_row != old_row:
                new_row = new_row.ljust(max(old_row_len, new_row_len))
                delta_frame_rows.append((i+1, new_row))
        
        extra_rows_to_clean = len(self.prev_frame_rows) - len(new_frame_rows)
        if extra_rows_to_clean > 0:
            for i in range(len(new_frame_rows), len(self.prev_frame_rows), 1):
                old_row = self.prev_frame_rows[i]
                old_row_len = self.display_len(old_row) + self.widechar_count(old_row)
                delta_frame_rows.append((i+1, ' ' * old_row_len)) # 打印空格以覆盖旧行
        return delta_frame_rows
    
    def print_frame(self, frame_rows):
        delta_frame_rows = self.calculate_delta_frame_row(frame_rows)
        self.prev_frame_rows = frame_rows

        for i, row in delta_frame_rows:
            ScreenFramePrinter.move_console_cursor(i+1, 1)
            print(row)

class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.sound_file_path = 'sound/background.mp3'
        self.track_length = 27
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
                start_time = time.time()
            time.sleep(1)
        self.sound_handle.stop()
    
    def stop(self):
        self.is_stop = True


frame_printer = ScreenFramePrinter()

class Board:
    ####  '🍄', '🍄‍🟫' #'🍳' #'🌹' #'🎒' #'👘'###
    EMOJI = [
        ['🥦', '🥔', '🍄', '🌰', '🌽', '🥕'],
        ['🍎', '🍌', '🍒', '🍋', '🍊', '🍑'],
        ['🌭', '🥪', '🥨', '🍗', '🍔', '🥩'],
        ['🍧', '🍨', '🍩', '🍭', '🍰', '🍪'],
        ['🍺', '🧋', '☕', '🥤', '🥛', '🍼'],
        ['🫖', '🍴', '🥄', '🥢', '🫙', '🍟'],
        ['🌻', '🌷', '🌵', '🌸', '🍀', '🍁'],
        ['🤡', '👻' , '👹', '👺', '🐲', '🎭'],
        ['🏀', '🏐', '🏈', '🏓', '🎾', '🎿'],
        ['💊', '💰', '🎧', '💿', '⛄', '💄'],
        ['💻', '🎮', '🎹', '🎰', '👜', '👟'],
        ['🐝', '🐶', '🐲', '☂️', '☔', '🌕', '🌏'],
    ]

    def __init__(self):
        self.board_width = 14
        self.board_height = 10
        self.gems = [[Gem('  ') for _ in range(self.board_width)] for _ in range(self.board_height)]
        self.init_gems()
        self.cursor_pos = (0, 0)
        self.gems[self.cursor_pos[0]][self.cursor_pos[1]].set_select(True)

        self.show_same_emoji = False
        self.prev_same_emoji_positions = []

        self.in_move_process = False
        self.in_option_process = False
        self.original_direction = None
        self.original_block_positions = []
        self.prev_block_positions = []

        self.matching_pos_list = []
        self.option_index = 0
    
    ## same emoji char appears as a pair within the board
    def init_gems(self):
        total = self.board_width * self.board_height
        remain_emojis = []
        [remain_emojis.extend(row) for row in Board.EMOJI]
        empty_slots = self.get_empty_slots()

        while total > 0:
            emoji = random.choice(remain_emojis)
            remain_emojis.remove(emoji)
            for _ in range(random.choice((1, 2))): #  for the same emoji, may generate one pair or two pairs
                if not empty_slots:
                    break
                # fill into one pair with the same same emoji
                for _ in range(2):
                    r, c = random.choice(empty_slots)
                    self.gems[r][c] = Gem(emoji)
                    empty_slots.remove((r, c))
                    total -= 1

    def random_gem(self):
        random_row = random.choice(Board.EMOJI)
        emoji = random.choice(random_row)
        return emoji
    
    def __repr__(self) -> str:
        return '\n'.join([','.join([str(gem) for gem in row]) for row in self.gems])
    
    def get_empty_slots(self):
        empty_positions = []
        for r in range(self.board_height):
            for c in range(self.board_width):
                if self.is_empty(r, c):
                    empty_positions.append((r, c))
        return empty_positions
    
    def get_not_empty_slots(self):
        not_empty_positions = []
        for r in range(self.board_height):
            for c in range(self.board_width):
                if not self.is_empty(r, c):
                    not_empty_positions.append((r, c))
        return not_empty_positions

    def clear_highlights(self):
        for row in self.gems:
            for gem in row:
                gem.set_highlight(False, '')
    
    def set_highlights(self):
        cursor_r, cursor_c = self.cursor_pos
        for r in range(self.board_height):
            for c in range(self.board_width):
                if r == cursor_r:
                    self.gems[r][c].set_highlight(True, 'r')
                if c == cursor_c:
                    self.gems[r][c].set_highlight(True, 'c')
        self.gems[cursor_r][cursor_c].set_highlight(True, 'rc')

    def find_same_emojis(self, emoji):
        same_emoji_positions = []
        for r in range(self.board_height):
            for c in range(self.board_width):
                if self.gems[r][c].emoji == emoji:
                    same_emoji_positions.append((r, c))
        return same_emoji_positions

    def clear_same_emoji(self):
        ## 清理原来的 selected 状态
        for r, c in self.prev_same_emoji_positions:
            self.gems[r][c].set_select(False)
            self.prev_same_emoji_positions = []

    def update_same_emoji(self):
        self.clear_same_emoji()

        cursor_r, cursor_c = self.cursor_pos
        self.prev_same_emoji_positions = self.find_same_emojis(self.gems[cursor_r][cursor_c].emoji)
        ## 标记新一批的select状态
        for r, c, in self.prev_same_emoji_positions:
            self.gems[r][c].set_select(True)

    def output_board(self):
        if self.show_same_emoji:
            self.update_same_emoji()
        else:
            self.clear_same_emoji()

        self.clear_highlights()
        self.set_highlights()

        rows = []
        for row in self.gems:
            gems_in_row = []
            for gem in row:
                gem_rows = gem.output_gem()
                gems_in_row.append(gem_rows)
            for i in range(3):
                output_row = []
                for gr in gems_in_row:
                    output_row.extend(gr[i])
                rows.append(''.join(output_row))
        return rows
        
    def valid_position(self, r, c):
        return 0<=r<self.board_height and 0<=c<self.board_width

    def is_empty(self, r, c):
        # check if the center of the gem is space
        return self.gems[r][c].emoji == '  '

    def move_cursor_to(self, new_r, new_c):
        old_r, old_c = self.cursor_pos
        self.cursor_pos = (new_r, new_c)
        self.gems[new_r][new_c].set_select(True)
        self.gems[old_r][old_c].set_select(False)
        self.play_move()

    def cursor_move_left(self):
        old_r, old_c = self.cursor_pos
        new_r, new_c = old_r, old_c - 1
        if self.valid_position(new_r, new_c):
            self.move_cursor_to(new_r, new_c)

    def cursor_move_right(self):
        old_r, old_c = self.cursor_pos
        new_r, new_c = old_r, old_c + 1
        if self.valid_position(new_r, new_c):
            self.move_cursor_to(new_r, new_c)

    def cursor_move_up(self):
        old_r, old_c = self.cursor_pos
        new_r, new_c = old_r - 1, old_c
        if self.valid_position(new_r, new_c):
            self.move_cursor_to(new_r, new_c)

    def cursor_move_down(self):
        old_r, old_c = self.cursor_pos
        new_r, new_c = old_r + 1, old_c
        if self.valid_position(new_r, new_c):
            self.move_cursor_to(new_r, new_c)

    def shift_pressed(self):
        return (ctypes.windll.user32.GetKeyState(0x10) & 0x8000) != 0

    def get_user_input(self):
        accepted_keys_and_map = {
            b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right',
            b'q': 'quit', b'Q': 'quit',
            b'a': 'help',
            b'x': 'shuffle', b'X': 'shuffle',
            b's': 'toggle_same', b'S': 'toggle_same',
            b'r': 'refresh',
            b'\r': 'enter',
        }
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':
                    key = msvcrt.getch()
                if key in accepted_keys_and_map:
                    cmd =  accepted_keys_and_map[key]
                    return cmd
            time.sleep(0.1)
            ## 特殊处理Shift键的单独事件
            if self.in_move_process and not self.shift_pressed():
                return 'move_end'
            elif not self.in_move_process and self.shift_pressed():
                return 'move_start'

    def find_moving_block(self, direction):
        r, c = self.cursor_pos
        if self.is_empty(r, c):
            return []
        moving_blocks = [(r, c)]
        if direction:
            while True:
                if direction == 'left':
                    next_block = (r, c-1)
                elif direction == 'right':
                    next_block = (r, c+1)
                elif direction == 'up':
                    next_block = (r-1, c)
                elif direction == 'down':
                    next_block = (r+1, c)
                if self.valid_position(*next_block):
                    if self.is_empty(*next_block):
                        break
                    else:
                        moving_blocks.append(next_block)
                else:
                    break
                r, c = next_block
        return moving_blocks

    def reset_blocks_to_original(self):
        if self.original_block_positions and self.prev_block_positions != self.original_block_positions:
            for index, (r, c) in enumerate(self.prev_block_positions):
                o_r, o_c = self.original_block_positions[index]
                self.gems[o_r][o_c] = self.gems[r][c]
                self.gems[r][c] = Gem()
            self.cursor_pos = self.original_block_positions[0]
            self.play_reset()

    def move_blocks(self, next_pos):
        if self.valid_position(*next_pos) and self.is_empty(*next_pos):
            self.prev_block_positions.append(next_pos)
            # 最尾一块的左方有空位, 说明可以移动
            for index in range(len(self.prev_block_positions) - 1, -1, -1):
                if index == 0:
                    self.gems[self.prev_block_positions[index][0]][self.prev_block_positions[index][1]] = Gem()
                else:
                    self.gems[self.prev_block_positions[index][0]][self.prev_block_positions[index][1]] = self.gems[self.prev_block_positions[index-1][0]][self.prev_block_positions[index-1][1]]
            self.prev_block_positions.pop(0)
            self.cursor_pos = self.prev_block_positions[0]
            self.play_drag()

    def find_matching_positions(self):
        # 检查是否有跟当前块匹配的块
        cursor_r, cursor_c = self.cursor_pos
        cursor_gem = self.gems[cursor_r][cursor_c]
        matching_gems = []
        # 先找到四个方向上第一个非空的块
        # left
        for col in range(cursor_c - 1, -1, -1):
            if not self.valid_position(cursor_r, col):
                break # 到头了
            if self.is_empty(cursor_r, col):
                continue
            # 只需要检查第一个非空的块
            if self.gems[cursor_r][col].emoji == cursor_gem.emoji:
                matching_gems.append((cursor_r, col))
            break
        # right
        for col in range(cursor_c + 1, self.board_width):
            if not self.valid_position(cursor_r, col):
                break # 到头了
            if self.is_empty(cursor_r, col):
                continue
            # 只需要检查第一个非空的块
            if self.gems[cursor_r][col].emoji == cursor_gem.emoji:
                matching_gems.append((cursor_r, col))
            break
        # up
        for row in range(cursor_r - 1, -1, -1):
            if not self.valid_position(row, cursor_c):
                break # 到头了
            if self.is_empty(row, cursor_c):
                continue
            # 只需要检查第一个非空的块
            if self.gems[row][cursor_c].emoji == cursor_gem.emoji:
                matching_gems.append((row, cursor_c))
            break
        # down
        for row in range(cursor_r + 1, self.board_height):
            if not self.valid_position(row, cursor_c):
                break # 到头了
            if self.is_empty(row, cursor_c):
                continue
            # 只需要检查第一个非空的块
            if self.gems[row][cursor_c].emoji == cursor_gem.emoji:
                matching_gems.append((row, cursor_c))
            break

        return matching_gems

    def clear_gems(self, *positions):
        for r, c in positions:
            self.gems[r][c] = Gem()
        self.play_clear()
    
    def swap_gems(self, gem_pos1, gem_pos2):
        r1, c1 = gem_pos1
        r2, c2 = gem_pos2
        self.gems[r1][c1], self.gems[r2][c2] = self.gems[r2][c2], self.gems[r1][c1]
    
    def shuffle_gems(self):
        not_empty_positions = self.get_not_empty_slots()
        while len(not_empty_positions) > 1:
            index1 = random.randint(0, len(not_empty_positions) - 1)
            index2 = random.randint(0, len(not_empty_positions) - 1)
            if index1 != index2:
                pos1 = not_empty_positions[index1]
                pos2 = not_empty_positions[index2]
                self.swap_gems(pos1, pos2)
                not_empty_positions.remove(pos1)
                not_empty_positions.remove(pos2)

    def play_move(self):
        playsound('sound/move.mp3', block=False)

    def play_drag(self):
        playsound('sound/drag.mp3', block=False)

    def play_clear(self):
        playsound('sound/clear.mp3', block=False)

    def play_reset(self):
        playsound('sound/reset.mp3', block=False)

    opposite_direction = {
        'left': 'right',
        'right': 'left',
        'up': 'down',
        'down': 'up',
    }
    def handle_user_input(self, cmd):
        if cmd == 'toggle_same':
            self.show_same_emoji = not self.show_same_emoji
        elif cmd in ('up', 'down', 'left', 'right'):
            if self.in_move_process:
                ### 移动关联块 ###
                if self.original_direction is None:
                    # 第一次移动，记录下移动方向
                    self.original_direction = cmd
                    self.original_block_positions = self.find_moving_block(cmd) #方向确定了, 更新该方向上连接的其他块
                    self.prev_block_positions = list(self.original_block_positions)
                else:
                    if self.original_direction != cmd and self.original_direction != self.opposite_direction[cmd]:
                        return # 移动方向不能改变, 只能继续前进或回退
                # 操作移动关联的块
                if self.prev_block_positions:
                    if cmd == 'left':
                        next_pos = (self.prev_block_positions[-1][0], self.prev_block_positions[-1][1] - 1) # 最后一块的左方
                    elif cmd == 'right':
                        next_pos = (self.prev_block_positions[-1][0], self.prev_block_positions[-1][1] + 1) # 最后一块的右方
                    elif cmd == 'up':
                        next_pos = (self.prev_block_positions[-1][0] - 1, self.prev_block_positions[-1][1]) # 最后一块的上方
                    elif cmd == 'down':
                        next_pos = (self.prev_block_positions[-1][0] + 1, self.prev_block_positions[-1][1]) # 最后一块的下方
                    self.move_blocks(next_pos)
            elif self.in_option_process:
                option_gem_pos = self.matching_pos_list[self.option_index]
                if cmd in ('left', 'down'):
                    self.gems[option_gem_pos[0]][option_gem_pos[1]].set_is_option(False) # 旧的
                    self.option_index =(self.option_index + len(self.matching_pos_list) - 1)%len(self.matching_pos_list)
                    option_gem_pos = self.matching_pos_list[self.option_index]
                    self.gems[option_gem_pos[0]][option_gem_pos[1]].set_is_option(True) # 新的
                elif cmd in ('right', 'up'):
                    self.gems[option_gem_pos[0]][option_gem_pos[1]].set_is_option(False) # 旧的
                    self.option_index =(self.option_index + 1)%len(self.matching_pos_list)
                    option_gem_pos = self.matching_pos_list[self.option_index]
                    self.gems[option_gem_pos[0]][option_gem_pos[1]].set_is_option(True) # 新的
            else:
                ### 只移动光标 ###
                if cmd == 'left':
                    self.cursor_move_left()
                elif cmd == 'right':
                    self.cursor_move_right()
                elif cmd == 'up':
                    self.cursor_move_up()
                elif cmd == 'down':
                    self.cursor_move_down()
        elif cmd == 'enter' and self.in_option_process:
            self.clear_gems(self.matching_pos_list[self.option_index], self.cursor_pos)
            self.in_option_process = False
            self.option_index = 0
            self.matching_pos_list = [] # 清空匹配块的位置
        elif cmd == 'move_start':
            self.in_move_process = True
            self.original_block_positions = self.find_moving_block(None) #方向还没确定,只能记录当前位置的块
        elif cmd == 'move_end':
            matching_pos_list = self.find_matching_positions()
            if not matching_pos_list:
                self.reset_blocks_to_original()
            else:
                if len(matching_pos_list) > 1:
                    self.in_option_process = True
                    self.option_index = 0
                    self.matching_pos_list = matching_pos_list
                    option_gem_pos = self.matching_pos_list[self.option_index]
                    self.gems[option_gem_pos[0]][option_gem_pos[1]].set_is_option(True)
                else:
                    self.clear_gems(*matching_pos_list, self.cursor_pos)
            # 重置标记
            self.in_move_process = False
            self.original_direction = None # 重置移动方向
            self.original_block_positions = [] # 清空移动块的位置
            self.prev_block_positions = [] # 清空上一次移动块的位置
        elif cmd == 'shuffle':
            self.shuffle_gems()
        elif cmd == 'quit':
            sys.exit()


class Game:
    def __init__(self):
        self.board = Board()
        self.messages = []
        self.need_help = True
        
    def output_title(self):
        return [f'{"="*22} 对对碰乐园 {"="*22}']

    def output_help(self):
        return [
            '====操作指南 ====',
            '获得此帮助: a',
            '移动光标: 方向键',
            '移动块: Shift + 方向键',
            '打乱: x',
            '标记相同物品: s',
            '确认选择多匹配之一: [回车]',
            '重绘界面: r',
            '退出游戏: q',
        ]

    def set_message(self, message):
        self.messages.append(message)
    
    def print_frame(self):
        frame_rows = self.output_title()
        frame_rows.extend(self.board.output_board())
        if self.need_help:
            frame_rows.extend(self.output_help())
            self.need_help = False
        if self.messages:
            frame_rows.extend(self.messages)
            self.messages.clear() # 一次性显示
        
        frame_printer.print_frame(frame_rows)

    def play(self):
        frame_printer.clear()
        self.print_frame()
        while True:
            cmd = self.board.get_user_input()
            if cmd == 'help':
                self.need_help = True
            if cmd == 'refresh':
                frame_printer.clear_cache()
                frame_printer.clear()
            else:
                self.board.handle_user_input(cmd)
            self.print_frame()

if __name__ == '__main__':
    try:
        background_sound = LoopPlayer()
        background_sound.start()
        game = Game()
        game.play()
    except Exception as ex:
        pass
    finally:
        background_sound.stop()
