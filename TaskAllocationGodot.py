#%%
import gym
import numpy as np
import argparse
import json

from gym import spaces
from godot_rl.core.godot_env import GodotEnv
from godot_rl.core.utils import lod_to_dol
import time


parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument(
    "--env_path",
    default="BVR_AirCombat/bin/FlyBy.exe",#envs/example_envs/builds/JumperHard/jumper_hard.x86_64",
    #default=None,
    type=str,
    help="The Godot binary to use, do not include for in editor training",
)

parser.add_argument("--speedup", default=100, type=int, help="whether to speed up the physics in the env")
parser.add_argument("--show_window", default=False, type=bool, help="whether renderize or not the screen")

args, extras = parser.parse_known_args()

env = GodotEnv( env_path=args.env_path,
         port=11008,
         show_window=True,
         seed=0,
         framerate=None,
         action_repeat=10,
         speedup=args.speedup,
         convert_action_space=False        
         )

episodes = 1

start_time = time.time()

for e in range(episodes):
    
    print(e)
    env.reset()
    
    #print(env.num_envs)
    for i in range(1000):
        
        action = env.action_space.sample()
                
        #print("Action\n", action)
        action = [np.array([0, 0, 20000, 0]) for x in action for i in range(env.num_envs)]
        
        # hdg_input = action["hdg"]
	    # level_input = action["level"] * SConv.FT2GDM	
	    # desiredG_input = action["maxG"]
	    # shoot_input = action["shoot"]
            
                           
        # Rescale and perform action
        #clipped_actions = action
        # Clip the actions to avoid out of bound error
        #if isinstance(env.action_space, spaces.Box):
        #    clipped_actions = np.clip(action, env.action_space.low, env.action_space.high)
        
        #clipped_actions = np.array([clipped_actions[0],clipped_actions[1]])
        #print("\n",clipped_actions)            
        #action =  np.ndarray([0.5, 0.5])
        obs, reward, done, trunc, info = env.step(action, order_ij=True)
        print (obs)
        
        if False not in done:
           break 
        
        # print (info)
        #print ("\n",action)
        #print(obs)

end_time = time.time()
execution_time = end_time - start_time
print("Execution time:", execution_time, "seconds")

env.close()
# %%

 # %%
