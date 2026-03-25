import sqlite3
import random
from typing import Dict, List
import re


def get_word_count(database_path: str) -> int:
    """查询 englishwords 表的总行数, 当前db文件一共有103971条
    
    Args:
        database_path: SQLite 数据库文件路径
        
    Returns:
        表中的总行数，如果出错返回 0
    """
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM englishwords")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return 0

def clean_meaning(meaning_str):
    ## trim
    meaning_str = meaning_str.strip()
    ## remove attribute
    meaning_str = re.sub(r'[a-z.&]+\.', ' ', meaning_str)
    ## remove [****]
    meaning_str = re.sub(r'\[.+\]', '', meaning_str)
    ## remove <****>
    meaning_str = re.sub(r'\<.+\>', '', meaning_str)

    return meaning_str

def merge_abbrivation(meaning_list: List[str]) -> List[str]:
    """合并缩写单词, 例如 ['Shielded', 'Twisted', 'Pair', '屏蔽双绞线', 'Spanning', 'Tree', 'protocol', '生成树协议'] 合并为 ['Shielded Twisted Pair', '屏蔽双绞线', 'Spanning Tree protocol', '生成树协议']
    Args:
        meaning_list: 单词的中文翻译列表
    Returns:
        合并后的中文翻译列表
    """
    eng_pattern = re.compile(r'[A-Za-z]+')
    eng_list = []
    new_meaning_list = []
    for w in meaning_list:
        if eng_pattern.match(w):
            eng_list.append(w)
        else:
            # reach a non-eng word, join collected eng words
            if eng_list:
                new_meaning_list.append(' '.join(eng_list))
                eng_list = []
            new_meaning_list.append(w)
    # append last eng words
    if eng_list:
        new_meaning_list.append(' '.join(eng_list))

    return new_meaning_list


def get_random_word_list(database_path: str, size:int=500) -> Dict[str, List[str]]:
    """查询出随机的一组单词
    Args:
        database_path: SQLite 数据库文件路径
        size: 需要单词数量
    Returns:
        单词与中文翻译的字典
    """
    max_size = 103971 # get_word_count(database_path)
    random_rowid_list = [random.randint(1, max_size) for _ in range(size)]
    str_row_id_list = ','.join([str(n) for n in random_rowid_list])
    word_dict = {}
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        sql_stat = f"select word, meaning from englishwords where  rowid in ({str_row_id_list});"
        
        cursor.execute(sql_stat)
        for row in cursor:
            word_dict[row[0]] = merge_abbrivation([m for m in clean_meaning(row[1]).split(' ') if m != ''])
        return word_dict
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return None


# if __name__ == "__main__":
#     db_path = "englishwords.db"
#     wd = get_random_word_list(db_path, 200)
#     print(f"数据库 {db_path} 中 englishwords 表的总行数为: {len(wd)}")
