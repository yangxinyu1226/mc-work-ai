import os
import sys
import json
import argparse

# 将根目录添加到 sys.path，以便可以正确地调用其他目录的脚本
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from src.util import get_llm_client, get_llm_response, write_json_file
from src.key_manager import get_next_api_key

BUILD_DIR = os.path.join(current_dir, '../build')

class VillagerGenerator:
    """
    村民生成器 - 负责在指定位置生成村民，可指定职业。
    """
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate(self, description: str) -> dict:
        """
        根据描述生成村民。
        Args:
            description: 村民的自然语言描述，例如 "在(10, 64, 10)生成一个农民村民"。
        Returns:
            一个字典，包含村民的生成指令。
        """
        print(f"VillagerGenerator: Generating villager for description: {description}")

        system_prompt = """你是一个Minecraft实体生成设计师。你的任务是根据用户的描述，设计一个Minecraft村民的生成位置和职业，并输出一个JSON对象。这个JSON对象应该包含'x'、'y'、'z'坐标和'profession'字段。

示例输出:
```json
{
  "x": 10,
  "y": 64,
  "z": 10,
  "profession": "farmer"
}
```

重要提示:
1.  所有坐标都是相对坐标，以(0,0,0)为基准。
2.  'profession'必须是有效的Minecraft村民职业ID，例如'farmer'、'librarian'、'armorer'等。
3.  请严格按照JSON对象格式返回，不要包含任何额外说明或代码块标记。"""    
        user_prompt = f"生成一个Minecraft村民：{description}"
        print(f"VillagerGenerator: Sending prompt to LLM: {user_prompt}")

        success, llm_output = get_llm_response(self.llm_client, system_prompt, user_prompt)

        if not success:
            print(f"VillagerGenerator: Error from LLM: {llm_output}")
            return {"description": description, "generated_structure": {}, "blocks": []}
        
        generated_villager_data = llm_output
        print(f"VillagerGenerator: Received LLM output: {generated_villager_data}")

        actual_block_commands = []
        # For now, we place a placeholder block at the villager's location.
        # Actual entity spawning would require a different mechanism in main_planner/supervisor.
        if all(k in generated_villager_data for k in ['x', 'y', 'z']):
            actual_block_commands.append({
                "x": generated_villager_data['x'],
                "y": generated_villager_data['y'],
                "z": generated_villager_data['z'],
                "block_type": "minecraft:barrier" # Using barrier for visibility during debugging, can be air
            })

        build_plan = {
            "description": description,
            "generated_structure": generated_villager_data, # Store the LLM's structured output
            "blocks": actual_block_commands
        }

        print(f"VillagerGenerator: Finished generating plan for: {description}")
        return build_plan

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Villager Generator for Minecraft AI Builder.')
    parser.add_argument('--name', type=str, required=True, help='Name of the task.')
    parser.add_argument('--prompt', type=str, required=True, help='Natural language prompt for generation.')
    args = parser.parse_args()

    api_key = get_next_api_key()
    llm_client = get_llm_client(api_key)

    generator = VillagerGenerator(llm_client)
    build_plan = generator.generate(args.prompt)

    output_filename = f"{args.name}_{os.path.splitext(os.path.basename(__file__))[0]}.json"
    output_filepath = os.path.join(BUILD_DIR, output_filename)
    write_json_file(output_filepath, build_plan)
    print(f"VillagerGenerator: Saved build plan to {output_filepath}")