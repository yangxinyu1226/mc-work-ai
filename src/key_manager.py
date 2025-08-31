# src/key_manager.py
import json
import os
import sys

# 确保可以从父目录导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from src.util import read_json_file, write_json_file

API_KEYS_LIST_PATH = os.path.join(current_dir, '../config/api_keys_list.json')
KEY_STATE_PATH = os.path.join(current_dir, '../config/key_state.json')

def get_next_api_key():
    """
    从列表中循环获取下一个API密钥。
    通过读写 key_state.json 来跟踪上一个使用的密钥索引。
    """
    # 1. 加载所有可用的API密钥
    api_keys = read_json_file(API_KEYS_LIST_PATH)
    if not api_keys:
        raise ValueError(f"API密钥列表为空或不存在于 {API_KEYS_LIST_PATH}")

    # 2. 加载上一次使用的密钥索引
    state = read_json_file(KEY_STATE_PATH)
    last_index = -1
    if state and 'last_used_index' in state:
        last_index = state['last_used_index']

    # 3. 计算下一个要使用的密钥索引（循环）
    next_index = (last_index + 1) % len(api_keys)

    # 4. 更新并保存状态
    write_json_file(KEY_STATE_PATH, {'last_used_index': next_index})

    # 5. 返回下一个密钥
    print(f"密钥管理器：正在使用索引为 {next_index} 的密钥。")
    return api_keys[next_index]
