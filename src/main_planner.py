# src/main_planner.py
import os
import sys
import time
import json
import subprocess

# 将根目录添加到 sys.path，以便可以正确地调用其他目录的脚本
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from src.util import get_llm_client, get_llm_response, read_json_file, write_json_file
from src.rcon_client import get_rcon_client
from src.key_manager import get_next_api_key

COMMAND_QUEUE_FILE = os.path.join(current_dir, '../command_queue.json')
BUILD_DIR = os.path.join(current_dir, '../build')
FINAL_PLAN_FILE = os.path.join(current_dir, '../final_build_plan.json')

def get_sub_tasks(client, prompt):
    """第一步：请求LLM将用户需求分解为生成器子任务。"""
    system_prompt = """你是一个《我的世界》项目经理。你的任务是将玩家的建筑请求分解成一个子任务列表，每个子任务都将由一个专门的"生成器"程序来处理。

可用的功能性生成器有：
- `building_generator.py`: 负责生成各种类型的建筑，如房屋、塔楼、城堡等。任务格式: `自然语言描述` (例如 "一个中式风格的二层别墅")
- `flat_land_generator.py`: 负责生成平坦的地面区域，可指定方块类型。任务格式: `自然语言描述` (例如 "一个100x100的草地平台")
- `cube_generator.py`: 负责生成各种尺寸和类型的立方体结构，可实心或空心。任务格式: `自然语言描述` (例如 "一个5x5x5的空心玻璃立方体")
- `lighting_generator.py`: 负责在建筑内部或外部添加照明。任务格式: `自然语言描述` (例如 "为房屋内部添加柔和照明")
- `landscape_generator.py`: 负责生成地形、山脉、河流、湖泊等自然景观。任务格式: `自然语言描述` (例如 "在建筑周围生成一片小山丘和一条小溪")
- `yard_generator.py`: 负责生成建筑周围的庭院、花园、围栏等。任务格式: `自然语言描述` (例如 "一个带围栏和花坛的庭院")
- `villager_generator.py`: 负责在指定位置生成村民，可指定职业。任务格式: `自然语言描述` (例如 "在村庄中心生成一个农民村民")
- `decoration_generator.py`: 负责在建筑外部添加装饰细节，如雕塑、旗帜、喷泉等。任务格式: `自然语言描述` (例如 "在别墅入口处添加一个龙形雕塑")
- `interior_generator.py`: 负责生成建筑内部的家具、房间布局和功能性物品。任务格式: `自然语言描述` (例如 "为客厅添加一套中式家具")
- `path_road_generator.py`: 负责生成各种类型的路径、道路、桥梁或隧道。任务格式: `自然语言描述` (例如 "一条通往别墅的石砖小径")

重要提示:
1.  你必须为每个任务指定一个有意义的英文名称 (`name`)，例如 `main_house`, `front_yard`, `main_path`。
2.  每个生成器都将接收一个自然语言描述作为其任务。

**示例输入:**
玩家请求: "我要建一个带院子的小房子，里面有家具，外面有路灯。"

**示例输出 (JSON格式):**
```json
[
  {
    "generator": "building_generator.py",
    "name": "small_house",
    "task": "一个带窗户和门的简单小房子"
  },
  {
    "generator": "yard_generator.py",
    "name": "house_yard",
    "task": "一个带围栏和花坛的院子"
  },
  {
    "generator": "interior_generator.py",
    "name": "house_furniture",
    "task": "为小房子内部添加基本家具"
  },
  {
    "generator": "lighting_generator.py",
    "name": "outdoor_lights",
    "task": "沿院子小径添加路灯"
  }
]
```

请严格按照JSON格式返回，不要包含任何额外说明。"""    
    user_prompt = f"玩家请求: \"{prompt}\""
    
    print("总规划师：正在请求大模型分解任务...")
    success, sub_tasks = get_llm_response(client, system_prompt, user_prompt)
    
    if success:
        print(f"总规划师：成功获取子任务列表: {sub_tasks}")
    else:
        print(f"总规划师：获取子任务失败: {sub_tasks}")
        
    return success, sub_tasks

def clear_build_directory():
    """Clear all .json files in build directory."""
    print("总规划师：正在清理 build 目录...")
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
        return
        
    for file_name in os.listdir(BUILD_DIR):
        if file_name.endswith('.json'):
            os.remove(os.path.join(BUILD_DIR, file_name))
    # 同时删除旧的最终规划文件
    if os.path.exists(FINAL_PLAN_FILE):
        os.remove(FINAL_PLAN_FILE)

def run_generators(sub_tasks):
    """第二步：执行所有生成器子任务。"""
    print("总规划师：正在启动生成器...")
    for task in sub_tasks:
        generator_script = os.path.join(current_dir, '../generators', task['generator'])
        
        # 所有功能性生成器都使用 --prompt
        cmd = [
            sys.executable,
            generator_script,
            '--name', task['name'],
            '--prompt', task['task']
        ]
        
        print(f"总规划师：运行指令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    print("总规划师：所有生成器执行完毕。")

def run_supervisor(prompt):
    """第三步：执行监理师程序。"""
    print("总规划师：正在启动监理师...")
    supervisor_script = os.path.join(current_dir, '../supervisor/supervisor.py')
    cmd = [
        sys.executable,
        supervisor_script,
        '--prompt', prompt
    ]
    subprocess.run(cmd, check=True)
    print("总规划师：监理师执行完毕。")

def main():
    print("AI建筑总规划师已启动（新架构）...")
    
    # 使用密钥管理器获取密钥并初始化客户端
    api_key = get_next_api_key()
    llm_client = get_llm_client(api_key)
    rcon_client = get_rcon_client()

    while True:
        try:
            # 1. 等待新指令
            requests = read_json_file(COMMAND_QUEUE_FILE)
            if not requests:
                time.sleep(1)
                continue
            
            request_data = requests.pop(0)
            
            if not isinstance(request_data, dict) or 'prompt' not in request_data or 'player' not in request_data:
                print(f"警告：队列中发现无效指令格式，已跳过: {request_data}")
                write_json_file(COMMAND_QUEUE_FILE, requests)  # Save the queue after popping invalid entry
                continue

            prompt = request_data['prompt']
            player_name = request_data['player']
            write_json_file(COMMAND_QUEUE_FILE, requests)
            print(f"总规划师：接收到新任务: '{prompt}' (来自玩家: {player_name})")

            # 工作流程开始
            # -----------------------------------------------------
            
            # 0. 清理工作目录
            clear_build_directory()

            # 1. 获取子任务
            success, sub_tasks = get_sub_tasks(llm_client, prompt)
            if not success:
                continue

            # 2. 运行生成器
            run_generators(sub_tasks)

            # 3. 运行监理师
            run_supervisor(prompt)

            # 4. 组装并执行最终计划
            print("总规划师：正在组装最终建筑方案...")
            final_plan = read_json_file(FINAL_PLAN_FILE)
            if not final_plan:
                print("总规划师：错误：找不到最终规划文件。建造中止。")
                continue

            pos_success, pos_result = rcon_client.get_player_position(player_name)
            if not pos_success:
                print(f"总规划师：执行失败，无法获取玩家位置: {pos_result}")
                continue
            base_x, base_y, base_z = pos_result

            final_block_list = []
            for component_plan in final_plan:
                component_file = os.path.join(BUILD_DIR, component_plan['file_name'])
                component_data = read_json_file(component_file)
                if not component_data:
                    print(f"警告：找不到组件文件 {component_plan['file_name']}，已跳过。")
                    continue
                
                offset = component_plan.get('offset', {'x': 0, 'y': 0, 'z': 0})
                for block in component_data.get('blocks', []):
                    final_block_list.append({
                        'x': int(base_x + offset.get('x', 0) + block['x']),
                        'y': int(base_y + offset.get('y', 0) + block['y']),
                        'z': int(base_z + offset.get('z', 0) + block['z']),
                        'block_type': block['block_type']
                    })
            
            print(f"总规划师：组装完成，总计 {len(final_block_list)} 个方块。准备施工！")
            rcon_client.execute_build(final_block_list)

        except FileNotFoundError as e:
            print(f"主循环发生文件未找到错误: {e}")
            time.sleep(1)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"主循环发生数据错误: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"主循环发生致命错误: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()