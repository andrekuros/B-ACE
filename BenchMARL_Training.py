#%%%

from benchmarl.environments import VmasTask 
from benchmarl.environments import PettingZooTask
import torch

from benchmarl.environments.godotrl import b_ace

from benchmarl.experiment import Experiment, ExperimentConfig
from benchmarl.models.mlp import MlpConfig
from benchmarl.algorithms import IppoConfig, IsacConfig, IqlConfig, QmixConfig, VdnConfig, VdnConfig, MappoConfig, MaddpgConfig, IddpgConfig
from benchmarl.models.gnn import GnnConfig

if __name__ == "__main__":
    
    # Loads from "benchmarl/conf/experiment/base_experiment.yaml"
    experiment_config = ExperimentConfig.get_from_yaml()

    experiment_config.sampling_device = 'cpu'
    experiment_config.train_device = 'cuda'
    experiment_config.max_n_iters = 250
    
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
    
    experiment_config.off_policy_n_envs_per_worker= 3
    experiment_config.on_policy_n_envs_per_worker= 3
     
    #experiment_config.evaluation = True  # Enable evaluation mode
    #experiment_config.restore_file = "D:\Projects\B-ACE\B-ACE\Results\maddpg_b_ace_mlp__14627b2c_24_03_17-21_29_33\checkpoints\checkpoint_2340000.pt"
    #experiment_config.loggers = []
    
    experiment_config.save_folder = "Results"
    experiment_config.lr = 0.000003
    
    #TASK Config
    task = b_ace.B_ACE.b_ace.get_from_yaml()  
    b_ace_config = { 'EnvConfig' : {
                        'task': 'b_ace_v1',
                        'env_path': 'BVR_AirCombat/bin/B_ACE_v4.exe',
                        'renderize': 1,
                        'experiment_mode'  : 0,
                        'parallel_envs': 1,
                        'seed': 10,
                        'port': 12500,
                        'action_repeat': 20,
                        'speedup': 2000,
                        'action_type': 'Low_Level_Continuous' ,                        
                        'full_observation': 0,
                        'actions_2d': 0
                        },
                    "SimConfig" : {                        
                        'num_allies': 1,
                        'num_enemies': 1
                        ,
                        'enemies_behavior': 'baseline1',
                        'agents_behavior' : 'external'    
                    }
                }
      
    task.config = b_ace_config    
            
    algorithm_config = IddpgConfig.get_from_yaml()

    # Loads from "benchmarl/conf/model/layers/mlp.yaml"
    #model_config = GnnConfig.get_from_yaml()
    model_config = MlpConfig.get_from_yaml()
    critic_model_config = MlpConfig.get_from_yaml()

    model_config.layers = [256,256]

    for i in range (3):

        experiment = Experiment(
            task=task,
            algorithm_config=algorithm_config,
            model_config=model_config,
            critic_model_config=critic_model_config,
            seed=i,
            config=experiment_config
        )
        experiment.run()
# %%
