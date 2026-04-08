import random
import os
import re
import msvcrt
import sys
import time
import threading
from playsound3 import playsound


# 牌的定义
SUITS = ['♠', '♥', '♣', '♦']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

DISPLAY_RANKS = ['𝐀', '𝟮', '𝟯', '𝟰', '𝟱', '𝟲', '𝟳', '𝟴', '𝟵', '𝟭𝟬', '𝐉', '𝐐', '𝐊']

BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

class LoopPlayer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.sound_file = r'./sound/background.mid'
        self.sound_handle = None
        self.is_stop = False
        
    def run(self):
        self.sound_handle = playsound(self.sound_file, block=False)
        start_time = time.time()
        while not self.is_stop:
            if time.time() - start_time >= 260: # whole sound duration
                # loop the sound
                self.sound_handle.stop()
                self.sound_handle = playsound(self.sound_file, block=False)
                start_time = time.time()
            time.sleep(1)
        self.sound_handle.stop()
    
    def stop(self):
        self.is_stop = True

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
        return self.suit + self.rank
    
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
    
    def __str__(self):
        return '\n'.join(map(str, self.cards))
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def remove_card(self, card: Card=None):
        if self.cards:
            if card is None:
                return self.cards.pop()
            else:
                if card in self.cards:
                    self.cards.remove(card)
                    return card
        return None
    
    def remove_all(self):
        self.cards.clear()
    
    def size(self):
        return len(self.cards)
    
    def is_empty(self):
        return len(self.cards) == 0

    def get_top_card(self):
        if self.cards:
            return self.cards[-1]
        return None
    
    def get_top_continuous_cards(self):
        continuous_cards = []
        if self.cards:
            for card in reversed(self.cards):
                if not continuous_cards:
                    continuous_cards.append(card)
                    last_rank = card.get_rank_value()
                elif card.face_up and card.get_rank_value() == last_rank + 1:
                    continuous_cards.insert(0, card)
                    last_rank = card.get_rank_value()
                else:
                    break
        return continuous_cards

    def select_continuous(self):
        for card in self.get_top_continuous_cards():
            card.set_selected(True)

    def clear_selection(self):
        for card in self.cards:
            card.set_selected(False)
    
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
    empty_slot = [
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

    stock_deck = [
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

    def __init__(self, draw_count=1):
        self.need_help = True # 第一次打印屏幕默认显示提示信息
        self.draw_count = draw_count  # 翻牌数量：1或3
        self.stock = Pile()  # 牌叠
        self.drawn_from_stock = Pile() # 从牌叠翻出的牌
        self.waste = Pile()  # 废牌堆
        
        self.foundations = [Pile() for _ in range(4)]  # 四个 foundation
        self.tableaus = [Pile() for _ in range(7)]  # 七个 tableau
        self.setup_game()

    def setup_game(self):
        # 创建一副完整的牌
        rnd_suit = SUITS.copy()
        random.shuffle(rnd_suit)
        rnd_rank = RANKS.copy()
        random.shuffle(rnd_rank)
        deck = [Card(suit, rank) for suit in rnd_suit for rank in rnd_rank]
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
        # 先将用剩的牌放到废弃区
        if not self.drawn_from_stock.is_empty():
            # 保持牌的顺序
            for card in self.drawn_from_stock.cards:
                card.face_up = False
                self.waste.add_card(card)
            self.drawn_from_stock.remove_all()
        
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
                self.drawn_from_stock.add_card(card)
    
    def shuffle_stock(self):
        while not self.drawn_from_stock.is_empty():
            card = self.drawn_from_stock.remove_card()
            card.face_up = False
            self.stock.add_card(card)
        while not self.waste.is_empty():
            card = self.waste.remove_card()
            card.face_up = False
            self.stock.add_card(card)
        random.shuffle(self.stock.cards)

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
        
        is_valid = False
        
        if to_pile == self.foundations:
            top_card = from_pile.get_top_card()
            for foundation_pile in self.foundations:
                if self.is_valid_move_to_foundation(top_card, foundation_pile):
                    to_pile = foundation_pile
                    is_valid = True
                    break
            if not is_valid:
                return False
        
        if from_pile in self.tableaus and to_pile in self.tableaus:
            continuous_cards = from_pile.get_top_continuous_cards()
            for valid_index, card in enumerate(continuous_cards):
                if self.is_valid_move_to_tableau(card, to_pile):
                    # 从这张牌开始直到尾, 执行移动
                    for i in range(valid_index, len(continuous_cards)):
                        from_pile.remove_card(continuous_cards[i])
                        to_pile.add_card(continuous_cards[i])
                    is_valid = True
                    break
        else:
            card = from_pile.get_top_card()
            
            # 检查移动是否合法
            if to_pile in self.tableaus:
                if not self.is_valid_move_to_tableau(card, to_pile):
                    return False
            
            is_valid = True
            # 执行移动
            from_pile.remove_card()
            to_pile.add_card(card)
            card.set_selected(False)
        
        if is_valid:
            # 如果是从 tableau 移动，检查新的顶部牌是否需要翻面
            if from_pile in self.tableaus and not from_pile.is_empty():
                top_card = from_pile.get_top_card()
                if not top_card.face_up:
                    top_card.face_up = True

        return is_valid
    
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

        print("基础牌堆(f):")
        for i in range(7):
            for j in range(4):
                print(foundation_lines[i + j*7], end=" ")
            print()
    
    def display_stock_and_waste(self):
        # 显示牌叠和废牌堆
        stock_lines = []
        if not self.stock.is_empty():
            stock_lines = self.stock_deck
        else:
            stock_lines = self.empty_slot
        
        waste_lines = []
        if not self.drawn_from_stock.is_empty():
            temp_pile = Pile()
            for card in self.drawn_from_stock.cards:
                temp_pile.add_card(card)
            all_card_arr = temp_pile.show_cards(compact=True)
            waste_lines = [""]
            waste_lines.extend(all_card_arr)
            waste_lines.append("")
        else:
            waste_lines = self.empty_slot

        print("\n备用牌堆  ||  翻牌堆(w):")
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

        print("\n牌阵区:")
        # print index
        for i in range(7):
            print(" " * 4 + str(i+1) + " " * 4, end="  ")
        print()
        # print cards
        for row in tableau_lines:
            print(row)

    def display_operation_tips(self):
        # 显示操作提示
        print("\n操作提示:")
        print("0. 输入 'h' 显示此提示信息")
        print("1. 输入 'd','/','0' 从备用牌堆抽牌")
        print("2. 输入 's', '*' 备用牌堆重洗牌[相当于翻1张牌]")
        print("3. 输入 'w/8'(翻牌区), 'f/9'(基础牌堆), '1-7'(牌阵区) 移动纸牌")
        print("4. 输入 'x' 开始新游戏, 'q' 退出游戏")
        self.need_help = False

    def display(self):
        # 清屏
        self.clear()

        # 打印所有内容
        self.display_foundations()
        self.display_stock_and_waste()
        self.display_tableaus()
        if self.need_help:
            self.display_operation_tips()

    def get_user_input(self):
        accepted_keys_and_map = {
            b'h': 'help',
            b'd': 'draw', b'/': 'draw',
            b's': 'shuffle', b'*': 'shuffle',
            b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right',
            b'x': 'new', b'q': 'quit',
            b'm': 'move',
            b'1': '1', b'2': '2', b'3': '3', b'4': '4', b'5': '5', b'6': '6', b'7': '7',
            b'w': 'w', b'8': 'w', b'0': 'w',
            b'f': 'f', b'9': 'f',
        }
        key = None
        while key is None:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\xe0'):
                    # arrow keys
                    key = msvcrt.getch()
                if key in accepted_keys_and_map:
                    return accepted_keys_and_map[key]
                else:
                    key = None
                print("输入无效，请重试:", end="")

    def play(self):
        from_pile = None
        to_pile = None

        while True:
            self.display()
            
            if self.check_win():
                print(f"\n{RED}❉⊱•❉⊱• 恭喜你赢了! •⊰❉•⊰❉{RESET}")
                new_round = input("再玩一局(y/n)?")
                if new_round.lower() != 'y':
                    return False
                else:
                    return True
            
            print("请输入操作: ")
            choice = self.get_user_input()

            if choice == 'help':
                self.need_help = True
                continue
            if choice == 'quit':
                quit_confirm = input("确认退出游戏(y/n)?")
                if quit_confirm.lower() == 'y':
                    return False
            elif choice == 'new':
                new_round_confirm = input("确认重开一局(y/n)?")
                if new_round_confirm.lower() == 'y':
                    return True
                else:
                    continue
            elif choice == 'draw':
                self.draw_cards()
                from_pile = None
                to_pile = None
            elif choice == 'shuffle':
                self.shuffle_stock()
            elif choice in ('1', '2', '3', '4', '5', '6', '7', 'f', 'w'):
                # 移动卡片
                selected_pile = None
                if choice == 'w':
                    if from_pile is None:
                        if not self.drawn_from_stock.is_empty():
                            self.drawn_from_stock.get_top_card().set_selected(True)
                            selected_pile = self.drawn_from_stock
                            self.display()
                    else:
                        if from_pile == self.drawn_from_stock:
                            # unselect
                            self.drawn_from_stock.get_top_card().set_selected(False)
                            from_pile = None
                elif choice == 'f':
                    if from_pile is None:
                        for pile in self.foundations:
                            if not pile.is_empty():
                                selected_pile = pile
                                pile.get_top_card().set_selected(True)
                                break
                    elif from_pile is not None and from_pile in self.foundations:
                        # change to next non-empty foundation slot
                        search_index = (self.foundations.index(from_pile) + 1) % 4
                        for i in range(4):
                            if not self.foundations[search_index].is_empty():
                                from_pile.get_top_card().set_selected(False) # unselect previous one
                                from_pile = self.foundations[search_index] # change to new one
                                from_pile.get_top_card().set_selected(True) # highlight
                                break
                            else:
                                search_index = (search_index + 1) % 4
                    else:
                        # will assign to to_pile
                        selected_pile = self.foundations

                elif choice in ('1', '2', '3', '4', '5', '6', '7'):
                    selected_pile = self.tableaus[int(choice)-1]
                    selected_pile.select_continuous()
                    self.display()
                
                if selected_pile:           
                    if from_pile is None:
                        from_pile = selected_pile
                    else:
                        to_pile = selected_pile
                
                if from_pile and to_pile:
                    if from_pile != to_pile and self.move_card(from_pile, to_pile):
                        print("移动成功！")
                    else:
                        print("移动无效，请重试。")
                    
                    from_pile.clear_selection()
                    if isinstance(to_pile, Pile):
                        to_pile.clear_selection()
                    from_pile = None
                    to_pile = None
            else:
                print("输入无效，请重试。")

def main():
    print("欢迎来到纸牌游戏！")
    
    while True:
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
        
        new_game = game.play()
        if not new_game:
            print("感谢游玩纸牌游戏！再见!")
            break

if __name__ == "__main__":
    background_player = LoopPlayer()
    background_player.start()
    try:
        main()
    except Exception:
        print("游戏已中断。")
    finally:
        background_player.stop()
