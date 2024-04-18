#%%%
import argparse
import sys
from typing import List
from benchmarl.environments import VmasTask 
from benchmarl.environments import PettingZooTask
import torch
from tensordict import TensorDict, TensorDictBase
from benchmarl.environments.godotrl import b_ace
from benchmarl.experiment import Experiment, ExperimentConfig
from benchmarl.models.mlp import MlpConfig
from benchmarl.algorithms import IppoConfig, IsacConfig, IqlConfig, IddpgConfig
from benchmarl.algorithms import QmixConfig, VdnConfig, MappoConfig, MaddpgConfig
from benchmarl.models.gnn import GnnConfig
from benchmarl.experiment.callback import Callback

def update_dict(config_dict, key_path, value):
    keys = key_path.split('.')
    current_dict = config_dict
    for key in keys[:-1]:
        if key not in current_dict:
            print(f"Error: Key '{key}' not found in the configuration.")
            sys.exit(1)
        current_dict = current_dict[key]
    if keys[-1] not in current_dict:
        print(f"Error: Key '{keys[-1]}' not found in the configuration.")
        sys.exit(1)
    current_dict[keys[-1]] = value


class SaveBest(Callback):
    
    def __init__(self):
        self.best_mean_reward = -1000000
        #self.folder_name_backup = self.experiment.folder_name
            
    def on_evaluation_end(self, rollouts: List[TensorDictBase]):
        
        if self.experiment.mean_return > self.best_mean_reward:
            #self.experiment.folder_name = self.folder_name_backup + "/Best"
            print("New Best Saved ", self.experiment.mean_return)
            self.best_mean_reward = self.experiment.mean_return
            self.experiment._save_experiment()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Run benchmarl experiments.')
    parser.add_argument('--algorithm', type=str, default='iddpg', choices=['ippo', 'isac', 'iql', 'qmix', 'vdn', 'mappo', 'maddpg', 'iddpg'], help='Algorithm configuration to use.')
    parser.add_argument('--config', nargs='*', action='append', help='Key-value pairs to update the b_ace_config.')
    parser.add_argument('--savebest', type=bool, default=False, help='Set to save Checkpoint of best rewards')
    
    saveBest = False
    args = parser.parse_args()
    
    # Loads from "benchmarl/conf/experiment/base_experiment.yaml"
    experiment_config = ExperimentConfig.get_from_yaml()

    experiment_config.sampling_device = 'cuda'
    experiment_config.train_device = 'cuda'
    experiment_config.max_n_iters = 500
    experiment_config.checkpoint_interval = 150000
    
    # Whether to share the parameters of the policy within agent groups
    experiment_config.share_policy_params: True
    experiment_config.prefer_continuous_actions = True  
    experiment_config.evaluation_interval = 18000
    experiment_config.evaluation_episodes = 20   
    experiment_config.evaluation_deterministic_actions = False  
    
             
    
    # experiment_config.exploration_eps_init = 1.0
    # experiment_config.exploration_eps_end = 1.0   
    
    # ----- On policy Configuration ----- #
       
    experiment_config.on_policy_collected_frames_per_batch = 6000    
    #experiment_config.on_policy_n_minibatch_iters = 64    
    #experiment_config.on_policy_minibatch_size = 512
    
    # ----- Off Policy Configuration -----   #
    
    experiment_config.off_policy_collected_frames_per_batch: 6000
    # This is the number of times off_policy_train_batch_size will be sampled from the buffer and trained over.
    experiment_config.off_policy_n_optimizer_steps: 64    
    experiment_config.off_policy_train_batch_size: 512    
    experiment_config.off_policy_memory_size: 1_000_000    
    experiment_config.off_policy_init_random_frames: 0
    
    experiment_config.off_policy_n_envs_per_worker= 4
    experiment_config.on_policy_n_envs_per_worker= 4
     
    #experiment_config.evaluation = True  # Enable evaluation mode
    #experiment_config.restore_file = "D:\Projects\B-ACE\B-ACE\Results\maddpg_b_ace_mlp__14627b2c_24_03_17-21_29_33\checkpoints\checkpoint_2340000.pt"
    #experiment_config.loggers = []
    
    experiment_config.save_folder = "Results"
    experiment_config.lr = 0.0005
    
    #TASK Config    
    b_ace_config = { 	
                    "EnvConfig" : 
                    {
                        "task": "b_ace_v1",
                        "env_path": "BVR_AirCombat/bin/B_ACE_v6.exe",
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
                        "full_observation": 1,
                        
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
                            "beh_config" : {
                                "dShot" : 0.85,
                                "lCrank": 0.60,
                                "lBreak": 0.95
                            },
                            "base_behavior": "external",                  
                            "init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
                            "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                            "init_hdg": 0.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},				
                            "rnd_shot_dist_var": 0.0,
                            "wez_models" : "res://assets/Default_Wez_params.json"
                        },	
                        "red_agents":
                        { 
                            "num_agents" : 1, 
                            "base_behavior": "baseline1",
                            "beh_config" : {
                                "dShot" : 0.85,
                                "lCrank": 0.60,
                                "lBreak": 0.95
                            },
                            "init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
                            "offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
                            "init_hdg" : 180.0,                        
                            "target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                            "rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},				
                            "rnd_shot_dist_var": 0.0,
                            "wez_models" : "res://assets/Default_Wez_params.json"
                        }
                    }	
}
        
    task = b_ace.B_ACE.b_ace.get_from_yaml()
 
 
    # Update the configuration dictionary based on command-line input
    if args.config:
        for config_arg in args.config:
            for param in config_arg:
                key_value = param.split('=')
                if len(key_value) != 2:
                    print(f"Error: Invalid configuration argument format: {param}")
                    sys.exit(1)
                key_path, value = key_value
                update_dict(b_ace_config, key_path, value)

    # Print the updated configuration dictionary
    print("Updated configuration:")
    print(b_ace_config)
    task.config = b_ace_config
    
    task.config = b_ace_config       
    if args.savebest == True:
        saveBest = True
    
    
    # Set the algorithm configuration based on the provided argument
    if args.algorithm == 'ippo':
        algorithm_config = IppoConfig.get_from_yaml()
    elif args.algorithm == 'isac':
        algorithm_config = IsacConfig.get_from_yaml()
    elif args.algorithm == 'iql':
        algorithm_config = IqlConfig.get_from_yaml()
    elif args.algorithm == 'qmix':
        algorithm_config = QmixConfig.get_from_yaml()
    elif args.algorithm == 'vdn':
        algorithm_config = VdnConfig.get_from_yaml()
    elif args.algorithm == 'mappo':
        algorithm_config = MappoConfig.get_from_yaml()
    elif args.algorithm == 'maddpg':
        algorithm_config = MaddpgConfig.get_from_yaml()
    else:  # 'iddpg'
        #algorithm_config = IddpgConfig.get_from_yaml()
        algorithm_config = IppoConfig.get_from_yaml()
    
    # Loads from "benchmarl/conf/model/layers/mlp.yaml"
    #model_config = GnnConfig.get_from_yaml()
    model_config = GnnConfig.get_from_yaml()
    critic_model_config = MlpConfig.get_from_yaml()

    model_config.layers = [256,256]
    
    for i in range (3):

        experiment = Experiment(
            task=task,
            algorithm_config=algorithm_config,
            model_config=model_config,
            critic_model_config=critic_model_config,
            seed=i,
            config=experiment_config,
            callbacks=None#[SaveBest() ],
        )
        experiment.run()
# %%
