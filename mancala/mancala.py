import os
import random
import subprocess
import msvcrt
import time
import sys
import os
import re
import threading


# 颜色代码
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class ScreenFramePrinter:
    COLOR_PATTERN = re.compile(r'\x1b\[\d+m')
    WIDECHAR_PATTERN = re.compile(r'[^\u0001-\u4e00]{1}')  # 任意宽字符, 如中文, Emoji等
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
                start_time = time.time()
            time.sleep(1)
        self.sound_handle.stop()
    
    def stop(self):
        self.is_stop = True

class MancalaGame:
    def __init__(self, mode=1, mirror_control=False):
        # 初始化棋盘 (逆时针方向): [坑1-6 (下标0-5), 玩家1存储区(下标6), 坑7-12 (下标7-12), AI/玩家2存储区(下标13)]
        self.board = [4] * 6 + [0] + [4] * 6 + [0]
        self.mode = mode
        self.mirror_control = mirror_control
        self.current_player = 1  # 1或2
        self.is_extra_round = False
        self.messages = []
        self.player_selector_index = [None, 0, 7] # [None, player1, player2]
        self.game_over = False
        self.frame_printer = ScreenFramePrinter()
    
    def get_user_input(self):
        accepted_keys_and_map = {
            b'K': 'left', b'M': 'right',
            b'q': 'quit', b'Q': 'quit',
            b'\r': 'enter',
        }
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':
                    key = msvcrt.getch()
                if key in accepted_keys_and_map:
                    return accepted_keys_and_map[key]
            time.sleep(0.1)
    
    def handle_user_input(self, key):
        if self.current_player == 1:
            allowed_pits = list(range(0, 6)) # 转换为内部索引 (0-5)
        else:
            allowed_pits = list(range(7, 13)) # 转换为内部索引 (7-12)
        
        if key in ('left', 'right'):
            if key == 'left':
                if self.current_player == 2 and self.mirror_control:
                    new_index = self.player_selector_index[self.current_player] + 1
                else:
                    new_index = self.player_selector_index[self.current_player] - 1
            elif key == 'right':
                if self.current_player == 2 and self.mirror_control:
                    new_index = self.player_selector_index[self.current_player] - 1
                else:
                    new_index = self.player_selector_index[self.current_player] + 1
            if new_index < allowed_pits[0]:
                new_index = allowed_pits[-1]
            elif new_index > allowed_pits[-1]:
                new_index = allowed_pits[0]
            # 更新选择器位置
            self.player_selector_index[self.current_player] = new_index
        elif key == 'enter':
            if self.is_valid_move(self.player_selector_index[self.current_player]):
                return self.player_selector_index[self.current_player]
        elif key == 'quit':
            return sys.exit()

    def clear(self):
        self.frame_printer.clear()
    
    def output_title(self):
        return [f"{GREEN}{'=' * 70}{RESET}",
                f"{GREEN}{' ' * 34}播棋{' ' * 34}{RESET}",
                f"{GREEN}{'=' * 70}{RESET}"
        ]
    
    def output_upper_player_info(self):
        player_name = "AI" if self.mode == 1 else "玩家2"
        return [f"{YELLOW if self.current_player == 2 else GREEN}{player_name}: {BLUE}{self.board[13]}{RESET}"]

    def output_lower_player_info(self):
        player_name = "玩家" if self.mode == 1 else "玩家1"
        return [f"{YELLOW if self.current_player == 1 else GREEN}{player_name}: {BLUE}{self.board[6]}{RESET}"]

    def output_one_slot(self, gem_count, is_highlight=False):
        slot_rows = []
        slot_rows.append('╭──────╮')
        display_count = min(3, gem_count)
        slot_rows.append('│'+'💎' * display_count + '  ' * (3 - display_count) +'│')
        display_count = min(3, max(0,gem_count - 3))
        slot_rows.append('│'+'💎' * display_count + '  ' * (3 - display_count) +'│')
        display_count = min(2, max(0,gem_count - 6))
        slot_rows.append('│'+'💎' * display_count + '  ' * (2 - display_count) + f'{gem_count:>2}' + '│')
        slot_rows.append('╰──────╯')
        return [f'{YELLOW}{row}{RESET}' if is_highlight else row for row in slot_rows]
    
    def output_one_stock(self, gem_count):
        stock_rows = []
        stock_rows.append('╭────────╮')
        for r in range(11):
            row = '│'
            for c in range(4):
                if c * 11 + r + 1 <= gem_count:
                    row += '💎'
            row += '  ' * (4 - row.count('💎')) + '│'
            stock_rows.append(row)
        ## amend last row, set gem count at right corner
        if stock_rows[-1][-2] == '💎':
            stock_rows[-1] = stock_rows[-1][:-2] + f'{gem_count:>2}' + '│'
        else:
            stock_rows[-1] = stock_rows[-1][:-3] + f'{gem_count:>2}' + '│'
        stock_rows.append('╰────────╯')
        return stock_rows
    
    def output_placeholder(self, width=8, height=5):
        return [' ' * width] * height
    
    def output_circle_indicators(self):
        left_row = '🠔' * 47 + ' '
        down = '🠗'
        right_row = '🠖' * 47 + ' '
        up = '🠕'
        return [f'{GREEN}{row}{RESET}' for row in [left_row, down + ' ' * 46 + up, right_row]]

    def concate_blocks(self, *blocks):
        over_all_rows = []
        for row_index in range(len(blocks[0])):
            concated_row = ''
            for block in blocks:
                concated_row += block[row_index]
            over_all_rows.append(concated_row)
        return over_all_rows
    
    def output_game_status(self):
        status_rows = []
        status_rows.append(f"{GREEN}{'=' * 70}{RESET}")
        if self.mode == 1:
            current_name = "玩家" if self.current_player == 1 else "AI"
        else:
            current_name = "玩家1" if self.current_player == 1 else "玩家2"
        status_rows.append(f"当前玩家: {current_name}" + (" (额外回合)" if self.is_extra_round else ""))
        status_rows.append("请选择要移动的格子(左右箭头,[回车]确认)")
        return status_rows

    def output_board(self):
        """打印游戏棋盘"""
        # self.frame_printer.clear()

        highlight_slot_index = self.player_selector_index[self.current_player]
        slots = [self.output_one_slot(cnt, index == highlight_slot_index) for index, cnt in enumerate(self.board)]
        
        upper_slots = slots[12:6:-1]
        lower_slots = slots[0:6]

        upper_player_stock_rows = self.output_one_stock(self.board[13]) # 占13行
        lower_player_stock_rows = self.output_one_stock(self.board[6]) # 占13行

        heading_placeholders = self.output_placeholder(1, 5)
        circle_indicators = self.output_circle_indicators()

        ## 玩家2的坑
        upper_player_concated_rows = self.concate_blocks(upper_player_stock_rows[0:5], heading_placeholders, self.concate_blocks(*upper_slots), heading_placeholders, lower_player_stock_rows[0:5])
        # for row in concated_rows:
        #     print(row)

        ## 中间分隔区
        separator_concated_rows = self.concate_blocks(upper_player_stock_rows[5:8], heading_placeholders[:3], circle_indicators, heading_placeholders[:3], lower_player_stock_rows[5:8])
        # for row in concated_rows:
        #     print(row)

        ## 玩家1的坑
        lower_player_concated_rows = self.concate_blocks(upper_player_stock_rows[8:13], heading_placeholders, self.concate_blocks(*lower_slots), heading_placeholders, lower_player_stock_rows[8:13])
        # for row in concated_rows:
        #     print(row)

        board_rows = upper_player_concated_rows + separator_concated_rows + lower_player_concated_rows
        return board_rows
    
    def output_winner_info(self):
        winner_rows = []
        winner = self.get_winner()
        if self.mode == 1:
            if winner == "平局":
                winner_rows.append(f"游戏结束！平局！")
                winner_rows.append(f"你的得分: {self.board[6]}")
                winner_rows.append(f"AI得分: {self.board[13]}")
            else:
                winner_rows.append(f"游戏结束！{'你' if winner == '玩家1' else 'AI'} 获胜！")
                winner_rows.append(f"你的得分: {self.board[6]}")
                winner_rows.append(f"AI得分: {self.board[13]}")
        else:
            winner_rows.append(f"游戏结束！{winner} 获胜！")
            winner_rows.append(f"玩家1得分: {self.board[6]}")
            winner_rows.append(f"玩家2得分: {self.board[13]}")
        return winner_rows
    
    def set_message(self, message):
        self.messages.append(message)

    def print_frame(self):
        # 标题
        title_rows = self.output_title()
        # 玩家2的信息
        upper_player_info_rows = self.output_upper_player_info()
        # 棋盘
        board_rows = self.output_board()
        # 玩家1的信息
        lower_player_info_rows = self.output_lower_player_info()
        # 游戏状态
        game_status_rows = self.output_game_status()

        frame_rows = title_rows + upper_player_info_rows + board_rows + lower_player_info_rows + game_status_rows
        if self.messages:
            frame_rows = frame_rows + self.messages
            self.messages.clear()
        if self.game_over:
            frame_rows += self.output_winner_info()
        self.frame_printer.print_frame(frame_rows)

    def is_valid_move(self, pit):
        """检查移动是否有效"""
        if self.current_player == 1:
            return 0 <= pit <= 5 and self.board[pit] > 0
        else:
            return 7 <= pit <= 12 and self.board[pit] > 0
    
    def make_move(self, pit):
        """执行移动"""
        stones = self.board[pit]
        self.board[pit] = 0
        current_pos = pit
        
        while stones > 0:
            current_pos = (current_pos + 1) % 14
            # 跳过对方的存储区
            if (self.current_player == 1 and current_pos == 13) or \
               (self.current_player == 2 and current_pos == 6):
                continue
            self.board[current_pos] += 1
            stones -= 1
        
        # 检查最后一粒棋子的位置
        last_pos = current_pos
        
        # 检查是否需要捕获对方的棋子
        """
        若最后一粒棋子落入自己一侧的空坑，且对面（对方一侧对应位置）的坑中有棋子，
        则将这两个坑的棋子（自己的最后一粒+对方对应坑中的所有棋子）一并收入自己的存储区。
        """
        if self.current_player == 1 and 0 <= last_pos <= 5 and self.board[last_pos] == 1:
            opposite_pit = 12 - last_pos
            if self.board[opposite_pit] > 0:
                self.board[6] += self.board[last_pos] + self.board[opposite_pit]
                self.board[last_pos] = 0
                self.board[opposite_pit] = 0
        elif self.current_player == 2 and 7 <= last_pos <= 12 and self.board[last_pos] == 1:
            opposite_pit = 12 - last_pos
            if self.board[opposite_pit] > 0:
                self.board[13] += self.board[last_pos] + self.board[opposite_pit]
                self.board[last_pos] = 0
                self.board[opposite_pit] = 0
        
        # 检查是否获得额外回合
        extra_turn = False
        if (self.current_player == 1 and last_pos == 6) or \
           (self.current_player == 2 and last_pos == 13):
           # 最后一粒棋子刚好放在玩家自己的存储区，获得额外回合
            extra_turn = True
        
        # 切换玩家（如果没有额外回合）
        if not extra_turn:
            self.current_player = 2 if self.current_player == 1 else 1
            self.is_extra_round = False
        else:
            # 当前玩家再玩一轮
            self.is_extra_round = True
    
    def is_game_over(self):
        """检查游戏是否结束"""
        if not self.game_over:
            p1_pits_empty = all(self.board[i] == 0 for i in range(0, 6))
            p2_pits_empty = all(self.board[i] == 0 for i in range(7, 13))
            self.game_over = p1_pits_empty or p2_pits_empty
        return self.game_over
    
    def end_game(self):
        """结束游戏，收集剩余棋子"""
        # 收集玩家1的剩余棋子
        for i in range(0, 6):
            self.board[6] += self.board[i]
            self.board[i] = 0
        # 收集玩家2的剩余棋子
        for i in range(7, 13):
            self.board[13] += self.board[i]
            self.board[i] = 0
    
    def get_winner(self):
        """获取获胜者"""
        if self.mode == 1:
            if self.board[6] > self.board[13]:
                return "玩家1"
            elif self.board[13] > self.board[6]:
                return "AI"
            else:
                return "平局"
        else:
            if self.board[6] > self.board[13]:
                return "玩家1"
            elif self.board[13] > self.board[6]:
                return "玩家2"
            else:
                return "平局"
    
    def ai_move(self):
        """AI 移动"""
        # 简单的AI策略：优先选择能获得额外回合的移动
        valid_moves = [i for i in range(7, 13) if self.board[i] > 0]
        
        # 尝试找到能获得额外回合的移动
        for move in valid_moves:
            # 模拟移动
            test_board = self.board.copy()
            stones = test_board[move]
            test_board[move] = 0
            current_pos = move
            
            while stones > 0:
                current_pos = (current_pos + 1) % 14
                if current_pos == 6:  # 跳过玩家1的存储区
                    continue
                test_board[current_pos] += 1
                stones -= 1
            
            # 检查是否获得额外回合
            if current_pos == 13:
                return move
        
        # 如果没有，随机选择一个移动
        return random.choice(valid_moves)

def main():
    # 选择游戏模式
    print("选择游戏模式：")
    print("1. 人机对战")
    print("2. 双人对战")
    mode = input("请输入选择 (1/2,直接[回车]默认1): ").strip()
    mode = 1 if mode == '' else int(mode)
    
    mirror_control = True
    if mode == 2:
        mirror_control = input("玩家2是否镜像控制 (y/n,直接[回车]默认y): ").strip()
        if mirror_control.lower() == "y" or mirror_control == '':
            mirror_control = True # 两玩家正向操作键盘
        else:
            mirror_control = False # 两玩家对向而坐, 分别朝向键盘底边和上边(相当于键盘竖着的放, 垂直于显示器)

    # 游戏开始
    game = MancalaGame(mode, mirror_control)
    game.clear()

    while not game.is_game_over():
        game.print_frame()
        
        if game.mode == 2 or (game.mode == 1 and game.current_player == 1):
            # 玩家输入
            while True:
                try:
                    if game.mode == 1:
                        cmd = game.get_user_input()
                        pit = game.handle_user_input(cmd)
                    elif game.current_player == 1:
                        cmd = game.get_user_input()
                        pit = game.handle_user_input(cmd)
                    else:
                        cmd = game.get_user_input()
                        pit = game.handle_user_input(cmd)

                    if pit is not None:
                        if game.is_valid_move(pit):
                            game.make_move(pit)
                            break
                    else:
                        if cmd == 'enter':
                            game.set_message("无法移动空格子，请重新选择！")
                        game.print_frame()
                except ValueError:
                    pass
        else:
            # AI 移动
            game.set_message("AI 正在思考...")
            game.print_frame()
            time.sleep(0.5)
            ai_pit = game.ai_move()
            game.set_message(f"AI 选择了格子{ai_pit - 6}")
            game.make_move(ai_pit)
    
    # 游戏结束
    game.end_game()
    game.print_frame()


if __name__ == "__main__":
    main()
