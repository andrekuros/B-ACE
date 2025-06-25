import os
import sys
from pathlib import Path
import datetime
from typing import Optional, Tuple
import random
import json
import numpy as np
import torch
from gymnasium.spaces import Box, Discrete

script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)
project_root = script_dir.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from b_ace_py.B_ACE_GodotPettingZooWrapper import  B_ACE_GodotPettingZooWrapper
from b_ace_py.utils import load_b_ace_config
from tianshou.exploration import GaussianNoise

from torch.distributions import Normal, Distribution
from tianshou.data import Collector, VectorReplayBuffer, PrioritizedVectorReplayBuffer
from tianshou.env import SubprocVectorEnv, DummyVectorEnv

from tianshou.policy import PPOPolicy
from tianshou.trainer import OffpolicyTrainer

from tianshou.utils.net.common import ActorCritic, DataParallelNet, Net
from tianshou.utils.net.continuous import Actor, Critic

from tianshou.policy import BasePolicy, DDPGPolicy
#from custom_dqn_policy import  CustomDQNPolicy as DQNPolicy
from CustomMultiAgentPolicyManager import CustomMultiAgentPolicyManager as MultiAgentPolicyManager
#from tianshou.policy import MultiAgentPolicyManager

import wandb
from tianshou.utils import WandbLogger

from torch.utils.tensorboard import SummaryWriter
from DNN_B_ACE_ACTOR import DNN_B_ACE_ACTOR
from DNN_B_ACE_CRITIC import DNN_B_ACE_CRITIC
from DNN_B_ACE import DNN_B_ACE
from Task_MHA_B_ACE import Task_MHA_B_ACE
from Task_DNN_B_ACE import Task_DNN_B_ACE
from Task_B_ACE_Env import B_ACE_TaskEnv

#from CollectorMA import CollectorMA
#from MAParalellPolicy import MAParalellPolicy

model  =  "DNN_B_ACE"#Task_MHA_B_ACE"#"SISL_Task_MultiHead" #"CNN_ATT_SISL" #"MultiHead_SISL" Task_DNN_B_ACE
test_num  =  "_B_ACE_Eval"
policyModel  =  "DDPG"
name = model + "_" + policyModel + "_" + test_num

train_env_num = 10
test_env_num  = 4

now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
log_name = name + str(now)
log_path = os.path.join('./', "Logs", "KTAB", log_name)
logger = None

load_policy_name = f'none.pth'
save_policy_name = f'policy_{log_name}'
policy_path = model + policyModel

model_load_path = os.path.join(policy_path, load_policy_name)  
model_save_path = os.path.join(policy_path, save_policy_name)        
os.makedirs(os.path.join(policy_path), exist_ok=True)  
os.makedirs(os.path.join(log_path), exist_ok=True)

Policy_Config = {
    "same_policy" : True,
    "load_model" : False    
                }

B_ACE_Config = { 	
                    "EnvConfig" : 
                    {
                        "task": "b_ace_v1",
                        "env_path": "../../bin/B_ACE_v0.1.exe",
                        "port": 12500,
                        "renderize": 1,
                        "phy_fps": 20,
                        "speed_up": 50000,
                        "max_cycles": 36000,
                        "experiment_mode"  : 0,
                        "parallel_envs": 1,	
                        "seed": 0,	
                        "action_repeat": 20,	
                        "action_type": "Low_Level_Continuous",                        
                        "stop_mission" : 1,                                     
                        "RewardsConfig" : {
                                    "mission_factor": 0.001,				
                                    "missile_fire_factor": -0.1,		
                                    "missile_no_fire_factor": -0.001,
                                    "missile_miss_factor": -0.5,
                                    "detect_loss_factor": -0.1,
                                    "keep_track_factor": 0.001,
                                    "hit_enemy_factor": 3.0,
                                    "hit_own_factor": -5.0,			
                                    "mission_accomplished_factor": 10.0,			
                                }
                    },

                    "AgentsConfig" : 
                    {
                        "blue_agents": { 
                            "num_agents" : 1,
                            "share_states" : 1, 
                            "share_tracks" : 1,
                            "mission"    : "DCA",
                            "beh_config" : {
                                            "dShot" : [1.04, 1.04, 1.04], #[1.04, 0.50, 1.09]
                                            "lCrank": [1.06, 0.98, 0.98], #1.06, 0.98, 0.98
                                            "lBreak": [1.05, 1.05, 1.05], #1.05, 1.17, 0.45
                                        },
                            "base_behavior": "external",                  
                            "init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
                            "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                            "init_hdg": 0.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},				
                            "rnd_shot_dist_var": 0.025,
                            "rnd_crank_var": 0.025,
                            "rnd_break_var": 0.025,
                            "wez_models" : "res://assets/wez/Default_Wez_params.json"
                        },	
                        "red_agents":
                        { 
                            "num_agents" : 1,
                            "share_states" : 1, 
                            "share_tracks" : 1,
                            "base_behavior": "baseline1",
                            "mission"    : "striker",
                            # "beh_config" : {
                            #                "dShot" : [0.50, 0.99, 1.04, 0.50, 0.99, 0.93, 0.57, 0.50, 0.50, 0.50],
                            #                "lCrank": [0.64, 0.96, 1.14, 0.69, 0.96, 0.69, 1.07, 0.20, 0.98, 0.69],
                            #                 "lBreak": [1.17, 0.51, 1.05, 0.25, 0.84, 0.51, 0.61, 0.37, 1.17, 0.51]  
                            #              },
                            
                            # "beh_config" : {
                            #                 "dShot" : [0.50, 0.99, 1.04],
                            #                 "lCrank": [0.98, 0.96, 1.14],
                            #                 "lBreak": [1.17, 0.51, 1.05]
                            #             },
                            "beh_config" : {
                                            "dShot" : [1.04],
                                            "lCrank": [1.06],
                                             "lBreak": [1.05]  
                                          },
                         
                            "init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
                            "offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
                            "init_hdg" : 180.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},				
                            "rnd_shot_dist_var": 0.025,
                            "rnd_crank_var": 0.025,
                            "rnd_break_var": 0.025,
                            "wez_models" : "res://assets/wez/Default_Wez_params.json"
                        }
                    }	
            }


trainer_params = {"max_epoch": 200,
                  "step_per_epoch": 180000 * 2,#5 * (150 * n_agents),
                  "step_per_collect": 36000 * 2,# * (10 * n_agents),                  
                  "batch_size" : 1024,                 
                  "update_per_step": 1 / (20), #Off-Policy Only (run after close a Collect (run many times as necessary to meet the value))                  
                  "repeat_per_collect": 64, #On-Policy Only                 
                  "episode_per_test": 20,                  
                  "warmup_size" : 1,
                  "train_envs" : train_env_num,
                  "test_envs" : test_env_num,
                  "priorized_buffer" : False,
                  "wandb_log" : False
}

#RunConfig Store data for Logs and comparisons (Recommended Wandb)
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
    actor_optim = torch.optim.Adam(actor.parameters(), lr=0.0001)

    critic = DNN_B_ACE_CRITIC(
        obs_shape=agent_observation_space.shape[0], # + 4,  # Modified to accept both obs and act
        action_shape=4,
        device=device,
        max_action = 1.0
    ).to(device)
    critic_optim = torch.optim.Adam(critic.parameters(), lr=0.001)

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
            estimation_step=100,
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

    return policy, actor_optim, env.agents

def _get_env():
    """This function is needed to provide callables for DummyVectorEnv."""   
    
    B_ACE_Config["EnvConfig"]["seed"] = random.randint(0, 1000000)
        
    env = B_ACE_GodotPettingZooWrapper(convert_action_space = False,
                                    device = "cpu",
                                    **B_ACE_Config)    
    #env = PettingZooEnv(env)  
    return env  

#print(json.dumps(runConfig, indent=4))

if __name__ == "__main__":
                        
    torch.set_grad_enabled(True) 

    # ======== Step 1: Environment setup =========
    train_envs = SubprocVectorEnv([_get_env for _ in range(train_env_num)], share_memory = False )
    test_envs = SubprocVectorEnv([_get_env for _ in range(test_env_num)], share_memory = False) 
    
    # Seeds Definition
    seed = B_ACE_Config['EnvConfig']['seed']
    np.random.seed(seed)
    torch.manual_seed(seed)
    train_envs.seed(seed)
    test_envs.seed(seed)    

    # ======== Step 2: Agent setup =========
    policy, optim, agents = _get_agents()    

    # ======== Step 3: Collector setup =========
    train_collector = Collector(
        policy,
        train_envs,
        VectorReplayBuffer(300_000, len(train_envs)),            
        exploration_noise=True  
    )     
    test_collector = Collector(policy, test_envs, exploration_noise=True)
    
    info = { "Buffer"  : "PriorizedReplayBuffer" if trainer_params["priorized_buffer"] else "ReplayBuffer",
            " Warmup_ep" : trainer_params['warmup_size'] * train_env_num}

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
        
        current_sigma = 0.1 - (0.09 * (epoch / 200))
        if Policy_Config["same_policy"]:
                policy.policies[agents[0]].exploration_noise = GaussianNoise(sigma = max(0.01, current_sigma) )# Ensure it doesn't go below a min     
        else:
            for agent in agents:
                        policy.policies[agent].exploration_noise = GaussianNoise(sigma = max(0.01, current_sigma) ) # Ensure it doesn't go below a min      
                
    # def test_fn(epoch, env_step):

    #     epsilon = trainer_params['ts_eps_max']#0.01#max(0.001, 0.1 - epoch * 0.001)
    #     # if Policy_Config["same_policy"]:
    #     #     policy.policies[agents[0]].set_eps(epsilon)
    #     # else:            
    #     #     for agent in agents:                             
    #     #         policy.policies[agent].set_eps(epsilon)
                
        
    #     if global_step_holder[0] % 10 == 0:
            
    #         if Policy_Config["same_policy"]:
    #             torch.save(policy.policies[agents[0]].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_Step.pth")
    #             print("Steps Policy Saved " , str(global_step_holder[0]))
            
    #         else:
    #             for n,agent in enumerate(agents):
    #                 torch.save(policy.policies[agent].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_" + agent + "Step" + str(global_step_holder[0]) + ".pth")
                
    #             print("Steps Policy Saved " , str(global_step_holder[0]))

        
    def reward_metric(rews):       
                
        global_step_holder[0] +=1 
        #print(rews)
        return rews#np.mean(rews)#np.sum(rews)

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
#       test_fn=test_fn,
 #      stop_fn=stop_fn,
        save_best_fn=save_best_fn,
        # save_test_best_fn=save_test_best_fn,
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
