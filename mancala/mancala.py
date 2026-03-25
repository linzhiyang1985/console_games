import os
import random

# 颜色代码
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class MancalaGame:
    def __init__(self):
        # 初始化棋盘 (逆时针方向): [坑1-6 (下标0-5), 玩家1存储区(下标6), 坑7-12 (下标7-12), AI/玩家2存储区(下标13)] 
        self.board = [4] * 6 + [0] + [4] * 6 + [0]
        self.current_player = 1  # 1或2
        self.is_extra_turn = False
    
    def print_board(self, mode="1"):
        """打印游戏棋盘"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        p1_name = "玩家" if mode == "1" else "玩家1"
        p2_name = "AI" if mode == "1" else "玩家2"
        
        print(f"{GREEN}==============================={RESET}")
        print(f"{GREEN}        MANCALA 游戏{RESET}")
        print(f"{GREEN}==============================={RESET}")
        
        # 玩家2的存储区
        print(f"{YELLOW if self.current_player == 2 else GREEN}{p2_name}: {BLUE}{self.board[13]}{RESET}")
        
        # 玩家2的坑序号
        print(f"{YELLOW if self.current_player == 2 else GREEN}{' ' * 4}{' ' * 4}", end="") #前置空格
        for i in range(12, 6, -1):
            print(f" {YELLOW if self.current_player == 2 else GREEN}{i-6}{RESET} ", end=" ")
        print()
        
        # 玩家2的坑
        print(f"{YELLOW if self.current_player == 2 else GREEN}{' ' * 4}{' ' * 4}", end="") #前置空格
        for i in range(12, 6, -1):
            stones = self.board[i]
            if stones > 0:
                print(f"{YELLOW if self.current_player == 2 else GREEN}[{BLUE}{stones}{YELLOW if self.current_player == 2 else GREEN}]", end=" ")
            else:
                print(f"{YELLOW if self.current_player == 2 else GREEN}[ ]", end=" ")
        print()
        
        # 中间分隔线, 玩家2的存储区在左, 玩家1的存储区在右
        print(f"{YELLOW if self.current_player == 2 else GREEN}{' ' * 2}[{BLUE}{self.board[13]}{YELLOW if self.current_player == 2 else GREEN}]"+ \
              f"{GREEN}{'-' * 2}{'-' * 23}{'-' * 4}" \
              f"{YELLOW if self.current_player == 1 else GREEN}[{BLUE}{self.board[6]}{YELLOW if self.current_player == 1 else GREEN}] {RESET}")
        
        # 玩家1的坑
        print(f"{YELLOW if self.current_player == 1 else GREEN}{' ' * 4}{' ' * 4}", end="") #前置空格
        for i in range(0, 6):
            stones = self.board[i]
            if stones > 0:
                print(f"{YELLOW if self.current_player == 1 else GREEN}[{BLUE}{stones}{YELLOW if self.current_player == 1 else GREEN}]", end=" ")
            else:
                print(f"{YELLOW if self.current_player == 1 else GREEN}[ ]", end=" ")
        print()
        
        # 玩家1的坑序号
        print(f"{YELLOW if self.current_player == 1 else GREEN}{' ' * 4}{' ' * 4}", end="") #前置空格
        for i in range(0, 6):
            print(f" {YELLOW if self.current_player == 1 else GREEN}{i+1}{RESET} ", end=" ")
        print()
        
        # 玩家1的存储区
        print(f"{YELLOW if self.current_player == 1 else GREEN}{p1_name}: {BLUE}{self.board[6]}{RESET}")
        
        print(f"{GREEN}==============================={RESET}")
        if mode == "1":
            current_name = "玩家" if self.current_player == 1 else "AI"
        else:
            current_name = "玩家1" if self.current_player == 1 else "玩家2"
        print(f"当前玩家: {current_name}" + (" (额外回合)" if self.is_extra_turn else ""))
    
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
            self.is_extra_turn = False
        else:
            # 当前玩家再玩一轮
            self.is_extra_turn = True
    
    def is_game_over(self):
        """检查游戏是否结束"""
        p1_pits_empty = all(self.board[i] == 0 for i in range(0, 6))
        p2_pits_empty = all(self.board[i] == 0 for i in range(7, 13))
        return p1_pits_empty or p2_pits_empty
    
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
    
    def get_winner(self, mode="1"):
        """获取获胜者"""
        if mode == "1":
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
    game = MancalaGame()
    
    # 选择游戏模式
    print("选择游戏模式：")
    print("1. 人机对战")
    print("2. 双人对战")
    mode = input("请输入选择 (1/2): ")
    
    while not game.is_game_over():
        game.print_board(mode)
        
        if mode == "2" or (mode == "1" and game.current_player == 1):
            # 玩家输入
            while True:
                try:
                    if mode == "1":
                        pit = int(input("玩家，请选择要移动的坑 (1-6): ")) - 1 # 转换为内部索引 (0-5)
                    elif game.current_player == 1:
                        pit = int(input("玩家1，请选择要移动的坑 (1-6): ")) - 1 # 转换为内部索引 (0-5)
                    else:
                        pit = int(input("玩家2，请选择要移动的坑 (1-6): ")) + 6  # 转换为内部索引 (7-12)

                    if game.is_valid_move(pit):
                        game.make_move(pit)
                        break
                    else:
                        print("无效的移动，请重新选择！")
                except ValueError:
                    print("请输入有效的数字！")
        else:
            # AI 移动
            print("AI 正在思考...")
            import time
            time.sleep(1)
            ai_pit = game.ai_move()
            print(f"AI 选择了坑 {ai_pit - 6}")
            game.make_move(ai_pit)
    
    # 游戏结束
    game.end_game()
    game.print_board(mode)
    winner = game.get_winner(mode)
    if mode == "1":
        if winner == "平局":
            print(f"游戏结束！平局！")
            print(f"你的得分: {game.board[6]}")
            print(f"AI得分: {game.board[13]}")
        else:
            print(f"游戏结束！{'你' if winner == '玩家1' else 'AI'} 获胜！")
            print(f"你的得分: {game.board[6]}")
            print(f"AI得分: {game.board[13]}")
    else:
        print(f"游戏结束！{winner} 获胜！")
        print(f"玩家1得分: {game.board[6]}")
        print(f"玩家2得分: {game.board[13]}")

if __name__ == "__main__":
    main()