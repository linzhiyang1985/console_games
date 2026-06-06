from dataclasses import dataclass
import re
import os
import subprocess
import msvcrt
import time
import threading
import random
import sys
from playsound3 import playsound


@dataclass
class Color:
    RESET_FG = '\033[0m'

    BLACK_FG = '\033[30m'
    DARK_RED_FG = '\033[31m'
    DARK_GREEN_FG = '\033[32m'
    DARK_YELLOW_FG = '\033[33m'
    DARK_BLUE_FG = '\033[34m'
    DARK_MAGENTA_FG = '\033[35m'
    DARK_CYAN_FG = '\033[36m'
    DARK_WHITE_FG = '\033[37m'

    BRIGHT_BLACK_FG = '\033[90m'
    BRIGHT_RED_FG = '\033[91m'
    BRIGHT_GREEN_FG = '\033[92m'
    BRIGHT_YELLOW_FG = '\033[93m'
    BRIGHT_BLUE_FG = '\033[94m'
    BRIGHT_MAGENTA_FG = '\033[95m'
    BRIGHT_CYAN_FG = '\033[96m'
    WHITE_FG = '\033[97m'


class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.sound_file_path = 'sound/background.mp3'
        self.track_length = 31
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

frame_printer = ScreenFramePrinter()


class Bottle:
    def __init__(self, drops:list[Color]):
        self.drops = drops # 从下到上
        self.is_focused = False
        self.is_selected = False
        self.is_sealed = False
    
    def __repr__(self):
        return repr(self.drops)

    def set_focus(self, focused:bool=True):
        self.is_focused = focused

    def set_selected(self, selected:bool=True):
        self.is_selected = selected

    def set_sealed(self, sealed:bool=True):
        self.is_sealed = sealed
    
    @property
    def is_full(self):
        return all(drop is not None for drop in self.drops)
    
    @property
    def is_empty(self):
        return all(drop is None for drop in self.drops)

    def output_bottle(self):
        bottle_cover = [
            " ╭─────╮ ",
            "╭╯     ╰╮",
        ]
        bottle_water = "░░░░░░░"
        bottle_empty = "       "
        bottle_bottom = "╰───────╯"
        
        rows = bottle_cover[:]
        if self.is_sealed:
            rows[1] = f"╭╯{Color.BRIGHT_BLACK_FG+'█'*5+Color.RESET_FG}╰╮"
        for drop in reversed(self.drops):
            if drop:
                rows.append(f'│{drop + bottle_water + Color.RESET_FG}│')
            else:
                rows.append(f'│{bottle_empty}│')
        rows.append(bottle_bottom)

        if self.is_selected:
            border_color = Color.DARK_MAGENTA_FG
        elif self.is_focused:
            border_color = Color.DARK_YELLOW_FG
        else:
            border_color = None
        
        if border_color:
            new_rows = []
            for r in rows:
                new_rows.append(''.join([border_color + c + Color.RESET_FG if c in ('│', '╰', '─', '╯', '╭', '╮') else c for c in r]))
            rows = new_rows
        
        return rows

class PourWater:
    BOTTLES_PER_ROW = 4

    def __init__(self, level):
        self.bottle_deck:list[Bottle] = []
        self.bottle_count = 3 + level
        self.init_bottles(self.bottle_count) # 最少三个瓶子
        self.BOTTLES_PER_ROW = max(4, (self.bottle_count + 2)//5)
        self.cursor_index = 0
        self.pour_from_index = -1
        self.pour_to_index = -1
        self.need_help = False
        
    def add_bottle(self, bottle:Bottle):
        self.bottle_deck.append(bottle)
    
    def add_empty_bottle(self):
        self.bottle_deck.append(Bottle([None, None, None, None]))
    
    def init_bottles(self, num_bottles:int):
        for i in range(num_bottles):
            self.add_empty_bottle()
        colors = random.choices([Color.BRIGHT_RED_FG, Color.BRIGHT_GREEN_FG, Color.BRIGHT_YELLOW_FG, Color.BRIGHT_BLUE_FG, Color.BRIGHT_MAGENTA_FG, Color.BRIGHT_CYAN_FG, Color.WHITE_FG], k=num_bottles)
        for c in colors:
            for piece in range(4):
                while True:
                    bottle_index = random.randint(0, num_bottles-1)
                    if not self.bottle_deck[bottle_index].is_full:
                        self.bottle_deck[bottle_index].drops[self.bottle_deck[bottle_index].drops.index(None)] = c
                        break

        self.add_empty_bottle()
        self.add_empty_bottle()

        self.bottle_deck[0].set_focus(True)

    def output(self):
        output_rows = [f' ======= Pour Water ({self.bottle_count} bottles) ======']
        bottle_rows = []
        for b in self.bottle_deck:
            bottle_rows.append(b.output_bottle())
        while bottle_rows:
            in_one_array = bottle_rows[:self.BOTTLES_PER_ROW]
            # concat bottles
            for row_index in range(7):
                output_rows.append(' '.join([bottle[row_index] for bottle in in_one_array]))
            output_rows.append('')

            bottle_rows = bottle_rows[self.BOTTLES_PER_ROW:]
        return output_rows

    def pour(self, bottle_from_index:int, bottle_to_index:int):
        bottle_from = self.bottle_deck[bottle_from_index]
        bottle_to = self.bottle_deck[bottle_to_index]
        if bottle_from.is_sealed or bottle_to.is_sealed:
            return False
        if bottle_from.is_empty:
            return False
        if bottle_to.is_full:
            return False
        
        to_color = None #空水杯可接收任意颜色
        for to_index in range(3, -1, -1):
            if bottle_to.drops[to_index] is not None:
                to_color = bottle_to.drops[to_index] #非空水杯只能接收与顶部相同颜色的水
                break
        if to_color is None:
            to_index = -1

        poured = False
        while (not bottle_to.is_full) and (not bottle_from.is_empty):
            for from_index in range(3, -1, -1):
                if bottle_from.drops[from_index] is None:
                    continue
                else:
                    # 顶部水滴
                    if to_color is not None and bottle_from.drops[from_index] != to_color:
                        return poured # 颜色不匹配, 不能倒
                    if to_color is None or to_color == bottle_from.drops[from_index]:
                        drop_color = bottle_from.drops[from_index]
                        to_index += 1
                        bottle_to.drops[to_index] = drop_color
                        bottle_from.drops[from_index] = None
                        to_color = drop_color
                        if not poured:
                            self.play_pour()
                            poured = True
                        self.print_frame()
                        time.sleep(0.1)
                    break
        return poured
    
    def check_seal(self, bottle_index:int):
        bottle = self.bottle_deck[bottle_index]
        if bottle.is_full:
            if len(set(bottle.drops)) == 1:
                bottle.set_sealed(True)
                time.sleep(0.2)
                self.play_seal()
                return True
        return False
        

    def check_win(self):
        for b in self.bottle_deck:
            if b.is_sealed or b.is_empty:
                continue
            else:
                return False
        return True
    
    def cursor_move_prev(self):
        old_index = self.cursor_index
        if self.cursor_index > 0:
            self.cursor_index -= 1
        else:
            self.cursor_index = len(self.bottle_deck) - 1
        self.bottle_deck[old_index].set_focus(False)
        self.bottle_deck[self.cursor_index].set_focus(True)
    
    def cursor_move_next(self):
        old_index = self.cursor_index
        if self.cursor_index < len(self.bottle_deck) - 1:
            self.cursor_index += 1
        else:
            self.cursor_index = 0
        self.bottle_deck[old_index].set_focus(False)
        self.bottle_deck[self.cursor_index].set_focus(True)
    
    def cursor_move_next_array(self):
        old_index = self.cursor_index
        # new_index = (self.cursor_index + self.BOTTLES_PER_ROW)//self.BOTTLES_PER_ROW * self.BOTTLES_PER_ROW
        new_index = self.cursor_index + self.BOTTLES_PER_ROW
        if new_index >= len(self.bottle_deck):
            new_index = len(self.bottle_deck) - 1
        self.cursor_index = new_index

        self.bottle_deck[old_index].set_focus(False)
        self.bottle_deck[self.cursor_index].set_focus(True)
    
    def cursor_move_prev_array(self):
        old_index = self.cursor_index
        new_index = self.cursor_index - self.BOTTLES_PER_ROW
        if new_index < 0:
            new_index = min(len(self.bottle_deck) - 1, len(self.bottle_deck) // self.BOTTLES_PER_ROW * self.BOTTLES_PER_ROW + (new_index + self.BOTTLES_PER_ROW))
        self.cursor_index = new_index

        self.bottle_deck[old_index].set_focus(False)
        self.bottle_deck[self.cursor_index].set_focus(True)

    def play_select(self):
        playsound('sound/select.mp3', False)

    def play_pour(self, block=False):
        playsound('sound/pour.mp3', block=block)
    
    def play_seal(self):
        playsound('sound/seal.mp3', False)

    def play_win(self):
        playsound('sound/win.mp3', False)

    def get_user_input(self):
        accepted_keys_and_map = {
            b'H': 'prev_array', b'P': 'next_array',
            b'K': 'prev', b'M': 'next',
            b'q': 'quit', b'Q': 'quit',
            b'r': 'refresh', b'R': 'refresh',
            b'a': 'help', b'A': 'help',
            b'n': 'new_bottle', b'N': 'new_bottle',
            b'\r': 'enter', b'd': 'enter', b'D': 'enter',
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

    def handle_input(self, cmd:str):
        if cmd == 'quit':
            exit(0)
        elif cmd == 'help':
            self.need_help = True
        elif cmd == 'refresh':
            frame_printer.clear_cache()
            frame_printer.clear()
        elif cmd == 'prev':
            self.cursor_move_prev()
        elif cmd == 'next':
            self.cursor_move_next()
        elif cmd == 'prev_array':
            self.cursor_move_prev_array()
        elif cmd == 'next_array':
            self.cursor_move_next_array()
        elif cmd == 'new_bottle':
            self.add_empty_bottle()
            frame_printer.clear_cache()
        elif cmd == 'enter':
            if self.pour_from_index == -1:
                self.pour_from_index = self.cursor_index
                self.bottle_deck[self.pour_from_index].set_selected(True)
                self.play_select()
            else:
                self.pour_to_index = self.cursor_index
                if self.pour_from_index != self.pour_to_index:
                    poured = self.pour(self.pour_from_index, self.pour_to_index)
                    if poured:
                        self.check_seal(self.pour_to_index)
                self.bottle_deck[self.pour_from_index].set_selected(False)
                self.pour_from_index = -1
                self.pour_to_index = -1
    
    def print_frame(self, messages=[]):
        rows = self.output()
        if self.need_help:
            rows.append('A: Help, arrow: Move, N: New Bottle, D/Enter: Pour, R: Refresh')
            self.need_help = False
        rows.extend(messages)
        frame_printer.print_frame(rows)

    def play(self):
        frame_printer.clear()
        self.print_frame()

        while True:
            cmd = self.get_user_input()
            self.handle_input(cmd)
            
            is_win = self.check_win()
            if is_win:
                self.play_win()
                messages = ['Win!', 'Press Enter to continue...']
            else:
                messages = []
            
            self.print_frame(messages)
            if is_win:
                break

if __name__ == '__main__':
    try:
        start_level = int(sys.argv[1])
    except:
        start_level = 0
    try:
        background_sound = LoopPlayer()
        background_sound.start()

        for level in range(start_level,98):
            # for _ in range(3):
                # 每个level玩3局
                frame_printer.clear_cache()
                pw = PourWater(level)
                pw.play()
                input()
    except:
        pass
    finally:
        background_sound.stop()
