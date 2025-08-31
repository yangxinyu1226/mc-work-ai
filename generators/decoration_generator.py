import os
import sys
import json
import argparse

# 将根目录添加到 sys.path，以便可以正确地调用其他目录的脚本
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from src.util import get_llm_client, get_llm_response, write_json_file, generate_blocks_from_task
from src.key_manager import get_next_api_key

BUILD_DIR = os.path.join(current_dir, '../build')

class DecorationGenerator:
    """
    装饰生成器 - 负责在建筑外部添加装饰细节，如雕塑、旗帜、喷泉等。
    """
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate(self, description: str) -> dict:
        """
        根据描述生成装饰。
        Args:
            description: 装饰的自然语言描述，例如 "在建筑入口处放置一个喷泉"。
        Returns:
            一个字典，包含装饰的方块布局和结构信息。
        """
        print(f"DecorationGenerator: Generating decoration for description: {description}")

        system_prompt = """你是一个Minecraft装饰设计师。你的任务是根据用户的描述，设计一个Minecraft装饰，并输出一个JSON数组，其中每个元素都是一个几何图元生成任务。每个任务都必须包含'tool'和'args'字段。

可用的几何图元工具及其参数示例：
- 'cube': {'x': 0, 'y': 0, 'z': 0, 'size_x': 1, 'size_y': 1, 'size_z': 1, 'block_type': 'minecraft:stone_bricks'}
- 'cylinder': {'x': 0, 'y': 0, 'z': 0, 'radius': 3, 'height': 1, 'block_type': 'minecraft:water'}
- 'single_block': {'x': 0, 'y': 0, 'z': 0, 'block_type': 'minecraft:torch'}
- 'arch': {'x': 0, 'y': 0, 'z': 0, 'radius': 5, 'width': 3, 'block_type': 'minecraft:stone_bricks'}

重要提示:
1.  所有坐标都是相对坐标，以(0,0,0)为基准。
2.  'block_type'必须是有效的Minecraft方块ID，例如'minecraft:stone_bricks'、'minecraft:water'、'minecraft:red_banner'。
3.  请严格按照JSON数组格式返回，不要包含任何额外说明或代码块标记。"""    
        user_prompt = f"设计一个Minecraft装饰：{description}"
        print(f"DecorationGenerator: Sending prompt to LLM: {user_prompt}")

        success, llm_output = get_llm_response(self.llm_client, system_prompt, user_prompt)

        if not success:
            print(f"DecorationGenerator: Error from LLM: {llm_output}")
            return {"description": description, "generated_structure": {}, "blocks": []}
        
        generated_components = llm_output
        print(f"DecorationGenerator: Received LLM output: {generated_components}")

        actual_block_commands = []
        for component_task in generated_components:
            blocks = generate_blocks_from_task(component_task)
            actual_block_commands.extend(blocks)

        # Calculate bounding box and dimensions
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

        if actual_block_commands:
            for block in actual_block_commands:
                min_x = min(min_x, block['x'])
                min_y = min(min_y, block['y'])
                min_z = min(min_z, block['z'])
                max_x = max(max_x, block['x'])
                max_y = max(max_y, block['y'])
                max_z = max(max_z, block['z'])
            
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            depth = max_z - min_z + 1
        else:
            min_x, min_y, min_z = 0, 0, 0
            max_x, max_y, max_z = 0, 0, 0
            width, height, depth = 0, 0, 0

        spatial_metadata = {
            "bounding_box": {
                "min_x": min_x, "min_y": min_y, "min_z": min_z,
                "max_x": max_x, "max_y": max_y, "max_z": max_z
            },
            "dimensions": {"width": width, "height": height, "depth": depth}
        }

        final_generated_structure = {
            "design_components": generated_components,
            "spatial_metadata": spatial_metadata
        }

        build_plan = {
            "description": description,
            "generated_structure": final_generated_structure,
            "blocks": actual_block_commands
        }

        print(f"DecorationGenerator: Finished generating plan for: {description}")
        return build_plan

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decoration Generator for Minecraft AI Builder.')
    parser.add_argument('--name', type=str, required=True, help='Name of the task.')
    parser.add_argument('--prompt', type=str, required=True, help='Natural language prompt for generation.')
    args = parser.parse_args()

    api_key = get_next_api_key()
    llm_client = get_llm_client(api_key)

    generator = DecorationGenerator(llm_client)
    build_plan = generator.generate(args.prompt)

    output_filename = f"{args.name}_{os.path.splitext(os.path.basename(__file__))[0]}.json"
    output_filepath = os.path.join(BUILD_DIR, output_filename)
    write_json_file(output_filepath, build_plan)
    print(f"DecorationGenerator: Saved build plan to {output_filepath}")
