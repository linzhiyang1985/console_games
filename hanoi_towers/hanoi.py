import os
import time
import msvcrt
import shutil
from playsound3 import playsound

IS_WINDOWS = os.name == 'nt'

class Hanoi:
    COLORS = (
        '\033[0m', #RESET_FG
        '\033[90m', #BRIGHT_BLACK_FG
        '\033[91m', #BRIGHT_RED_FG
        '\033[92m', #BRIGHT_GREEN_FG
        '\033[93m', #BRIGHT_YELLOW_FG
        '\033[94m', #BRIGHT_BLUE_FG
        '\033[95m', #BRIGHT_MAGENTA_FG
        '\033[96m', #BRIGHT_CYAN_FG
        '\033[97m', #WHITE_FG
        '\033[31m', #DARK_RED_FG
        '\033[32m', #DARK_GREEN_FG
        '\033[33m', #DARK_YELLOW_FG
        '\033[34m', #DARK_BLUE_FG
        '\033[35m', #DARK_MAGENTA_FG
        '\033[36m', #DARK_CYAN_FG
        '\033[37m', #DARK_WHITE_FG
    )
    def __init__(self, n):
        self.n = n
        self.pegs = [[], [], []]
        self.history = []
        self.current_step = -1
        for i in range(n, 0, -1):
            self.pegs[0].append(i)
        self.prohibit_sound = False
    
    def move_cursor(self, row: int, column: int):
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
    
    def play_disk(self, disk):
        if self.prohibit_sound:
            return
        sound_files = ('DO_1.mp3', 'RE_2.mp3','MI_3.mp3','FA_4.mp3','SO_5.mp3','LA_6.mp3','XI_7.mp3','do_8.mp3')
        playsound('./sound/' + sound_files[(disk-1)%len(sound_files)], False)

    def move(self, from_peg, to_peg):
        if not self.pegs[from_peg]:
            return False
        if self.pegs[to_peg] and self.pegs[to_peg][-1] < self.pegs[from_peg][-1]:
            return False
        disk = self.pegs[from_peg].pop()
        self.pegs[to_peg].append(disk)
        self.play_disk(disk)
        return True

    def solve(self):
        self.history = []
        self.current_step = -1
        self._solve_recursive(self.n, 0, 2, 1)
        return self.history

    def _solve_recursive(self, n, from_peg, to_peg, aux_peg):
        if n == 1:
            self.history.append((from_peg, to_peg))
            return
        self._solve_recursive(n - 1, from_peg, aux_peg, to_peg)
        self.history.append((from_peg, to_peg))
        self._solve_recursive(n - 1, aux_peg, to_peg, from_peg)

    def execute_step(self, step_idx=None):
        if step_idx is None:
            if self.current_step < len(self.history) - 1:
                self.current_step += 1
            else:
                return False
        else:
            if step_idx < 0 or step_idx >= len(self.history):
                return False
            self.current_step = step_idx
        from_peg, to_peg = self.history[self.current_step]
        self.move(from_peg, to_peg)
        return True

    def goback(self, steps=1):
        if self.current_step < 0:
            return False
        for _ in range(steps):
            if self.current_step < 0:
                break
            to_peg, from_peg = self.history[self.current_step]
            disk = self.pegs[from_peg].pop()
            self.play_disk(disk)
            self.pegs[to_peg].append(disk)
            self.current_step -= 1
        return True

    def get_state(self):
        return {
            'pegs': [list(peg) for peg in self.pegs],
            'current_step': self.current_step
        }

    def set_state(self, state):
        self.pegs = [list(peg) for peg in state['pegs']]
        self.current_step = state['current_step']

    def draw_title(self, is_animate=False):
        self.move_cursor(0, 0)
        print(f"\n{'=' * 50}")
        print(f"  汉诺塔演示 - 第 {self.current_step + 1}/{len(self.history)} 步" + (" - 自动播放中q停止" if is_animate else " "*30))
        print(f"{'=' * 50}\n")
    
    def update_step_in_title(self, is_animate=True):
        self.move_cursor(3, 0)
        print(f"  汉诺塔演示 - 第 {self.current_step + 1}/{len(self.history)} 步" +(" - 自动播放中q停止" if is_animate else " "*30))

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_pegs(self):
        self.move_cursor(6, 0)
        pivot_of_pegs = []
        max_disk = self.n
        for level in range(max_disk, -1, -1):
            line = ""
            peg_segments = []
            if self.current_step >= 0:
                from_idx, to_idx = self.history[self.current_step]
            else:
                from_idx, to_idx = -1, -1
            for peg_idx in range(3):
                disk = 0
                segment = ""
                if level < len(self.pegs[peg_idx]):
                    disk = self.pegs[peg_idx][level]
                left_space = max_disk - disk
                right_space = left_space
                segment += " " * (left_space + 2)
                segment += "█" * disk
                if level ==max_disk:
                    segment += "|" + ('↑' if peg_idx == from_idx else ('↓' if peg_idx == to_idx else ' ')) + '|'
                else:
                    segment += "|" + (str(disk) if disk else ' ') + '|'
                segment += "█" * disk
                segment += " " * (right_space + 2)
                
                if len(pivot_of_pegs) < 3:
                    pivot_of_pegs.append(len(segment)//2)
                index_of_separator = segment.index("|")
                # add color effect
                segment = self.COLORS[(disk+1)%len(self.COLORS)] + segment[:index_of_separator] + self.COLORS[0] +\
                            segment[index_of_separator:index_of_separator + 3] + \
                            self.COLORS[(disk+1)%len(self.COLORS)] + segment[index_of_separator + 3:] + self.COLORS[0]
                peg_segments.append(segment)
            line = ''.join(peg_segments)
            print(line)
        print(" " * pivot_of_pegs[0] + "A" + " " * (pivot_of_pegs[0] + pivot_of_pegs[1]) + "B" + " " * (pivot_of_pegs[1] + pivot_of_pegs[2]) + "C")
        print()

    def display(self, is_animate=False):
        self.update_step_in_title(is_animate)
        self.display_pegs()

    def display_control_tips(self):
        self.move_cursor(5 + self.n + 2 + 3, 0)
        print("\n命令说明:")
        print("n/→ - 下一步")
        print("b/← - 上一步(回退)")
        print("gNum - 跳转到第Num步")
        print("a - 自动播放动画")
        print("r - 重新开始")
        print("q - 退出")
        print()
    
    def clear_control_tips(self):
        self.move_cursor(5 + self.n + 2 + 3, 0)
        [print(' '*30) for _ in range(8)]
    
    def display_message(self, message):
        self.clear_message()
        self.move_cursor(5 + self.n + 2 + 2, 0)
        print(message, end='')
    
    def clear_message(self):
        self.move_cursor(5 + self.n + 2 + 2, 0)
        print('\r'+ ' '*shutil.get_terminal_size().columns + '\r', end='')

    def play_animation(self, delay=0.5):
        self.display()
        for i in range(len(self.history)):
            time.sleep(delay)
            self.execute_step()
            self.display(is_animate=True)
            if msvcrt.kbhit():
                key = msvcrt.getch() # any key to stop animation
                return

def get_user_input():
    valid_key_and_cmd = {
        b'q': 'quit',
        b'b': 'back', b'n': 'next',
        b'K': 'back', b'M': 'next',
        b'g': 'goto',
        b'a': 'animation',
        b'r': 'restart',
    }
    is_goto_mode = False
    step_num = ''
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if is_goto_mode:
                if key >= b'0' and key <= b'9':
                    step_num += key.decode()
                else:
                    is_goto_mode = False
                    if len(step_num) > 0:
                        return 'goto', step_num
            if key == b'\xe0':
                key = msvcrt.getch()
            if key in valid_key_and_cmd:
                cmd = valid_key_and_cmd[key]
                if cmd == 'goto':
                    is_goto_mode = True
                    continue
                else:
                    return cmd, None
        time.sleep(0.1)

def main():
    print("\n" + "=" * 50)
    print("       欢迎使用汉诺塔演示程序")
    print("=" * 50)
    try:
        n = int(input("\n请输入汉诺塔层数 (建议 1-9): "))
        if n < 1 or n > 9:
            print("层数必须在 1-9 之间")
            return
    except ValueError:
        print("输入无效，请输入数字")
        return

    hanoi = Hanoi(n)
    hanoi.solve()

    hanoi.clear()
    hanoi.draw_title(is_animate=False)
    
    hanoi.display()
    hanoi.display_control_tips()

    while True:
        cmd, param = get_user_input()
        if not cmd:
            continue

        if cmd == 'quit':
            hanoi.clear_control_tips()
            hanoi.display_message("感谢使用，再见！")
            break
        elif cmd == 'next':
            if hanoi.execute_step():
                hanoi.display()
                hanoi.clear_message()
            else:
                hanoi.display_message("已经到最后一步了！")
        elif cmd == 'back':
            if hanoi.goback():
                hanoi.display()
                hanoi.clear_message()
            else:
                hanoi.display_message("已经回到初始状态了！")
        elif cmd == 'goto':
            try:
                hanoi.prohibit_sound = True
                target = int(param)
                saved_state = hanoi.get_state()
                hanoi.set_state({'pegs': [[], [], []], 'current_step': -1})
                for i in range(n, 0, -1):
                    hanoi.pegs[0].append(i)
                if 0 <= target <= len(hanoi.history):
                    for _ in range(target):
                        hanoi.execute_step()
                    hanoi.display()
                else:
                    hanoi.set_state(saved_state)
                    hanoi.display_message(f"步骤无效，有效范围 1-{len(hanoi.history)}")
            except (IndexError, ValueError):
                hanoi.display_message("请输入有效的步骤号")
            finally:
                hanoi.prohibit_sound = False
        elif cmd == 'animation':
            hanoi.display_message("请输入每步延迟时间(秒，默认0.2): ")
            delay = input()
            hanoi.clear_message()

            try:
                delay = float(delay) if delay else 0.2
            except ValueError:
                delay = 0.2
            hanoi.play_animation(delay)
        elif cmd == 'restart':
            hanoi = Hanoi(n)
            hanoi.solve()

            hanoi.clear()
            hanoi.draw_title(is_animate=False)
            hanoi.display()
            hanoi.display_control_tips()

if __name__ == "__main__":
    main()
