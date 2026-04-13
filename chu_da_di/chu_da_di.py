import random
import re
import os

DISPLAY_SUITS = {'S': '♠', 'H': '♥', 'C': '♣', 'D': '♦'}
DISPLAY_RANKS = {'A':'𝐀', '2':'𝟮', '3':'𝟯', '4':'𝟰', '5':'𝟱', '6':'𝟲',
                 '7':'𝟳', '8':'𝟴', '9':'𝟵', '10':'𝟭𝟬', 'J':'𝐉', 'Q':'𝐐', 'K':'𝐊'}

BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# https://baijiahao.baidu.com/s?id=1835199996633113121
# https://mbd.baidu.com/newspage/data/dtlandingsuper?nid=dt_3988709418184650235

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
        self.face_up = False  # 是否正面朝上
        self.dot_matrix = None  # 卡片的点阵表示
        self.is_selected = False
        
    def __repr__(self):
        return f"{DISPLAY_SUITS[self.suit]}{DISPLAY_RANKS[self.rank]}"
    
    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank

    def set_selected(self, is_selected: bool):
        self.is_selected = is_selected
    
    def set_face_up(self, face_up: bool):
        self.face_up = face_up

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

    def render_card_row(self, card_row_str):
        rendered_str = ''
        suit_color = RED if ('♥' in card_row_str or '♦' in card_row_str) else BLUE
        for ch in card_row_str:
            if ch in ('╭', '─', '╮', '│', '╰', '╯'):
                rendered_str += (YELLOW if self.is_selected else GREEN) + ch + RESET
            elif ch in ('♠', '♣', '♦', '♥'): #'A', '2', '3', '4', '5', '6', '7', '8', '9', '1', '0', 'J', 'Q', 'K'
                rendered_str += suit_color + ch + RESET
            elif ch == ' ':
                rendered_str += ' '
            else:
                rendered_str += ch
        return rendered_str
    
    def get_rank_value(self):
        # 2最大，3最小
        rank_order = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
        return rank_order.index(self.rank)
    
    def get_suit_value(self):
        # 黑桃>红桃>梅花>方块
        suit_order = ['D', 'C', 'H', 'S']
        return suit_order.index(self.suit)

class Pile:
    def __init__(self):
        self.cards = []
    
    def __repr__(self) -> str:
        return (', '.join([str(card) for card in self.cards]))
    
    def __iter__(self):
        return iter(self.cards)
    
    def __len__(self):
        return len(self.cards)

    def __getitem__(self, index):
        return self.cards[index]

    def add_card(self, card: Card):
        self.cards.append(card)
    
    def sort_cards(self):
        # 按点数和花色排序
        self.cards.sort(key=lambda card: (card.get_rank_value(), card.get_suit_value()))
    
    def remove(self, card):
        self.cards.remove(card)
    
    def clear_cards(self):
        self.cards.clear()
    
    def refresh_cards(self, cards):
        self.clear_cards()
        for card in cards:
            self.add_card(card)
        self.sort_cards()

    def clear_selection(self):
        for card in self.cards:
            card.set_selected(False)

    def select_cards(self, selected_cards):
        for card in selected_cards:
            self.cards[self.cards.index(card)].set_selected(True)

    def get_selected_cards(self):
        return [card for card in self.cards if card.is_selected]
    
    def set_all_face_up(self):
        for card in self.cards:
            card.set_face_up(True)
    
    def set_all_face_down(self):
        for card in self.cards:
            card.set_face_up(False)


    def show_cards(self, direction='horizontal', compact=False):
        all_cards = []
        if direction == 'horizontal':
            for r in range(8): # each card span 7+1 rows, extract 1 row for selected cards to pop up
                concated_row = ''
                size = len(self.cards)
                for index, card in enumerate(self.cards):
                    if card.face_up:
                        arr = card.get_dot_matrix().copy()
                    else:
                        arr = Card.face_down_card_temp.copy()
                    if card.is_selected:
                        arr.append(' ' * 9)
                    else:
                        arr.insert(0, ' ' * 9)
                    if compact and index < size - 1:
                        for i in range(len(arr)):
                            if card.rank == '10':
                                arr[i] = arr[i][:4]
                            else:
                                arr[i] = arr[i][:3]
                    concated_row += card.render_card_row(arr[r]) ## + (' ' if not compact else '')
                all_cards.append(concated_row)
        else:
            pile_size = len(self.cards)
            for index, card in enumerate(self.cards):
                arr = card.get_dot_matrix().copy()
                if index == pile_size - 1:
                    # last card
                    if card.face_up:
                        all_cards.extend([card.render_card_row(row) for row in arr])
                    else:
                        all_cards.extend([card.render_card_row(row) for row in Card.face_down_card_temp])
                else:
                    if card.face_up:
                        all_cards.extend([card.render_card_row(row) for row in arr[:2]])
                    else:
                        all_cards.extend([card.render_card_row(row) for row in [
                            "╭───────╮",
                            "│░░░░░░░│"
                        ]])
        return all_cards

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.cards = Pile()
    
    def __repr__(self) -> str:
        self.cards.sort_cards()
        return self.name + ": " + str(self.cards)
    
    def has_diamond_3(self):
        return any(card.suit == 'D' and card.rank == '3' for card in self.cards)
    
    def play_card(self, cards):
        for card in cards:
            self.cards.remove(card)


class Game:
    def __init__(self):
        self.players = [Player('玩家', is_human=True), Player('电脑1'), Player('电脑2'), Player('电脑3')]
        self.player_last_moves = [Pile() for _ in self.players]
        self.current_player_index = 0
        self.last_player_index = -1
        self.last_cards = []
        self.pass_count = 0
    
    def initialize_deck(self):
        suits = ['S', 'H', 'C', 'D']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck
    
    def deal_cards(self):
        deck = self.initialize_deck()
        for i in range(13):
            for player in self.players:
                player.cards.add_card(deck.pop())
        for player in self.players:
            player.cards.sort_cards()
    
    def find_first_player(self):
        for i, player in enumerate(self.players):
            if player.has_diamond_3():
                return i
        return 0 # 没有玩家有方块3, 理论上不可能发生
        
    @staticmethod
    def determine_card_type(cards):
        if len(cards) == 1:
            return '单张'
        elif len(cards) == 2:
            if cards[0].rank == cards[1].rank:
                return '对子'
            else:
                return '无效'
        elif len(cards) == 3:
            if cards[0].rank == cards[1].rank == cards[2].rank:
                return '三个'
            else:
                return '无效'
        elif len(cards) == 5:
            # 检查顺子
            if Game.is_straight(cards):
                # 检查同花顺
                if Game.is_same_suit(cards):
                    return '同花顺'
                else:
                    return '顺子'
            # 检查同花
            elif Game.is_same_suit(cards):
                return '同花'
            # 检查三个带一对
            elif Game.is_three_with_pair(cards):
                return '三个带一对'
            # 检查四个带单张
            elif Game.is_four_with_single(cards):
                return '四个带单张'
            else:
                return '无效'
        else:
            return '无效'
        
    @staticmethod
    def is_straight(cards): #顺子
        # 2特殊，3最小, A只能出现在两端
        # '0', '1', '2', '3', '4', '5', '6', '7',  '8', '9', '10','11','12'
        # '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2'
        ranks = sorted([card.get_rank_value() for card in cards])
        
        # 检查连续, 且数字不重复
        if ranks == list(range(ranks[0], ranks[0]+5)): #加5超出12的组合一定不会匹配
            # 排除J-Q-K-A-2 (8,9,10,11,12)
            if ranks != [8, 9, 10, 11, 12]:
                return True
        # 检查特殊顺子情况
        # A-2-3-4-5 (11,12,0,1,2) -> 排序后 [0,1,2,11,12]
        # 有效, 但是最小顺子, 也是有2参与的唯一合法顺子
        if ranks == [0, 1, 2, 11, 12]:
            return True
        # 2-3-4-5-6 (12,0,1,2,3) -> 排序后 [0,1,2,3,12], 不连续, 不合法, False
        # K-A-2-3-4, Q-K-A-2-3 也是排序后不连续, 自然排除
        return False

    @staticmethod
    def is_same_suit(cards):
        return all(card.suit == cards[0].suit for card in cards)
    
    @staticmethod
    def is_three_with_pair(cards): #葫芦, 三个带一对
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        counts = sorted(rank_counts.values(), reverse=True)
        return counts == [3, 2] #五张牌中, 只有两种数字, 并且一种数字出现三次, 另一种数字出现两次
        
    @staticmethod
    def is_four_with_single(cards): #铁支, 四个带单张
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        counts = sorted(rank_counts.values(), reverse=True)
        return counts == [4, 1] #五张牌中, 只有两种数字, 并且一种数字出现四次, 另一种数字出现一次
    
    @staticmethod
    def compare_card_by_rank_then_suit(cards1, cards2):
        assert len(cards1)==len(cards2)

        # unpack rank and suit and sort the cards
        rank_and_suit1 = sorted([(card.get_rank_value(), card.get_suit_value()) for card in cards1], reverse=True)
        rank_and_suit2 = sorted([(card.get_rank_value(), card.get_suit_value()) for card in cards2], reverse=True)

        # 逐个牌比数字大小
        for index in range(len(rank_and_suit1)):
            if rank_and_suit1[index][0] == rank_and_suit2[index][0]:
                continue
            else:
                return rank_and_suit1[index][0] > rank_and_suit2[index][0]

        # 数字大小比不出, 说明全数字一模一样, 比最大的花色
        return rank_and_suit1[index][1] > rank_and_suit2[index][1]

    @staticmethod
    def compare_cards(cards1, cards2):
        type1 = Game.determine_card_type(cards1)
        type2 = Game.determine_card_type(cards2)
        
        if type1 != type2:
            type_order = ['单张', '对子', '三个', '顺子', '同花', '三个带一对', '四个带单张', '同花顺']
            return type_order.index(type1) > type_order.index(type2)
        
        # 同类型比较, 原则是先比数字, 再比花色
        if type1 in ('单张', '对子', '三个'):#数字都一样
            #综合来看, 也是符合这个原则: 先由大到小逐个比较数字, 再比较大/次大/第三大/第四大/第五大等一一对应的花色
            return Game.compare_card_by_rank_then_suit(cards1, cards2)
        elif type1 in ('顺子', '同花顺'):
            # 取最大牌点（2在顺子中视为小牌）
            ranks1 = sorted([card.get_rank_value() for card in cards1])
            ranks2 = sorted([card.get_rank_value() for card in cards2])
            # 特殊A-2-3-4-5 (11,12,0,1,2) -> 排序后 [0,1,2,11,12]
            # 有效, 但是最小顺子
            if ranks1 == [0, 1, 2, 11, 12]:
                max_rank1 = 2
            else:
                max_rank1 = max(ranks1)
            if ranks2 == [0, 1, 2, 11, 12]:
                max_rank2 = 2 #数字牌5
            else:
                max_rank2 = max(ranks2)
            if max_rank1 > max_rank2:
                return True
            else:
                # 最大数一样时(因为是顺子, 后续是逐个-1, 最大比不出大小则后面也也一定比不出, 不用再就数字的大小来比较),
                # 比同样数字的两张牌的花色, 因为每种花色只有一个牌, 而且因为顺子没有重复数字, 所以直接取过滤后的第一个元素
                # 花色一定不同, 一定可比出大小
                suit_of_max_rank_card1 = [c1.get_suit_value() for c1 in cards1 if c1.get_rank_value() == max_rank1][0]
                suit_of_max_rank_card2 = [c2.get_suit_value() for c2 in cards2 if c2.get_rank_value() == max_rank2][0]
                return suit_of_max_rank_card1 > suit_of_max_rank_card2
        elif type1 == '同花':
            #综合来看, 也是符合这个原则: 先由大到小逐个比较数字, 再比较大/次大/第三大/第四大/第五大等一一对应的花色
            return Game.compare_card_by_rank_then_suit(cards1, cards2)
        elif type1 == '三个带一对':
            # 比较三个的大小
            rank_counts1 = {}
            for card in cards1:
                rank_counts1[card.rank] = rank_counts1.get(card.rank, 0) + 1
            rank_counts2 = {}
            for card in cards2:
                rank_counts2[card.rank] = rank_counts2.get(card.rank, 0) + 1
            # 数字大小一定不一样, 不会需要比较到那一对
            rank1 = [rank for rank, count in rank_counts1.items() if count == 3][0]
            rank2 = [rank for rank, count in rank_counts2.items() if count == 3][0]
            temp_card1 = Card('S', rank1)
            temp_card2 = Card('S', rank2)
            return temp_card1.get_rank_value() > temp_card2.get_rank_value()
        elif type1 == '四个带单张':
            # 比较四个的大小
            rank_counts1 = {}
            for card in cards1:
                rank_counts1[card.rank] = rank_counts1.get(card.rank, 0) + 1
            rank_counts2 = {}
            for card in cards2:
                rank_counts2[card.rank] = rank_counts2.get(card.rank, 0) + 1
            # 数字大小一定不一样, 不会需要比较到单个
            rank1 = [rank for rank, count in rank_counts1.items() if count == 4][0]
            rank2 = [rank for rank, count in rank_counts2.items() if count == 4][0]
            temp_card1 = Card('S', rank1)
            temp_card2 = Card('S', rank2)
            return temp_card1.get_rank_value() > temp_card2.get_rank_value()
        return False
    
    def get_valid_moves(self, player, last_cards):
        valid_moves = []
        if not last_cards:
            # 首家可以出任何合法牌型
            # 单张
            for card in player.cards:
                valid_moves.append([card])
            # 对子
            for i in range(len(player.cards)-1):
                if player.cards[i].rank == player.cards[i+1].rank:
                    valid_moves.append([player.cards[i], player.cards[i+1]])
            # 三个
            for i in range(len(player.cards)-2):
                if player.cards[i].rank == player.cards[i+1].rank == player.cards[i+2].rank:
                    valid_moves.append([player.cards[i], player.cards[i+1], player.cards[i+2]])
            # 五张牌型
            # 生成所有5张牌的组合
            from itertools import combinations
            for combo in combinations(player.cards, 5):
                combo_list = list(combo)
                if self.determine_card_type(combo_list) != '无效':
                    valid_moves.append(combo_list)
            
            # 检查是否是首轮出牌（last_cards为空）且玩家持有方块3
            if player.has_diamond_3():
                # 过滤出包含方块3的牌型
                valid_moves = [move for move in valid_moves if any(card.suit == 'D' and card.rank == '3' for card in move)]
        else:
            # 必须出相同数量的牌且更大
            last_type = self.determine_card_type(last_cards)
            last_count = len(last_cards)
            
            if last_count == 1:
                for card in player.cards:
                    if self.compare_cards([card], last_cards):
                        valid_moves.append([card])
            elif last_count == 2:
                for i in range(len(player.cards)-1):
                    # 前提是手中的牌都按rank排好序的
                    if player.cards[i].rank == player.cards[i+1].rank:
                        if self.compare_cards([player.cards[i], player.cards[i+1]], last_cards):
                            valid_moves.append([player.cards[i], player.cards[i+1]])
            elif last_count == 3:
                for i in range(len(player.cards)-2):
                    # 前提是手中的牌都按rank排好序的
                    if player.cards[i].rank == player.cards[i+1].rank == player.cards[i+2].rank:
                        if self.compare_cards([player.cards[i], player.cards[i+1], player.cards[i+2]], last_cards):
                            valid_moves.append([player.cards[i], player.cards[i+1], player.cards[i+2]])
            elif last_count == 5:
                from itertools import combinations
                for combo in combinations(player.cards, 5):
                    combo_list = list(combo)
                    combo_type = self.determine_card_type(combo_list)
                    if combo_type != '无效':
                        if self.compare_cards(combo_list, last_cards):
                            valid_moves.append(combo_list)
        return valid_moves
    
    def ai_choose_move(self, player, last_cards):
        valid_moves = self.get_valid_moves(player, last_cards)
        if not valid_moves:
            return []
        
        # 强力AI策略
        # 1. 优先出最大的牌型
        # 2. 尽量保留大牌
        # 3. 考虑牌型的连贯性
        
        # 按牌型强度排序
        type_strength = {'单张': 1, '对子': 2, '三个': 3, '顺子': 4, '同花': 5, '三个带一对': 6, '四个带单张': 7, '同花顺': 8}
        
        # 分组并排序
        move_groups = {}
        for move in valid_moves:
            move_type = self.determine_card_type(move)
            if move_type not in move_groups:
                move_groups[move_type] = []
            move_groups[move_type].append(move)
        
        # 选择最强的牌型
        strongest_type = max(move_groups.keys(), key=lambda x: type_strength[x])
        strongest_moves = move_groups[strongest_type]
        
        # 从最强牌型中选择最合理的
        # 对于单张，保留最大的
        if strongest_type == '单张':
            strongest_moves.sort(key=lambda x: x[0].get_rank_value(), reverse=True)
            # 尽量保留2和A
            for move in strongest_moves:
                if move[0].rank not in ['2', 'A']:
                    return move
            return strongest_moves[0]
        # 对于其他牌型，选择最大的
        else:
            strongest_moves.sort(key=lambda x: self.get_move_strength(x), reverse=True)
            return strongest_moves[0]
    
    @staticmethod
    def get_move_strength(move):
        move = list(move)
        move_type = Game.determine_card_type(move)
        if move_type == '单张':
            return move[0].get_rank_value()
        elif move_type == '对子':
            return move[0].get_rank_value() * 10
        elif move_type == '三个':
            return move[0].get_rank_value() * 100
        elif move_type in ['顺子', '同花顺']:
            max_rank = max(card.get_rank_value() for card in move if card.rank != '2')
            return max_rank * 1000
        elif move_type == '同花':
            max_rank = max(card.get_rank_value() for card in move)
            return max_rank * 10000
        elif move_type == '三个带一对':
            rank_counts = {}
            for card in move:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
            three_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
            return Card('S', three_rank).get_rank_value() * 100000
        elif move_type == '四个带单张':
            rank_counts = {}
            for card in move:
                rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
            four_rank = [rank for rank, count in rank_counts.items() if count == 4][0]
            return Card('S', four_rank).get_rank_value() * 1000000
        return 0

    # def print_player_cards(self):
    #     for player in self.players:
    #         print(str(player))

    def print_title(self):
        print("=== 锄大地游戏 ===")
    
    @staticmethod
    def center_just(row, target_size=100):
        valid_display_char_size = len(re.sub(r'\x1b\[\d+m', '', row))
        left_padding = ' ' * ((target_size - valid_display_char_size)//2)
        right_padding = ' ' * (target_size - len(left_padding) - valid_display_char_size)
        return left_padding + row + right_padding
    
    @staticmethod
    def left_just(row, target_size=45):
        valid_display_char_size = len(re.sub(r'\x1b\[\d+m', '', row))
        left_padding = ' ' * (target_size - valid_display_char_size)
        return row + left_padding
    
    @staticmethod
    def right_just(row, target_size=45):
        valid_display_char_size = len(re.sub(r'\x1b\[\d+m', '', row))
        right_padding = ' ' * (target_size - valid_display_char_size)
        return right_padding + row
    
    def print_upper_player_deck(self, player:Player):
        if player.cards:
            for row in player.cards.show_cards(direction='horizontal', compact=True):
                print(self.center_just(row, 118))
        else:
            print(self.center_just(' 不出 ', 118))

    def build_table(self):
        table_rows = []

        if self.player_last_moves[2].cards:
            upper_cards = self.player_last_moves[2].show_cards(direction='horizontal', compact=False)
            # pad head and tail
            for row in upper_cards:
                table_rows.append(self.center_just(row, 100))
        else:
            for _ in range(7):
                table_rows.append(' ' * 100)
        
        # margin
        for _ in range(3):
            table_rows.append(' ' * 100)

        left_cards = self.player_last_moves[3].show_cards(direction='horizontal', compact=False)
        right_cards = self.player_last_moves[1].show_cards(direction='horizontal', compact=False)
        for row_index in range(8):
            if row_index < len(left_cards):
                left_row = self.left_just(left_cards[row_index])
            else:
                left_row = ' ' * 9 * 5 # maximum 5 cards
            
            if row_index < len(right_cards):
                right_row = self.right_just(right_cards[row_index])
            else:
                right_row = ' ' * 9 * 5 # maximum 5 cards

            new_row = left_row + ' ' * 10 +  right_row
            table_rows.append(new_row)
        
        # margin
        for _ in range(4):
            table_rows.append(' ' * 100)
        
        if self.player_last_moves[0].cards:
            lower_cards = self.player_last_moves[0].show_cards(direction='horizontal', compact=False)
            # pad head and tail
            for row in lower_cards:
                table_rows.append(self.center_just(row, 100))
        else:
            for _ in range(7):
                table_rows.append(' ' * 100)

        return table_rows

    def print_left_right_player_deck(self, left_player:Player, right_player:Player):
        left_cards = left_player.cards.show_cards(direction='vertical', compact=True)
        right_cards = right_player.cards.show_cards(direction='vertical', compact=True)
        
        table_area = self.build_table()
        for row_index in range(31):
            if row_index < len(left_cards):
                left_row = left_cards[row_index]
            else:
                left_row = ' ' * 9
            
            if row_index < len(right_cards):
                right_row = right_cards[row_index]
            else:
                right_row = ' ' * 9
            
            if row_index < len(table_area):
                table_row = table_area[row_index]
            else:
                table_row = ' ' * 100

            new_row = left_row + table_row  + right_row
            print(new_row)
    
    def print_lower_player_deck(self, player:Player):
        if player.cards:
            for row in player.cards.show_cards(direction='horizontal', compact=True):
                print(self.center_just(row, 118)) # 9 + 100 + 9
        else:
            print(self.center_just(' 不出 ', 118))

    def clear(self):
        os.system('cls')

    def display(self):
        self.clear()
        self.print_title()
        self.print_upper_player_deck(self.players[2])
        self.print_left_right_player_deck(self.players[3], self.players[1])
        self.print_lower_player_deck(self.players[0])
        input('')
        

    def play(self):
        self.deal_cards()
        self.current_player_index = self.find_first_player()
        
        print("=== 锄大地游戏开始 ===")
        print(f"首家是: {self.players[self.current_player_index].name}")
        self.display()

        while True:
            current_player = self.players[self.current_player_index]
            print(f"\n{current_player.name}'s turn")
            
            if current_player.is_human:
                print("你的牌:", current_player.cards)
                valid_moves = self.get_valid_moves(current_player, self.last_cards)
                
                if not valid_moves:
                    print("没有可出的牌，选择Pass")
                    self.pass_count += 1
                    self.player_last_moves[self.current_player_index].clear_cards()
                else:
                    # 检查是否是所有人Pass后由最后出牌的人继续出牌
                    must_play = (self.last_cards == [] and self.pass_count == 0 and self.last_player_index == -1)
                    
                    print("可出的牌:")
                    if not must_play:
                        print("0. Pass (不出牌)")
                    for i, move in enumerate(valid_moves):
                        print(f"{i+1}. {move} ({self.determine_card_type(move)})")
                    
                    while True:
                        try:
                            choice = int(input("请选择要出的牌 (输入编号): "))
                            if not must_play and choice == 0:
                                print("你选择了Pass")
                                self.pass_count += 1
                                self.player_last_moves[self.current_player_index].clear_cards()
                                break
                            elif 1 <= choice <= len(valid_moves):
                                chosen_move = valid_moves[choice-1]
                                current_player.play_card(chosen_move)
                                self.player_last_moves[self.current_player_index].refresh_cards(chosen_move)
                                self.player_last_moves[self.current_player_index].set_all_face_up()

                                self.last_cards = chosen_move
                                self.last_player_index = self.current_player_index
                                self.pass_count = 0
                                # print(f"你出了: {chosen_move} ({self.determine_card_type(chosen_move)}), 剩余{len(current_player.cards)}张牌")
                                self.display()
                                break
                            else:
                                print("输入无效，请重新输入")
                        except ValueError:
                            print("输入无效，请输入数字")
            else:
                # 检查是否是所有人Pass后由最后出牌的人继续出牌
                must_play = (self.last_cards == [] and self.pass_count == 0 and self.last_player_index == -1)
                
                if must_play:
                    # 必须出牌，不能Pass
                    valid_moves = self.get_valid_moves(current_player, self.last_cards)
                    if valid_moves:
                        chosen_move = self.ai_choose_move(current_player, self.last_cards)
                        current_player.play_card(chosen_move)
                        self.player_last_moves[self.current_player_index].refresh_cards(chosen_move)
                        self.player_last_moves[self.current_player_index].set_all_face_up()

                        self.last_cards = chosen_move
                        self.last_player_index = self.current_player_index
                        self.pass_count = 0
                        # print(f"{current_player.name} 出了: {chosen_move} ({self.determine_card_type(chosen_move)}), 剩余{len(current_player.cards)}张牌")
                    else:
                        # print(f"{current_player.name} 没有可出的牌")
                        self.pass_count += 1
                        self.player_last_moves[self.current_player_index].clear_cards()
                else:
                    chosen_move = self.ai_choose_move(current_player, self.last_cards)

                    if not chosen_move:
                        print(f"{current_player.name} Pass")
                        self.pass_count += 1
                        self.player_last_moves[self.current_player_index].clear_cards()
                    else:
                        current_player.play_card(chosen_move)
                        self.player_last_moves[self.current_player_index].refresh_cards(chosen_move)
                        self.player_last_moves[self.current_player_index].set_all_face_up()

                        self.last_cards = chosen_move
                        self.last_player_index = self.current_player_index
                        self.pass_count = 0
                        # print(f"{current_player.name} 出了: {chosen_move} ({self.determine_card_type(chosen_move)}), 剩余{len(current_player.cards)}张牌")
                
                self.display()
            
            # 检查是否有人出完牌
            if not current_player.cards:
                print(f"\n{RED if current_player.is_human else BLUE}❉⊱•❉⊱• {current_player.name} 获胜！•⊰❉•⊰❉{RESET}")
                break
            
            # 检查是否需要重新开始
            if self.pass_count >= 3:
                self.last_cards = []
                self.pass_count = 0
                print(f"所有人都Pass，{self.players[self.last_player_index].name}继续出牌")
                self.last_player_index = -1
            
            # 下一个玩家
            self.current_player_index = (self.current_player_index + 1) % 4
        
        print("\n=== 游戏结束 ===")
        print("各玩家剩余牌:")
        for player in self.players:
            if player.cards:
                print(GREEN + str(player) + RESET)

if __name__ == "__main__":
    while True:
        game = Game()
        game.play()
        resp = input("再玩一局？(y/[回车] || n):").strip()
        if resp.lower() != "y" and resp != "":
            print("谢谢参与！")
            break
    print("感谢游玩, 再见!")
