import msvcrt
import random
import os

class TicTacToe:
    def __init__(self):
        self.board = [' ' for _ in range(9)]
        self.current_player = 'X'
        self.game_mode = None
        self.winner = None
    
    def display_board(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n井字棋游戏 (Tic Tac Toe)")
        print("=" * 20)
        print(f"\n {self.board[6]} | {self.board[7]} | {self.board[8]} ")
        print("---+---+---")
        print(f" {self.board[3]} | {self.board[4]} | {self.board[5]} ")
        print("---+---+---")
        print(f" {self.board[0]} | {self.board[1]} | {self.board[2]} ")
        print("\n位置编号 (小键盘布局):")
        print(" 7 | 8 | 9 ")
        print("---+---+---")
        print(" 4 | 5 | 6 ")
        print("---+---+---")
        print(" 1 | 2 | 3 ")
        print("=" * 20)
    
    def check_winner(self):
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # 横向
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # 纵向
            [0, 4, 8], [2, 4, 6]               # 对角线
        ]
        
        for combo in winning_combinations:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != ' ':
                self.winner = self.board[combo[0]]
                return True
        return False
    
    def check_draw(self):
        return ' ' not in self.board
    
    def is_valid_move(self, position):
        return 1 <= position <= 9 and self.board[position - 1] == ' '
    
    def make_move(self, position):
        if self.is_valid_move(position):
            self.board[position - 1] = self.current_player
            return True
        return False
    
    def switch_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'
    
    def get_player_move(self):
        while True:
            try:
                print(f"玩家 {self.current_player}，请选择位置 (1-9, Q:退出本局): ")
                position = msvcrt.getch()
                if position in (b'Q', b'q'):
                    return 'Q'
                else:
                    position = int(position.decode('utf-8'))
                    if self.make_move(position):
                        break
                    else:
                        print("无效的位置，请重新选择！")
            except ValueError:
                print("请输入1-9之间的数字！(Q:退出本局)")
    
    def get_ai_move(self):
        print("AI正在思考...")
        
        # 小键盘布局的位置映射
        # 1->0, 2->1, 3->2, 4->3, 5->4, 6->5, 7->6, 8->7, 9->8
        
        # 简单的AI策略
        # 1. 检查是否能赢
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'O'
                if self.check_winner():
                    self.winner = None
                    return i + 1
                self.board[i] = ' '
        
        # 2. 检查是否需要阻止玩家赢
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'X'
                if self.check_winner():
                    self.board[i] = ' '
                    return i + 1
                self.board[i] = ' '
        
        # 3. 占据中心 (位置5)
        if self.board[4] == ' ':
            return 5
        
        # 4. 占据角落 (位置1, 3, 7, 9)
        corners = [0, 2, 6, 8]
        available_corners = [i + 1 for i in corners if self.board[i] == ' ']
        if available_corners:
            return random.choice(available_corners)
        
        # 5. 随机选择
        available_moves = [i + 1 for i in range(9) if self.board[i] == ' ']
        return random.choice(available_moves)
    
    def play_game(self):
        self.display_board()
        
        while True:
            is_quit = None
            if self.game_mode == '1':  # 人机对战
                if self.current_player == 'X':
                    is_quit = self.get_player_move()
                else:
                    position = self.get_ai_move()
                    self.make_move(position)
                    print(f"AI选择了位置 {position}")
            else:  # 两人对弈
                is_quit = self.get_player_move()
            
            if is_quit == 'Q':
                print("本局结束！")
                break
        
            self.display_board()
            
            if self.check_winner():
                print(f"\n恭喜！玩家 {self.winner} 获胜！")
                break
            
            if self.check_draw():
                print("\n游戏平局！")
                break
            
            self.switch_player()
    
    def reset_game(self):
        self.board = [' ' for _ in range(9)]
        self.current_player = 'X'
        self.winner = None

def main():
    game = TicTacToe()
    
    while True:
        print("\n" + "=" * 30)
        print("   井字棋游戏 (Tic Tac Toe)   ")
        print("=" * 30)
        print("1. 人机对战")
        print("2. 两人对弈")
        print("3/Q. 退出游戏")
        print("=" * 30)
        
        print("请选择游戏模式 (1,2,3,Q): ")
        choice = msvcrt.getch()
        if choice in (b'1', b'2', b'3', b'q', b'Q'):
            choice = choice.decode('utf-8')
            if choice in ('3', 'q', 'Q'):
                print("感谢游玩，再见！")
                break
            
            if choice in ['1', '2']:
                game.game_mode = choice
                game.reset_game()
                game.play_game()
            
            while True:
                print("\n是否再来一局？(y/Enter 或 n/q/Esc): ")
                key = msvcrt.getch()
                if key in (b'y', b'Y', b'\r'):
                    game.reset_game()
                    game.play_game()
                elif key in (b'n', b'N', b'q', b'Q', b'\x1b'):
                    break
                else:
                    print("请输入 y/Enter 或 n/q/Esc！")
        else:
            print("无效的选择，请重新输入！")

if __name__ == "__main__":
    main()