from multiprocessing import current_process
from stages.color import Color
from importlib import import_module
import msvcrt
import ctypes
import time
import os
from playsound3 import playsound
import threading
from random import choice as rand_choice


class Dot:
    def __init__(self, is_end_point:bool=False, color:Color=Color.WHITE):
        self.is_end_point:bool = is_end_point
        self.color:Color = color
        self.is_selected:bool = False
        self.joints:list = [' '] * 6 # up, right * 2, down, left * 2
        self.is_connected:bool = False
    
    def set_joint(self, dir:str):
        if dir == 'up':
            self.joints[0] = '│'
        elif dir == 'right':
            self.joints[1] = '─'
            self.joints[2] = '─'
        elif dir == 'down':
            self.joints[3] = '│'
        elif dir == 'left':
            self.joints[4] = '─'
            self.joints[5] = '─'
    
    def clear_joint(self, dir:str):
        if dir == 'up':
            self.joints[0] = ' '
        elif dir == 'right':
            self.joints[1] = ' '
            self.joints[2] = ' '
        elif dir == 'down':
            self.joints[3] = ' '
        elif dir == 'left':
            self.joints[4] = ' '
            self.joints[5] = ' '
    
    def set_select(self, is_selected:bool):
        self.is_selected = is_selected
    
    def set_connect(self, is_connected:bool):
        self.is_connected = is_connected
    
    def set_color(self, color:Color=Color.WHITE):
        if not self.is_end_point:
            self.color = color
    
    def get_color(self) -> Color:
        return self.color
    
    def clear_joints(self):
        self.joints = [' '] * 6

    def render(self):
        # 3*3
        content = self.color + ('●' if self.is_end_point else '∙') + Color.RESET
        rows = [[' ', ' ', self.joints[0], ' ', ' '],
                [self.joints[5], self.joints[4], content, self.joints[1], self.joints[2]], # ∙ ● ⬤
                [' ', ' ', self.joints[3],' ', ' ']]
        if self.is_selected:
            rows[0][0] = Color.YELLOW + '╭' + Color.RESET
            rows[0][-1] = Color.YELLOW + '╮' + Color.RESET
            rows[-1][0] = Color.YELLOW + '╰' + Color.RESET
            rows[-1][-1] = Color.YELLOW + '╯' + Color.RESET
        if self.is_connected:
            for row_index in range(len(rows)):
                for col_index in range(len(rows[row_index])):
                    if rows[row_index][col_index] != ' ':
                        rows[row_index][col_index] = self.color + rows[row_index][col_index] + Color.RESET
        return rows


class Deck:
    def __init__(self, stage_id):
        self.array, self.height, self.width, self.end_point_positions = self._load_stage(stage_id)
        self.cursor_pos = (0,0)
        dot = self.get_dot(*self.cursor_pos)
        dot.set_select(True)
        self.links = {}
    
    def _load_stage(self, stage_id):
        end_point_positions = []
        stage = import_module(f'stages.{stage_id}', package=f'stages.{stage_id}')
        # rows, cols
        height, width = stage.size
        array = []
        for row_index, row in enumerate(stage.deck):
            row_of_dots = []
            for col_index, dot_color in enumerate(row):
                if dot_color is None:
                    row_of_dots.append(Dot())
                else:
                    row_of_dots.append(Dot(is_end_point=True, color=dot_color))
                    end_point_positions.append((row_index, col_index))
            array.append(row_of_dots)
        return array, height, width, end_point_positions
    
    def print_deck(self):
        for row in self.array:
            dots_in_row = []
            for dot in row:
                dots_in_row.append(dot.render())
            lines_in_row = []
            for i in range(3): # 每个dot占3行
                line = []
                for dot in dots_in_row:
                    line += dot[i] # 每行包含5个字符
                lines_in_row.append(line)
            for line in lines_in_row:
                print(''.join(line))

    def get_dot(self, row_index, col_index) -> Dot|None:
        if 0<=row_index<self.width and 0<=col_index<self.height:
            return self.array[row_index][col_index]
        else:
            return None
    
    def get_end_points(self) -> list[Dot]:
        return [self.get_dot(*end_point) for end_point in self.end_point_positions]

    def get_cursor(self) -> tuple[int,int]:
        return self.cursor_pos

    def get_dot_at_cursor(self) -> Dot|None:
        return self.get_dot(*self.cursor_pos)
    
    def move_cursor(self, row_index, col_index):
        new_dot = self.get_dot(row_index, col_index)
        if new_dot is None:
            # 新坐标越界
            return False
        old_dot = self.get_dot_at_cursor()
        old_dot.set_select(False)
        new_dot.set_select(True)
        self.cursor_pos = (row_index, col_index)
        return True
    
    def move_up(self):
        return self.move_cursor(self.cursor_pos[0] - 1, self.cursor_pos[1])
    
    def move_down(self):
        return self.move_cursor(self.cursor_pos[0] + 1, self.cursor_pos[1])
    
    def move_left(self):
        return self.move_cursor(self.cursor_pos[0], self.cursor_pos[1] - 1)
    
    def move_right(self):
        return self.move_cursor(self.cursor_pos[0], self.cursor_pos[1] + 1)

    def move_cursor_by_direction(self, direction):
        if direction == 'up':
            return self.move_up()
        elif direction == 'right':
            return self.move_right()
        elif direction == 'down':
            return self.move_down()
        elif direction == 'left':
            return self.move_left()
        else:
            return False
    
    def _relative_position(self, r1, c1, r2, c2) -> str|None:
        if r1 == r2:
            return 'left' if c1 > c2 else 'right'
        elif c1 == c2:
            return 'up' if r1 > r2 else 'down'
        else:
            return None
    
    def get_link(self, link_color) -> list[tuple[int,int]]:
        if link_color not in self.links:
            return []
        return self.links[link_color]
    
    def set_link(self, link_color, dot_positions):
        self.links[link_color] = dot_positions

        if self.get_dot(*dot_positions[0]).is_end_point and \
           self.get_dot(*dot_positions[-1]).is_end_point:
           connected = True
           playsound('sound/connect.wav', block=False)
        else:
            connected = False
        
        for i in range(len(dot_positions)):
            dot_prev = self.get_dot(*dot_positions[i])
            if i < len(dot_positions) - 1:
                dot_next = self.get_dot(*dot_positions[i+1])
            else:
                dot_next = None
            if dot_next:
                # calculate relative position between these two dots
                prev_joint_direction = self._relative_position(*dot_positions[i], *dot_positions[i+1])
                dot_prev.set_joint(prev_joint_direction)
                if connected:
                    dot_prev.set_connect(True)
                    dot_prev.set_color(link_color)
                else:
                    dot_prev.set_connect(False)
                next_joint_direction = self._relative_position(*dot_positions[i+1], *dot_positions[i])
                dot_next.set_joint(next_joint_direction)
                if connected:
                    dot_next.set_connect(True)
                    dot_next.set_color(link_color)
                else:
                    dot_next.set_connect(False)
    
    def restart(self):
        self.links = {}
        self.cursor_pos = (0, 0)
    
    def clear_link_segment(self, dot_pos_a, dot_pos_b, reset_color_a=True, reset_color_b=True):
        # calculate relative position between these two dots
        prev_joint_direction = self._relative_position(*dot_pos_a, *dot_pos_b)
        dot_a = self.get_dot(*dot_pos_a)
        dot_a.clear_joint(prev_joint_direction)
        dot_a.set_connect(False)
        if reset_color_a:
            dot_a.set_color()
        next_joint_direction = self._relative_position(*dot_pos_b, *dot_pos_a)
        dot_b = self.get_dot(*dot_pos_b)
        dot_b.clear_joint(next_joint_direction)
        dot_b.set_connect(False)
        if reset_color_b:
            dot_b.set_color()

    def clear_link(self, link_color):
        if link_color not in self.links:
            self.links[link_color] = []
            return
        dot_positions = self.links[link_color]
        for i in range(len(dot_positions) - 1, 0, -1):
            self.clear_link_segment(dot_positions[i-1], dot_positions[i])
        dot_positions.clear()


def move_console_cursor(row: int, column: int):
    """移动光标到指定位置"""
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


def get_user_input():
    accepted_keys_and_map = {
        b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right',
        b'q': 'quit',
        b'r': 'restart',
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
                    cmd += ' link'
                return cmd

        time.sleep(0.1)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


class LineGame:
    def __init__(self, stage_id):
        self.stage_id = '-'.join([str(int(seg)) for seg in stage_id.split('-')])
        self.deck = Deck(stage_id)
    
    def move_selector(self, direction):
        return self.deck.move_cursor_by_direction(direction)
    
    def print_title(self):
        print(f'====连线游戏(第{self.stage_id}关)====')
        print()
    
    def print_help(self):
        print('操作指南:')
        print('1. 方向键: 移动光标')
        print('2. Shift + 方向键: 连接两节点')
        print('3. H键: 显示操作帮助')
        print('4. R键: 重新开始游戏')
        print('5. Q键: 退出游戏')

    def print_deck(self):
        move_console_cursor(2, 0)
        self.deck.print_deck()
    
    def check_win(self):
        end_points = self.deck.get_end_points()
        for end_point in end_points:
            if not end_point.is_connected:
                return False
        playsound('sound/win.wav', block=False)
        return True

    def play(self):
        clear()
        self.print_title()
        self.print_deck()
        while True:
            instruction = get_user_input()
            cmd = instruction.split(' ')
            if cmd[0] == 'quit':
                return True
            elif cmd[0] == 'help':
                self.print_deck()
                self.print_help()
            elif cmd[0] == 'restart':
                self.deck = Deck(self.stage_id)
            elif cmd[0] in ('up', 'down', 'left', 'right'):
                pos_prev = self.deck.get_cursor()
                dot_prev = self.deck.get_dot_at_cursor()
                color = dot_prev.get_color()
                if color == Color.WHITE and len(cmd) > 1 and cmd[1] == 'link':
                    # 如果是连接操作, 起始点应该是有颜色的
                    playsound('sound/error.wav', block=True)
                    pass
                else:
                    link_of_color = self.deck.get_link(color)
                    if self.move_selector(cmd[0]):
                        can_connect = True
                        # 移动成功, 但能不能连接要再判断
                        if len(cmd) > 1 and cmd[1] == 'link':
                            if dot_prev.is_end_point:
                                # 清除旧的, 重新连线
                                self.deck.clear_link(color)
                            pos_now = self.deck.get_cursor()
                            dot_now = self.deck.get_dot_at_cursor()
                            if dot_now.is_end_point and dot_now.get_color() != color:
                                # 颜色不同, 不能移动, 回退
                                self.deck.move_cursor(*pos_prev)
                                can_connect = False
                            elif not dot_now.is_end_point:
                                # 颜色不同, 但能覆盖
                                color_now = dot_now.get_color()
                                if color_now in self.deck.links:
                                    color_segments = self.deck.links[color_now]
                                    if pos_now in color_segments:
                                        while color_segments[-1] != pos_now:
                                            self.deck.clear_link_segment(color_segments[-1], color_segments[-2])
                                            color_segments.pop()
                                        # 当前节点也要清除
                                        self.deck.clear_link_segment(color_segments[-1], color_segments[-2], reset_color_a=False, reset_color_b=False)
                                        color_segments.pop()
                            if can_connect:
                                dot_now.set_color(color)
                                if link_of_color == []:
                                    link_of_color.append(pos_prev)
                                if pos_prev in link_of_color:
                                    while link_of_color[-1] != pos_prev:
                                        self.deck.clear_link_segment(link_of_color[-1], link_of_color[-2], reset_color_b=False)
                                        link_of_color.pop()
                                # self.deck.get_dot(*link_of_color[-1]).set_color(color) # 补偿颜色
                                link_of_color.append(pos_now)
                                self.deck.set_link(color, link_of_color)
                        if can_connect:
                            playsound('sound/move.wav', block=False)
                    self.print_deck()
            if self.check_win():
                print(f'你赢了! 第{self.stage_id}关结束')
                break

class Menu:
    stage_index = 0
    stage_page = 0

    @staticmethod
    def print_title():
        print(f'====连线游戏====')
        print()
    
    @staticmethod
    def load_stages():
        #stage files module names
        return [f.split('.')[0] for f in os.listdir('stages') if '-' in f]

    @staticmethod
    def print_menu():
        choice = ''
        while choice not in ('1', '2', '3'):
            move_console_cursor(2, 0)
            print('1. 新游戏')
            print('2. 选择关卡')
            print('3. 退出游戏')
            print(' ' * 40)
            move_console_cursor(5, 0)
            choice = input('请输入你的选择: ').strip()
        return choice
    

    @staticmethod
    def print_stage_list(selected_index, stage_id_list):
        move_console_cursor(2, 0)
        for index, stage_id in enumerate(stage_id_list):
            if index == selected_index:
                print(Color.BG_DARK_WHITE + stage_id + Color.RESET + ' ' * 16)
            else:
                print(stage_id + ' ' * 16)
    
    @staticmethod
    def play_filtered_stages(stage_files):
        for stage_id in stage_files:
            game = LineGame(stage_id)
            is_quit = game.play()
            if is_quit:
                break
            next_stage = input('下一局? (y/n)').strip().lower()
            if not (next_stage == '' or next_stage[0] == 'y'):
                break


class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.file_name_and_track_length = []
        files = [f for f in os.listdir('./music') if f.endswith('.mp3')]
        for name in files:
            min, sec = name.split('.')[0].split('_')
            track_length = int(min) * 60 + int(sec)
            self.file_name_and_track_length.append((name, track_length))
        self.sound_handle = None
        self.is_stop = False
        
    def run(self):
        start_time = time.time()
        sound_file, track_length = rand_choice(self.file_name_and_track_length)
        self.sound_handle = playsound(f'./music/{sound_file}', block=False)
        while not self.is_stop:
            if time.time() - start_time >= track_length: # whole sound duration
                # play random sound
                self.sound_handle.stop()
                start_time = time.time()
                sound_file, track_length = rand_choice(self.file_name_and_track_length)
                self.sound_handle = playsound(f'./music/{sound_file}', block=False)
            time.sleep(1)
        self.sound_handle.stop()
    
    def stop(self):
        self.is_stop = True


if __name__ == '__main__':
    try:
        background_player = LoopPlayer()
        background_player.start()
        clear()
        Menu.print_title()
        choice = Menu.print_menu()
        stage_id_list = Menu.load_stages()
        if choice == '1':
            Menu.play_filtered_stages(stage_id_list)
        elif choice == '2':
            while True:
                current_page_list = stage_id_list[Menu.stage_page * 10:(Menu.stage_page + 1) * 10] # 每10关为一页, 避免列表过长
                total_pages = len(stage_id_list) // 10 + (1 if len(stage_id_list) % 10 != 0 else 0)
                Menu.print_stage_list(Menu.stage_index, current_page_list)
                print('请用光标选择开始的关卡(↔翻页,↕选关)')
                cmd = get_user_input()
                if cmd == 'enter':
                    filtered_stage_list = stage_id_list[Menu.stage_page * 10 + Menu.stage_index:]
                    break
                elif cmd == 'up':
                    Menu.stage_index = (Menu.stage_index - 1 + len(current_page_list)) % len(current_page_list)
                elif cmd == 'down':
                    Menu.stage_index = (Menu.stage_index + 1) % len(current_page_list)
                elif cmd == 'left':
                    Menu.stage_page = (Menu.stage_page - 1 + total_pages) % total_pages
                    Menu.stage_index = 0
                elif cmd == 'right':
                    Menu.stage_page = (Menu.stage_page + 1) % total_pages
                    Menu.stage_index = 0
                elif cmd == 'quit':
                    break
            Menu.play_filtered_stages(filtered_stage_list)
    except Exception as e:
        pass
    finally:
        background_player.stop()
        print('游戏结束,再见!')
