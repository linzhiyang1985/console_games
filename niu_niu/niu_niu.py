import msvcrt
import random
import os

BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# 扑克牌类
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
        self.suit = suit  # 花色
        self.rank = rank  # 点数
        self.value = self._get_value()
        self.dot_matrix = None
    
    def __str__(self):
        return f"{self.suit}{self.rank}"
    
    def _get_value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 1
        else:
            return int(self.rank)
    
    def generate_dot_matrix(self):
        if self.dot_matrix is not None:
            return
        ## 只生成一次
        if len(self.rank) == 1:
            rank_left = self.rank + ' '
            rank_right = ' ' + self.rank
        else:
            rank_left = rank_right = self.rank
        suit_center = ' ' + self.suit + ' '
        
        card = []
        for row in self.card_temp:
            card.append(row.replace('♠KK', self.suit + rank_left).replace('KK♠', rank_right + self.suit).replace(' ♠ ', suit_center))
        self.dot_matrix = card

# 玩家类
class Player:
    def __init__(self, name, is_dealer=False):
        self.name = name
        self.is_dealer = is_dealer
        self.cards = []
        self.niu_type = None  # 牛型
        self.niu_value = 0  # 牛值
        self.niu_cards = []  # 牛牌
    
    def add_card(self, card):
        card.generate_dot_matrix() # 这张牌首次被抽中发给玩家的时候生成点阵
        self.cards.append(card)
    
    def clear_cards(self):
        self.cards.clear()
        self.niu_cards.clear()
        self.niu_type = None
        self.niu_value = 0
    
    def calculate_niu(self):
        #总点数
        sum_value = sum([card.value for card in self.cards])
                
        # 检查五小牛
        if sum_value <= 10:
            self.niu_type = '五小牛'
            self.niu_value = 100
            self.niu_cards = self.cards
            return
        
        # 检查五花牛
        if all(card.rank in ['J', 'Q', 'K'] for card in self.cards):
            self.niu_type = '五花牛'
            self.niu_value = 90
            self.niu_cards = self.cards
            return
        
        # 检查四炸
        ranks = [card.rank for card in self.cards]
        for rank in ranks:
            if ranks.count(rank) == 4:
                self.niu_type = '四炸'
                self.niu_value = 80
                self.niu_cards = [card for card in self.cards if card.rank == rank]
                return
        
        # 检查是否有牛
        has_niu = False
        best_niu = 0
        
        # 遍历所有3张牌的组合
        for i in range(5):
            for j in range(i+1, 5):
                for k in range(j+1, 5):
                    sum_three = self.cards[i].value + self.cards[j].value + self.cards[k].value
                    if sum_three % 10 == 0:
                        has_niu = True
                        # 计算剩余两张牌的和
                        sum_remaining = sum_value - sum_three # 剩下两张卡加起来一定是大于0的
                        niu = sum_remaining % 10
                        if niu == 0:
                            best_niu = 70
                            self.niu_type = '牛牛'
                            self.niu_value = 70
                            self.niu_cards = [self.cards[i], self.cards[j], self.cards[k]]
                            break
                        if niu > best_niu:
                            best_niu = niu
                            self.niu_cards = [self.cards[i], self.cards[j], self.cards[k]]
                if best_niu == 70:
                    break
            if best_niu == 70:
                break

        if has_niu:
            if best_niu < 10:
                self.niu_type = f'牛{["", "一", "二", "三", "四", "五", "六", "七", "八", "九"][best_niu]}'
                self.niu_value = best_niu + 50
        else:
            self.niu_type = '无牛'
            self.niu_value = max([card.value for card in self.cards]) # 无牛时，不比总和，只比5张牌里最大的一张。谁的单张最大谁赢（K>Q>J>10>...>A）
            self.niu_cards = [[card for card in self.cards if card.value == self.niu_value][0]] # 选出第一个最大的牌
    
    def show_cards(self):
        return ' '.join(BLUE + str(card) + RESET if card in self.niu_cards else str(card) + RESET for card in self.cards)
    
    def _render_card(self, card, is_niu_card=False):
        rendered_str = ''
        for ch in card:
            if ch in ('┌', '─', '┐', '│', '└', '┘'):
                rendered_str += (YELLOW if is_niu_card else BLUE) + ch + RESET
            elif ch in ('♠', '♣', '♦', '♥', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '1', '0', 'J', 'Q', 'K'):
                rendered_str += GREEN + ch + RESET
            elif ch == ' ':
                rendered_str += ' ' #RED + '/' + RESET # 斜线太密集看不清牌
            else:
                rendered_str += ch
        return rendered_str

    def show_dot_matrix(self):
        for row_index in range(7):
            concated_row = ''
            for card in self.cards:
                concated_row += self._render_card(card.dot_matrix[row_index], card in self.niu_cards) + '  '
            print(concated_row)
        print()

# 游戏类
class NiuNiuGame:
    def __init__(self):
        self.players = []
        self.deck = []
    
    def initialize_deck(self):
        # 创建一副完整的扑克牌
        suits = ['♥', '♠', '♦', '♣'] #{'H': '♥', 'S': '♠', 'D': '♦', 'C': '♣'}
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.deck)
    
    def shuffle_deck(self):
        random.shuffle(self.deck)

    def add_player(self, player: Player):
        self.players.append(player)
    
    def clear(self):
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def deal_cards(self):
        # 清空所有玩家的牌
        for player in self.players:
            player.clear_cards()
        
        # 发牌，每人5张, 最多6个人玩, 共发30张,一定够所有玩家
        serve_all = False
        serve_index = 0
        for _ in range(5):
            for player in self.players:
                # 牌已经洗乱, 直接从上面顺序取
                player.add_card(self.deck[serve_index])
                serve_index += 1

            if not serve_all:
                # 展示当前发的牌
                self.clear()
                self.show_cards()
                print("按任意键继续发牌, [回车]发全部...")
                next_serve = msvcrt.getch()
                if next_serve == b'\r':
                    serve_all = True
        # 展示全五张牌
        self.clear()
        self.show_cards()
    
    def show_cards(self):
        print("\n=== 牌型展示 ===")
        for player in self.players:
            print(f"{player.name}的牌：{player.show_cards()}")
            player.show_dot_matrix()
    
    def calculate_all_niu(self):
        for player in self.players:
            player.calculate_niu()
    
    def show_niu_results(self):
        print("\n=== 配牛结果 ===")
        for player in self.players:
            print(f"{player.name}：{player.niu_type}")
        self.show_cards()
    
    def compare_hands(self):
        print("\n=== 比牌结果 ===")
        ordered_players = sorted(self.players, key=lambda x: x.niu_value, reverse=True)

        previous_niu_value = ordered_players[0].niu_value
        player_index = 1
        for player in ordered_players:
            if player.niu_value < previous_niu_value:
                player_index += 1
                previous_niu_value = player.niu_value
            print(f"{player.name}：{player.niu_type}, 排名：第{player_index}")
    
    def play_round(self):
        # 每一轮重新洗牌
        self.shuffle_deck()
        
        # 发牌
        self.deal_cards()
                
        # 计算牛型
        self.calculate_all_niu()
        
        # 展示配牛结果
        self.clear()
        # self.show_niu_results()
        self.show_cards()
        
        # 比牌
        self.compare_hands()
            
    def start_game(self):
        print("====================================")
        print("        斗牛游戏开始！")
        print("====================================")
        
        # 添加玩家
        player_count = input("请输入玩家数量（2-6）：")
        while player_count not in ('2', '3', '4', '5', '6'):
            player_count = input("玩家数量必须在2-6之间，请重新输入：")
        player_count = int(player_count)
        
        for i in range(player_count):
            is_dealer = (i == 0)  # 第一个玩家为庄家
            default_name = '庄家' if is_dealer else f'玩家{i}'
            name = input('请输入' + default_name + '的名字(直接回车使用默认名称):')
            if not name:
                name = default_name
            self.add_player(Player(name, is_dealer))
        
        
        # 初始化牌 deck
        self.initialize_deck()
        
        # 游戏主循环
        while True:
            self.play_round()
            
            play_again = input("\n是否继续游戏？（y,[回车]/n）：").lower()
            if play_again != 'y' and play_again != '':
                break
        
        print("\n====================================")
        print("        游戏结束！")
        print("====================================")

# 运行游戏
if __name__ == "__main__":
    game = NiuNiuGame()
    game.start_game()