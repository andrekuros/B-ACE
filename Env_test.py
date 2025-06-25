# This is a simple example script demonstrating how to use the B_ACE_GodotRLPettingZooWrapper
# to interact with the B-ACE Godot environment from a Python script.
from b_ace_py.utils import load_b_ace_config
from b_ace_py.B_ACE_GodotPettingZooWrapper import B_ACE_GodotPettingZooWrapper

# Define the environment configuration
B_ACE_config = load_b_ace_config('./b_ace_py/Default_B_ACE_config.json')

# Define desired environment configuration
env_config = { 
                "EnvConfig":{
                    "env_path": "./bin/B_ACE_v0.1.exe", # Path to the Godot executable
                    "renderize": 1,
                    "speed_up": 50,
                    "action_type":"Low_Level_Continuous",
                }
            }
# Define desired agents configuration
agents_config = {
                    "AgentsConfig":{
                        "blue_agents":{
                            "num_agents":1,
                            "base_behavior": "external",       
                            "init_hdg":0.0
                        },
                        "red_agents":{
                            "num_agents":1,
                            "base_behavior": "baseline1",
                            "init_hdg":180.0
                        }
                    }
}

#Update de default configuration with the desired changes
B_ACE_config.update(env_config)
B_ACE_config.update(agents_config)

# Create an instance of the GodotRLPettingZooWrapper
# Pass the environment and agents configurations
print("Initializing Godot environment...")
env = B_ACE_GodotPettingZooWrapper(device = 'cpu', **B_ACE_config)

# Reset the environment to get the initial observations and info
observations = env.reset()
print (observations)
# print("Action: ", env.action_space)
# print("Observation: ", env.observation_space)
#print(env._get_env_info())
# Close the environment
print("\nSimple example script finished.")


import gymnasium as gym
import torch

from tianshou.data import Collector, CollectStats, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.policy import PPOPolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils.net.common import ActorCritic, Net
from tianshou.utils.net.discrete import Actor, Critic


device = "cuda" if torch.cuda.is_available() else "cpu"


def _get_env():
    """This function is needed to provide callables for DummyVectorEnv."""   
    
       
    env = B_ACE_GodotPettingZooWrapper( convert_action_space = True,
                                    device = "cpu",
                                    **B_ACE_config) 
    #env.action_space = env.action_space()
    #env = PettingZooEnv(env)  
    return env  


# environments
train_envs = DummyVectorEnv([lambda: _get_env() for _ in range(1)])
test_envs =  DummyVectorEnv([lambda: _get_env() for _ in range(1)])

# model & optimizer
assert env.observation_space.shape is not None  # for mypy
net = Net(state_shape=env.observation_space.shape, hidden_sizes=[64, 64], device=device)

actor = Actor(preprocess_net=net, action_shape=env.action_space.shape, device=device).to(device)
critic = Critic(preprocess_net=net, device=device).to(device)
actor_critic = ActorCritic(actor, critic)
optim = torch.optim.Adam(actor_critic.parameters(), lr=0.0003)

# PPO policy
dist = torch.distributions.Categorical
policy: PPOPolicy = PPOPolicy(
    actor=actor,
    critic=critic,
    optim=optim,
    dist_fn=dist,
    action_space=env.action_space,
    action_scaling=False,
)

# collector
train_collector = Collector[CollectStats](
    policy,
    train_envs,
    VectorReplayBuffer(20000, len(train_envs)),
)
test_collector = Collector[CollectStats](policy, test_envs)

train_result = OnpolicyTrainer(
    policy=policy,
    batch_size=256,
    train_collector=train_collector,
    test_collector=test_collector,
    max_epoch=10,
    step_per_epoch=50000,
    repeat_per_collect=10,
    episode_per_test=10,
    step_per_collect=2000,
    stop_fn=lambda mean_reward: mean_reward >= 195,
).run()