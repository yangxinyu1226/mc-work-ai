# src/rcon_client.py
import json
import re
from mcrcon import MCRcon

class RconClient:
    def __init__(self, server_address, rcon_password, player_id):
        self.server_address = server_address
        self.rcon_password = rcon_password
        self.player_id = player_id

    def get_player_position(self, player_name):
        """获取玩家位置，用于确定建筑的起点。"""
        try:
            with MCRcon(self.server_address, self.rcon_password) as mcr:
                response = mcr.command(f"data get entity {player_name} Pos").strip()
                
                # Find the first '[' and last ']'
                start_index = response.find('[')
                end_index = response.rfind(']')

                if start_index != -1 and end_index != -1 and start_index < end_index:
                    coord_string = response[start_index + 1 : end_index]
                    parts = coord_string.split(',')
                    if len(parts) == 3:
                        x = float(parts[0].strip().rstrip('d'))
                        y = float(parts[1].strip().rstrip('d'))
                        z = float(parts[2].strip().rstrip('d'))
                        return (True, [x, y, z])
                    else:
                        return (False, f"坐标格式不正确。捕获的字符串: '{coord_string}'")
                else:
                    return (False, f"无法从RCON响应中找到坐标括号[]。服务器响应: '{response}'")
        except Exception as e:
            return (False, f"RCON连接或命令执行失败: {e}")

    def execute_build(self, block_list):
        """连接RCON并执行所有setblock命令。"""
        if not block_list:
            print("建筑清单为空，无需执行。")
            return
        
        print(f"准备执行建造... 共计 {len(block_list)} 个方块。")
        try:
            with MCRcon(self.server_address, self.rcon_password) as mcr:
                start_msg_json = f'{{"text":"AI总规划师开始施工... 共 {len(block_list)} 个方块。","color":"gold"}}'
                mcr.command(f"tellraw @a [{start_msg_json}]")

                for i, block in enumerate(block_list):
                    cmd = f"setblock {block['x']} {block['y']} {block['z']} {block['block_type']}"
                    mcr.command(cmd)
                    if (i + 1) % 100 == 0:
                        progress_msg_json = f'{{"text":"建造进度: {i+1}/{len(block_list)}...","color":"yellow"}}'
                        mcr.command(f"tellraw @a [{progress_msg_json}]")
                
                end_msg_json = f'{{"text":"所有建筑已竣工！","color":"green"}}'
                mcr.command(f"tellraw @a [{end_msg_json}]")

            print("建造执行完毕。")
        except Exception as e:
            print(f"RCON执行期间发生错误: {e}")

def get_rcon_client():
    """从配置文件加载并返回一个RconClient实例"""
    with open('config/rcon_settings.json') as f:
        settings = json.load(f)
    
    return RconClient(
        server_address=settings['server_address'],
        rcon_password=settings['rcon_password'],
        player_id=settings['player_id']
    )
