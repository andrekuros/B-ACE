import os
import sys
from pathlib import Path
import datetime
from typing import Optional, Tuple
import random
import json
import numpy as np
import torch

script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)
project_root = script_dir.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from b_ace_py.B_ACE_GodotPettingZooWrapper import  B_ACE_GodotPettingZooWrapper
from b_ace_py.utils import load_b_ace_config

from tianshou.exploration import GaussianNoise
from tianshou.data import Collector, VectorReplayBuffer, ReplayBuffer
from tianshou.env import SubprocVectorEnv, DummyVectorEnv
from tianshou.trainer import OffpolicyTrainer
from tianshou.policy import BasePolicy, DDPGPolicy

from CustomModels.CustomMAPolicyManager import CustomMAPolicyManager as MultiAgentPolicyManager
#from tianshou.policy import MultiAgentPolicyManager

from CustomModels.DNN_B_ACE_ACTOR import DNN_B_ACE_ACTOR
from CustomModels.DNN_B_ACE_CRITIC import DNN_B_ACE_CRITIC


model  =  "DNN_B_ACE"
test_num  =  "Eval_01"
policyModel  =  "DDPG"
name = model + "_" + policyModel + "_" + test_num

train_env_num = 1
test_env_num  = 1

now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
log_name = name + str(now)
log_path = os.path.join('./', "Logs", log_name)

load_policy_name = f'XXXX.pth'
save_policy_name = f'policy_{log_name}'
policy_path = os.path.join('./', "Policies", model + "_" + policyModel)

model_load_path = os.path.join(policy_path, load_policy_name)  
model_save_path = os.path.join(policy_path, save_policy_name)        
os.makedirs(os.path.join(policy_path), exist_ok=True)  
os.makedirs(os.path.join(log_path), exist_ok=True)

Policy_Config = {
    "same_policy" : True, #Single policy for all agents or not
    "load_model" : False  #Start from random weight or not
                }

B_ACE_Config = { 	
                    "EnvConfig" : 
                    {                        
                        "env_path": "../../bin/B_ACE_v0.1.exe",
                        "port": 12500,
                        "renderize": 1,                        
                        "speed_up": 50000,                                                                        
                        "seed": 0,	                                                                                                
                    },

                    "AgentsConfig" : 
                    {
                        "blue_agents": { 
                            "num_agents" : 1,                           
                            "mission"    : "DCA",                           
                            "base_behavior": "external",                  
                            "init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
                            "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                            "init_hdg": 0.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},                            
                        },	
                        "red_agents":
                        { 
                            "num_agents" : 1,                            
                            "base_behavior": "baseline1",
                            "mission"    : "striker",
                            # "beh_config" : {
                            #                "dShot" : [0.50, 0.99, 1.04, 0.50, 0.99, 0.93, 0.57, 0.50, 0.50, 0.50],
                            #                "lCrank": [0.64, 0.96, 1.14, 0.69, 0.96, 0.69, 1.07, 0.20, 0.98, 0.69],
                            #                 "lBreak": [1.17, 0.51, 1.05, 0.25, 0.84, 0.51, 0.61, 0.37, 1.17, 0.51]  
                            #              },
                            
                            "beh_config" : {
                                             "dShot" : [0.50, 0.99, 1.04],
                                             "lCrank": [0.98, 0.96, 1.14],
                                             "lBreak": [1.17, 0.51, 1.05]
                                         },
                            # "beh_config" : {
                            #                 "dShot" : [1.04],
                            #                 "lCrank": [1.06],
                            #                  "lBreak": [1.05]  
                            #               },
                         
                            "init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
                            "offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
                            "init_hdg" : 180.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},				
                            "rnd_shot_dist_var": 0.025,
                            "rnd_crank_var": 0.025,
                            "rnd_break_var": 0.025,                            
                        }
                    }	
            }


trainer_params = {"max_epoch": 100,
                  "step_per_epoch": 30000 * train_env_num,
                  "step_per_collect": 1000 * train_env_num,                  
                  "batch_size" : 128,                 
                  "update_per_step": 1/10, #Off-Policy Only (run after close a Collect (run many times as necessary to meet the value))                                    
                  "episode_per_test": 30,                                    
                  "train_envs" : train_env_num,
                  "test_envs" : test_env_num                                    
}

#RunConfig Store data for Logs and comparisons 
runConfig = {}
runConfig["Training"] = policyModel 
runConfig["Model"] = model 
runConfig.update(Policy_Config)
runConfig.update(B_ACE_Config)
runConfig.update(trainer_params) 


def _get_agents(
    agent_learn: Optional[BasePolicy] = None,
    agent_opponent: Optional[BasePolicy] = None,
    policy_load_path = None,
) -> Tuple[BasePolicy, torch.optim.Optimizer, list]:

    env = _get_env()
    agent_observation_space = env.observation_space
    action_space = env.action_space
    device = "cuda" if torch.cuda.is_available() else "cpu"    
    
    agents = []

    if Policy_Config["same_policy"]:
        policies_number = 1
    else:
        policies_number = len(env.agents)

    # Define the actor and critic networks
    actor = DNN_B_ACE_ACTOR(
        obs_shape=agent_observation_space.shape[0],
        action_shape=4,
        device=device,
        max_action = 1.0
    ).to(device)
    actor_optim = torch.optim.Adam(actor.parameters(), lr=0.001)

    critic = DNN_B_ACE_CRITIC(
        obs_shape=agent_observation_space.shape[0], # + 4,  # Modified to accept both obs and act
        action_shape=4,
        device=device,        
    ).to(device)
    critic_optim = torch.optim.Adam(critic.parameters(), lr=0.01)

    for _ in range(policies_number):
        agent_learn = DDPGPolicy(
            actor=actor,
            critic=critic,
            actor_optim=actor_optim,
            critic_optim=critic_optim,
            tau=0.005,
            gamma=0.99,
            exploration_noise=GaussianNoise(sigma=0.5),
            action_space=action_space,            
            estimation_step=30,
            action_scaling=True
        )
         
        if Policy_Config["load_model"] is True:
            # Load the saved checkpoint
            agent_learn.load_state_dict(torch.load(model_load_path))
            print(f'Loaded-> {model_load_path}')

        agents.append(agent_learn)

    if Policy_Config["same_policy"]:
        agents = [agents[0] for _ in range(len(env.agents))]
    else:
        for _ in range(len(env.agents) - policies_number):
            agents.append(agents[0])

    policy = MultiAgentPolicyManager(policies=agents, env=env)
    env.close()
    
    return policy, actor_optim, env.agents

def _get_env():
    """This function is needed to provide callables for DummyVectorEnv."""   
    
    B_ACE_Config["EnvConfig"]["seed"] = random.randint(0, 1000000)
        
    env = B_ACE_GodotPettingZooWrapper(convert_action_space = False,
                                    device = "cpu",
                                    **B_ACE_Config)        
    return env  

#print(json.dumps(runConfig, indent=4))

if __name__ == "__main__":
                        
    torch.set_grad_enabled(True) 

    # ======== Step 1: Environment setup =========
    train_envs = DummyVectorEnv([_get_env for _ in range(train_env_num)])#, share_memory = False )
    test_envs = DummyVectorEnv([_get_env for _ in range(test_env_num)])#, share_memory = False) 
    
    # Seeds Definition
    seed = B_ACE_Config['EnvConfig']['seed']
    np.random.seed(seed)
    torch.manual_seed(seed)
    train_envs.seed(seed)
    test_envs.seed(seed)    

    # ======== Step 2: Agent setup =========
    policy, optim, agents = _get_agents()    

    # ======== Step 3: Collector setup =========
    if len(train_envs) > 1:
        buffer = VectorReplayBuffer(1_000_000, len(train_envs))
    else:
        buffer = ReplayBuffer(1_000_000)
    
    train_collector = Collector(
        policy,
        train_envs,
        buffer,
        exploration_noise=True
    )     
    test_collector = Collector(policy, test_envs)
    global_step_holder = [0] 
    

    
    # ======== Step 4: Callback functions setup =========
    def save_best_fn(policy):                
        
        if Policy_Config["same_policy"]:
            torch.save(policy.policies[agents[0]].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_BestRew.pth")
            print("Best Saved Rew" , str(global_step_holder[0]))
        
        else:
            for n,agent in enumerate(agents):
                torch.save(policy.policies[agent].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_" + agent + ".pth")
            
            print("Bests Saved Rew" , str(global_step_holder[0]))
        
    def save_test_best_fn(policy):                
        
        if Policy_Config["same_policy"]:
            torch.save(policy.policies[agents[0]].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_BestLen.pth")
            print("Best Saved Length" , str(global_step_holder[0]))
        
        else:
            for n,agent in enumerate(agents):
                torch.save(policy.policies[agent].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_" + agent + ".pth")
            
            print("Best Saved Length" , str(global_step_holder[0]))
        

    def train_fn(epoch, env_step):
        
        current_sigma = 0.5 - (0.49 * (epoch / 100))
        if Policy_Config["same_policy"]:
                policy.policies[agents[0]].exploration_noise = GaussianNoise(sigma = max(0.01, current_sigma) )# Ensure it doesn't go below a min     
        else:
            for agent in agents:
                        policy.policies[agent].exploration_noise = GaussianNoise(sigma = max(0.01, current_sigma) ) # Ensure it doesn't go below a min      

        
    def reward_metric(rews):       
                
        global_step_holder[0] +=1         
        return rews

    # ======== Step 5: Run the trainer =========
    offPolicyTrainer = OffpolicyTrainer(
        policy=policy,
        train_collector=train_collector,
        test_collector=test_collector,        
        max_epoch=trainer_params['max_epoch'],
        step_per_epoch=trainer_params['step_per_epoch'],
        step_per_collect=trainer_params['step_per_collect'],        
        episode_per_test= trainer_params['episode_per_test'],
        batch_size=trainer_params['batch_size'],
        train_fn=train_fn,
        save_best_fn=save_best_fn,        
        update_per_step=trainer_params['update_per_step'],
        #logger=logger,
        test_in_train=False,
        reward_metric=reward_metric,
        show_progress = True 
        )
    
    result = offPolicyTrainer.run()
    
    print(result)
    print(f"\n==========Result==========\n{result}")
    print("\n(the trained policy can be accessed via policy.policies[agents[0]])")
