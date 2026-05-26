import os
import random
import time
import msvcrt
import re
import subprocess
import threading
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


class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.sound_file_path = 'sound/background.wav'
        self.track_length = 35
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


class Game:
    def __init__(self):
        self.WIDTH = 40
        self.HEIGHT = 20
        self.player = {'x': self.WIDTH // 2, 'y': self.HEIGHT - 2}
        self.bullets = []
        self.obstacles = []
        self.powerups = []
        self.score = 0
        self.kill_count = 0
        self.bullet_speed = 1
        self.bullet_power = 1
        self.spread_width = 0
        self.last_shot_time = 0
        self.shot_interval = 0.2
        self.game_over = False
        
    def spawn_obstacle(self):
        types = [('A', 1), ('B', 1), ('C', 3), ('D', 2)]
        obstacle_type, health = random.choice(types)
        return {
            'x': random.randint(1, self.WIDTH - 2),
            'y': 0,
            'type': obstacle_type,
            'health': health,
            'move_direction': random.choice([-1, 1]) if obstacle_type == 'D' else 0
        }
        
    def spawn_powerup(self):
        types = ['*', '#']
        powerup_type = random.choice(types)
        return {
            'x': random.randint(1, self.WIDTH - 2),
            'y': 0,
            'type': powerup_type
        }


    def play_shoot(self):
        playsound('sound/shoot.wav', block=False)
    
    def play_explode(self, is_block=False):
        playsound('sound/explode.wav', block=is_block)
    
    def play_game_over(self):
        playsound('sound/game_over.wav')

    def shoot(self):
        now = time.time()
        if now - self.last_shot_time >= self.shot_interval / self.bullet_speed:
            self.play_shoot()
            for i in range(-self.spread_width, self.spread_width + 1):
                self.bullets.append({'x': self.player['x'] + i, 'y': self.player['y'] - 1, 'dx': i * 0.3, 'dy': -1})
            self.last_shot_time = now
            
    def move_player(self, dx):
        new_x = self.player['x'] + dx
        if 1 <= new_x < self.WIDTH - 1:
            self.player['x'] = new_x
        
    def update(self):
        if random.random() < 0.03:
            self.obstacles.append(self.spawn_obstacle())
        if random.random() < 0.01:
            self.powerups.append(self.spawn_powerup())
            
        new_bullets = []
        for bullet in self.bullets:
            bullet['x'] += bullet['dx']
            bullet['y'] += bullet['dy']
            if 0 < bullet['x'] < self.WIDTH and 0 < bullet['y'] < self.HEIGHT:
                new_bullets.append(bullet)
        self.bullets = new_bullets
        
        to_remove = []
        for i, obstacle in enumerate(self.obstacles):
            if obstacle['type'] == 'D':
                obstacle['x'] += obstacle['move_direction']
                if obstacle['x'] <= 0 or obstacle['x'] >= self.WIDTH - 1:
                    obstacle['move_direction'] *= -1
            obstacle['y'] += 0.5
            
            if obstacle['x'] == self.player['x'] and int(obstacle['y']) == self.player['y']:
                self.game_over = True
                self.play_explode(is_block=True)
                background_player.stop()
                self.play_game_over()
                return
            
            if obstacle['y'] >= self.HEIGHT:
                to_remove.append(i)
            
            for j, bullet in list(enumerate(self.bullets)):
                if int(bullet['x']) == obstacle['x'] and \
                   int(obstacle['y']) - 1.2 <= int(bullet['y']) <= int(obstacle['y']): #子弹稍微穿越过了障碍物也算击中
                    obstacle['health'] -= self.bullet_power
                    del self.bullets[j]
                    if obstacle['health'] <= 0:
                        self.score += 10
                        self.kill_count += 1
                        to_remove.append(i)
                        self.play_explode()
                    break
        
        for i in reversed(to_remove):
            del self.obstacles[i]
        
        to_remove_powerup = []
        for i, powerup in enumerate(self.powerups):
            powerup['y'] += 0.3
            
            if powerup['y'] >= self.HEIGHT:
                to_remove_powerup.append(i)
                continue
            
            if int(powerup['x']) == self.player['x'] and int(powerup['y']) == self.player['y']:
                if powerup['type'] == '*':
                    self.bullet_power += 1
                elif powerup['type'] == '#':
                    self.spread_width += 1
                to_remove_powerup.append(i)
        
        for i in reversed(to_remove_powerup):
            del self.powerups[i]
        
        if self.kill_count > 0 and self.kill_count % 20 == 0:
            self.bullet_speed += 1
    
    def get_status_rows(self):
        rows = []
        rows.append(f'击落:{self.kill_count} 得分:{self.score}')
        rows.append(f'威力:{self.bullet_power} 射速: x{self.bullet_speed} 散射宽度:{self.spread_width}')
        rows.append('使用 ← → 或 A D 移动，空格键射击，ESC退出')
        rows.append('障碍物: A(1弹), B(1弹), C(3弹), D(2弹,移动)')
        rows.append('奖励: *(威力+1) #(散射)')
        return rows
    
    def output_frame(self):
        screen = [[' ' for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        
        for i in range(self.WIDTH):
            screen[0][i] = '='
            screen[self.HEIGHT - 1][i] = '='
        for i in range(1, self.HEIGHT - 1):
            screen[i][0] = '|'
            screen[i][self.WIDTH - 1] = '|'
        
        screen[self.player['y']][self.player['x']] = 'O'
        
        for bullet in self.bullets:
            screen[int(bullet['y'])][int(bullet['x'])] = '|'
        
        for obstacle in self.obstacles:
            screen[int(obstacle['y'])][obstacle['x']] = obstacle['type']
        
        for powerup in self.powerups:
            screen[int(powerup['y'])][int(powerup['x'])] = powerup['type']
        
        frame = ['~'* 15 + 'O型战机' + '~'*15]
        for row in screen:
            line = ''
            for index, cell in enumerate(row):
                # render with color
                if index != 0 and index != self.WIDTH - 1 and cell == '|':
                    line += Color.GREEN + cell + Color.RESET
                elif cell in 'ABCD':
                    line += Color.MAGENTA + cell + Color.RESET
                elif cell == 'O':
                    line += Color.BLUE + cell + Color.RESET
                else:
                    line += cell
            frame.append(line)
            
        frame.extend(self.get_status_rows())
        return frame
        
    def handle_input(self):
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27: # ESC
                self.game_over = True
            elif key == 32: # 空格
                self.shoot()
            elif key == 224: # 方向键
                arrow_key = ord(msvcrt.getch())
                if arrow_key == 75: # 左
                    self.move_player(-1)
                elif arrow_key == 77: # 右
                    self.move_player(1)
            elif key == 97 or key == 65: # a 或 A
                self.move_player(-1)
            elif key == 100 or key == 68: # d 或 D
                self.move_player(1)
        
    def run(self):
        frame_printer.clear()
        while not self.game_over:
            self.handle_input()
            self.update()
            frame = self.output_frame()
            frame_printer.print_frame(frame)
            time.sleep(0.1)
        
        frame = self.output_frame()
        frame.append(f'游戏结束! 最终得分:{self.score}')
        frame_printer.print_frame(frame)


if __name__ == '__main__':
    try:
        background_player = LoopPlayer()
        background_player.start()

        game = Game()
        game.run()
    except:
        pass
    finally:
        background_player.stop()
