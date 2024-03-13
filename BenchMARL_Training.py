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
    experiment_config.prefer_continuous_actions = False
    experiment_config.evaluation_interval = 18000
    experiment_config.checkpoint_interval = 60000
    
    # Number of frames collected and each experiment iteration
    experiment_config.on_policy_collected_frames_per_batch = 6000
    # This is the number of times collected_frames_per_batch will be split into minibatches and trained
    experiment_config.on_policy_n_minibatch_iters = 64
    # In on-policy algorithms the train_batch_size will be equal to the on_policy_collected_frames_per_batch
    # and it will be split into minibatches with this number of frames for training
    experiment_config.on_policy_minibatch_size = 256
    # experiment_config.exploration_eps_init = 1.0
    # experiment_config.exploration_eps_end = 1.0   
    experiment_config.evaluation_episodes = 20              
    experiment_config.on_policy_n_envs_per_worker = 1
    experiment_config.off_policy_n_envs_per_worker = 1

    # experiment_config.evaluation = True  # Enable evaluation mode
    # experiment_config.restore_file = "mappo_b_ace_mlp__a5dbb727_24_02_26-23_09_37/checkpoints/checkpoint_2142000.pt"
    # experiment_config.loggers = []
    experiment_config.save_folder = "Results"
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
        'num_allies': 1,
        'num_enemies': 1,
        'action_type': 'Low_Level_Discrete',
        'enemies_baseline': 'baseline1',
        'full_observation': 0
    }
    
    task.config = config_dict
            
    algorithm_config = IqlConfig.get_from_yaml()

    # Loads from "benchmarl/conf/model/layers/mlp.yaml"
    # model_config = GnnConfig.get_from_yaml()
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
