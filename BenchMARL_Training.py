#%%%

from benchmarl.environments import VmasTask
from benchmarl.environments import PettingZooTask
import torch

from benchmarl.environments.godotrl import b_ace

from benchmarl.experiment import Experiment, ExperimentConfig
from benchmarl.models.mlp import MlpConfig
from benchmarl.algorithms import IppoConfig, IqlConfig, QmixConfig, VdnConfig, VdnConfig, MappoConfig, MaddpgConfig
from benchmarl.models.gnn import GnnConfig

if __name__ == "__main__":
    
    # Loads from "benchmarl/conf/experiment/base_experiment.yaml"
    experiment_config = ExperimentConfig.get_from_yaml()

    experiment_config.sampling_device = 'cuda'
    experiment_config.train_device = 'cuda'
    experiment_config.prefer_continuous_actions = True
    experiment_config.checkpoint_interval = 180000
    
    experiment_config.evaluation_interval = 18000
    experiment_config.evaluation_episodes = 20              
    
    # experiment_config.exploration_eps_init = 1.0
    # experiment_config.exploration_eps_end = 1.0   
    
    # ----- On policy Configuration ----- #
    
    # Number of frames collected and each experiment iteration
    experiment_config.on_policy_collected_frames_per_batch = 6000
    # This is the number of times collected_frames_per_batch will be split into minibatches and trained
    experiment_config.on_policy_n_minibatch_iters = 64
    # In on-policy algorithms the train_batch_size will be equal to the on_policy_collected_frames_per_batch
    # and it will be split into minibatches with this number of frames for training
    experiment_config.on_policy_minibatch_size = 256
    
    # ----- Off Policy Configuration -----   #
    
    # Number of frames collected and each experiment iteration
    experiment_config.off_policy_collected_frames_per_batch: 6000
    # Number of environments used for collection
    # If the environment is vectorized, this will be the number of batched environments.
    # Otherwise batching will be simulated and each env will be run sequentially.
    # This is the number of times off_policy_train_batch_size will be sampled from the buffer and trained over.
    experiment_config.off_policy_n_optimizer_steps: 64
    # Number of frames used for each off_policy_n_optimizer_steps when training off-policy algorithms
    experiment_config.off_policy_train_batch_size: 1000
    # Maximum number of frames to keep in replay buffer memory for off-policy algorithms
    experiment_config.off_policy_memory_size: 30_000_000
    # Number of random action frames to prefill the replay buffer with
    experiment_config.off_policy_init_random_frames: 0
    
    
    experiment_config.off_policy_n_envs_per_worker= 1
    experiment_config.on_policy_n_envs_per_worker= 1
     
    experiment_config.evaluation = True  # Enable evaluation mode
    experiment_config.restore_file = "D:\Projects\B-ACE\B-ACE\Results\maddpg_b_ace_mlp__14627b2c_24_03_17-21_29_33\checkpoints\checkpoint_2340000.pt"
    experiment_config.loggers = []
    
    #experiment_config.save_folder = "Results"
    # experiment_config.lr = 0.0003
    
    #TASK Config
    task = b_ace.B_ACE.b_ace.get_from_yaml()  
    config_dict = {
        'task': 'b_ace_v1',
        'env_path': 'BVR_AirCombat/bin/B_ACE_v1.exe',
        'show_window': True,
        'seed': 0,
        'port': 12500,
        'action_repeat': 20,
        'speedup': 2000,
        'num_allies': 2,
        'num_enemies': 2,
        'action_type': 'Low_Level_Continuous' ,
        'enemies_baseline': 'baseline1',
        'full_observation': 0
    }
    
    task.config = config_dict
            
    algorithm_config = MaddpgConfig.get_from_yaml()

    # Loads from "benchmarl/conf/model/layers/mlp.yaml"
    #model_config = GnnConfig.get_from_yaml()
    model_config = MlpConfig.get_from_yaml()
    critic_model_config = MlpConfig.get_from_yaml()

    model_config.layers = [256,512,512]

    for i in range (1):

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
