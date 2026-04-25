import random
import re
import os
import time
import msvcrt

DISPLAY_SUITS = {'S': '♠', 'H': '♥', 'C': '♣', 'D': '♦'}
DISPLAY_RANKS = {'A':'𝐀', '2':'𝟮', '3':'𝟯', '4':'𝟰', '5':'𝟱', '6':'𝟲',
                 '7':'𝟳', '8':'𝟴', '9':'𝟵', '10':'𝟭𝟬', 'J':'𝐉', 'Q':'𝐐', 'K':'𝐊'}
SUIT_ORDER = ['D', 'C', 'H', 'S']
RAND_ORDER = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


class Card:
    
    card_temp = [
        '╭───────╮',
        '│♠KK    │',
        '│       │',
        '│   ♠   │',
        '│       │',
        '│    KK♠│',
        '╰───────╯',
    ]

    face_down_card_temp = [
        "╭───────╮",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "│░░░░░░░│",
        "╰───────╯"
    ]
    
    def __init__(self, suit, rank):
        self.suit = suit  # 花色: 'S'=黑桃, 'H'=红桃, 'C'=梅花, 'D'=方块
        self.rank = rank  # 点数: '2'-'A'
        self.face_up = True  # 是否正面朝上
        self.dot_matrix = None  # 卡片的点阵表示
        
    def __repr__(self):
        return f"{DISPLAY_SUITS[self.suit]}{DISPLAY_RANKS[self.rank]}"
    
    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank
    
    def set_face_up(self, face_up: bool):
        self.face_up = face_up

    def get_suit(self):
        return self.suit
    
    def get_rank(self):
        return self.rank
    
    def get_rank_value(self):
        return RAND_ORDER.index(self.rank)
    
    def get_suit_value(self):
        return SUIT_ORDER.index(self.suit)

    def get_dot_matrix(self):
        if self.dot_matrix is not None:
            return self.dot_matrix
        ## 只生成一次
        if len(self.rank) == 1:
            rank_left = DISPLAY_RANKS[self.rank] + ' '
            rank_right = ' ' + DISPLAY_RANKS[self.rank]
        else:
            rank_left = rank_right = DISPLAY_RANKS[self.rank]
        suit_center = ' ' + DISPLAY_SUITS[self.suit] + ' '
        
        card = []
        for row in self.card_temp:
            card.append(row.replace('♠KK', DISPLAY_SUITS[self.suit] + rank_left).replace('KK♠', rank_right + DISPLAY_SUITS[self.suit]).replace(' ♠ ', suit_center))
        self.dot_matrix = card
        return self.dot_matrix

    @staticmethod
    def render_card_row(card_row_str):
        rendered_str = ''
        for ch in card_row_str:
            if ch in ('╭', '─', '╮', '│', '╰', '╯'):
                rendered_str += GREEN + ch + RESET
            elif ch in ('♠', '♣', '♦', '♥'):
                suit_color = RED if ch in ('♥', '♦') else BLUE
                rendered_str += suit_color + ch + RESET
            elif ch == ' ':
                rendered_str += ' '
            else:
                rendered_str += ch
        return rendered_str
    
class Pile:
    def __init__(self, cards: list[Card] = []):
        self.cards = cards
    
    def __repr__(self) -> str:
        self.sort_cards()
        return (', '.join([str(card) for card in self.cards]))
    
    def __iter__(self):
        return iter(self.cards)
    
    def __len__(self):
        return len(self.cards)

    def __getitem__(self, index):
        return self.cards[index]

    def add_card(self, card: Card):
        self.cards.append(card)
    
    def add_cards(self, cards: list[Card]):
        self.cards.extend(cards)
    
    def remove_card(self, card):
        self.cards.remove(card)
    
    def sort_cards(self):
        # 按花色和点数排序
        self.cards.sort(key=lambda card: (card.get_suit_value(), card.get_rank_value()))
    
    def set_all_face_up(self):
        for card in self.cards:
            card.set_face_up(True)
    
    def set_all_face_down(self):
        for card in self.cards:
            card.set_face_up(False)

    def show_cards(self, direction='horizontal', compact=False, reversed=False):
        all_cards = []
        if direction == 'horizontal':
            for r in range(7):
                concated_row = ''
                size = len(self.cards)
                if size == 1:
                    if self.cards[0].face_up:
                        all_cards.append(self.cards[0].get_dot_matrix()[r])
                    else:
                        all_cards.append(Card.face_down_card_temp[r])
                else:
                    for index, card in enumerate(self.cards):
                        if card.face_up:
                            arr = card.get_dot_matrix().copy()
                        else:
                            arr = Card.face_down_card_temp.copy()
                        if compact:
                            if index == 0 and not reversed:
                                for i in range(len(arr)):
                                    arr[i] = arr[i][:5]
                            if 0 < index < size - 1:
                                for i in range(len(arr)):
                                    if reversed:
                                        arr[i] = arr[i][-5:]
                                    else:
                                        arr[i] = arr[i][:5]
                            if index == size - 1 and reversed:
                                for i in range(len(arr)):
                                    arr[i] = arr[i][-5:]
                        concated_row += arr[r]
                    all_cards.append(concated_row)
        else:
            pile_size = len(self.cards)
            if pile_size == 1:
                if self.cards[0].face_up:
                    all_cards.extend(self.cards[0].get_dot_matrix().copy())
                else:
                    all_cards.extend(Card.face_down_card_temp)
            else:
                for index, card in enumerate(self.cards):
                    arr = card.get_dot_matrix().copy()
                    if index == pile_size - 1:
                        # last card
                        if not reversed:
                            if card.face_up:
                                all_cards.extend(arr)
                            else:
                                all_cards.extend(Card.face_down_card_temp)
                        else:
                            if card.face_up:
                                all_cards.extend(arr[-2:])
                            else:
                                all_cards.extend([
                                    "│░░░░░░░│",
                                    "╰───────╯"
                                ])
                    elif index == 0:
                        # first card
                        if not reversed:
                            if card.face_up:
                                all_cards.extend(arr[:2])
                            else:
                                all_cards.extend([
                                    "╭───────╮",
                                    "│░░░░░░░│"
                                ])
                        else:
                            if card.face_up:
                                all_cards.extend(arr)
                            else:
                                all_cards.extend(Card.face_down_card_temp)
                    else:
                        if not reversed:
                            if card.face_up:
                                all_cards.extend(arr[:2])
                            else:
                                all_cards.extend([
                                    "╭───────╮",
                                    "│░░░░░░░│"
                                ])
                        else:
                            if card.face_up:
                                all_cards.extend(arr[-2:])
                            else:
                                all_cards.extend([
                                    "│░░░░░░░│",
                                    "╰───────╯"
                                ])
        return all_cards
    
    @staticmethod
    def calculate_valid_display_char_size(row):
        return len(re.sub(r'\x1b\[\d+m', '', row))

class PigTailGame:
    def __init__(self):
        self.players = [Pile([]) for _ in range(2)] # store hand cards of each player
        self.deck = []
        self.current_player = 0
        self.card_pointer = 0
        self.draw_mode = 'deck' # 'deck' or 'hand'
        self.hand_pointer = -1
        self.center_pile = []
        self.need_help = True
        self.previous_suit = None
    
    def initialize_deck(self, animate=False):
        suits = ['D', 'C', 'H', 'S']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        for suit in suits:
            for rank in ranks:
                new_card = Card(suit, rank)
                self.deck.append(new_card)
                if animate:
                    self.clear()
                    self.display_deck()
                    time.sleep(0.2)
        
        # shuffle 5 times
        for _ in range(5):
            random.shuffle(self.deck)
            if animate:
                self.clear()
                self.display_deck()
                time.sleep(0.2)
                [card.set_face_up(False) for card in self.deck]
                self.clear()
                self.display_deck()
                time.sleep(0.2)
                [card.set_face_up(True) for card in self.deck]
        if animate:
            [card.set_face_up(False) for card in self.deck]
            self.display()

    def draw_card_from_deck(self, index):
        if index < 0 or index >= len(self.deck):
            return None
        card = self.deck.pop(index)
        if self.card_pointer < 0 or self.card_pointer >= len(self.deck):
            self.card_pointer = len(self.deck) - 1
        return card
    
    def card_pointer_move_backward(self):
        deck_size = len(self.deck)
        self.card_pointer = (self.card_pointer + deck_size - 1) % deck_size

    def card_pointer_move_forward(self):
        deck_size = len(self.deck)
        self.card_pointer = (self.card_pointer + 1) % deck_size
    
    def draw_card_from_hand(self, index):
        if index < 0 or index >= len(self.players[self.current_player]):
            return None
        card = self.players[self.current_player][index]
        self.players[self.current_player].remove_card(card)
        self.draw_mode = 'deck'
        return card
    
    def hand_pointer_move_backward(self):
        self.hand_pointer = (self.hand_pointer - 1) % len(self.players[self.current_player])
    
    def hand_pointer_move_forward(self):
        self.hand_pointer = (self.hand_pointer + 1) % len(self.players[self.current_player])

    def clear(self):
        os.system('cls')
    
    IS_WINDOWS = os.name == 'nt'
    def move_cursor(self, row: int, column: int):
        """移动光标到指定位置"""
        if self.IS_WINDOWS:
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
    
    def display_title_and_rule(self):
        print(GREEN + ' ' * 22 + "===== 猪尾巴纸牌游戏 =====" + RESET)
        print(GREEN + ' ' * 7 + "规则：抽牌比花色，花色相同则拿走所有牌，最后持牌少者获胜" + RESET)

    def display_deck(self):
        # 以环形摊开牌组,以供选择
        p_upper = Pile(self.deck[0:13])
        p_right = Pile(self.deck[13:26])
        p_lower = Pile(list(reversed(self.deck[26:39])))
        p_left = Pile(list(reversed(self.deck[39:52])))

        rows_upper = p_upper.show_cards(direction='horizontal', compact=True)
        rows_right = p_right.show_cards(direction='vertical', compact=True)
        rows_lower = p_lower.show_cards(direction='horizontal', compact=True, reversed=True)
        rows_left = p_left.show_cards(direction='vertical', compact=True, reversed=True)

        deck_row_index = 0
        temp_pile = Pile(self.center_pile[-8:]) # maximum show recent 8 cards
        center_card_arr = temp_pile.show_cards(direction='horizontal', compact=True)

        # 组织牌组显示
        deck_arr = []
        while deck_row_index < 35:
            if deck_row_index < 2:
                deck_arr.append(rows_upper.pop(0))
            elif deck_row_index < 7:
                row = rows_upper.pop(0)
                if len(rows_left) >= 33 - deck_row_index:
                    row_left_content = rows_left.pop(0)
                    row = row_left_content + row[len(row_left_content):]
                if rows_right:
                    row_right_content = rows_right.pop(0)
                    row = row[:-1*len(row_right_content)] + row_right_content
                deck_arr.append(row)
            elif deck_row_index < 28:
                if len(rows_left) >= 33 - deck_row_index:
                    row_left_content = rows_left.pop(0)
                else:
                    row_left_content = ' ' * 9
                if rows_right:
                    row_right_content = rows_right.pop(0)
                else:
                    row_right_content = ' ' * 9
                
                if deck_row_index == 8:
                    center_content = f'{len(self.center_pile)} cards on table'.center(51)
                elif deck_row_index > 8 and center_card_arr:
                    center_content = center_card_arr.pop(0).center(51)
                else:
                    center_content = ' ' * 51
                deck_arr.append(row_left_content + center_content + row_right_content)
            elif deck_row_index < 35:
                row = rows_lower.pop(0)
                row = f"{row:>69}"
                if rows_left and len(rows_left) >= 33 - deck_row_index:
                    row_left_content = rows_left.pop(0)
                    row = row_left_content + row[len(row_left_content):]
                if len(p_lower) == 0:
                    if rows_right:
                        row_right_content = rows_right.pop(0)
                        row = row[:-1*len(row_right_content)] + row_right_content
                deck_arr.append(row)
            deck_row_index += 1
        
        # 附加四周的pointer符号区域
        if self.deck:
            # calc suit symbol position
            ## upper
            suit_row = re.sub(r'[^-]', ' ', re.sub(r'(♠|♥|♣|♦)', '-', deck_arr[1]))
            suit_row = suit_row.replace('-', '#', -1)
            if 0<=self.card_pointer<13:
                card_segments = suit_row.split('#')
                pointer_index = self.card_pointer # [0..12] --> [0..12]
                card_segments[pointer_index] = card_segments[pointer_index] + '↓'
                suit_row = '#'.join(card_segments)
                suit_row = suit_row.replace('↓#', '↓')
            suit_row = suit_row.replace('#', ' ')
            deck_arr.insert(0, suit_row)
            
            ## right
            suit_row = re.sub(r'[^@]', ' ', re.sub(r'(♠|♥|♣|♦)', '@', ''.join([row[-8] for row in deck_arr])))
            if '@' in suit_row:
                # this one belongs to upper row
                first_index = suit_row.index('@')
                suit_row = suit_row[:first_index] + ' ' + suit_row[first_index+1:]
            while suit_row.count('@') > 13:
                # additional one belongs to lower row
                last_index = suit_row.rindex('@')
                suit_row = suit_row[:last_index] + ' ' + suit_row[last_index+1:]
            if 13<=self.card_pointer<26:
                card_segments = suit_row.split('@')
                segment_index = self.card_pointer -13 # [13..25] --> [0..12]
                card_segments[segment_index] = card_segments[segment_index] + '←'
                suit_row = '@'.join(card_segments)
                suit_row = suit_row.replace('←@', '←')
            suit_row = suit_row.replace('@', ' ')
            for row_index in range(len(deck_arr)):
                deck_arr[row_index] = deck_arr[row_index] + suit_row[row_index]

            ## lower
            suit_row = re.sub(r'[^-]', ' ', re.sub(r'(♠|♥|♣|♦)', '-', deck_arr[-2]))
            suit_row = suit_row.replace('-', '#', -1)
            if 26<=self.card_pointer<39:
                card_segments = suit_row.split('#')
                max_index = 26 + len(p_lower) - 1
                segment_index = max_index - self.card_pointer # [26..38] --> [12..0]
                card_segments[segment_index] = card_segments[segment_index] + '↑'
                suit_row = '#'.join(card_segments)
                suit_row = suit_row.replace('↑#', '↑')
            suit_row = suit_row.replace('#', ' ')
            deck_arr.append(suit_row)

            ## left
            suit_row = re.sub(r'[^$]', ' ', re.sub(r'(♠|♥|♣|♦)', '$', ''.join([row[7] for row in deck_arr])))
            if '$' in suit_row:
                last_index = suit_row.rindex('$')
                suit_row = suit_row[:last_index] + ' ' + suit_row[last_index+1:]
            if 39<=self.card_pointer<52:
                card_segments = suit_row.split('$')
                max_index = 39 + len(p_left) - 1
                segment_index = max_index - self.card_pointer # [39..51] --> [12..0]
                card_segments[segment_index] = card_segments[segment_index] + '→'
                suit_row = '$'.join(card_segments)
                suit_row = suit_row.replace('→$', '→').replace('$', ' ')
            suit_row = suit_row.replace('$', ' ')
            for row_index in range(len(deck_arr)):
                deck_arr[row_index] = suit_row[row_index] + deck_arr[row_index]

        # 正式打印
        for row in deck_arr:
            print(Card.render_card_row(row))

    def display_hand(self):
        print()
        player = self.players[self.current_player]
        if len(player) == 0:
            self.draw_mode = 'deck'
            print("当前玩家没有牌")
        else:
            print("选择出牌:", end='')
            cards = str(player).split(', ')
            prev_suit = None
            for index, card in enumerate(cards):
                if prev_suit != card[0]:
                    print()
                    prev_suit = card[0]
                card_row = Card.render_card_row(card)
                print(' ' + card_row + ' ' if self.hand_pointer != index else '[' + card_row + ']', end=' ')
            print()

    def display_player_stat(self):
        print()
        print(f"玩家 {self.current_player + 1} 的回合")
        player_counts = []
        for i, player in enumerate(self.players):
            count = len(player)
            player_counts.append(count)
            print(f"玩家 {i + 1} 的手牌数量: {count}: {Card.render_card_row(repr(player))}")
        return player_counts
    
    def display_controls(self):
        if self.need_help:
            print()
            print("按[回车]随机抽牌")
            print("或[方向键],[n/p]选牌, [空格]抽取指定的牌")
            print("按[x]切换抽牌模式 - 当前抽" + ("手牌" if self.draw_mode == 'hand' else "中心牌"))
            print("按[h]查看操作帮助")
            print("按[q]退出游戏")
            self.need_help = False
    
    def display(self):
        self.clear()
        self.display_title_and_rule()
        print()
        self.display_deck()
        if self.draw_mode == 'hand':
            self.display_hand()
        self.display_player_stat()
        self.display_controls()


    def get_user_input(self):
        accepted_keys_and_map = {
            b'K': 'left', b'M': 'right',
            b'H': 'up', b'P': 'down',
            b'n': 'next', b'p': 'prev',
            b'x': 'switch_mode', # switch choosing cards between hand cards and center cards
            b' ': 'draw_target',
            b'\r': 'draw_random',
            b'h': 'show_help',
            b'q': 'quit',
        }
        while True:
            key = None
            while key is None:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\xe0':
                        key = msvcrt.getch()
                        if key in accepted_keys_and_map:
                            cmd = accepted_keys_and_map[key]
                    elif key in accepted_keys_and_map:
                        cmd = accepted_keys_and_map[key]
                time.sleep(0.1)
            
            # process key
            if cmd in ('next', 'prev'):
                if cmd == 'next':
                    self.card_pointer_move_forward()
                elif cmd == 'prev':
                    self.card_pointer_move_backward()
                self.display()
            elif cmd in ('up', 'down', 'left', 'right'):
                if self.draw_mode == 'deck':
                    if (0<=self.card_pointer<13 and cmd == 'right') or \
                        (13<=self.card_pointer<26 and cmd == 'down') or \
                        (26<=self.card_pointer<39 and cmd == 'left') or \
                        (39<=self.card_pointer<52 and cmd == 'up'):
                        self.card_pointer_move_forward()
                    elif (0<=self.card_pointer<13 and cmd == 'left') or \
                        (13<=self.card_pointer<26 and cmd == 'up') or \
                        (26<=self.card_pointer<39 and cmd == 'right') or \
                        (39<=self.card_pointer<52 and cmd == 'down'):
                        self.card_pointer_move_backward()
                    self.display()
                else:
                    # hand mode
                    if cmd == 'left':
                        self.hand_pointer_move_backward()
                    elif cmd == 'right':
                        self.hand_pointer_move_forward()
                    elif cmd in ('up', 'down'):
                        all_suit_kinds = list(set([card.get_suit() for card in self.players[self.current_player]]))
                        all_suit_kinds.sort(key= lambda x: SUIT_ORDER.index(x))
                        current_card_suit = self.players[self.current_player][self.hand_pointer].get_suit()
                        target_suit = all_suit_kinds[(all_suit_kinds.index(current_card_suit) + len(all_suit_kinds) + (-1 if cmd == 'up' else 1)) % len(all_suit_kinds)]
                        for index, card in enumerate(self.players[self.current_player]):
                            if card.get_suit() == target_suit:
                                self.hand_pointer = index
                                break
                    self.display()
            else:
                if cmd == 'draw_target':
                    if self.draw_mode == 'deck':
                        return self.card_pointer
                    else:
                        return self.hand_pointer
                elif cmd == 'draw_random':
                    return random.randint(0, len(self.deck) - 1)
                elif cmd == 'switch_mode':
                    self.draw_mode = 'hand' if self.draw_mode == 'deck' else 'deck'
                    self.hand_pointer = 0
                    self.display()
                elif cmd == 'show_help':
                    self.need_help = True
                    self.display_controls()
                elif cmd == 'quit':
                    exit(0)
                else:
                    print("未知按键")

    def play_turn(self):
        self.display()
        
        draw_index = self.get_user_input()
        
        if self.draw_mode == 'deck':
            card = self.draw_card_from_deck(int(draw_index))
        else:
            card = self.draw_card_from_hand(int(draw_index))
        if not card:
            return False
        
        print(f"抽到的牌: {card}")
        current_suit = card.get_suit()
        
        self.center_pile.append(card)
        
        if self.previous_suit:
            if current_suit == self.previous_suit:
                print(f"花色相同！玩家 {self.current_player + 1} 拿走所有牌")
                self.players[self.current_player].add_cards(self.center_pile)
                self.center_pile = []
                self.previous_suit = None
            else:
                self.previous_suit = current_suit
        else:
            self.previous_suit = current_suit
        
        self.current_player = (self.current_player + 1) % len(self.players)
        return True
    
    def play_game(self):        
        while self.deck:
            self.display()
            if not self.play_turn():
                break
        self.display()
        self.end_game()
    
    
    def end_game(self):
        print()
        print("===== 游戏结束 =====")
        print(f"牌桌上剩 {len(self.center_pile)} 张牌")
        player_counts = [len(player) for player in self.players]
        print()
        # 牌少者胜
        if player_counts[0] > player_counts[1]:
            print(f"玩家 2 获胜！")
        elif player_counts[0] < player_counts[1]:
            print(f"玩家 1 获胜！")
        else:
            print(f"平局！玩家 1 和 2 手牌数量相同")

if __name__ == "__main__":
    game = PigTailGame()
    game.initialize_deck(animate=False)
    game.play_game()
