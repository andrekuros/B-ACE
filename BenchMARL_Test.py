
#%%%
# Parallel env
from torchrl.envs.libs.pettingzoo import PettingZooWrapper
from GodotRLPettingZooWrapper import GodotRLPettingZooWrapper

from GodotRLPettingZooWrapper import GodotRLPettingZooWrapper

def wenv():
    return PettingZooWrapper(
                env=GodotRLPettingZooWrapper(   env_path="BVR_AirCombat/bin/FlyBy.exe", 
                                                num_agents = 2 , 
                                                show_window=True, 
                                                seed = 0,
                                                framerate = None,
                                                action_repeat = 10,
                                                speedup  = 100,
                                                convert_action_space = False),

                    use_mask=False, # Must use it since one player plays at a time
                    group_map=None # # Use default for AEC (one group per player)
                    
                )


env = wenv()

# env = GodotRLPettingZooWrapper(   env_path="BVR_AirCombat/bin/FlyBy.exe", 
#                                                 num_agents = 2 , 
#                                                 show_window=True, 
#                                                 seed = 0,
#                                                 framerate = None,
#                                                 action_repeat = 10,
#                                                 speedup  = 100,
#                                                 convert_action_space = False)

# 

print(env.group_map)
print(env.observation_spec)
result = env.reset()

# #%%%
# # AEC env
# from pettingzoo.classic import tictactoe_v3
# from torchrl.envs.libs.pettingzoo import PettingZooWrapper
# from torchrl.envs.utils import MarlGroupMapType

# env = PettingZooWrapper(
#                     env=LeadingOnesTrailingZerosEnv(),
#                     use_mask=True, # Must use it since one player plays at a time
#                     group_map=None # # Use default for AEC (one group per player)
#                 )
# print(env.group_map)

# {'player_1': ['player_1'], 'player_2': ['player_2']}
env.rollout(100)

# %%
