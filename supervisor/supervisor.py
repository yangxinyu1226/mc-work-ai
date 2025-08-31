# supervisor/supervisor.py
import argparse
import os
import sys
import json

# 将 src 目录添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from src.util import get_llm_client, get_llm_response, read_json_file, write_json_file
from src.key_manager import get_next_api_key # Added this import

def main():
    parser = argparse.ArgumentParser(description="监理师：整合所有建筑部件并生成最终建造规划。")
    parser.add_argument("--prompt", type=str, required=True, help="玩家的原始建筑指令。")

    args = parser.parse_args()

    print("监理师已启动...正在检查 build 目录。")

    build_dir = os.path.join(current_dir, '../build')
    if not os.path.exists(build_dir) or not os.listdir(build_dir):
        print("监理师：build 目录为空，无需执行。")
        return

    # 1. 读取所有生成的JSON文件
    build_components = []
    component_files = [f for f in os.listdir(build_dir) if f.endswith('.json')]
    for file_name in component_files:
        file_path = os.path.join(build_dir, file_name)
        component_data = read_json_file(file_path)
        if component_data:
            # 包含完整的 component_data，其中应包含 generated_structure 和 spatial_metadata
            build_components.append({
                "file_name": file_name,
                "description": component_data.get("description"),
                "generated_structure": component_data.get("generated_structure", {}),
                "blocks_count": len(component_data.get("blocks", []))
            })

    if not build_components:
        print("监理师：未能从 build 目录加载任何建筑组件。")
        return

    print(f"监理师：找到了 {len(build_components)} 个建筑组件。")

    # 2. 构建发送给LLM的提示
    system_prompt = """你是一个顶级的《我的世界》建筑结构工程师。你的任务是将一系列分散的建筑组件，根据玩家的原始意图，组合成一个完整、协调、美观且无冲突的建筑。

你收到的输入包含两部分：
1. `original_prompt`: 玩家的原始指令。
2. `components`: 一个JSON列表，其中每个对象代表一个已由“生成器”程序创建好的建筑组件。每个组件都包含：
   - `file_name`: 组件的文件名。
   - `description`: 组件的自然语言描述。
   - `generated_structure`: 包含该组件的详细设计信息，特别是`spatial_metadata`，其中有`bounding_box` (min_x, min_y, min_z, max_x, max_y, max_z) 和 `dimensions` (width, height, depth)。
   - `blocks_count`: 该组件包含的方块数量。

你的任务是决定每个组件在最终建筑中的相对位置。你需要输出一个JSON数组，其中每个元素都包含：
- `file_name`: 组件的文件名。
- `offset`: 一个包含 `x`, `y`, `z` 的对象，代表这个组件相对于总建筑基点(0,0,0)的偏移量。

请仔细分析玩家的意图和每个组件的功能及其空间信息（`bounding_box`和`dimensions`），给出一个合理且**无重叠**的空间布局。确保所有组件都放置在逻辑上合理的位置，例如地基在最下面，墙壁在地基之上，屋顶在最顶端，道路连接各个区域，景观与建筑协调。

**特别注意：**
- **坐标系**：所有偏移量都是相对于整个建筑的基点(0,0,0)的相对坐标。请确保`y`坐标从地面（通常是0或1）开始向上递增。
- **避免重叠**：这是最重要的规则。任何两个组件的边界框在最终布局中都不能有重叠。请利用`bounding_box`和`dimensions`信息进行精确计算。
- **逻辑连接和层次**：例如，平坦地形（flat_land_generator）通常是基础，应该放置在最低层。建筑（building_generator）应该放置在平坦地形上。道路（path_road_generator）应该连接不同的区域。
- **自下而上，由内而外**：考虑从基础开始，逐步向上和向外放置组件。

**示例输出格式:**
```json
[
  {
    "file_name": "base_platform_flat_land_generator.json",
    "offset": {"x": -50, "y": 0, "z": -50}
  },
  {
    "file_name": "main_building_building_generator.json",
    "offset": {"x": 0, "y": 1, "z": 0}
  },
  {
    "file_name": "surrounding_yard_yard_generator.json",
    "offset": {"x": -10, "y": 0, "z": -10}
  },
  {
    "file_name": "main_path_path_road_generator.json",
    "offset": {"x": -5, "y": 1, "z": -5}
  }
]
```

请只返回最终的JSON布局数组，不要包含任何其他解释。"""

    user_prompt_data = {
        "original_prompt": args.prompt,
        "components": build_components
    }
    user_prompt = json.dumps(user_prompt_data, indent=2, ensure_ascii=False)

    print("监理师：正在请求大模型进行最终规划...")

    # 3. 调用LLM
    try:
        api_key = get_next_api_key()
        client = get_llm_client(api_key)
        success, final_plan = get_llm_response(client, system_prompt, user_prompt)

        if not success:
            print(f"监理师：大模型规划失败: {final_plan}")
            sys.exit(1)

        print("监理师：成功从大模型获取最终布局规划。")

        # 4. 保存最终规划
        final_plan_path = os.path.join(build_dir, '../final_build_plan.json')
        write_json_file(final_plan_path, final_plan)

        print(f"监理师：最终建筑规划已保存到 {final_plan_path}")

    except Exception as e:
        print(f"监理师在执行过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()