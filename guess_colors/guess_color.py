from dataclasses import dataclass
import random
import msvcrt
import os
import time
import sys
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

    RESET_FG = '\033[0m'

BEAD = ('▗▟█▙▖', '█████', '▝▜█▛▘')

BEAD_COLORS = (Color.BLUE_FG, Color.RED_FG, Color.GREEN_FG, Color.YELLOW_FG, Color.MAGENTA_FG, Color.DARK_WHITE_FG)
def color_preview():
    for color in dir(Color):
        if color.endswith('_FG'):
            print(color)
            color_value = getattr(Color, color)
            reset = getattr(Color, 'RESET_FG')
            print(color_value + '\n'.join(BEAD) + reset)
# color_preview()
def bead_preview():
    for color in BEAD_COLORS:
        print(color + '\n'.join(BEAD) + Color.RESET_FG)
# bead_preview()

class Game:
    def __init__(self, allow_same_color=False):
        self.allow_same_color = allow_same_color
        self.colors = self._generate_color_sequence()
        self.win = False
        self.game_over = False
        self.current_guess = [None, None, None, None] # unsettled guess, fixed 4 slots
        self.guesses = [] # submitted guesses, maximum 8 times
        self.guess_results = [] # compare results, maximum 8 times

        self.v_cursor_position = 0
        self.h_cursor_position = 0

        self.is_stop_sound = False
        self.bg_sound_thread = threading.Thread(target=self.play_background_sound)
        self.bg_sound_thread.start()
    
    def play_background_sound(self):
            # loop the sound
        sound_handle = playsound('sound/bg_sound.wav', block=False)
        start_time = time.time()
        while not self.is_stop_sound:
            if time.time() - start_time >= 22:
                # loop the sound
                sound_handle.stop()
                sound_handle = playsound('sound/bg_sound.wav', block=False)
                start_time = time.time()
            time.sleep(1)
        sound_handle.stop()
    
    def stop_sound(self):
        self.is_stop_sound = True
    
    def play_move_sound(self):
        playsound('sound/move_effect.wav', block=False)
    
    def play_plug_sound(self):
        playsound('sound/plug_effect.wav', block=False)
    
    def play_correct_effect(self, times=1):
        for _ in range(times):
            playsound('sound/correct_effect.wav', block=False)
            time.sleep(0.2)
    
    def play_win_sound(self):
        self.stop_sound()
        playsound('sound/win_sound.wav', block=False)
        self.play_background_sound()

    def _generate_color_sequence(self):
        color_list = []
        while len(color_list) < 4:
            color = random.choice(BEAD_COLORS)
            picked_color = random.choice(BEAD_COLORS)
            if not self.allow_same_color and picked_color in color_list:
                continue
            color_list.append(picked_color)
        return color_list
    
    def set_current_guess(self, position, color):
        self.current_guess[position] = color
        self.play_plug_sound()
    
    def get_current_guess(self):
        return self.current_guess
    
    def settle_guess(self):
        if None not in self.current_guess:
            self.guesses.append(self.current_guess.copy())
            result = self.compare(self.current_guess, self.colors)
            self.play_correct_effect(result[0] + result[1])
            self.guess_results.append(result)
            self.current_guess = [None, None, None, None]
            self.v_cursor_position = 0
            if result[0] == 4: # All slots color right & position right
                self.win = True
                self.play_win_sound()
                self.game_over = True
            elif len(self.guess_results) == 8: # All guess chance used, loss
                self.win = False
                self.game_over = True
    
    @staticmethod
    def compare(guess_list, answer_list):
        count_color_right_position_right = [0, 0, 0, 0]
        count_only_color_right = 0

        for i in range(4):
            if guess_list[i] == answer_list[i]:
                count_color_right_position_right[i] = 1
        
        remain_guess = [guess_list[c_idx] for c_idx in range(4) if count_color_right_position_right[c_idx] == 0]
        remain_color = [answer_list[c_idx] for c_idx in range(4) if count_color_right_position_right[c_idx] == 0]
        for guess in remain_guess.copy():
            if guess in remain_color:
                count_only_color_right += 1
                remain_guess.remove(guess)
                remain_color.remove(guess)

        return sum(count_color_right_position_right), count_only_color_right
    
    def move_down(self):
        self.v_cursor_position = (self.v_cursor_position + 1) % 4
        self.play_move_sound()
    
    def move_up(self):
        self.v_cursor_position = (self.v_cursor_position - 1) % 4
        self.play_move_sound()
    
    def move_left(self):
        self.h_cursor_position = (self.h_cursor_position - 1) % 6
        self.play_move_sound()
    
    def move_right(self):
        self.h_cursor_position = (self.h_cursor_position + 1) % 6
        self.play_move_sound()

    @staticmethod
    def print_title():
        # print title
        print(Color.BRIGHT_GREEN_FG + '='*35 + ' 猜颜色 ' + '='*36 + Color.RESET_FG)

    @staticmethod
    def print_control_tips():
        # print control tips
        print()
        print('游戏目标: 猜出颜色及排列顺序')
        print('控制提示: ')
        print('1. 上下左右键移动光标')
        print('2. 空格/Z键设置颜色')
        print('3. 回车键确认猜测')
        print('4. Q/ESC 退出游戏')

    def print_board(self):
        # print title
        self.print_title()

        # print header
        print(Color.BRIGHT_GREEN_FG + ''.join([f'{"-"*2}第{chr(120813+guess_round_index)}轮{"-"*2}{"+" if guess_round_index < 7 else ""}' for guess_round_index in range(8)]) + Color.RESET_FG + \
            ("" if not self.game_over else (Color.BRIGHT_BLUE_FG + "+--谜底--" + Color.RESET_FG)))
        
        # print compare results
        result_row = ''
        for guess_round_index, guess_result in enumerate(self.guess_results):
            count_color_right_position_right, count_only_color_right = guess_result
            result_row += '  ' + Color.BRIGHT_RED_FG + '☻'* count_color_right_position_right + \
                                Color.DARK_WHITE_FG + '☻'* count_only_color_right + \
                                '_'*(4 - count_color_right_position_right - count_only_color_right) + \
                                Color.BRIGHT_GREEN_FG + '   +' + Color.RESET_FG
        print(result_row)

        # each bead for each guess round
        for bead_index in range(4):
            ## print open quote lane row
            quote_lane_row = (' '*9 + Color.BRIGHT_GREEN_FG + '+' + Color.RESET_FG) * len(self.guesses) + (' '*2 + ('╔════╗' if bead_index == self.v_cursor_position else '      ') + ' '*2)
            print(quote_lane_row)

            ## collect bead colors
            bead_colors = []
            for guess_round_index in range(8):
                if guess_round_index < len(self.guesses):
                    bead_colors.append(self.guesses[guess_round_index][bead_index])
                else:
                    if guess_round_index == len(self.guesses):
                        # it could be color choosen in current_guess
                        bead_colors.append(self.current_guess[bead_index])
                    else:
                        bead_colors.append(None)
            if self.game_over:
                bead_colors.append(self.colors[bead_index])
            
            ## print beads
            for row in BEAD:
                row_content = ''
                for col_idx, color in enumerate(bead_colors):
                    if color is None:
                        row_content += ' '* 10
                    else:
                        row_content += f'{" "*2}{color + row + Color.RESET_FG}{" "*2}{Color.BRIGHT_GREEN_FG + "+" + Color.RESET_FG if col_idx < len(bead_colors) - 1 else ""}'
                print(row_content)
            
            ## print close quote lane row
            quote_lane_row = (' '*9 + Color.BRIGHT_GREEN_FG + '+' + Color.RESET_FG) * len(self.guesses) + (' '*2 + ('╚════╝' if bead_index == self.v_cursor_position else '      ') + ' '*2)
            print(quote_lane_row)

        bead_open_quote = ['╔', '║', '╚']
        bead_close_quote = ['╗', '║', '╝']
        print(Color.BRIGHT_GREEN_FG + '='*34 + ' 可选颜色 ' + '='*35 + Color.RESET_FG)
        for row_idx, row in enumerate(BEAD):
            concated_row = ' '* 8
            for col_idx, color in enumerate(BEAD_COLORS):
                concated_row += f'{" " + (bead_open_quote[row_idx]  if col_idx == self.h_cursor_position else " ")}{" " + color + row + Color.RESET_FG}{" " + (bead_close_quote[row_idx] if col_idx == self.h_cursor_position else " ") +" "}'
            print(concated_row)
            
        # print control tips
        self.print_control_tips()


def clear():
    os.system('cls')

# 检测操作系统
IS_WINDOWS = os.name == 'nt'

def move_cursor(row: int, column: int):
        """移动光标到指定位置"""
        if IS_WINDOWS:
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

def dialog_to_set_same_color():
    allow_same_color = False
    move_cursor(2, 0)
    print("设置是否可重复颜色([回车]确定选择, ESC退出游戏): " + ("\033[104m" if allow_same_color else "") + "是" + Color.RESET_FG + "  " + ("\033[104m" if not allow_same_color else "") + "否" + Color.RESET_FG)
    while True:
        updated = False
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\r':
                break # confirm setting
            elif key == b'\xe0':
                key = msvcrt.getch()
                if key == b'K' and not allow_same_color:
                    allow_same_color = True
                    updated = True
                elif key == b'M' and allow_same_color:
                    allow_same_color = False
                    updated = True
                if updated:
                    move_cursor(2, 0)
                    print("设置是否可重复颜色([回车]确定选择, ESC退出游戏): " + ("\033[104m" if allow_same_color else "") + "是" + Color.RESET_FG + "  " + ("\033[104m" if not allow_same_color else "") + "否" + Color.RESET_FG)
            elif key == b'\x1b':
                sys.exit(0)
        time.sleep(0.1)    
    return allow_same_color

def main_loop():
    clear()
    Game.print_title()
    allow_same_color = dialog_to_set_same_color()
    
    # start game
    clear()
    game = Game(allow_same_color)
    game.print_board()
    
    while True:
        # Get user input and process
        key = None
        while key is None:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\xe0', b'\x00'):
                    # arrow keys
                    key = msvcrt.getch()
                    if key == b'H':
                        game.move_up()
                    elif key == b'P':
                        game.move_down()
                    elif key == b'K':
                        game.move_left()
                    elif key == b'M':
                        game.move_right()
                elif key == b' ' or key == b'z':
                    game.set_current_guess(game.v_cursor_position, BEAD_COLORS[game.h_cursor_position])
                    game.move_down()
                elif key == b'\r':
                    # confirm guess
                    game.settle_guess()
                    if game.game_over:
                        break
                elif key in (b'Q', b'q', b'\x1b'):
                    game.stop_sound()
                    sys.exit(0)
                else:
                    key = None
            time.sleep(0.1)
        
        # Update board
        clear()
        game.print_board()

        if game.game_over:
            print(Color.BRIGHT_BLUE_FG)
            print(f"本局游戏结束: {'你赢了!' if game.win else '你输了!'}")
            print("再来一局吗? Y/ENTER同意,其他键退出")
            print(Color.RESET_FG, end="")
            if msvcrt.getch() in (b'y', b'Y', b'\r'):
                # new round
                clear()
                game.stop_sound()
                game = Game(allow_same_color)
                game.print_board()
            else:
                game.stop_sound()
                print("游戏结束。")
                break


if __name__ == '__main__':
    main_loop()
