#%%
import gym
import numpy as np
import argparse
import json

from gym import spaces
from godot_rl.core.godot_env import GodotEnv
from godot_rl.core.utils import lod_to_dol
import time

def encode_escolhas(ids_tarefas):
    # Cria uma sequência de dígitos binários correspondente aos IDs das tarefas,
    # adicionando zeros à esquerda para que cada ID tenha 6 dígitos binários
    escolhas_bin = ''.join(format(id_tarefa, '06b') for id_tarefa in ids_tarefas)
    # Converte a sequência de dígitos binários para um número inteiro
    escolhas_int = int(escolhas_bin, 2)
    return escolhas_int

def decode_escolhas(escolhas_int, num_tarefas):
    # Converte o número inteiro para uma sequência de dígitos binários com zero à esquerda
    escolhas_bin = bin(escolhas_int)[2:].zfill(num_tarefas * 6)
    # Separa a sequência de dígitos binários em grupos de 6 para obter os IDs das tarefas
    ids_tarefas = [int(escolhas_bin[i:i+6], 2) for i in range(0, len(escolhas_bin), 6)]
    return ids_tarefas


parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument(
    "--env_path",
    default="BVR_AirCombat/bin/FlyBy.exe",#envs/example_envs/builds/JumperHard/jumper_hard.x86_64",
    #default=None,
    type=str,
    help="The Godot binary to use, do not include for in editor training",
)

parser.add_argument("--speedup", default=150, type=int, help="whether to speed up the physics in the env")
parser.add_argument("--show_window", default=False, type=bool, help="whether renderize or not the screen")

args, extras = parser.parse_known_args()

env = GodotEnv( env_path=args.env_path,
         port=11008,
         show_window=True,
         seed=0,
         framerate=None,
         action_repeat=10,
         speedup=args.speedup,
         convert_action_space=False,         
         )

episodes = 2

start_time = time.time()

for e in range(episodes):
    
    env.reset()
    for i in range(300):
        
        action = env.action_space.sample()
                
        #print("Action\n", action)
        action = [np.array([0.0,0.0]) for x in action for _ in range(env.num_envs)]
            
                           
        # Rescale and perform action
        #clipped_actions = action
        # Clip the actions to avoid out of bound error
        #if isinstance(env.action_space, spaces.Box):
        #    clipped_actions = np.clip(action, env.action_space.low, env.action_space.high)
        
        #clipped_actions = np.array([clipped_actions[0],clipped_actions[1]])
        #print("\n",clipped_actions)            
        #action =  np.ndarray([0.5, 0.5])
        obs, reward, done, trunc, info = env.step(action, order_ij=True)
        #print (done)
        
        if False not in done:
           break 
        
        #print (info)
        #print ("\n",action)
        #print(obs)

end_time = time.time()
execution_time = end_time - start_time
print("Execution time:", execution_time, "seconds")

env.close()
# %%
