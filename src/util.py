# src/util.py
import json
import os
import openai

# ==============================================================================
#                             文件读写工具
# ==============================================================================

def read_json_file(file_path):
    """读取并解析JSON文件。"""
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"读取或解析JSON文件时出错 {file_path}: {e}")
        return None

def write_json_file(file_path, data):
    """将数据写入JSON文件。"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"写入JSON文件时出错 {file_path}: {e}")

# ==============================================================================
#                             API 相关工具
# ==============================================================================

def load_api_key_list():
    """从 config/api_keys_list.json 加载API密钥列表。"""
    keys_path = os.path.join(os.path.dirname(__file__), '../config/api_keys_list.json')
    return read_json_file(keys_path)

def get_llm_client(api_key):
    """根据提供的API Key获取大语言模型API客户端。"""
    if not api_key:
        raise ValueError("API Key不能为空。")
    
    return openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )

def get_llm_response(client, system_prompt, user_prompt):
    """
    请求LLM获取响应。

    :param client: OpenAI API客户端实例。
    :param system_prompt: 系统提示词。
    :param user_prompt: 用户提示词。
    :return: (成功状态, 响应内容或错误信息)
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4096,
            temperature=0.7, # 提高一点温度以增加创造性
        )
        
        text_response = response.choices[0].message.content.strip()
        
        if not text_response:
            return (False, "LLM 返回了空响应。")
        
        # 移除可能的代码块标记
        if text_response.startswith('```json'):
            text_response = text_response[len('```json'):].strip()
        if text_response.endswith('```'):
            text_response = text_response[:-len('```')].strip()
            
        return (True, json.loads(text_response))

    except json.JSONDecodeError as e:
        return (False, f"解析LLM响应的JSON时发生错误: {e}\n原始响应: {text_response}")
    except Exception as e:
        return (False, f"调用 LLM API 时发生错误: {e}")

# ==============================================================================
#                             几何形状生成器
# ==============================================================================

def generate_blocks_from_task(task):
    """根据任务描述调用相应的形状生成器。"""
    tool_map = {
        'cube': generate_cube,
        'line': generate_line,
        'sphere': generate_sphere,
        'hollow_cube': lambda **kwargs: generate_cube(hollow=True, **kwargs),
        'hollow_sphere': lambda **kwargs: generate_sphere(hollow=True, **kwargs),
        'cylinder': generate_cylinder,
        'pyramid': generate_pyramid,
        'circle': generate_circle,
        'arch': generate_arch,
        'single_block': lambda **kwargs: generate_cube(size_x=1, size_y=1, size_z=1, **kwargs),
    }
    tool_name = task.get('tool')
    if tool_name in tool_map:
        return tool_map[tool_name](**task.get('args', {}))
    return []

def generate_cube(hollow=False, **kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    z = kwargs.get('z', 0)
    size_x = kwargs.get('size_x', 1)
    size_y = kwargs.get('size_y', 1)
    size_z = kwargs.get('size_z', 1)
    block_type = kwargs.get('block_type', 'stone')
    
    blocks = []
    for i in range(size_x):
        for j in range(size_y):
            for k in range(size_z):
                is_shell = (i == 0 or i == size_x - 1 or j == 0 or j == size_y - 1 or k == 0 or k == size_z - 1)
                if not hollow or is_shell:
                    blocks.append({'x': x + i, 'y': y + j, 'z': z + k, 'block_type': block_type})
    return blocks

def generate_line(**kwargs):
    x1 = kwargs.get('x1', 0)
    y1 = kwargs.get('y1', 0)
    z1 = kwargs.get('z1', 0)
    x2 = kwargs.get('x2', 0)
    y2 = kwargs.get('y2', 0)
    z2 = kwargs.get('z2', 0)
    block_type = kwargs.get('block_type', 'stone')

    blocks = []
    dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
    steps = max(abs(dx), abs(dy), abs(dz))
    if steps == 0:
        return [{'x': x1, 'y': y1, 'z': z1, 'block_type': block_type}]
    
    x_inc, y_inc, z_inc = dx / steps, dy / steps, dz / steps
    x, y, z = float(x1), float(y1), float(z1)
    for _ in range(int(steps) + 1):
        blocks.append({'x': round(x), 'y': round(y), 'z': round(z), 'block_type': block_type})
        x += x_inc
        y += y_inc
        z += z_inc
    return blocks

def generate_sphere(hollow=False, **kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    z = kwargs.get('z', 0)
    radius = kwargs.get('radius', 5)
    block_type = kwargs.get('block_type', 'stone')

    blocks = []
    r_sq = radius * radius
    inner_r_sq = (radius - 1) * (radius - 1)

    for i in range(-radius, radius + 1):
        for j in range(-radius, radius + 1):
            for k in range(-radius, radius + 1):
                dist_sq = i*i + j*j + k*k
                if dist_sq <= r_sq:
                    if not hollow or dist_sq > inner_r_sq:
                        blocks.append({'x': x + i, 'y': y + j, 'z': z + k, 'block_type': block_type})
    return blocks

def generate_cylinder(hollow=False, **kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    z = kwargs.get('z', 0)
    radius = kwargs.get('radius', 5)
    height = kwargs.get('height', 10)
    block_type = kwargs.get('block_type', 'stone')

    blocks = []
    r_sq = radius * radius
    inner_r_sq = (radius - 1) * (radius - 1)
    for j in range(height):
        for i in range(-radius, radius + 1):
            for k in range(-radius, radius + 1):
                dist_sq = i*i + k*k
                if dist_sq <= r_sq:
                    if not hollow or dist_sq > inner_r_sq:
                        blocks.append({'x': x + i, 'y': y + j, 'z': z + k, 'block_type': block_type})
    return blocks

def generate_pyramid(**kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    z = kwargs.get('z', 0)
    base_size = kwargs.get('base_size', 10)
    block_type = kwargs.get('block_type', 'sandstone')

    blocks = []
    height = (base_size + 1) // 2
    for j in range(height):
        layer_size = base_size - 2 * j
        if layer_size <= 0: break
        offset = j
        for i in range(layer_size):
            for k in range(layer_size):
                blocks.append({'x': x + i + offset, 'y': y + j, 'z': z + k + offset, 'block_type': block_type})
    return blocks

def generate_circle(hollow=False, **kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    z = kwargs.get('z', 0)
    radius = kwargs.get('radius', 5)
    block_type = kwargs.get('block_type', 'stone')

    blocks = []
    r_sq = radius * radius
    inner_r_sq = (radius - 1) * (radius - 1)
    for i in range(-radius, radius + 1):
        for k in range(-radius, radius + 1):
            dist_sq = i*i + k*k
            if dist_sq <= r_sq:
                if not hollow or dist_sq > inner_r_sq:
                    blocks.append({'x': x + i, 'y': y, 'z': z + k, 'block_type': block_type})
    return blocks

def generate_arch(**kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    z = kwargs.get('z', 0)
    radius = kwargs.get('radius', 5)
    width = kwargs.get('width', 3)
    block_type = kwargs.get('block_type', 'stone_bricks')

    blocks = []
    for k in range(width):
        for i in range(-radius, radius + 1):
            for j in range(radius + 1):
                # Equation for a semicircle
                if abs(i*i + j*j - radius*radius) < radius:
                    blocks.append({'x': x + i, 'y': y + j, 'z': z + k, 'block_type': block_type})
    return blocks
