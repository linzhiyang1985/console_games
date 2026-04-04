import random
import sys
import re
import os

CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fa5]{1}')  # 中文字符的Unicode范围

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
    card_temp = [
        '┌───────┐',
        '│♠KK    │',
        '│       │',
        '│   ♠   │',
        '│       │',
        '│    KK♠│',
        '└───────┘'
    ]

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.dot_matrix = None
    
    def __str__(self):
        card_color = RED if self.suit in ('♥', '♦') else BLUE
        return f"{card_color}{self.suit}{RESET}{DISPLAY_RANKS[RANKS.index(self.rank)]}"
    
    def get_value(self):
        if self.rank == 'A':
            return 1
        elif self.rank in ['J', 'Q', 'K']:
            return 11 + ['J', 'Q', 'K'].index(self.rank)
        else:
            return int(self.rank)

    def generate_dot_matrix(self):
        if self.dot_matrix is not None:
            return
        ## 只生成一次
        if len(self.rank) == 1:
            rank_left = DISPLAY_RANKS[RANKS.index(self.rank)] + ' '
            rank_right = ' ' + DISPLAY_RANKS[RANKS.index(self.rank)]
        else:
            rank_left = rank_right = DISPLAY_RANKS[RANKS.index(self.rank)]
        suit_center = ' ' + self.suit + ' '
        
        card = []
        for row in self.card_temp:
            card.append(row.replace('♠KK', self.suit + rank_left).replace('KK♠', rank_right + self.suit).replace(' ♠ ', suit_center))
        self.dot_matrix = card


class Deck:
    def __init__(self):
        self.cards = []
        for suit in SUITS:
            for rank in RANKS:
                self.cards.append(Card(suit, rank))
        self.shuffle()
    
    def shuffle(self):
        random.shuffle(self.cards)
    
    def deal(self, num=1):
        return [self.cards.pop() for _ in range(num)]


class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human
        self.hand = []
        self.passes = 0
        self.max_passes = 3
        self.is_out = False
    
    def add_cards(self, cards):
        self.hand.extend(cards)
        # 按花色和点数排序
        self.hand.sort(key=lambda x: (SUITS.index(x.suit), x.get_value()))
    
    def has_playable_card(self, table):
        for card in self.hand:
            if self.is_playable(card, table):
                return True
        return False
    
    def is_playable(self, card, table):
        # 检查是否有同花色的相邻牌
        for suit, cards_on_table in table.items():
            if card.suit == suit:
                if not cards_on_table:  # 该花色还没有牌，只能出7
                    return card.rank == '7'
                min_rank = min([card.get_value() for card in cards_on_table])
                max_rank = max([card.get_value() for card in cards_on_table])
                card_value = card.get_value()
                return card_value == min_rank - 1 or card_value == max_rank + 1
        # 如果没有任何牌在桌上，只能出7
        return card.rank == '7'
    
    def get_hand_option_str(self):
        hand_strs = [f'{self.name}的牌:']
        hand_strs.append('0. 不出,过')
        for i, card in enumerate(self.hand):
            hand_strs.append(f"{i+1}. {card}")
        return hand_strs
    
    def play_card(self, table):
        if not self.has_playable_card(table):
            self.passes += 1
            return None
        
        if self.is_human:
            # 人类玩家选择出牌
            # print("\n".join(self.get_hand_option_str()))
            
            while True:
                try:
                    choice = input("请输入出牌的序号, 或0/p跳过此轮, 或q退出游戏: ")
                    if choice == '0' or choice == 'p':
                        if self.passes < self.max_passes:
                            self.passes += 1
                            return None
                        else:
                            print("无法跳过此轮出牌, 已超过最大次数。")
                            confirm_out = input("是否确认出局? (y/n): ")
                            if confirm_out.lower() == 'y':
                                self.is_out = True
                                print(f"\n{self.name} 无法跳过此轮出牌, 出局!")
                                return None
                    elif choice == 'q':
                        print("游戏结束！")
                        sys.exit()
                    else:
                        choice = int(choice) - 1
                        if 0 <= choice < len(self.hand):
                            card = self.hand[choice]
                            if self.is_playable(card, table):
                                self.hand.pop(choice)
                                return card
                            else:
                                print("该牌不能出，请重新选择。")
                        else:
                            print("无效的序号, 请重新选择。")
                except ValueError:
                    print("无效输入, 请输入数字, 或0/p跳过此轮, 或q退出游戏。")
        else:
            # 电脑玩家自动出牌 - 高级策略
            playable_cards = [card for card in self.hand if self.is_playable(card, table)]
            if playable_cards:
                # 计算每张可打牌的得分和风险
                best_card = None
                best_score = -1
                
                for card in playable_cards:
                    score = self.calculate_card_score(card, table)
                    risk = self.calculate_card_risk(card, table)
                    # 综合考虑得分和风险
                    net_score = score - risk
                    
                    if net_score > best_score:
                        best_score = net_score
                        best_card = card
                
                # 决定是否出牌：如果最佳牌的得分较低，且风险较高，可能选择不出牌
                if best_card:
                    # 计算出牌的整体价值
                    if best_score > 20 or self.passes >= 2:  # 如果得分高或已经pass了2次，就出牌
                        self.hand.remove(best_card)
                        return best_card
                    else:
                        # 选择不出牌，以阻止别人出牌
                        self.passes += 1
                        print(f"{self.name}跳过此轮出牌")
                        return None
            self.passes += 1
            return None
    
    def calculate_card_risk(self, card, table):
        """计算出牌的风险，风险越高越不优先出"""
        risk = 0
        card_value = card.get_value()
        cards_on_table = table.get(card.suit, [])
        
        # 1. 检查出牌后是否会为其他玩家创造更多出牌机会
        if not cards_on_table:
            # 出7会打开新花色，可能为其他玩家创造机会
            risk += 30
        else:
            min_rank = min([card.get_value() for card in cards_on_table])
            max_rank = max([card.get_value() for card in cards_on_table])
            
            # 出两端的牌会扩展花色范围，可能为其他玩家创造机会
            if card_value == min_rank - 1:
                # 如果出的是A，不会再往小了出，风险较低
                if card_value != 1:
                    risk += 20
            elif card_value == max_rank + 1:
                # 如果出的是K，不会再往大了出，风险较低
                if card_value != 13:
                    risk += 20
        
        # 2. 检查手中是否有该花色的其他牌，如果出了这张牌会影响后续出牌
        suit_cards = [c.get_value() for c in self.hand if c.suit == card.suit]
        if len(suit_cards) > 1:
            # 如果这是该花色的唯一可打牌，出了之后可能无法再出该花色的其他牌
            playable_suit_cards = []
            for v in suit_cards:
                test_card = Card(card.suit, self.get_rank_from_value(v))
                if self.is_playable(test_card, table):
                    playable_suit_cards.append(v)
            if len(playable_suit_cards) == 1:
                risk += 25
        
        # 3. 考虑其他玩家的手牌情况（简单模拟）
        # 假设其他玩家可能有相邻的牌
        risk += 10  # 基础风险
        
        return risk
    
    def get_rank_from_value(self, value):
        """根据数值获取牌的等级"""
        if value == 1:
            return 'A'
        elif value == 11:
            return 'J'
        elif value == 12:
            return 'Q'
        elif value == 13:
            return 'K'
        else:
            return str(value)
    
    def calculate_card_score(self, card, table):
        """计算牌的得分，得分越高越优先出"""
        score = 0
        card_value = card.get_value()
        
        # 1. 计算该花色在手中的剩余牌数（越少越好，得分越高）
        suit_count = sum(1 for c in self.hand if c.suit == card.suit)
        score += (14 - suit_count) * 5  # 剩余牌越少，得分越高
        
        # 2. 检查该牌是否能扩展花色的范围（两端牌优先）
        cards_on_table = table.get(card.suit, [])
        if not cards_on_table:
            # 该花色还没有牌，只能是7
            score += 100  # 出7能打开新花色，优先级最高
        else:
            min_rank = min([card.get_value() for card in cards_on_table])
            max_rank = max([card.get_value() for card in cards_on_table])
            
            # 出两端的牌，扩展范围
            if card_value == min_rank - 1:
                score += 30  # 出最小端
                # 如果是A，得分更高（因为不能再往小了出）
                if card_value == 1:
                    score += 20
            elif card_value == max_rank + 1:
                score += 30  # 出最大端
                # 如果是K，得分更高（因为不能再往大了出）
                if card_value == 13:
                    score += 20
        
        # 3. 优先出点数大的牌（减少手牌数量）
        score += card_value * 2
        
        # 4. 考虑该花色的完整性（如果手中有该花色的连续牌，优先出中间的）
        # 检查手中是否有该花色的连续牌
        suit_cards = sorted([c.get_value() for c in self.hand if c.suit == card.suit])
        if len(suit_cards) > 1:
            # 检查是否是连续序列的一部分
            for i, val in enumerate(suit_cards):
                if val == card_value:
                    # 检查前后是否有连续的牌
                    has_prev = i > 0 and suit_cards[i-1] == val - 1
                    has_next = i < len(suit_cards) - 1 and suit_cards[i+1] == val + 1
                    if has_prev and has_next:
                        score += 15  # 中间牌，优先出以断开连续
                    break
        
        return score
    
    # def play_sevens(self, table):
    #     # 开局出所有的7
    #     sevens = [card for card in self.hand if card.rank == '7']
    #     for seven in sevens:
    #         self.hand.remove(seven)
    #         if seven.suit not in table:
    #             table[seven.suit] = []
    #         table[seven.suit].append(seven)
    #         print(f"{self.name:<3} 出牌 {seven}")
    #     return sevens

class Game:
    def __init__(self):
        self.deck = Deck()
        self.players = [
            Player("玩家", is_human=True),
            Player("电脑1"),
            Player("电脑2"),
            Player("电脑3")
        ]

        random.shuffle(self.players) # 随机选一个玩家开始

        self.table = {suit: [] for suit in SUITS}
    
    def deal_cards(self):
        # 发牌：每人12张
        for _ in range(12):
            for player in self.players:
                card = self.deck.deal()[0]
                while card.get_value() == 7:
                    # 发牌7，直接放在桌上
                    self.table[card.suit].append(card)
                    # 继续发牌，直到不是7
                    card = self.deck.deal()[0]
                player.add_cards([card])

    def clear(self):
        os.system('cls')

    def start_game(self):
        print("=== 排七游戏开始 ===")
        
        # 发牌
        self.deal_cards()
        
        # # 显示初始桌面
        # self.draw_table()
        
        # 游戏主循环
        game_over = False
        while not game_over:
            for player in self.players:
                if player.is_out:
                    continue
                                
                print(f"\n=== 轮到{player.name}出牌 ===")
                print(f"剩余过牌次数: {player.max_passes - player.passes}")
                
                # 玩家出牌
                if player.is_human:
                    hand_options = player.get_hand_option_str()
                    self.draw_table(padding_texts=hand_options)

                card = player.play_card(self.table)
                if card:
                    print(f"{player.name:<3} 出牌 {card}")
                    # 更新桌面
                    if card.suit not in self.table:
                        self.table[card.suit] = []
                    self.table[card.suit].append(card)
                    # 排序，方便后续判断
                    self.table[card.suit].sort(key=lambda x: x.get_value())
                else:
                    # 检查是否已超过最大过牌次数
                    if player.passes > player.max_passes: # 最后这次+1其实不生效, 玩家已经没资格跳过
                        player.is_out = True
                        print(f"\n{player.name} 无法跳过此轮出牌, 出局!")
                        continue
                    else:
                        print(f"{player.name:<3} 跳过此轮出牌")
                
                if player.is_human:
                    # 显示各玩家剩余牌数和过牌次数
                    self.show_status()
                
                # 检查是否已出完牌
                if not player.hand:
                    print(f"\n{RED}❉⊱•❉⊱• {player.name}赢了! •⊰❉•⊰❉{RESET}")
                    game_over = True
                    break

                # # 显示桌面
                # self.draw_table()

            if all(player.is_out for player in self.players):
                print("\n=== 所有玩家都出局, 游戏结束。 ===")
                game_over = True

        print("\n=== 游戏结束 ===")
        for player in self.players:
            print(f"{player.name:<3}: 剩下{len(player.hand)}张牌, 过牌{min(3, player.passes)}次" + ('(已出局)' if player.is_out else ''))
            print(f"{player.name:<3}手牌: {', '.join([str(card) for card in player.hand])}")
        # 最后显示桌面
        self.draw_table()
        
    def draw_table(self, padding_texts=[]):
        for suit in SUITS:
            self.show_dot_matrix(self.table[suit], padding_texts)
            if padding_texts:
                print(padding_texts.pop(0))
            else:
                print()


    def show_status(self):
        print("\n=== 玩家状态 ===")
        for player in self.players:
            print(f"{player.name:<3}: 剩余{len(player.hand)}张牌, 剩余过牌{max(0,player.max_passes - player.passes)}次" + ('(已出局)' if player.is_out else ''))
    
    def get_rank_str(self, value):
        if value == 1:
            return 'A'
        elif value == 11:
            return 'J'
        elif value == 12:
            return 'Q'
        elif value == 13:
            return 'K'
        else:
            return str(value)

    def render_card(self, card):
        rendered_str = ''
        char_color = RED if ('♥' in card or '♦' in card) else BLUE
        for ch in card:
            if ch in ('┌', '─', '┐', '│', '└', '┘'):
                rendered_str += GREEN + ch + RESET
            elif ch in ('♠', '♣', '♦', '♥', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '1', '0', 'J', 'Q', 'K'):
                rendered_str += char_color + ch + RESET
            elif ch == ' ':
                rendered_str += ' '
            else:
                rendered_str += ch
        return rendered_str

    def show_dot_matrix(self, cards, padding_texts=[], padding_align=10):
        smallest_cards = min(cards, key=lambda x: x.get_value())        
        padding_card_spaces = ''
        for _ in range(smallest_cards.get_value() - 1):
            padding_card_spaces += ' ' * len(Card.card_temp[0]) + '  '
        
        for row_index in range(7):
            if padding_align > 0:
                if padding_texts:
                    one_pad = padding_texts.pop(0)
                    chinese_chars = len(CHINESE_CHAR_PATTERN.findall(one_pad)) # 一个中文字符占用2个符号宽
                    if '\x1b' in one_pad:
                        actual_display_len = one_pad.find('\x1b') + 1 + (len(one_pad) - one_pad.find('\x1b[0m') - 4)
                    else:
                        actual_display_len = len(one_pad)
                    padding_text_spaces = f'{one_pad}{" " * (padding_align - actual_display_len - chinese_chars)}'
                else:
                    padding_text_spaces = ' ' * padding_align
            else:
                padding_text_spaces = ''
                
            concated_row = padding_text_spaces + padding_card_spaces
            for card in cards:
                card.generate_dot_matrix()
                concated_row += self.render_card(card.dot_matrix[row_index]) + '  '
            print(concated_row)


if __name__ == "__main__":
    while True:
        game = Game()
        game.start_game()
        
        response = input("再来一局? (y,[回车]/n)")
        if not response.lower().startswith('y') and not response.strip() == '':
            break
        else:
            game.clear()
