import os
import datetime
from typing import Optional, Tuple
import json
import numpy as np
import torch
from gymnasium.spaces import Box, Discrete

import random

from torch.distributions import Normal, Distribution

from tianshou.data import Collector, VectorReplayBuffer, PrioritizedVectorReplayBuffer
from tianshou.env import SubprocVectorEnv, DummyVectorEnv
#from tianshou.env.pettingzoo_env_parallel import PettingZooParallelEnv
#from tianshou.env.pettingzoo_env import PettingZooEnv
#from PettingZooParallelEnv import PettingZooParallelEnv


from tianshou.policy import PPOPolicy
from tianshou.trainer import OnpolicyTrainer

from tianshou.utils.net.common import ActorCritic, DataParallelNet, Net
from tianshou.utils.net.continuous import Actor, Critic

from tianshou.policy import BasePolicy, DQNPolicy, MultiAgentPolicyManager, DDPGPolicy
from tianshou.trainer import OffpolicyTrainer
from torch.utils.tensorboard import SummaryWriter
from DNN_B_ACE_ACTOR import DNN_B_ACE_ACTOR
from DNN_B_ACE_CRITIC import DNN_B_ACE_CRITIC
from Task_MHA_B_ACE import Task_MHA_B_ACE
from Task_DNN_B_ACE import Task_DNN_B_ACE
from Task_B_ACE_Env import B_ACE_TaskEnv

from CollectorMA import CollectorMA
from MAParalellPolicy import MAParalellPolicy


####---------------------------#######
#Tianshou Adjustment
import wandb
# os.environ["WANDB_NOTEBOOK_NAME"] = "Tianshow_Training_GoDot.ipybn"
from tianshou.utils import WandbLogger
# from tianshou.utils.logger.base import LOG_DATA_TYPE
# def new_write(self, step_type: str, step: int, data: LOG_DATA_TYPE) -> None:
#      data[step_type] = step
#      wandb.log(data)   
# WandbLogger.write = new_write 
####---------------------------#######


model  =  "Task_MHA"#Task_MHA_B_ACE"#"SISL_Task_MultiHead" #"CNN_ATT_SISL" #"MultiHead_SISL" Task_DNN_B_ACE
test_num  =  "_B_ACE_Eval"
policyModel  =  "DQN"
name = model + "_" + policyModel + "_" + test_num

train_env_num = 4
test_env_num  = 15


now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
log_name = name + str(now)
log_path = os.path.join('./', "Logs", "dqn_sisl", log_name)

load_policy_name = f'policy_Task_MHA_B_ACE_B_ACE03241118-103140_573_BestRew.pth'
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
                        "env_path": "..\..\BVR_AirCombat/bin/B_ACE_v12.exe",
                        "port": 12500,
                        "renderize": 0,
                        "debug_view": 0,
                        "phy_fps": 20,
                        "speed_up": 50000,
                        "max_cycles": 36000,
                        "experiment_mode"  : 0,
                        "parallel_envs": 1,	
                        "seed": 2,	
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
                            "num_agents" : 2,
                            "share_states" : 0, 
                            "share_states" : 0,
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
                            "num_agents" : 4,
                            "share_states" : 0, 
                            "share_tracks" : 0,
                            "base_behavior": "baseline2",
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
#max_cycles = B_ACE_Config["max_cycles"]
#n_agents = 1#B_ACE_Config["n_pursuers"]

dqn_params =    {
                "discount_factor": 0.99, 
                "estimation_step": 180, 
                "target_update_freq": 6000 * 3 ,#max_cycles * n_agents,
                "reward_normalization" : False,
                "clip_loss_grad" : True,
                "optminizer": "Adam",
                "lr": 0.00005, 
                "max_tasks" : 30
                }

PPO_params= {    
                'action_scaling': False,
                'discount_factor': 0.98,
                'max_grad_norm': 0.5,
                'eps_clip': 0.2,
                'vf_coef': 0.5,
                'ent_coef': 0.01,
                'gae_lambda': 0.95,
                'reward_normalization': False, 
                'dual_clip': None,
                'value_clip': False,   
                'deterministic_eval': True,
                'advantage_normalization': False,
                'recompute_advantage': False,
                'action_bound_method': "clip",
                'lr_scheduler': None,
            }


trainer_params = {"max_epoch": 500,
                  "step_per_epoch": 18000,#5 * (150 * n_agents),
                  "step_per_collect": 6000,# * (10 * n_agents),
                  
                  "batch_size" : 1024,
                  
                  "update_per_step": 1 / (100), #Off-Policy Only (run after close a Collect (run many times as necessary to meet the value))
                  
                  "repeat_per_collect": 32, #On-Policy Only
                  
                  "episode_per_test": 30,                  
                  "tn_eps_max": 0.20,
                  "ts_eps_max": 0.001,
                  "warmup_size" : 1,
                  "train_envs" : train_env_num,
                  "test_envs" : test_env_num
}
#agent_learn = PPOPolicy(**policy_params)


runConfig = dqn_params
runConfig["Training"] = policyModel 
runConfig["Model"] = model 

runConfig.update(Policy_Config)
runConfig.update(B_ACE_Config)
runConfig.update(trainer_params) 
runConfig.update(dqn_params)


def _get_agents(
    agent_learn: Optional[BasePolicy] = None,
    agent_opponent: Optional[BasePolicy] = None,
    optim: Optional[torch.optim.Optimizer] = None,
    policy_load_path = None,
) -> Tuple[BasePolicy, torch.optim.Optimizer, list]:
    
    env = _get_env()       
    agent_observation_space = env.observation_space("agent_0")
   
    #print(env.action_space)
    #action_shape = 50#env.action_space.shape
    
    print("ActionSPACE: ", env.action_space)
    action_space = env.action_space
    device="cuda" if torch.cuda.is_available() else "cpu"  

    agents = []        
    
    if Policy_Config["same_policy"]:
        policies_number = 1
    else:
        policies_number = len(env.agents)

    for _ in range(policies_number):      
        
        #print(agent_observation_space)
        
        if policyModel == "DQN":

            if model == "Task_MHA":
                net = Task_MHA_B_ACE(
                    #obs_shape=agent_observation_space.shape,                                                  
                    num_tasks = dqn_params["max_tasks"],
                    num_features_per_task= 14,                    
                    nhead = 4,
                    device="cuda" if torch.cuda.is_available() else "cpu"
                    
                ).to(device) 
            
            if model == "Task_DNN":
                net = Task_DNN_B_ACE(
                    #obs_shape=agent_observation_space.shape,                                                  
                    num_tasks = dqn_params["max_tasks"],
                    num_features_per_task= 14,                    
                    nhead = 4,
                    device="cuda" if torch.cuda.is_available() else "cpu"
                    
                ).to(device) 
                
            optim = torch.optim.Adam(net.parameters(), lr=dqn_params["lr"], weight_decay=0.0, amsgrad= True)       
            
            agent_learn = DQNPolicy(
                model=net,
                optim=optim,
                action_space = Discrete(dqn_params["max_tasks"]),
                discount_factor= dqn_params["discount_factor"],
                estimation_step=dqn_params["estimation_step"],
                target_update_freq=dqn_params["target_update_freq"],
                reward_normalization = dqn_params["reward_normalization"],
                clip_loss_grad = dqn_params["clip_loss_grad"]
            )                   
        
        elif policyModel == "PPO":
            
            if model == "Task_DNN":
                actor = DNN_B_ACE_ACTOR(
                    obs_shape=agent_observation_space.shape[0],                
                    action_shape=4,                
                    device="cuda" if torch.cuda.is_available() else "cpu"                
                ).to(device)

                critic = DNN_B_ACE_CRITIC(
                    obs_shape=agent_observation_space.shape[0],                
                    action_shape=4,                
                    device="cuda" if torch.cuda.is_available() else "cpu"                
                ).to(device)
            
            
            if model == "Task_MHA":
                # PPO-specific setup with MHA architecture
                actor = Task_MHA_B_ACE(
                    num_tasks=dqn_params["max_tasks"],
                    num_features_per_task=14,
                    nhead=4,
                    device=device,
                ).to(device)

                critic = Task_MHA_B_ACE(
                    num_tasks=dqn_params["max_tasks"],
                    num_features_per_task=14,
                    nhead=4,
                    device=device,
                ).to(device)
            
                                    
            actor_critic = ActorCritic(actor, critic)
        
            # orthogonal initialization
            # for m in actor_critic.modules():
            #     if isinstance(m, torch.nn.Linear):
            #         torch.nn.init.orthogonal_(m.weight)
            #         torch.nn.init.zeros_(m.bias)            
            
            # dist = torch.distributions.Normal(torch.tensor([0.0]), torch.tensor([1.0])) 
                # define policy
            def dist(mu, sigma) -> Distribution:
                return Normal(mu, sigma)        
                
            #optim_actor  = torch.optim.Adam(netActor.parameters(),  lr=dqn_params["lr"], weight_decay=0.0, amsgrad= True )
            #optim_critic = torch.optim.Adam(netCritic.parameters(), lr=dqn_params["lr"], weight_decay=0.0, amsgrad= True )
            optim = torch.optim.Adam(actor_critic.parameters(), lr=dqn_params["lr"])
                    
            agent_learn = PPOPolicy(
                actor=actor,
                critic=critic,
                optim=optim,
                dist_fn=dist,                
                action_scaling  =       PPO_params['action_scaling'],
                discount_factor =       PPO_params['discount_factor'],
                max_grad_norm   =       PPO_params['max_grad_norm'],
                eps_clip        =       PPO_params['eps_clip'],
                vf_coef         =       PPO_params['vf_coef'],
                ent_coef        =       PPO_params['ent_coef'],
                gae_lambda      =       PPO_params['gae_lambda'],
                reward_normalization=   PPO_params['reward_normalization'],
                action_space    =  action_space,
                deterministic_eval=     PPO_params['deterministic_eval'],
                advantage_normalization=PPO_params['advantage_normalization'],
                recompute_advantage=    PPO_params['recompute_advantage'],
                action_bound_method=    PPO_params['action_bound_method'],
                lr_scheduler=None
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
    
    policy = MultiAgentPolicyManager(policies = agents, env=env)  
    #policy = MAParalellPolicy(policies = agents, env=env, device="cuda" if torch.cuda.is_available() else "cpu" )  
        
    return policy, optim, env.agents

def _get_env():
    """This function is needed to provide callables for DummyVectorEnv."""   
    
    B_ACE_Config["EnvConfig"]["seed"] = random.randint(0, 1000000)
    
    env = B_ACE_TaskEnv( convert_action_space = True,
                                    device = "cpu",
                                    **B_ACE_Config)
    
    #env.action_space = env.action_space()
    #env = PettingZooEnv(env)  
    
    return env  
   

# print(json.dumps(runConfig, indent=4))
if __name__ == "__main__":
                        
    torch.set_grad_enabled(True) 
   
    # ======== Step 1: Environment setup =========
    train_envs = SubprocVectorEnv([_get_env for _ in range(train_env_num)])#, share_memory = True )
    test_envs = SubprocVectorEnv([_get_env for _ in range(test_env_num)])#, share_memory = True) 
    
    #train_envs = DummyVectorEnv([_get_env for _ in range(train_env_num)])#, share_memory = True )
    #test_envs = DummyVectorEnv([_get_env for _ in range(test_env_num)])#, share_memory = True) 

    # seed
    seed = B_ACE_Config['EnvConfig']['seed']
    np.random.seed(seed)
    
    torch.manual_seed(seed)

    train_envs.seed(seed)
    test_envs.seed(seed)

    # ======== Step 2: Agent setup =========
    policy, optim, agents = _get_agents()    

    
    if True:
        # ======== Step 3: Collector setup =========
        train_collector = Collector(
            policy,
            train_envs,
            VectorReplayBuffer(100_000, len(train_envs)),
            #PrioritizedVectorReplayBuffer( 300_000, len(train_envs), alpha=0.6, beta=0.4) , 
            #ListReplayBuffer(100000)       
            # buffer = StateMemoryVectorReplayBuffer(
            #         300_000,
            #         len(train_envs),  # Assuming train_envs is your vectorized environment
            #         memory_size=10,                
            #     ),
            exploration_noise=True             
        )
        test_collector = Collector(policy, test_envs, exploration_noise=True)
        
    else:
        agents_buffers_training = {agent : 
                        PrioritizedVectorReplayBuffer( 300_000, 
                                                        len(train_envs), 
                                                        alpha=0.6, 
                                                        beta=0.4) 
                                                        for agent in agents
                        }
        agents_buffers_test = {agent : 
                        PrioritizedVectorReplayBuffer( 300_000, 
                                                        len(train_envs), 
                                                        alpha=0.6, 
                                                        beta=0.4) 
                                                        for agent in agents
                        }
    
        # ======== Step 3: Collector setup =========
        train_collector = CollectorMA(
            policy,
            train_envs,
            agents_buffers_training, 
            agents=agents,  # Pass the list of agent IDs                       
            exploration_noise=True             
        )
        test_collector = CollectorMA(policy, test_envs, agents_buffers_test,agents=agents, exploration_noise=True)

    
        
    print("Buffer Warming Up ")    
    for i in range(trainer_params["warmup_size"]):#int(trainer_params['batch_size'] / (300 * 10 ) )):
        
         train_collector.collect(n_episode=train_env_num)#,random=True) #trainer_params['batch_size'] * train_env_num))
         #train_collector.collect(n_step=300 * 10)
         print(".", end="") 
    
    # len_buffer = len(train_collector.buffer) / (B_ACE_Config["max_cycles"] * SISL_Config["n_pursuers"])
    # print("\nBuffer Lenght: ", len_buffer ) 
    len_buffer = 0
    
    info = { "Buffer"  : "PriorizedReplayBuffer", " Warmup_ep" : len_buffer}
    
    # ======== tensorboard logging setup =========                       
    logger = WandbLogger(
        train_interval = runConfig["EnvConfig"]["max_cycles"] / 400 ,
        test_interval = 1,#runConfig["max_cycles"] * runConfig["n_pursuers"],
        update_interval = runConfig["EnvConfig"]["max_cycles"] / 400,
        save_interval = 1,
        write_flush = True,
        project = "B_ACE_EVAL",
        name = log_name,
        entity = None,
        run_id = log_name,
        config = runConfig,
        monitor_gym = True )
    
    writer = SummaryWriter(log_path)    
    writer.add_text("args", str(runConfig))    
    logger.load(writer)

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
        

    def stop_fn(mean_rewards):
        return mean_rewards >= 99999939.0

    def train_fn(epoch, env_step):
        epsilon = trainer_params['tn_eps_max'] - (trainer_params['tn_eps_max'] - trainer_params['tn_eps_max']/100)*(epoch/trainer_params['max_epoch'])          
        if Policy_Config["same_policy"]:
            policy.policies[agents[0]].set_eps(epsilon)
        else:
            for agent in agents:
                policy.policies[agent].set_eps(epsilon)
                
        
        # if env_step % 500 == 0:
            # logger.write("train/env_step", env_step, {"train/eps": eps})


    def test_fn(epoch, env_step):

        epsilon = trainer_params['ts_eps_max']#0.01#max(0.001, 0.1 - epoch * 0.001)
        if Policy_Config["same_policy"]:
            policy.policies[agents[0]].set_eps(epsilon)
        else:            
            for agent in agents:                             
                policy.policies[agent].set_eps(epsilon)
                
        
        if global_step_holder[0] % 10 == 0:
            
            if Policy_Config["same_policy"]:
                torch.save(policy.policies[agents[0]].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_Step.pth")
                print("Steps Policy Saved " , str(global_step_holder[0]))
            
            else:
                for n,agent in enumerate(agents):
                    torch.save(policy.policies[agent].state_dict(), model_save_path + "_" + str(global_step_holder[0]) + "_" + agent + "Step" + str(global_step_holder[0]) + ".pth")
                
                print("Steps Policy Saved " , str(global_step_holder[0]))

        
    def reward_metric(rews):       
                
        global_step_holder[0] +=1 
        #print(rews)
        return rews#np.mean(rews)#np.sum(rews)




    # # # ======== Step 5: Run the trainer =========   
    # onPolicyTrainer = OnpolicyTrainer(
    #     policy=policy,
    #     train_collector=train_collector,
    #     test_collector=test_collector,
    #     max_epoch=trainer_params['max_epoch'],
        
    #     step_per_epoch=trainer_params['step_per_epoch'],
                        
    #     batch_size=trainer_params['batch_size'],
    #     step_per_collect=trainer_params['step_per_collect'],
    #     repeat_per_collect=trainer_params['repeat_per_collect'],
        
    #     episode_per_test=trainer_params['episode_per_test'],
    #     stop_fn=stop_fn,
    #     save_best_fn=save_best_fn,
    #     reward_metric=reward_metric,
    #     test_in_train=True,
    #     show_progress = True,
    #     logger=logger,
    # )
    

    # writer.close()
    
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
        test_fn=test_fn,
        stop_fn=stop_fn,
        save_best_fn=save_best_fn,
        # save_test_best_fn=save_test_best_fn,
        update_per_step=trainer_params['update_per_step'],
        logger=logger,
        test_in_train=False,
        reward_metric=reward_metric,
        show_progress = True 
               
         )
    
    result = offPolicyTrainer.run()
    writer.close()
    # return result, policy.policies[agents[1]]
    print(f"\n==========Result==========\n{result}")
    print("\n(the trained policy can be accessed via policy.policies[agents[0]])")