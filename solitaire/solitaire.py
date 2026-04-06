import random
import os
import re


# 牌的定义
SUITS = ['♠', '♥', '♣', '♦']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

DISPLAY_RANKS = ['𝐀', '𝟮', '𝟯', '𝟰', '𝟱', '𝟲', '𝟳', '𝟴', '𝟵', '𝟭𝟬', '𝐉', '𝐐', '𝐊']

BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


class Card:
    face_down_rows = [
        "╭───────╮",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "╰───────╯"
    ]

    face_up_temp = [
        '╭───────╮',
        '│♠KK    │',
        '│       │',
        '│   ♠   │',
        '│       │',
        '│    KK♠│',
        '╰───────╯',
    ]

    def __init__(self, suit, rank):
        self.suit = suit  # 花色：♠, ♥, ♣, ♦
        self.rank = rank  # 点数：A, 2-10, J, Q, K
        self.face_up = False  # 是否正面朝上
        self.dot_matrix = None  # 卡片的点阵表示
        self.is_selected = False
    
    def __str__(self):
        if not self.face_up:
            return '\n'.join(self.face_down_rows)
        else:
            return '\n'.join(self.get_dot_matrix())
    
    def set_selected(self, is_selected: bool):
        self.is_selected = is_selected

    def get_dot_matrix(self):
        if self.dot_matrix is not None:
            return self.dot_matrix
        ## 只生成一次
        if len(self.rank) == 1:
            rank_left = DISPLAY_RANKS[RANKS.index(self.rank)] + ' '
            rank_right = ' ' + DISPLAY_RANKS[RANKS.index(self.rank)]
        else:
            rank_left = rank_right = DISPLAY_RANKS[RANKS.index(self.rank)]
        suit_center = ' ' + self.suit + ' '
        
        card = []
        for row in self.face_up_temp:
            card.append(row.replace('♠KK', self.suit + rank_left).replace('KK♠', rank_right + self.suit).replace(' ♠ ', suit_center))
        self.dot_matrix = card
        return self.dot_matrix

    def render_card_row(self, card_row_str):
        rendered_str = ''
        char_color = RED if ('♥' in card_row_str or '♦' in card_row_str) else BLUE
        for ch in card_row_str:
            if ch in ('╭', '─', '╮', '│', '╰', '╯'):
                rendered_str += (YELLOW if self.is_selected else GREEN) + ch + RESET
            elif ch in ('♠', '♣', '♦', '♥', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '1', '0', 'J', 'Q', 'K'):
                rendered_str += char_color + ch + RESET
            elif ch == ' ':
                rendered_str += ' '
            else:
                rendered_str += ch
        return rendered_str
    
    def get_rank_value(self):
        if self.rank == 'A':
            return 1
        elif self.rank in ['J', 'Q', 'K']:
            return 11 + ['J', 'Q', 'K'].index(self.rank)
        else:
            return int(self.rank)
    
    def is_red(self):
        return self.suit in ['♥', '♦']
    
    def is_black(self):
        return self.suit in ['♠', '♣']

class Pile:
    def __init__(self):
        self.cards: list[Card] = []
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def remove_card(self):
        if self.cards:
            return self.cards.pop()
        return None
    
    def get_top_card(self):
        if self.cards:
            return self.cards[-1]
        return None
    
    def size(self):
        return len(self.cards)
    
    def is_empty(self):
        return len(self.cards) == 0
    
    def show_cards(self, direction='horizontal', compact=False):
        all_cards = []
        if direction == 'horizontal':
            for r in range(7): # each card span 7 rows
                concated_row = ''
                size = len(self.cards)
                for index, card in enumerate(self.cards):
                    arr = card.get_dot_matrix().copy()
                    if compact and index < size - 1:
                        for i in range(len(arr)):
                            if card.rank == '10':
                                arr[i] = arr[i][:4]
                            else:
                                arr[i] = arr[i][:3]
                    concated_row += card.render_card_row(arr[r]) + ('  ' if not compact else '')
                all_cards.append(concated_row)
        else:
            pile_size = self.size()
            for index, card in enumerate(self.cards):
                arr = card.get_dot_matrix()
                if index == pile_size - 1:
                    # last card
                    if card.face_up:
                        all_cards.extend([card.render_card_row(row) for row in arr])
                    else:
                        all_cards.extend([card.render_card_row(row) for row in Card.face_down_rows])
                else:
                    if card.face_up:
                        all_cards.extend([card.render_card_row(row) for row in arr[:2]])
                    else:
                        all_cards.extend([card.render_card_row(row) for row in [
                            "╭───────╮",
                            "│░░░░░░░│"
                        ]])
        return all_cards

class Solitaire:
    def __init__(self, draw_count=1):
        self.draw_count = draw_count  # 翻牌数量：1或3
        self.stock = Pile()  # 牌叠
        self.waste = Pile()  # 废牌堆
        self.foundations = [Pile() for _ in range(4)]  # 四个 foundation
        self.tableaus = [Pile() for _ in range(7)]  # 七个 tableau
        self.setup_game()
    
    def setup_game(self):
        # 创建一副完整的牌
        deck = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        
        # 洗牌
        random.shuffle(deck)
        
        # 初始化 tableau
        for i in range(7):
            for j in range(i + 1):
                card = deck.pop()
                if j == i:  # 最后一张牌正面朝上
                    card.face_up = True
                self.tableaus[i].add_card(card)
        
        # 剩余的牌放入牌叠
        for card in deck:
            self.stock.add_card(card)
    
    def draw_cards(self):
        if self.stock.is_empty():
            # 牌叠空了，将废牌堆倒回牌叠
            while not self.waste.is_empty():
                card = self.waste.remove_card()
                card.face_up = False
                self.stock.add_card(card)
        
        # 从牌叠翻牌到废牌堆
        for _ in range(self.draw_count):
            if not self.stock.is_empty():
                card = self.stock.remove_card()
                card.face_up = True
                self.waste.add_card(card)
    
    def is_valid_move_to_tableau(self, card, tableau):
        if tableau.is_empty():
            return card.rank == 'K'  # 空 tableau 只能放 K
        
        top_card = tableau.get_top_card()
        return (card.is_red() != top_card.is_red() and 
                (self._get_rank_order(card.rank) == self._get_rank_order(top_card.rank) - 1))
    
    def is_valid_move_to_foundation(self, card, foundation):
        if foundation.is_empty():
            return card.rank == 'A'  # 空 foundation 只能放 A
        
        top_card = foundation.get_top_card()
        return (card.suit == top_card.suit and 
                (self._get_rank_order(card.rank) == self._get_rank_order(top_card.rank) + 1))
    
    def _get_rank_order(self, rank):
        order = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
        return order[rank]
    
    def move_card(self, from_pile, to_pile):
        if from_pile.is_empty():
            return False
        
        card = from_pile.get_top_card()
        
        # 检查移动是否合法
        if to_pile in self.tableaus:
            if not self.is_valid_move_to_tableau(card, to_pile):
                return False
        elif to_pile in self.foundations:
            if not self.is_valid_move_to_foundation(card, to_pile):
                return False
        
        # 执行移动
        from_pile.remove_card()
        to_pile.add_card(card)
        
        # 如果是从 tableau 移动，检查新的顶部牌是否需要翻面
        if from_pile in self.tableaus and not from_pile.is_empty():
            top_card = from_pile.get_top_card()
            if not top_card.face_up:
                top_card.face_up = True
        
        return True
    
    def check_win(self):
        # 检查所有 foundation 是否都有13张牌
        for foundation in self.foundations:
            if foundation.size() != 13:
                return False
        return True
    
    def clear(self):
        os.system('cls')

    def display_foundations(self):
        # 显示 foundation
        foundation_lines = []
        for i, foundation in enumerate(self.foundations):
            if foundation.is_empty():
                dummy_card = Card(SUITS[0], RANKS[0])
                foundation_lines.append(dummy_card.render_card_row("╭───────╮"))
                foundation_lines.append(dummy_card.render_card_row("│       │"))
                foundation_lines.append(dummy_card.render_card_row("│       │"))
                foundation_lines.append(dummy_card.render_card_row("│   {0}   │".format(i+1)))
                foundation_lines.append(dummy_card.render_card_row("│       │"))
                foundation_lines.append(dummy_card.render_card_row("│       │"))
                foundation_lines.append(dummy_card.render_card_row("╰───────╯"))
            else:
                card = foundation.get_top_card()
                foundation_lines.extend([card.render_card_row(row) for row in card.get_dot_matrix()])

        print("Foundations:")
        for i in range(7):
            for j in range(4):
                print(foundation_lines[i + j*7], end=" ")
            print()
    
    def display_stock_and_waste(self):
        # 显示牌叠和废牌堆
        stock_lines = []
        if not self.stock.is_empty():
            stock_lines = [
                    "╭──────╮   ",
                    "│╭──────╮  ",
                    "││╭───────╮",
                    "│││░░░░░░░│",
                    "│││░░░░░░░│",
                    "│││░░░░░░░│",
                    "╰││░░░░░░░│",
                    " ╰│░░░░░░░│",
                    "  ╰───────╯"
            ]
        else:
            stock_lines = [
                "",
                "╭───────╮",
                "│       │",
                "│       │",
                "│ Empty │",
                "│       │",
                "│       │",
                "╰───────╯",
                ""
            ]
        
        waste_lines = []
        if not self.waste.is_empty():
            temp_pile = Pile()
            for card in self.waste.cards[-1*self.draw_count:]:
                temp_pile.add_card(card)
            all_card_arr = temp_pile.show_cards(compact=True)
            waste_lines = [""]
            waste_lines.extend(all_card_arr)
            waste_lines.append("")
        else:
            waste_lines = [
                "",
                "╭───────╮",
                "│       │",
                "│       │",
                "│ Empty │",
                "│       │",
                "│       │",
                "╰───────╯",
                ""
            ]

        print("\nStock / Waste:")
        for i in range(9):
            print(stock_lines[i], end="  ")
            print(waste_lines[i])

    def display_tableaus(self):
        # 显示 tableau
        tableau_lines = []
        for pile_index, column_pile in enumerate(self.tableaus):
            col_arr = column_pile.show_cards(direction='vertical')
            for row_index, row in enumerate(col_arr):
                if len(tableau_lines) <= row_index:
                    new_row = ' ' * (9+2) * pile_index + row
                    tableau_lines.append(new_row)
                else:
                    # tableau_lines[row_index] += '  ' + row
                    
                    expect_preceeding_size = (9+2) * pile_index - 2
                    valid_display_char_size = len(re.sub(r'\x1b\[\d+m', '', tableau_lines[row_index]))
                    if valid_display_char_size < expect_preceeding_size:
                        tableau_lines[row_index] += ' ' * (expect_preceeding_size - valid_display_char_size)
                    tableau_lines[row_index] += '  ' + row

        print("\nTableaus:")
        for row in tableau_lines:
            print(row)

    def display_operation_tips(self):
        # 显示操作提示
        print("\n操作提示:")
        print("1. 输入 'd' 从牌叠抽牌")
        print("2. 输入 'm' 移动卡片")
        print("3. 输入 'q' 退出游戏")

    def display(self):
        # 清屏
        self.clear()

        # 打印所有内容
        self.display_foundations()
        self.display_stock_and_waste()
        self.display_tableaus()
        self.display_operation_tips()

    def play(self):
        while True:
            self.display()
            
            if self.check_win():
                print("恭喜你赢了！")
                break
            
            choice = input("请输入操作: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'd':
                self.draw_cards()
            elif choice == 'm':
                # 移动卡片
                print("\n移动卡片:")
                print("来源选项: s (stock), w (waste), t1-t7 (tableau 1-7)")
                print("目标选项: f1-f4 (foundation 1-4), t1-t7 (tableau 1-7)")
                
                source = input("请输入来源: ").strip().lower()
                target = input("请输入目标: ").strip().lower()
                
                # 确定来源牌堆
                from_pile = None
                if source == 's':
                    from_pile = self.stock
                elif source == 'w':
                    from_pile = self.waste
                elif source.startswith('t'):
                    try:
                        idx = int(source[1]) - 1
                        if 0 <= idx < 7:
                            from_pile = self.tableaus[idx]
                    except:
                        pass
                
                # 确定目标牌堆
                to_pile = None
                if target.startswith('f'):
                    try:
                        idx = int(target[1]) - 1
                        if 0 <= idx < 4:
                            to_pile = self.foundations[idx]
                    except:
                        pass
                elif target.startswith('t'):
                    try:
                        idx = int(target[1]) - 1
                        if 0 <= idx < 7:
                            to_pile = self.tableaus[idx]
                    except:
                        pass
                
                if from_pile and to_pile:
                    if self.move_card(from_pile, to_pile):
                        print("移动成功！")
                    else:
                        print("移动无效，请重试。")
                else:
                    print("输入无效，请重试。")
            else:
                print("输入无效，请重试。")

def main():
    print("欢迎来到纸牌游戏！")
    print("请选择翻牌模式:")
    print("1. 翻1张")
    print("2. 翻3张")
    
    while True:
        choice = input("请输入选项 (1/2): ").strip()
        if choice == '1':
            game = Solitaire(draw_count=1)
            break
        elif choice == '2':
            game = Solitaire(draw_count=3)
            break
        else:
            print("输入无效，请重试。")
    
    game.play()

if __name__ == "__main__":
    main()
