from enum import Enum, auto
from dataclasses import dataclass
from random import choice
import keyboard
import subprocess
import os
import sys
import time
import threading
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

    BRIGHT_BLACK_FG = '\033[90m'
    BRIGHT_RED_FG = '\033[91m'
    BRIGHT_GREEN_FG = '\033[92m'
    BRIGHT_YELLOW_FG = '\033[93m'
    BRIGHT_BLUE_FG = '\033[94m'
    BRIGHT_MAGENTA_FG = '\033[95m'
    BRIGHT_CYAN_FG = '\033[96m'
    WHITE_FG = '\033[97m'

    YELLOW_BG = '\033[103m'

    RESET_FG = '\033[0m'

class BugHeadColor(Enum):
    RED = Color.RED_FG
    GREEN = Color.GREEN_FG
    BLUE = Color.BLUE_FG
    YELLOW = Color.YELLOW_FG
    MAGENTA = Color.MAGENTA_FG
    CYAN = Color.CYAN_FG
    # WHITE = Color.DARK_WHITE_FG

class BugBodyColor(Enum):
    # RED = Color.BRIGHT_RED_FG
    # GREEN = Color.BRIGHT_GREEN_FG
    # BLUE = Color.BRIGHT_BLUE_FG
    # MAGENTA = Color.BRIGHT_MAGENTA_FG
    # CYAN = Color.BRIGHT_CYAN_FG
    # WHITE = Color.WHITE_FG
    RED = Color.RED_FG
    GREEN = Color.GREEN_FG
    BLUE = Color.BLUE_FG
    YELLOW = Color.YELLOW_FG
    MAGENTA = Color.MAGENTA_FG
    CYAN = Color.CYAN_FG
    # WHITE = Color.DARK_WHITE_FG

class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.sound_file_path = 'sound/background.mp3'
        self.track_length = 63
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

class Bug:
    HEAD = '●'   #✕◆■█◆⊙𑗕+●⦿
    BODY = '○'   #□⊙-o
    def __init__(self, color: str, size: int, head_position: tuple[int, int], direction: Direction):
        self.color_name = color
        self.size = size
        self.head_position = head_position
        self.direction = direction
        self.is_selected = False

    @property
    def head_color(self) -> str:
        color = getattr(BugHeadColor, self.color_name).value
        if self.is_selected:
            return color.replace('[', '[107;') # yellow bg
        return color
    
    @property
    def body_color(self) -> str:
        color = getattr(BugBodyColor, self.color_name).value
        if self.is_selected:
            return color.replace('[', '[107;') # yellow bg
        return color

    def set_selected(self, is_selected: bool):
        self.is_selected = is_selected

    def __repr__(self):
        bug_array = [[self.head_color+ self.HEAD + Color.RESET_FG,]]
        for _ in range(self.size - 1):
            if self.direction == Direction.UP:
                bug_array.append([self.body_color + self.BODY + Color.RESET_FG])
            elif self.direction == Direction.DOWN:
                bug_array.insert(0, [self.body_color + self.BODY + Color.RESET_FG])
            elif self.direction == Direction.LEFT:
                bug_array[0].append(self.body_color + self.BODY + Color.RESET_FG)
            elif self.direction == Direction.RIGHT:
                bug_array[0].insert(0, self.body_color + self.BODY + Color.RESET_FG)
        return '\n'.join([''.join(row) for row in bug_array])
    
    def get_positions(self):
        if self.size == 0:
            return []
        
        positions = [self.head_position]
        if self.direction == Direction.UP:
            for i in range(1, self.size):
                positions.append((self.head_position[0] + i, self.head_position[1]))
        elif self.direction == Direction.DOWN:
            for i in range(1, self.size):
                positions.append((self.head_position[0] - i, self.head_position[1]))
        elif self.direction == Direction.LEFT:
            for i in range(1, self.size):
                positions.append((self.head_position[0], self.head_position[1] + i))
        elif self.direction == Direction.RIGHT:
            for i in range(1, self.size):
                positions.append((self.head_position[0], self.head_position[1] - i))
        return positions

class Board:
    def __init__(self, count: int):
        self.count = count # bug count
        self.board = [[0] * 5 for _ in range(5)]
        self.bugs = []
        self.head_position_and_direction = {}
        self.selected_bug_index = 0
        self.init_board()
    
    def __repr__(self) -> str:
        return '\n'.join([''.join([str(cell) for cell in row]) for row in self.board])

    def expand_board(self):
        board_size = len(self.board)
        for row in self.board:
            row.insert(0, 0)
            row.append(0)
        self.board.insert(0, [0] * (board_size + 2))
        self.board.append([0] * (board_size + 2))

        self.head_position_and_direction.clear()

        for bug in self.bugs:
            r, c = bug.head_position
            bug.head_position = (r + 1, c + 1)
            self.head_position_and_direction[bug.head_position] = bug.direction

    def check_conflict(self, head_position, direction):
        if direction == Direction.UP:
            r, c = head_position
            for check_r in range(r - 1, -1, -1):
                if self.board[check_r][c] == 2 and self.head_position_and_direction[(check_r, c)] == Direction.DOWN:  # another head
                    return True # conflict found
        elif direction == Direction.DOWN:
            r, c = head_position
            for check_r in range(r + 1, len(self.board)):
                if self.board[check_r][c] == 2 and self.head_position_and_direction[(check_r, c)] == Direction.UP:  # another head
                    return True # conflict found
        elif direction == Direction.LEFT:
            r, c = head_position
            for check_c in range(c - 1, -1, -1):
                if self.board[r][check_c] == 2 and self.head_position_and_direction[(r, check_c)] == Direction.RIGHT:  # another head
                    return True # conflict found
        elif direction == Direction.RIGHT:
            r, c = head_position
            for check_c in range(c + 1, len(self.board[0])):
                if self.board[r][check_c] == 2 and self.head_position_and_direction[(r, check_c)] == Direction.LEFT:  # another head
                    return True # conflict found
        return False # no conflict found    

    def init_board(self):
        count_remain = self.count
        while count_remain > 0:
            direction = choice(list(Direction))
            size = choice((3, 4))
            position = self.find_empty_area(direction, size)
            color = choice(('RED', 'GREEN', 'BLUE', 'YELLOW', 'MAGENTA', 'CYAN'))
            if position is not None:
                bug = Bug(color, size, position, direction)
                self.bugs.append(bug)
                self.head_position_and_direction[position] = direction
                positions = bug.get_positions()
                self.board[positions[0][0]][positions[0][1]] = 2
                for r, c in positions[1:]:
                    self.board[r][c] = 1
                count_remain -= 1
            else:
                # expand board size
                self.expand_board()
        self.bugs.sort(key=lambda x: x.head_position)
        self.bugs[0].set_selected(True)
        return self.board
    
    def find_empty_area(self, direction, size):
        board_size = len(self.board)
        if direction == Direction.UP or direction == Direction.DOWN:
            for col_index in range(len(self.board[0])):
                for row_index in range(len(self.board)):
                    if self.board[row_index][col_index] == 0 and row_index + size <= board_size:
                        if all([self.board[row_index + i][col_index] == 0 for i in range(1, size)]) and not self.check_conflict((row_index, col_index), direction):
                            if direction == Direction.UP:
                                return (row_index, col_index)
                            else:
                                return (row_index + size - 1, col_index)
        elif direction == Direction.LEFT or direction == Direction.RIGHT:
            for row_index in range(len(self.board)):
                for col_index in range(len(self.board[0])):
                    if self.board[row_index][col_index] == 0 and col_index + size <= board_size:
                        if all([self.board[row_index][col_index + i] == 0 for i in range(1, size)]) and not self.check_conflict((row_index, col_index), direction):
                            if direction == Direction.LEFT:
                                return (row_index, col_index)
                            else:
                                return (row_index, col_index + size - 1)
        return None

    def render(self):
        rendered_array = [['.'] * len(self.board[0]) for row in self.board]
        for bug in self.bugs:
            positions = bug.get_positions()
            for index, (r, c) in enumerate(positions):
                if index == 0:
                    rendered_array[r][c] = bug.head_color + bug.HEAD + Color.RESET_FG
                else:
                    rendered_array[r][c] = bug.body_color + bug.BODY + Color.RESET_FG
        return rendered_array
    
    def select_next_bug(self):
        if self.bugs:
            if self.selected_bug_index < len(self.bugs):
                self.bugs[self.selected_bug_index].set_selected(False)
            self.selected_bug_index = (self.selected_bug_index + 1) % len(self.bugs)
            self.bugs[self.selected_bug_index].set_selected(True)
    
    def select_prev_bug(self):
        if self.bugs:
            if self.selected_bug_index < len(self.bugs):
                self.bugs[self.selected_bug_index].set_selected(False)
            self.selected_bug_index = (self.selected_bug_index - 1 + len(self.bugs)) % len(self.bugs)
            self.bugs[self.selected_bug_index].set_selected(True)

    def move_bug(self):
        bug = self.bugs[self.selected_bug_index]
        head_r, head_c = bug.head_position
        board_size = len(self.board)
        original_positions = bug.get_positions()
        if bug.direction == Direction.UP:
            if head_r > 0 and self.board[head_r - 1][head_c] == 0:
                bug.head_position = (head_r - 1, head_c)
            elif head_r == 0:
                bug.size -=1
        elif bug.direction == Direction.DOWN:
            if head_r < board_size - 1 and self.board[head_r + 1][head_c] == 0:
                bug.head_position = (head_r + 1, head_c)
            elif head_r == board_size - 1:
                bug.size -=1
        elif bug.direction == Direction.LEFT:
            if head_c > 0 and self.board[head_r][head_c - 1] == 0:
                bug.head_position = (head_r, head_c - 1)
            elif head_c == 0:
                bug.size -=1
        elif bug.direction == Direction.RIGHT:
            if head_c < board_size - 1 and self.board[head_r][head_c + 1] == 0:
                bug.head_position = (head_r, head_c + 1)
            elif head_c == board_size - 1:
                bug.size -=1
        
        if bug.size == 0:
            self.bugs.remove(bug)
            self.select_next_bug()
        
        new_positions = bug.get_positions()
        if new_positions == original_positions:
            return False
        else:
            # update board
            for index, (r, c) in enumerate(new_positions):
                if index == 0:
                    self.board[r][c] = 2
                else:
                    self.board[r][c] = 1
            for pos in original_positions:
                if pos not in new_positions:
                    self.board[pos[0]][pos[1]] = 0
            return True


class Game:
    def __init__(self, count: int):
        self.count = count # bug count
        self.board = Board(count)
    
    @staticmethod
    def clear():
        subprocess.run('cls' if (os.name == 'nt') else 'clear', shell=True)

    def get_user_input(self):
        accepted_keys_and_map = {
            'left': 'prev_bug',
            'right': 'next_bug',
            'up': 'prev_bug',
            'down': 'next_bug',
            'q': 'quit',
            'space': 'go',
            'esc': 'quit',
            'enter': 'next_level',
        }
        while True:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN and event.name in accepted_keys_and_map:
                return accepted_keys_and_map[event.name]
    
    def output_title(self):
        return f'=== Unleash Bugs - {self.count} Bugs ==='
    
    def select_next_bug(self):
        self.board.select_next_bug()

    def select_prev_bug(self):
        self.board.select_prev_bug()

    def play_move(self):
        return playsound('sound/move.mp3', block=False)
    
    def play_blocked(self):
        return playsound('sound/blocked.mp3', block=False)

    def move_bug(self):
        return self.board.move_bug()

    def refresh_screen(self):
        self.clear()
        print(self.output_title())
        
        render_arr = self.board.render()
        for row in render_arr:
            for cell in row:
                print(cell, end='')
            print()
        
        ## DEBUG ##
        # for row in self.board.board:
        #     print(row)

    def play(self):
        self.refresh_screen()

        while True:
            command = self.get_user_input()
            if command == 'quit':
                print('Thanks for playing, good bye!')
                sys.exit()
            elif command == 'go':
                sound = self.play_move()
                original_bug_count = len(self.board.bugs)
                result = self.move_bug()
                while result == True:
                    time.sleep(0.15)
                    self.refresh_screen()
                    bug_count = len(self.board.bugs)
                    if original_bug_count > bug_count:
                        break
                    result = self.move_bug()
                sound.stop()

                if original_bug_count == len(self.board.bugs):
                    self.play_blocked()
                
                if len(self.board.bugs) == 0:
                    self.refresh_screen()
                    print('You win!')
                    print('Press <Enter> to continue...<Esc>/<Q> to quit')
                    choice = self.get_user_input()
                    if choice == 'next_level':
                        break
                    elif choice == 'quit':
                        print('Thanks for playing, good bye!')
                        sys.exit()
            elif command == 'prev_bug':
                self.select_prev_bug()
            elif command == 'next_bug':
                self.select_next_bug()
            else:
                continue
            self.refresh_screen()

if __name__ == '__main__':
    try:
        background_sound = LoopPlayer()
        background_sound.start()
        for i in range(4, 600):
            game = Game(i)
            game.refresh_screen()
            game.play()
    except Exception as ex:
        print(ex)
    finally:
        background_sound.stop()
