import random
import os
import sys
import msvcrt
from dataclasses import dataclass


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_hit = False
        self.revealed = False
        self.flagged = False
        self.question = False
        self.neighbor_mines = 0

@dataclass
class Color:
    RESET = '\033[0m'

    BLACK = '\033[40m'
    RED = '\033[41m'
    GREEN = '\033[42m'
    YELLOW = '\033[43m'
    BLUE = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN = '\033[46m'
    DARK_WHITE = '\033[47m'
    
    BRIGHT_BLACK = '\033[100m'
    BRIGHT_RED = '\033[101m'
    BRIGHT_GREEN = '\033[102m'
    BRIGHT_YELLOW = '\033[103m'
    BRIGHT_BLUE = '\033[104m'
    BRIGHT_MAGENTA = '\033[105m'
    BRIGHT_CYAN = '\033[106m'
    WHITE = '\033[107m'

class Game:
    def __init__(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.mine_positions = []
        self.board = [[Cell(row, col) for col in range(cols)] for row in range(rows)]
        self.revealed_cells = 0
        self.flagged_cells = 0
        self.first_click = True
        self.assist = False
        self.game_over = False
    
    def start(self):
        pass  # 地雷会在第一次点击时放置
    
    def place_mines(self, first_row, first_col):
        # 确保第一次点击的位置不是地雷
        safe_positions = [(first_row, first_col)] + self.get_neighbors(first_row, first_col)
        
        while len(self.mine_positions) < self.mines:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            if (row, col) not in self.mine_positions and (row, col) not in safe_positions:
                self.mine_positions.append((row, col))
                self.board[row][col].is_mine = True
        
        # 计算每个格子周围的地雷数
        for row in range(self.rows):
            for col in range(self.cols):
                if not self.board[row][col].is_mine:
                    neighbors = self.get_neighbors(row, col)
                    mine_count = sum(1 for r, c in neighbors if self.board[r][c].is_mine)
                    self.board[row][col].neighbor_mines = mine_count
    
    def get_neighbors(self, row, col):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    neighbors.append((r, c))
        return neighbors
    
    def reveal_cell(self, row, col):
        cell = self.board[row][col]
        
        if cell.revealed or cell.flagged or cell.question:
            return False
        
        # 第一次点击时放置地雷
        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False
        
        if cell.is_mine:
            cell.is_hit = True
            self.mines -= 1
            return True  # 踩中地雷
        
        # 递归揭示空白格子
        self._reveal_recursive(row, col)
        return False
    
    def _reveal_recursive(self, row, col):
        cell = self.board[row][col]
        
        if cell.revealed or cell.flagged or cell.question:
            return
        
        cell.revealed = True
        self.revealed_cells += 1
        
        if cell.neighbor_mines == 0:
            for r, c in self.get_neighbors(row, col):
                self._reveal_recursive(r, c)
    
    def reveal_neighbors(self, row, col):
        cell = self.board[row][col]
        if cell.revealed and cell.neighbor_mines > 0:
            neighbors = self.get_neighbors(row, col)
            flagged_neighbors = sum(1 for r, c in neighbors if self.board[r][c].flagged)
            if flagged_neighbors == cell.neighbor_mines:
                # 所有周围的地雷已经标记，揭开所有邻居
                for r, c in neighbors:
                    result = self.reveal_cell(r, c)
                    if result:
                        return result # 点到雷了,说明之前的标记有误
        return False


    def toggle_flag(self, row, col):
        cell = self.board[row][col]
        if cell.revealed:
            return
        if cell.flagged:
            cell.flagged = False
            self.flagged_cells -= 1
        else:
            cell.flagged = True
            cell.question = False
            self.flagged_cells += 1
    
    def toggle_question(self, row, col):
        cell = self.board[row][col]
        if cell.revealed:
            return
        if cell.question:
            cell.question = False
        else:
            cell.question = True
            cell.flagged = False
    
    def check_win(self):
        return self.revealed_cells == self.rows * self.cols - self.mines
    
    def reveal_all_mines(self):
        for pos in self.mine_positions:
            row, col = pos
            if not self.board[row][col].flagged:
                self.board[row][col].revealed = True
                self.board[row][col].question = False


    
    def display_board(self, current_row, current_col):
        print("===== 扫雷游戏 ====")
        print(f"剩余雷数目: {self.mines - self.flagged_cells}")
        print("    ", end="")
        for col in range(self.cols):
            print(((Color.BLUE if col%2==0 else Color.BRIGHT_BLUE) if col != current_col else Color.BRIGHT_YELLOW) + f" {col:<2}", end="")
        print()
        
        print(Color.BLUE + "   -" + "---" * self.cols + Color.RESET)

        if self.assist:
            neighbors = self.get_neighbors(current_row, current_col)
        
        for row in range(self.rows):
            print(((Color.BLUE if row%2==1 else Color.BRIGHT_BLUE) if row != current_row else Color.BRIGHT_YELLOW) + f"{row:2} |" + Color.RESET, end="")
            for col in range(self.cols):
                cell = self.board[row][col]
                
                if cell.revealed:
                    if cell.is_mine:
                        cell_color = Color.RED
                        cell_content ='✷' if self.game_over and cell.is_hit else '✇' # exploded mine and unflagged ones
                    elif cell.neighbor_mines == 0:
                        cell_color = Color.DARK_WHITE
                        cell_content = ' '
                    else:
                        cell_color = Color.RESET
                        cell_content =cell.neighbor_mines
                elif cell.flagged:
                    cell_color = Color.RED
                    cell_content = '✘' if self.game_over and (not cell.is_mine) else '⚐' # wrong flag and correct flag
                elif cell.question:
                    cell_color = Color.RESET
                    cell_content = '?'
                else:
                    cell_color = Color.RESET
                    cell_content = ' '
                
                if self.assist and (row, col) in neighbors:
                    cell_color = Color.BRIGHT_BLACK if cell.revealed and cell.neighbor_mines == 0 else Color.BRIGHT_MAGENTA

                if row == current_row and col == current_col:
                    cell_color = Color.MAGENTA # overwrite above default color
                    print(cell_color + '[', end='')
                else:
                    print(cell_color + ' ', end="")
                
                
                print(cell_content, end='')
                
                if row == current_row and col == current_col:
                    print(Color.MAGENTA + "]" + Color.RESET, end="")
                else:
                    print(cell_color + " " + Color.RESET, end="")
            print()


def clear_screen():
    os.system('cls')

def menu_selection():
    rows = 9
    cols = 9
    mines = 10
    while True:
        clear_screen()
        print("===== 扫雷游戏 ====")
        print("请选择难度级别：")
        print("1. 初级 (9x9, 10个地雷)")
        print("2. 中级 (16x16, 40个地雷)")
        print("3. 高级 (30x16, 99个地雷)")
        print("4. 自定义")
        print("ESC. 退出")
        
        key = msvcrt.getch()
        if key == b'\x1b':
            sys.exit()
        else:
            key = key.decode('utf-8')
        if key == '1':
            break
        elif key == '2':
            rows = 16
            cols = 16
            mines = 40
            break
        elif key == '3':
            rows = 16
            cols = 30
            mines = 99
            break
        elif key == '4':
            try:
                clear_screen()
                rows = int(input("请输入行数: "))
                cols = int(input("请输入列数: "))
                mines = int(input("请输入地雷数: "))
                if mines >= rows * cols:
                    print("地雷数不能超过格子总数！")
                    continue
                break
            except ValueError:
                print("输入无效，请重新输入！")
                continue
    return rows, cols, mines

def main():
    while True:
        rows, cols, mines = menu_selection()
        game = Game(rows, cols, mines)
        game.start()
    
        current_row, current_col = random.randint(0, rows - 1), random.randint(0, cols - 1)
        game_over = False
    
        while not game_over:
            clear_screen()
            game.display_board(current_row, current_col)
            print("\n操作说明：")
            print("方向键：移动光标")
            print("R键：揭开格子")
            print("F键：标记地雷")
            print("V键：问号标记")
            print(f"A键：辅助模式({'关' if game.assist else '开'})")
            print("ESC：退出游戏")
            
            key = msvcrt.getch()
            if key == b'\xe0':
                key = msvcrt.getch()

            if key == b'\x1b':  # ESC键
                break
            elif key == b'H':  # 上箭头
                current_row = max(0, current_row - 1)
            elif key == b'P':  # 下箭头
                current_row = min(game.rows - 1, current_row + 1)
            elif key == b'K':  # 左箭头
                current_col = max(0, current_col - 1)
            elif key == b'M':  # 右箭头
                current_col = min(game.cols - 1, current_col + 1)
            elif key == b'f' or key == b'F':
                game.toggle_flag(current_row, current_col)
            elif key == b'v' or key == b'V':
                game.toggle_question(current_row, current_col)
            elif key == b'r' or key == b'R':
                cell = game.board[current_row][current_col]
                if not cell.revealed:
                    if game.reveal_cell(current_row, current_col):
                        game.game_over = game_over = True
                        game.reveal_all_mines()
                        clear_screen()
                        game.display_board(-1, -1)  # 显示最终状态
                        print("\n游戏结束！你踩中了地雷！")
                else:
                    if game.reveal_neighbors(current_row, current_col):
                        game.game_over = game_over = True
                        game.reveal_all_mines()
                        clear_screen()
                        game.display_board(-1, -1)  # 显示最终状态
                        print("\n游戏结束！你踩中了地雷！")
                if game.check_win():
                    game.game_over = game_over = True
                    clear_screen()
                    game.reveal_all_mines()
                    game.display_board(-1, -1)  # 显示最终状态
                    print("\n恭喜你！成功扫完所有地雷！")
                if game_over:
                    print("[回车]重玩, 按任意键退出...")
                    key = msvcrt.getch()
                    if key == b'\r':
                        break
                    else:
                        return
            elif key == b'a' or key == b'A':
                game.assist = not game.assist

if __name__ == "__main__":
    main()