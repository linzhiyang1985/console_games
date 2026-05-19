import msvcrt
import time
import random
import re
import os
import subprocess
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

    BG_DARK_BLUE = '\033[44m'
    BG_DARK_WHITE = '\033[47m' #47--bg, XXXX--fg


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


class RushGame:
    def __init__(self):
        self.screen_width = 100
        self.screen_height = 45
        self.ground_level = self.screen_height - 5
        self.runner_x = 8
        self.runner_y = self.ground_level - 9
        self.runner_last_line_index = 0;
        self.is_jumping = False
        self.jump_velocity = 0
        self.gravity = 1.2
        self.jump_strength = -6.6
        self.score = 0
        self.game_over = False
        self.paused = False
        self.obstacles = []
        self.rewards = []
        self.ground_heights = [random.randint(0, 2) for _ in range(self.screen_width)]
        self.speed = 1.5
        self.base_speed = 1.5
        self.obstacle_spawn_timer = 0
        self.reward_spawn_timer = 0
        self.screen_buffer = []
        
    def clear_screen(self):
        frame_printer.clear()
    
    def init_buffer(self):
        self.screen_buffer = [[' ' for _ in range(self.screen_width)] for _ in range(self.screen_height)]
    
    def set_char(self, y, x, char):
        if 0 <= y < self.screen_height and 0 <= x < self.screen_width:
            self.screen_buffer[y][x] = char
    
    def set_string(self, y, x, text):
        for i, char in enumerate(text):
            if 0 <= x + i < self.screen_width:
                self.set_char(y, x + i, char)
    
    def generate_ground(self):
        for i in range(len(self.ground_heights)):
            if random.random() < 0.1:
                change = random.choice([-1, 0, 1])
                self.ground_heights[i] = max(0, min(3, self.ground_heights[i] + change))
    
    def play_jump(self):
        playsound('sound/jump.mp3', block=False)
    
    def play_reward(self):
        playsound('sound/reward.mp3', block=False)
    
    def play_game_over(self):
        playsound('sound/lose.mp3', block=False)

    def draw_ground(self):
        for x in range(1, self.screen_width - 1):
            height = self.ground_heights[x]
            for y in range(self.ground_level - height, self.ground_level):
                self.set_char(y, x, '.')
            self.set_char(self.ground_level - height, x, '_')
    
    def draw_runner(self):
        x = self.runner_x
        y = int(self.runner_y)
        sprite = [
           r"    \O/    ",
            "   O0O0O   ",
            "0  OXXXO  0",
            " 0OOOOOOO0 ",
            "   OOOOO   ",
            "    OOO    ",
            "   OOOOO   ",
            "   OO OO   ",
            "  OO   OO  ",
        ]
        # last_2_line_changes = [("  OO   OO  ", " OO     OO "), ("   OO OO   ", "  OO   OO  ")]
        last_2_line_changes = [("   OO  OO  ", " OO    OO  "), ("  OO  OO   ", "  OO    OO ")]
        for i, line in enumerate(sprite):
            self.set_string(y + i, x, line)
        self.set_string(y + i + 1, x, last_2_line_changes[self.runner_last_line_index][0])
        self.set_string(y + i + 2, x, last_2_line_changes[self.runner_last_line_index][1])
        if not self.game_over:
            self.runner_last_line_index = (self.runner_last_line_index + 1) % len(last_2_line_changes)
    
    def update_runner(self):
        if self.is_jumping:
            # raise(jump_velocity < 0) to the top(==0) then fall(>0)
            self.runner_y += self.jump_velocity
            self.jump_velocity += self.gravity
            
            ground_y = self.ground_level - 9 - self.ground_heights[self.runner_x]
            if self.runner_y >= ground_y: # fall onto the ground
                self.runner_y = ground_y
                self.is_jumping = False
                self.jump_velocity = 0
    
    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = self.jump_strength
            self.play_jump()
    
    def spawn_obstacle(self):
        height = random.randint(5, 7)
        obstacle = {
            'x': self.screen_width - 10,
            'y': self.ground_level - height,
            'width': 9,
            'height': height
        }
        self.obstacles.append(obstacle)
    
    def spawn_reward(self):
        reward_y = self.ground_level - 10 - random.randint(0, 2)
        reward = {
            'x': self.screen_width - 10,
            'y': reward_y,
            'width': 9,
            'height': 7
        }
        self.rewards.append(reward)
    
    def draw_obstacle(self, obs):
        x, y, h = obs['x'], obs['y'], obs['height']
        sprite = [
            "   WWW   ",
            "  WWVWW  ",
            "WWWWVWWWW",
            " WWWVWWW ",
            "  WWVWW  ",
            " WWWVWWW ",
            "WWW   WWW"
        ]
        for i in range(min(h, len(sprite))):
            self.set_string(y + i, x, sprite[i])
    
    def draw_reward(self, rew):
        x, y = rew['x'], rew['y']
        sprite = [
            "   *   ",
            "  ***  ",
            " ***** ",
            "*******",
            " ***** ",
            "  ***  ",
            "   *   "
        ]
        for i, line in enumerate(sprite):
            self.set_string(y + i, x, line)
    
    def update_obstacles(self):
        for obs in self.obstacles:
            obs['x'] = int(obs['x'] - self.speed)
        self.obstacles = [obs for obs in self.obstacles if obs['x'] > -10]
    
    def update_rewards(self):
        for rew in self.rewards:
            rew['x'] = int(rew['x'] - self.speed)
        self.rewards = [rew for rew in self.rewards if rew['x'] > -10]
    
    def check_collision(self):
        # shrink range
        runner_rect = {
            'x': self.runner_x + 2,
            'y': self.runner_y + 2,
            'width': 7,
            'height': 7
        }
        
        for obs in self.obstacles:
            obs_rect = {
                'x': obs['x'] + 1,
                'y': obs['y'],
                'width': 7,
                'height': obs['height']
            }
            if self.rects_intersect(runner_rect, obs_rect):
                return True
        return False
    
    def check_reward_collision(self):
        runner_rect = {
            'x': self.runner_x + 2,
            'y': self.runner_y + 2,
            'width': 5,
            'height': 7
        }
        
        collected = []
        for rew in self.rewards:
            rew_rect = {
                'x': rew['x'],
                'y': rew['y'],
                'width': 9,
                'height': 9
            }
            if self.rects_intersect(runner_rect, rew_rect):
                collected.append(rew)
                self.score += 10
                self.play_reward()
        
        for rew in collected:
            if rew in self.rewards:
                self.rewards.remove(rew)
    
    def rects_intersect(self, r1, r2):
        return not (r1['x'] + r1['width'] <= r2['x'] or 
                    r2['x'] + r2['width'] <= r1['x'] or
                    r1['y'] + r1['height'] <= r2['y'] or
                    r2['y'] + r2['height'] <= r1['y'])
    
    def draw_title(self):
        title = "==== SIMPLE RUSH ===="
        center_x = self.screen_width // 2 - len(title) // 2
        self.set_string(0, center_x, title)

    def draw_score(self):
        speed_display = self.base_speed + (self.score // 150) * 0.3
        score_text = f"SCORE: {self.score:05d}  SPEED: {speed_display:.1f}"
        self.set_string(1, 2, score_text)
    
    def draw_border(self):
        self.set_string(2, 0, '+' + '-' * (self.screen_width - 2) + '+')
        for y in range(3, self.screen_height - 2):
            self.set_char(y, 0, '|')
            self.set_char(y, self.screen_width - 1, '|')
        self.set_string(self.screen_height - 2, 0, '+' + '-' * (self.screen_width - 2) + '+')
    
    def draw_instructions(self):
        instructions = "SPACE: Jump  Q: Quit  P: Pause"
        self.set_string(self.screen_height - 1, 2, instructions)
    
    def draw_game_over(self):
        game_over_art = [
            "  ########  ",
            " ##      ##",
            "##  GAME  ##",
            "##  OVER! ##",
            " ##      ## ",
            "  ########  "
        ]
        
        center_y = self.screen_height // 2 - 3
        center_x = self.screen_width // 2 - 6
        
        for i, line in enumerate(game_over_art):
            self.set_string(center_y + i, center_x, line)
        
        final_score_text = f"Final Score: {self.score}"
        self.set_string(center_y + 7, center_x - 5, final_score_text)
        self.set_string(center_y + 9, center_x - 10, "Press R to Restart or Q to Quit")
    
    def draw_paused(self):
        paused_text = "[ PAUSED ]"
        center_x = self.screen_width // 2 - 5
        center_y = self.screen_height // 2
        self.set_string(center_y, center_x, paused_text)
    
    def handle_input(self):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if isinstance(key, bytes):
                try:
                    key = key.decode('utf-8', errors='ignore')
                except:
                    return 'none'
            
            if key == ' ':
                if not self.game_over and not self.paused:
                    self.jump()
                return 'jump'
            elif key.lower() == 'q':
                return 'quit'
            elif key.lower() == 'p' and not self.game_over:
                self.paused = not self.paused
                return 'pause'
            elif key.lower() == 'r' and self.game_over:
                return 'restart'
        return 'none'
    
    def render(self):
        self.init_buffer()
        
        self.draw_title()
        self.draw_border()
        self.draw_score()
        self.draw_ground()
        self.draw_runner()
        
        for obs in self.obstacles:
            self.draw_obstacle(obs)
        
        for rew in self.rewards:
            self.draw_reward(rew)
        
        if self.game_over:
            self.draw_game_over()
        elif self.paused:
            self.draw_paused()
        
        self.draw_instructions()
        
        # self.clear_screen()
        # for row in self.screen_buffer:
        #     print(''.join(row))
        line_array = []
        for row in self.screen_buffer:
            if 'E' in row or 'e' in row:
                # direct print line content
                line = ''.join(row).replace('|', Color.DARK_CYAN + '|' + Color.RESET).replace('#', Color.RED + '#' + Color.RESET)
            else:
                line = ''
                for c in row:
                    # coloring
                    if c in ('.', '_'):
                        # ground
                        line += Color.DARK_YELLOW + c + Color.RESET
                    elif c in ('O', '0', 'X', '\\', '/'):
                        # runner
                        line += Color.GREEN + c + Color.RESET
                    elif c in ('W', 'V'):
                        # obstacle
                        line += Color.GRAY + c + Color.RESET
                    elif c == '*':
                        # reward
                        line += Color.BLUE + c + Color.RESET
                    elif c in ('+', '-', '|'):
                        # border
                        line += Color.DARK_CYAN + c + Color.RESET
                    elif c == '#':
                        #game over rect
                        line += Color.RED + c + Color.RESET
                    else:
                        line += c
            line_array.append(line)
        frame_printer.print_frame(line_array)
    
    def update(self):
        if not self.game_over and not self.paused:
            self.update_runner()
            
            self.obstacle_spawn_timer += 1
            if self.obstacle_spawn_timer >= random.randint(100, 180):
                if random.random() < 0.7:
                    self.spawn_obstacle()
                else:
                    self.spawn_reward()
                self.obstacle_spawn_timer = 0
            
            self.reward_spawn_timer += 1
            if self.reward_spawn_timer >= random.randint(150, 250) and random.random() < 0.3:
                self.spawn_reward()
                self.reward_spawn_timer = 0
            
            self.update_obstacles()
            self.update_rewards()
            
            self.check_reward_collision()
            
            if self.check_collision():
                self.game_over = True
                self.play_game_over()
            
            self.score += 1
            self.speed = self.base_speed + (self.score // 150) * 0.3
            
            if random.random() < 0.3:
                self.generate_ground()
    
    def run(self):
        try:
            os.system('mode con cols={} lines={}'.format(self.screen_width + 2, self.screen_height + 2))
        except:
            pass
        
        self.render()
        
        last_render = time.time()
        render_delay = 0.05
        
        while True:
            current_time = time.time()
            
            action = self.handle_input()
            
            if action == 'quit':
                break
            elif action == 'restart':
                self.__init__()
                self.render()
            elif action == 'pause':
                self.render()
                time.sleep(0.1)
                continue
            
            if current_time - last_render >= render_delay:
                self.update() # each frame
                self.render()
                last_render = current_time
            
            time.sleep(0.01)
        
        self.clear_screen()
        print("Thanks for playing!")
        print(f"Final Score: {self.score}")

def main():
    try:
        game = RushGame()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted. Thanks for playing!")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
