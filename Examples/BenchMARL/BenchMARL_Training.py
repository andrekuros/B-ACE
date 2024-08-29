#%%%
import argparse
import sys
import os
from pathlib import Path
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


def get_policy():
    current_folder = Path(os.path.dirname(os.path.realpath(__file__)))
    config_folder = current_folder / "yaml"

    config = ExperimentConfig.get_from_yaml(str(config_folder / "experiment.yaml"))
    config.restore_file = str(current_folder / "checkpoint.pt")

    experiment = Experiment(
        config=config,
        task=VmasTask.RM_NAVIGATION.get_from_yaml(
            str(config_folder / "rm_navigation.yaml")
        ),
        algorithm_config=IppoConfig.get_from_yaml(str(config_folder / "ippo.yaml")),
        model_config=RmGnnConfig.get_from_yaml(str(config_folder / "rmgnn.yaml")),
        critic_model_config=RmGnnConfig.get_from_yaml(
            str(config_folder / "rmgnn.yaml")
        ),
        seed=0,
    )

    return experiment.policy

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

    experiment_config.sampling_device = 'cpu'
    experiment_config.train_device = 'cpu'
    experiment_config.max_n_iters = 300
    experiment_config.checkpoint_interval = 12000000
    
    # Whether to share the parameters of the policy within agent groups
    experiment_config.share_policy_params= True
    experiment_config.prefer_continuous_actions = True  
    experiment_config.evaluation_interval = 36000
    experiment_config.evaluation_episodes = 30   
    experiment_config.evaluation_deterministic_actions = True  
    
    experiment_config.exploration_eps_init = 0.50
    experiment_config.exploration_eps_end = 0.01   
    
    # ----- On policy Configuration ----- #
    experiment_config.on_policy_collected_frames_per_batch = 12000    
    experiment_config.on_policy_n_minibatch_iters = 1     
    experiment_config.on_policy_minibatch_size = 1
    
    
    #-------------------------------------------#
    
    # ----- Off Policy Configuration -----   #
    
    experiment_config.off_policy_collected_frames_per_batch: 12000
    experiment_config.off_policy_n_optimizer_steps= 64    
    experiment_config.off_policy_train_batch_size= 256    
    experiment_config.off_policy_memory_size: 100_000    
    experiment_config.off_policy_init_random_frames= 0
       
    #-------------------------------------------#
    experiment_config.off_policy_n_envs_per_worker= 4
    experiment_config.on_policy_n_envs_per_worker= 4
 
    experiment_config.lr = 0.000005
    
    #TASK Config    
    b_ace_config = { 	
                    "EnvConfig" : 
                    {
                        "task": "b_ace_v1",
                        "env_path": "../../BVR_AirCombat/bin/B_ACE_v12.exe",
                        "port": 12500,
                        "renderize": 0,
                        "debug_view": 0,
                        "phy_fps": 20,
                        "speed_up": 50000,
                        "max_cycles": 36000,
                        "experiment_mode"  : 0,
                        "parallel_envs": 1,	
                        "seed": 0,	
                        "action_repeat": 20,	
                        "action_type": "Low_Level_Continuous",                        
                        "full_observation": 1,
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
                            "num_agents" : 4,
                            "mission"    : "DCA",
                            "beh_config" : {
                                            "dShot" : [1.04, 0.50, 1.09],
                                            "lCrank": [1.06, 0.98, 0.98],
                                            "lBreak": [1.05, 1.17, 0.45]
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
                            "base_behavior": "baseline1",
                            "mission"    : "striker",
                            "beh_config" : {
                                "dShot" : [1.04],#, 0.50, 1.09],
                                "lCrank": [1.06],#, 0.98, 0.98],
                                "lBreak": [1.05]#, 1.17, 0.45]
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
        #algorithm_config = MAPpoConfig.get_from_yaml()
        algorithm_config = MappoConfig.get_from_yaml()
        #algorithm_config.share_param_critic = True
        
    #algorithm_config.share_param_critic = True
    # Loads from "benchmarl/conf/model/layers/mlp.yaml"
    #model_config = GnnConfig.get_from_yaml()
    model_config = MlpConfig.get_from_yaml()
    
    critic_model_config = MlpConfig.get_from_yaml()

    model_config.layers = [256,256,256]
    
    #experiment_config.evaluation = False  # Enable evaluation mode
    #experiment_config.restore_file = "D:\Projects\B-ACE\B-ACE\Results\iddpg_b_ace_mlp__861c72db_24_07_25-09_33_27\checkpoints\checkpoint_480000.pt"
    #experiment_config.loggers = []
    
    if False:
        
        
        experiment_config.restore_file = "D:\Projects\B-ACE\B-ACE\Results\iddpg_b_ace_mlp__861c72db_24_07_25-09_33_27\checkpoints\checkpoint_480000.pt"
        
        experiment_to_load = Experiment(
            task=task,
            algorithm_config=algorithm_config,
            model_config=model_config,
            critic_model_config=critic_model_config,
            seed=0,
            config=experiment_config,
            callbacks=None#[SaveBest() ],
        )
        
        loaded_policy = experiment_to_load.policy
        
        experiment_config.restore_file = None
    else:        
        experiment_config.save_folder = "Results"
    
    for i in range (0,5):

        experiment = Experiment(
            task=task,
            algorithm_config=algorithm_config,
            model_config=model_config,
            critic_model_config=critic_model_config,
            seed=i,
            config=experiment_config,
            callbacks=None#[SaveBest() ],
        )
        if False:
            experiment.policy = loaded_policy
        experiment.run()
# %%
