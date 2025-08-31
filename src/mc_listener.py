# src/mc_listener.py
import re
import tailer
import json
import os
import time

# 定义文件路径
# 由于此脚本在 src/ 目录下运行，因此需要使用相对路径返回上一级
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/rcon_settings.json')
QUEUE_PATH = os.path.join(os.path.dirname(__file__), '../command_queue.json')

# 确保 command_queue.json 文件存在
if not os.path.exists(QUEUE_PATH):
    with open(QUEUE_PATH, "w") as f:
        json.dump([], f)

# 加载配置
with open(CONFIG_PATH) as f:
    config = json.load(f)

LOG_FILE_PATH = config['log_file_path']
PLAYER_ID = config['player_id']

print("正在监听服务器日志文件...")
# 为了效率，在循环外编译正则表达式
chat_pattern = re.compile(r'\[.+\] \[(?:Server thread/INFO|Async Chat Thread - #\d+/INFO)\]: <(.+?)> ?(.*)')

try:
    # 使用 'gbk' 编码, 这在某些地区的Windows系统上很常见，并且可能适用于此服务器日志。
    for line in tailer.follow(open(LOG_FILE_PATH, encoding='gbk', errors='replace')):
        try:
            match = chat_pattern.search(line)
            
            if match:
                sender = match.group(1)
                message = match.group(2)
                
                # 检查消息是否以特定前缀开头
                if message.lower().startswith("!build "):
                    # 提取指令内容
                    prompt = message[len("!build "):].strip()
                    
                    if not prompt:
                        continue

                    print(f"检测到玩家 {sender} 的请求: {prompt}")

                    # 将请求添加到队列文件
                    # Ensure the file exists and is initialized before reading/writing
                    if not os.path.exists(QUEUE_PATH) or os.path.getsize(QUEUE_PATH) == 0:
                        with open(QUEUE_PATH, "w") as f:
                            json.dump([], f)

                    with open(QUEUE_PATH, "r+") as f:
                        requests = json.load(f)
                        requests.append({"player": sender, "prompt": prompt})
                        f.seek(0)
                        json.dump(requests, f)
                        f.truncate()
                    print("请求已添加到队列。")
        except Exception as e:
            print(f"处理单行日志时出错: {e} - 日志行: {line.strip()}")
            continue

except FileNotFoundError:
    print(f"错误: 找不到日志文件，请检查路径配置: {LOG_FILE_PATH}")
except Exception as e:
    print(f"监听日志文件时发生致命错误: {e}")
