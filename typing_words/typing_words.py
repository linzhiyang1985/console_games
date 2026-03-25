import shutil
import os
from typing import Dict, Optional, List
from dataclasses import dataclass
import threading
import time
import random
from dict_reader import get_random_word_list


# 检测操作系统
IS_WINDOWS = os.name == 'nt'

if IS_WINDOWS:
    import msvcrt
    from colorama import init, Fore, Style
    init(autoreset=True)
else:
    import curses

# 单词库
# WORD_DATABASE: Dict[str, str] = {
#     "apple": "苹果",
#     "banana": "香蕉",
#     "orange": "橙子",
#     "grape": "葡萄",
#     "watermelon": "西瓜",
#     "strawberry": "草莓",
#     "cherry": "樱桃",
#     "peach": "桃子",
#     "pear": "梨",
#     "mango": "芒果",
#     "computer": "电脑",
#     "keyboard": "键盘",
#     "mouse": "鼠标",
#     "monitor": "显示器",
#     "printer": "打印机",
#     "internet": "互联网",
#     "software": "软件",
#     "hardware": "硬件",
#     "program": "程序",
#     "database": "数据库",
#     "happy": "快乐的",
#     "beautiful": "美丽的",
#     "wonderful": "精彩的",
#     "amazing": "令人惊奇的",
#     "excellent": "优秀的",
#     "fantastic": "极好的",
#     "perfect": "完美的",
#     "special": "特别的",
#     "important": "重要的",
#     "different": "不同的",
#     "school": "学校",
#     "teacher": "老师",
#     "student": "学生",
#     "book": "书",
#     "pen": "笔",
#     "paper": "纸",
#     "desk": "书桌",
#     "classroom": "教室",
#     "education": "教育",
#     "knowledge": "知识",
#     "science": "科学",
#     "friend": "朋友",
#     "family": "家庭",
#     "love": "爱",
#     "home": "家",
#     "mother": "母亲",
#     "father": "父亲",
#     "brother": "兄弟",
#     "sister": "姐妹",
#     "children": "孩子",
#     "people": "人们",
#     "world": "世界",
#     "country": "国家",
#     "city": "城市",
#     "river": "河流",
#     "mountain": "山",
#     "forest": "森林",
#     "ocean": "海洋",
#     "sky": "天空",
#     "sun": "太阳",
#     "moon": "月亮",
#     "star": "星星",
#     "weather": "天气",
#     "rain": "雨",
#     "snow": "雪",
#     "wind": "风",
#     "cloud": "云",
#     "time": "时间",
#     "day": "天",
#     "night": "夜晚",
#     "morning": "早上",
#     "evening": "晚上",
#     "today": "今天",
#     "tomorrow": "明天",
#     "yesterday": "昨天",
#     "week": "周",
#     "month": "月",
#     "year": "年",
#     "red": "红色",
#     "blue": "蓝色",
#     "green": "绿色",
#     "yellow": "黄色",
#     "black": "黑色",
#     "white": "白色",
#     "big": "大的",
#     "small": "小的",
#     "long": "长的",
#     "short": "短的",
#     "good": "好的",
#     "bad": "坏的",
#     "new": "新的",
#     "old": "旧的",
#     "hot": "热的",
#     "cold": "冷的",
#     "eat": "吃",
#     "drink": "喝",
#     "sleep": "睡觉",
#     "run": "跑",
#     "walk": "走",
#     "jump": "跳",
#     "swim": "游泳",
#     "read": "读",
#     "write": "写",
#     "speak": "说",
#     "listen": "听",
#     "think": "思考",
#     "work": "工作",
#     "play": "玩",
#     "study": "学习",
#     "help": "帮助",
#     "give": "给",
#     "take": "拿",
#     "make": "制作",
#     "get": "得到",
#     "buy": "买",
#     "sell": "卖",
#     "open": "打开",
#     "close": "关闭",
#     "begin": "开始",
#     "end": "结束",
#     "come": "来",
#     "go": "去",
#     "see": "看见",
#     "look": "看",
#     "know": "知道",
#     "want": "想要",
#     "need": "需要",
#     "like": "喜欢",
# }
WORD_DATABASE = get_random_word_list("englishwords.db", 200)

@dataclass
class FallingWord:
    """下落的单词"""
    word: str
    meaning: str
    x: int
    y: float
    speed: float
    matched: bool = False
    match_time: float = 0


class TypingGame:
    """打字游戏类"""

    def __init__(self):
        """初始化游戏"""
        self.words: List[FallingWord] = []
        self.score = 0
        self.input_buffer = ""
        self.game_running = False
        self.last_spawn_time = 0
        self.spawn_interval = 3.0
        self.base_speed = 0.1
        self.screen_height = 24
        self.screen_width = 80
        self.screen_size_changed = True
        self.bottom_margin = 4
        self.divide_line_y = self.screen_height - self.bottom_margin
        self.missed_words = 0
        self.matched_words = 0
        self.lock = threading.Lock()
        self._update_terminal_size()

    def _update_terminal_size(self):
        """更新终端大小"""
        try:
            size = shutil.get_terminal_size()
            if size.columns != self.screen_width or size.lines != self.screen_height:
                self.screen_width = size.columns
                self.screen_height = size.lines
                self.screen_size_changed = True
                self.divide_line_y = self.screen_height - self.bottom_margin
        except:
            pass

    def clear_screen(self):
        """清屏"""
        if IS_WINDOWS:
            os.system('cls')
        else:
            os.system('clear')

    def get_random_word(self) -> tuple:
        """获取随机单词"""
        word = random.choice(list(WORD_DATABASE.keys()))
        meaning = WORD_DATABASE[word]
        if isinstance(meaning, list):
            meaning = random.choice(meaning)
        return word, meaning
    
    def spawn_word(self):
        """生成新单词"""
        word, meaning = self.get_random_word()
        max_x = max(0, self.screen_width - len(word) - len(meaning) - 5)
        x = random.randint(2, max(2, max_x))
        speed = self.base_speed + random.uniform(0, 0.2) + (self.score / 4000)

        falling_word = FallingWord(
            word=word,
            meaning=meaning,
            x=x,
            y=4,
            speed=speed
        )

        with self.lock:
            self.words.append(falling_word)
    
    def update_words(self):
        """更新所有单词位置"""
        with self.lock:
            for word in self.words:
                if not word.matched:
                    """更新未匹配单词位置"""
                    word.y += word.speed

            current_time = time.time()
            new_words = []
            for word in self.words:
                if word.matched:
                    if current_time - word.match_time < 3.0:
                        """保留匹配单词3秒"""
                        new_words.append(word)
                else:
                    """未匹配单词如果还有下降的空间,将其添加到新列表"""
                    if word.y < self.screen_height - self.bottom_margin:
                        new_words.append(word)
                    else:
                        """否则从单词列表中移除, 并记为missed"""
                        self.missed_words += 1
                        self.draw_status()
            """新列表覆盖旧列表"""
            self.words = new_words
    
    def check_match(self, input_text: str) -> Optional[FallingWord]:
        """检查输入是否匹配某个单词"""
        with self.lock:
            for word in self.words:
                if not word.matched and word.word.lower() == input_text.lower():
                    word.matched = True
                    word.match_time = time.time()
                    self.score += len(word.word) * 10
                    self.matched_words += 1
                    return word
        return None

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

    def draw_input(self):
        self.move_cursor(self.divide_line_y + 1, 0)
        # 绘制输入框
        input_prompt = "输入: "
        print(Fore.WHITE + input_prompt + Fore.GREEN + Style.BRIGHT + self.input_buffer + (' ' * 20) + Style.RESET_ALL)
        print()

    def draw_frame(self):
        # 清屏并移动到顶部
        self.clear_screen()

        # 绘制标题
        title = "打字练习游戏"
        print(Fore.CYAN + Style.BRIGHT + title.center(self.screen_width))

        # 绘制分数信息
        self.draw_status()
        print(Fore.WHITE + "按 ESC 退出游戏, 按 ENTER 清空输入")
        print()

        self.move_cursor(self.divide_line_y, 0)

        # 绘制分界线
        print(Fore.WHITE + "─" * (self.screen_width - 1))

        self.draw_input()
    
    def draw_status(self):
        """绘制游戏状态"""
        self.move_cursor(2, 0)
        score_text = f"得分: {self.score} | 已输入: {self.matched_words} | 错过: {self.missed_words}"
        print(Fore.WHITE + score_text)

    def draw_words(self):
        self.move_cursor(5, 0)
        # 绘制下落区域
        """绘制所有单词"""
        with self.lock:
            # 创建一个空的屏幕缓冲区
            screen_buffer = [[' ' for _ in range(self.screen_width)] for _ in range(self.divide_line_y - 5)]

            for word in self.words:
                y = int(word.y) - 5
                match_length = 0
                if 0 <= y < len(screen_buffer):
                    x = word.x
                    if word.matched:
                        # 已匹配的单词显示中文意思
                        display_text = f"{word.word}={word.meaning}"
                        color = Fore.CYAN + Style.BRIGHT
                    else:
                        display_text = word.word
                        
                        # 未匹配单词根据进度(即下落的高度)显示不同颜色
                        progress = word.y / (self.divide_line_y - 3)
                        if progress < 0.5:
                            color = Fore.GREEN
                        elif progress < 0.8:
                            color = Fore.YELLOW
                        else:
                            color = Fore.RED
                        if word.word.startswith(self.input_buffer):
                            match_color = Fore.BLUE
                            match_length = len(self.input_buffer)
                        else:
                            match_color = color
                            match_length = 0

                    # 写入缓冲区
                    available_space = min(len(display_text), self.screen_width - x)
                    # 写入匹配部分
                    if match_length > 0:
                        screen_buffer[y][x: x+match_length] = [match_color + char + Style.RESET_ALL for char in display_text[:match_length]]
                    # 写入非匹配部分
                    screen_buffer[y][x+match_length: x+available_space] = [color + char + Style.RESET_ALL for char in display_text[match_length:available_space]]
                    screen_buffer[y][x] = color + screen_buffer[y][x]
                    screen_buffer[y][x+available_space-1] = screen_buffer[y][x+available_space-1] + Style.RESET_ALL

            # 打印缓冲区
            for row in screen_buffer:
                line = ''.join(row)
                # 处理颜色代码
                print(line)

    def draw(self):
        """绘制游戏画面"""
        self._update_terminal_size()
        if self.screen_size_changed:
            self.draw_frame()
            self.screen_size_changed = False
        # 绘制下落区域
        self.draw_words()
        self.draw_input()

    def get_key(self):
        """获取键盘输入（非阻塞）"""
        if IS_WINDOWS:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\r':
                    return 'ENTER'
                elif key == b'\x1b':
                    return 'ESC'
                elif key == b'\x08':
                    return 'BACKSPACE'
                elif key == b'\x00' or key == b'\xe0':
                    # 特殊键
                    msvcrt.getch()
                    return None
                else:
                    try:
                        return key.decode('utf-8')
                    except:
                        return key.decode('gbk', errors='ignore')
            return None
        else:
            # Linux/Mac 使用 select
            import select
            import tty
            import termios

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key == '\r':
                        return 'ENTER'
                    elif key == '\x1b':
                        return 'ESC'
                    elif key == '\x7f':
                        return 'BACKSPACE'
                    else:
                        return key
                return None
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def run(self):
        """游戏主循环"""
        self.game_running = True
        self.last_spawn_time = time.time()

        try:
            while self.game_running:
                current_time = time.time()

                # 生成新单词
                if current_time - self.last_spawn_time >= self.spawn_interval:
                    self.spawn_word()
                    self.last_spawn_time = current_time
                    self.spawn_interval = max(1.5, 3.0 - self.score / 1000)

                # 更新单词位置
                self.update_words()

                # 处理输入
                key = self.get_key()
                if key:
                    if key == 'ENTER':
                        self.input_buffer = ""
                    elif key == 'ESC':
                        self.game_running = False
                    elif key == 'BACKSPACE':
                        self.input_buffer = self.input_buffer[:-1]
                    elif len(key) == 1 and 32 <= ord(key) <= 126:
                        if len(self.input_buffer) < 30:
                            self.input_buffer += key
                            matched_word = self.check_match(self.input_buffer)
                            if matched_word:
                                self.input_buffer = ""
                                self.draw_status()
                # 绘制画面
                self.draw()

                # 控制帧率
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            self.show_game_over()

    def show_game_over(self):
        """显示游戏结束画面"""
        self.clear_screen()

        game_over_text = "游戏结束!"
        final_score = f"最终得分: {self.score}"
        stats = f"正确输入: {self.matched_words} | 错过: {self.missed_words}"
        if (self.matched_words + self.missed_words) > 0:
            accuracy = f"准确率: {(self.matched_words / (self.matched_words + self.missed_words) * 100):.1f}%"
        else:
            accuracy = "准确率: N/A"

        print()
        print(Fore.RED + Style.BRIGHT + game_over_text.center(self.screen_width))
        print()
        print(Fore.CYAN + final_score.center(self.screen_width))
        print(Fore.WHITE + stats.center(self.screen_width))
        print(Fore.WHITE + accuracy.center(self.screen_width))
        print()
        print(Fore.WHITE + "按任意键退出...".center(self.screen_width))

        if IS_WINDOWS:
            while True:
                if msvcrt.kbhit():
                    msvcrt.getch()
                    break
                time.sleep(0.05)
        else:
            input()


def main():
    """主函数"""
    game = TypingGame()
    game.run()

if __name__ == "__main__":
    main()
