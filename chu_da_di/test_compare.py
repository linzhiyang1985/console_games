import sys
import os

# 添加当前目录到路径，以便导入chu_da_di模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chu_da_di import Game, Card

def test_compare_cards():
    """测试compare_cards函数的所有代码分支"""
    print("开始测试compare_cards函数...")
    
    # 测试1: 不同牌型比较（同张数）
    print("\n测试1: 不同牌型比较（同张数）")
    # 五张牌型之间的比较
    # 顺子 vs 同花
    card1 = [Card('S', '3'), Card('H', '4'), Card('C', '5'), Card('D', '6'), Card('S', '7')]  # 顺子
    card2 = [Card('S', '3'), Card('S', '5'), Card('S', '8'), Card('S', 'J'), Card('S', 'K')]  # 同花
    result = Game.compare_cards(card1, card2)
    print(f"顺子 vs 同花: {result} (预期: False)")
    assert not result, "顺子应该小于同花"
    
    # 同花 vs 三个带一对
    card1 = [Card('S', '3'), Card('S', '5'), Card('S', '8'), Card('S', 'J'), Card('S', 'K')]  # 同花
    card2 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A'), Card('D', 'K'), Card('S', 'K')]  # 三个带一对
    result = Game.compare_cards(card1, card2)
    print(f"同花 vs 三个带一对: {result} (预期: False)")
    assert not result, "同花应该小于三个带一对"
    
    # 三个带一对 vs 四个带单张
    card1 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A'), Card('D', 'K'), Card('S', 'K')]  # 三个带一对
    card2 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A'), Card('D', 'A'), Card('S', 'K')]  # 四个带单张
    result = Game.compare_cards(card1, card2)
    print(f"三个带一对 vs 四个带单张: {result} (预期: False)")
    assert not result, "三个带一对应该小于四个带单张"
    
    # 四个带单张 vs 同花顺
    card1 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A'), Card('D', 'A'), Card('S', 'K')]  # 四个带单张
    card2 = [Card('S', '3'), Card('S', '4'), Card('S', '5'), Card('S', '6'), Card('S', '7')]  # 同花顺
    result = Game.compare_cards(card1, card2)
    print(f"四个带单张 vs 同花顺: {result} (预期: False)")
    assert not result, "四个带单张应该小于同花顺"
    
    # 测试2: 单张比较
    print("\n测试2: 单张比较")
    # 数字不同
    card1 = [Card('S', 'A')]
    card2 = [Card('S', 'K')]
    result = Game.compare_cards(card1, card2)
    print(f"单张 A vs K: {result} (预期: True)")
    assert result, "A应该大于K"
    
    # 数字相同，花色不同
    card1 = [Card('S', 'A')]  # 黑桃
    card2 = [Card('H', 'A')]  # 红桃
    result = Game.compare_cards(card1, card2)
    print(f"单张 黑桃A vs 红桃A: {result} (预期: True)")
    assert result, "黑桃应该大于红桃"
    
    # 测试3: 对子比较
    print("\n测试3: 对子比较")
    # 数字不同
    card1 = [Card('S', 'A'), Card('H', 'A')]
    card2 = [Card('S', 'K'), Card('H', 'K')]
    result = Game.compare_cards(card1, card2)
    print(f"对子 AA vs KK: {result} (预期: True)")
    assert result, "AA应该大于KK"
    
    # 数字相同，花色不同
    card1 = [Card('S', 'A'), Card('H', 'A')]  # 黑桃+红桃
    card2 = [Card('H', 'A'), Card('C', 'A')]  # 红桃+梅花
    result = Game.compare_cards(card1, card2)
    print(f"对子 黑桃A+红桃A vs 红桃A+梅花A: {result} (预期: True)")
    assert result, "黑桃+红桃应该大于红桃+梅花"
    
    # 测试4: 三个比较
    print("\n测试4: 三个比较")
    # 数字不同
    card1 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A')]
    card2 = [Card('S', 'K'), Card('H', 'K'), Card('C', 'K')]
    result = Game.compare_cards(card1, card2)
    print(f"三个 AAA vs KKK: {result} (预期: True)")
    assert result, "AAA应该大于KKK"
    
    # 测试5: 顺子比较
    print("\n测试5: 顺子比较")
    # 普通顺子
    card1 = [Card('S', '10'), Card('H', 'J'), Card('C', 'Q'), Card('D', 'K'), Card('S', 'A')]
    card2 = [Card('S', '9'), Card('H', '10'), Card('C', 'J'), Card('D', 'Q'), Card('S', 'K')]
    result = Game.compare_cards(card1, card2)
    print(f"顺子 10JQKA vs 910JQK: {result} (预期: True)")
    assert result, "10JQKA应该大于910JQK"
    
    # 特殊顺子 A-2-3-4-5
    card1 = [Card('S', '3'), Card('H', '4'), Card('C', '5'), Card('D', '6'), Card('S', '7')]
    card2 = [Card('S', 'A'), Card('H', '2'), Card('C', '3'), Card('D', '4'), Card('S', '5')]
    result = Game.compare_cards(card1, card2)
    print(f"顺子 34567 vs A2345: {result} (预期: True)")
    assert result, "34567应该大于A2345"
    
    # 顺子数字相同，花色不同
    card1 = [Card('S', '10'), Card('S', 'J'), Card('S', 'Q'), Card('S', 'K'), Card('S', 'A')]
    card2 = [Card('H', '10'), Card('H', 'J'), Card('H', 'Q'), Card('H', 'K'), Card('H', 'A')]
    result = Game.compare_cards(card1, card2)
    print(f"顺子 黑桃10JQKA vs 红桃10JQKA: {result} (预期: True)")
    assert result, "黑桃10JQKA应该大于红桃10JQKA"
    
    # 测试6: 同花顺比较
    print("\n测试6: 同花顺比较")
    # 普通同花顺
    card1 = [Card('S', '10'), Card('S', 'J'), Card('S', 'Q'), Card('S', 'K'), Card('S', 'A')]
    card2 = [Card('S', '9'), Card('S', '10'), Card('S', 'J'), Card('S', 'Q'), Card('S', 'K')]
    result = Game.compare_cards(card1, card2)
    print(f"同花顺 黑桃10JQKA vs 黑桃910JQK: {result} (预期: True)")
    assert result, "黑桃10JQKA应该大于黑桃910JQK"
    
    # 特殊同花顺 A-2-3-4-5
    card1 = [Card('S', '3'), Card('S', '4'), Card('S', '5'), Card('S', '6'), Card('S', '7')]
    card2 = [Card('S', 'A'), Card('S', '2'), Card('S', '3'), Card('S', '4'), Card('S', '5')]
    result = Game.compare_cards(card1, card2)
    print(f"同花顺 黑桃34567 vs 黑桃A2345: {result} (预期: True)")
    assert result, "黑桃34567应该大于黑桃A2345"
    
    # 测试7: 同花比较
    print("\n测试7: 同花比较")
    # 最大数字不同
    card1 = [Card('S', 'A'), Card('S', 'K'), Card('S', 'Q'), Card('S', 'J'), Card('S', '10')]
    card2 = [Card('S', 'K'), Card('S', 'Q'), Card('S', 'J'), Card('S', '10'), Card('S', '9')]
    result = Game.compare_cards(card1, card2)
    print(f"同花 黑桃AKQJ10 vs 黑桃KQJ109: {result} (预期: True)")
    assert result, "黑桃AKQJ10应该大于黑桃KQJ109"
    
    # 最大数字相同，花色不同
    card1 = [Card('S', 'A'), Card('S', 'K'), Card('S', 'Q'), Card('S', 'J'), Card('S', '10')]
    card2 = [Card('H', 'A'), Card('H', 'K'), Card('H', 'Q'), Card('H', 'J'), Card('H', '10')]
    result = Game.compare_cards(card1, card2)
    print(f"同花 黑桃AKQJ10 vs 红桃AKQJ10: {result} (预期: True)")
    assert result, "黑桃AKQJ10应该大于红桃AKQJ10"
    
    # 测试8: 三个带一对比较
    print("\n测试8: 三个带一对比较")
    # 三个的数字不同
    card1 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A'), Card('D', 'K'), Card('S', 'K')]
    card2 = [Card('S', 'K'), Card('H', 'K'), Card('C', 'K'), Card('D', 'Q'), Card('S', 'Q')]
    result = Game.compare_cards(card1, card2)
    print(f"三个带一对 AAA+KK vs KKK+QQ: {result} (预期: True)")
    assert result, "AAA+KK应该大于KKK+QQ"
    
    # 测试9: 四个带单张比较
    print("\n测试9: 四个带单张比较")
    # 四个的数字不同
    card1 = [Card('S', 'A'), Card('H', 'A'), Card('C', 'A'), Card('D', 'A'), Card('S', 'K')]
    card2 = [Card('S', 'K'), Card('H', 'K'), Card('C', 'K'), Card('D', 'K'), Card('S', 'Q')]
    result = Game.compare_cards(card1, card2)
    print(f"四个带单张 AAAA+K vs KKKK+Q: {result} (预期: True)")
    assert result, "AAAA+K应该大于KKKK+Q"
    
    # 测试10: 同花, 花色小但是最大数大的组合之间比较
    print("\n测试10: 同花, 花色小但是最大数大的组合之间比较")
    card1 = [Card('D', '3'), Card('D', '7'), Card('D', '10'), Card('D', 'Q'), Card('D', 'K')]
    card2 = [Card('S', '3'), Card('S', '9'), Card('S', '10'), Card('S', 'J'), Card('S', 'Q')]
    result = Game.compare_cards(card1, card2)
    print(f"同花 方片3710QK vs 黑桃3910JQ: {result} (预期: True)")
    assert result, "方片3710QK应该大于黑桃3910JQ"
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    test_compare_cards()
