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
from tianshou.env.pettingzoo_env_parallel import PettingZooParallelEnv
from tianshou.env.pettingzoo_env import PettingZooEnv

#from PettingZooParallelEnv import PettingZooParallelEnv


from tianshou.policy import PPOPolicy
from tianshou.trainer import OnpolicyTrainer

from tianshou.utils.net.common import ActorCritic, DataParallelNet, Net
from tianshou.utils.net.continuous import Actor, Critic

from tianshou.policy import BasePolicy, DQNPolicy, MultiAgentPolicyManager, RandomPolicy, RainbowPolicy
from tianshou.trainer import OffpolicyTrainer
from torch.utils.tensorboard import SummaryWriter
from DNN_B_ACE_ACTOR import DNN_B_ACE_ACTOR
from DNN_B_ACE_CRITIC import DNN_B_ACE_CRITIC
from GodotRLPettingZooWrapper import GodotRLPettingZooWrapper

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


model  =  "PPO_DNN"#"SISL_Task_MultiHead" #"CNN_ATT_SISL" #"MultiHead_SISL" 
test_num  =  "_B_ACE01"
policyModel  =  "PPO"
name = model + test_num

train_env_num = 20
test_env_num = 10

now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
log_name = name + str(now)
log_path = os.path.join('./', "Logs", "dqn_sisl", log_name)

load_policy_name = f'policy_SISL_Task_MultiHead_Desk_NewExpCor231219-173711_44.pth'
save_policy_name = f'policy_{log_name}'
policy_path = "ppo_B_ACE"


model_load_path = os.path.join(policy_path, load_policy_name)  
model_save_path = os.path.join(policy_path, save_policy_name)        
os.makedirs(os.path.join(policy_path), exist_ok=True)  
os.makedirs(os.path.join(log_path), exist_ok=True)

Policy_Config = {
    "same_policy" : True,
    "load_model" : False,
    "freeze_CNN" : False     
                }

B_ACE_Config = { 	
                    "EnvConfig" : 
                    {
                        "task": "b_ace_v1",
                        "env_path": "BVR_AirCombat/bin/B_ACE_v6.console.exe",
                        "port": 12500,
                        "renderize": 0,
                        "debug_view": 0,
                        "phy_fps": 20,
                        "speed_up": 50000,
                        "max_cycles": 36000,
                        "experiment_mode"  : 0,
                        "parallel_envs": 1,	
                        "seed": 1,	
                        "action_repeat": 20,	
                        "action_type": "Low_Level_Continuous",                        
                        "full_observation": 0,                        
                        
                        "RewardsConfig" : {
                            "mission_factor": 1.0,
                            "missile_fire_factor": -0.1,
                            "missile_no_fire_factor": -0.001,
                            "missile_miss_factor": -0.5,
                            "detect_loss_factor": -0.1,
                            "keep_track_factor": 0.005,
                            "hit_enemy_factor": 3.0,
                            "hit_own_factor": -5.0,
                            "situation_factor": 0.1,
                            "final_team_killed_factor": -5.0,
                            "final_enemy_on_target_factor": -3.0,
                            "final_enemies_killed_factor": 5.0,
                            "final_max_cycles_factor": 3.0
                        }
                    },

                    "AgentsConfig" : 
                    {
                        "blue_agents": { 
                            "num_agents" : 1,
                            "base_behavior": "external", 
                            "beh_config" : {
                                "dShot" : 0.85,
                                "lCrank": 0.60,
                                "lBreak": 0.95
                            },                                             
                            "init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
                            "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                            "init_hdg": 0.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},				
                            "rnd_shot_dist_var": 0.0,
                            "wez_models" : "res://assets/Default_Wez_params.json"
                        },	
                        "red_agents":
                        { 
                            "num_agents" : 1, 
                            "base_behavior": "duck",
                            "beh_config" : {
                                "dShot" : 0.85,
                                "lCrank": 0.60,
                                "lBreak": 0.95
                            },
                            "init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
                            "offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
                            "init_hdg" : 180.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},				
                            "rnd_shot_dist_var": 0.0,
                            "wez_models" : "res://assets/Default_Wez_params.json"
                        }
                    }	
                }
#max_cycles = B_ACE_Config["max_cycles"]
n_agents = 1#B_ACE_Config["n_pursuers"]

dqn_params =    {
                "discount_factor": 0.98, 
                "estimation_step": 20, 
                "target_update_freq": 3000,#max_cycles * n_agents,
                "optminizer": "Adam",
                "lr": 0.00016 
                }

PPO_params= {    
                'action_scaling': True,
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
                  "step_per_epoch": 60000,#5 * (150 * n_agents),
                  "step_per_collect": 6000,# * (10 * n_agents),
                  
                  "batch_size" : 300,
                  
                  "update_per_step": 1 / 100, #Off-Policy Only (run after close a Collect (run many times as necessary to meet the value))
                  
                  "repeat_per_collect":64, #On-Policy Only
                  
                  "episode_per_test": 30,                  
                  "tn_eps_max": 0.80,
                  "ts_eps_max": 0.01,
                  "warmup_size" : 0
                  }
#agent_learn = PPOPolicy(**policy_params)


runConfig = dqn_params
runConfig.update(Policy_Config)
runConfig.update(B_ACE_Config)
runConfig.update(trainer_params) 
runConfig.update(PPO_params)


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
    print(device)

    agents = []        
    
    if Policy_Config["same_policy"]:
        policies_number = 1
    else:
        policies_number = 2#len(env.agents)

    for _ in range(policies_number):      
        
        print(agent_observation_space)
        if model == "DNN_B_ACE":
            net = DNN_B_ACE(
                obs_shape=agent_observation_space.shape,                
                action_shape=4,                
                device="cuda" if torch.cuda.is_available() else "cpu"
                
            ).to(device)        
                   
        if policyModel == "DQN":
            agent_learn = DQNPolicy(
                model=net,
                optim=optim,
                action_space = action_shape,
                discount_factor= dqn_params["discount_factor"],
                estimation_step=dqn_params["estimation_step"],
                target_update_freq=dqn_params["target_update_freq"],
                reward_normalization = False,
                clip_loss_grad = False 
            ) 
         
         
        if model == "PPO_DNN":
            
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
    
    env = GodotRLPettingZooWrapper( convert_action_space = True,
                                    device = 'cpu',
                                    **B_ACE_Config)
    
    env.action_space = env.action_space()
    #env = PettingZooEnv(env)  
    
    return env  
   

# print(json.dumps(runConfig, indent=4))
if __name__ == "__main__":
                        
    torch.set_grad_enabled(True) 
   
    # ======== Step 1: Environment setup =========
    train_envs = SubprocVectorEnv([_get_env for _ in range(train_env_num)])#, share_memory = True )
    test_envs = SubprocVectorEnv([_get_env for _ in range(test_env_num)])#, share_memory = True) 

    # seed
    seed = 100
    np.random.seed(seed)
    
    torch.manual_seed(seed)

    #train_envs.seed(seed)
    #test_envs.seed(seed)

    # ======== Step 2: Agent setup =========
    policy, optim, agents = _get_agents()    

    
    if True:
        # ======== Step 3: Collector setup =========
        train_collector = Collector(
            policy,
            train_envs,
            #VectorReplayBuffer(300_000, len(train_envs)),
            PrioritizedVectorReplayBuffer( 300_000, len(train_envs), alpha=0.6, beta=0.4) , 
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
        project = "B_ACE01",
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
        return rews#np.sum(rews)




    # # ======== Step 5: Run the trainer =========   
    onPolicyTrainer = OnpolicyTrainer(
        policy=policy,
        train_collector=train_collector,
        test_collector=test_collector,
        max_epoch=trainer_params['max_epoch'],
        
        step_per_epoch=trainer_params['step_per_epoch'],
                        
        batch_size=trainer_params['batch_size'],
        step_per_collect=trainer_params['step_per_collect'],
        repeat_per_collect=trainer_params['repeat_per_collect'],
        
        episode_per_test=trainer_params['episode_per_test'],
        stop_fn=stop_fn,
        save_best_fn=save_best_fn,
        reward_metric=reward_metric,
        test_in_train=True,
        show_progress = True,
        logger=logger,
    )
    

    writer.close()
    
    # # ======== Step 5: Run the trainer =========
    # offPolicyTrainer = OffpolicyTrainer(
    #     policy=policy,
    #     train_collector=train_collector,
    #     test_collector=test_collector,        
    #     max_epoch=trainer_params['max_epoch'],
    #     step_per_epoch=trainer_params['step_per_epoch'],
    #     step_per_collect=trainer_params['step_per_collect'],        
    #     episode_per_test= trainer_params['episode_per_test'],
    #     batch_size=trainer_params['batch_size'],
    #     train_fn=train_fn,
    #     test_fn=test_fn,
    #     stop_fn=stop_fn,
    #     save_best_fn=save_best_fn,
    #     # save_test_best_fn=save_test_best_fn,
    #     update_per_step=trainer_params['update_per_step'],
    #     logger=logger,
    #     test_in_train=True,
    #     reward_metric=reward_metric,
    #     show_progress = True 
               
    #     )
    
    result = onPolicyTrainer.run()
    writer.close()
    # return result, policy.policies[agents[1]]
    print(f"\n==========Result==========\n{result}")
    print("\n(the trained policy can be accessed via policy.policies[agents[0]])")