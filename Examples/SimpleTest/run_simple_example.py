# This is a simple example script demonstrating how to use the B_ACE_GodotRLPettingZooWrapper
# to interact with the B-ACE Godot environment from a Python script.
# Get the absolute path of the directory where the current script resides
import os
import sys
from pathlib import Path
#script_directory = os.path.dirname(os.path.abspath(__file__))

script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)
project_root = script_dir.parent.parent.resolve()
# Add the project root to sys.path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import time
from b_ace_py.godot_env import GodotEnv
from b_ace_py.utils import convert_macos_path
from b_ace_py.utils import load_b_ace_config

import gymnasium as gym
import numpy as np

# Import the custom PettingZoo wrapper
from b_ace_py.B_ACE_GodotPettingZooWrapper import B_ACE_GodotPettingZooWrapper

# Define the environment configuration
B_ACE_config = load_b_ace_config(Path(str(project_root) + '/b_ace_py/Default_B_ACE_config.json'))

# This configuration is passed to the Godot environment
env_config = { "EnvConfig":{
    "env_path": str(project_root) + "/bin/B_ACE_v0.1.exe", # Path to the Godot executable
    "renderize": 1
    }
}
# Define the agents configuration
agents_config = {"AgentsConfig":{
                    "blue_agents":{
                        "num_agents":2,
                        "base_behavior": "external",       
                        "init_hdg":0.0
                    },
                    "red_agents":{
                        "num_agents":2,
                        "base_behavior": "baseline1",
                        "init_hdg":180.0
                    }
                }
}

B_ACE_config.update(env_config)
B_ACE_config.update(agents_config)

# Create an instance of the GodotRLPettingZooWrapper
# Pass the environment and agents configurations
print("Initializing Godot environment...")
env = B_ACE_GodotPettingZooWrapper(device = 'cpu', **B_ACE_config)
print("Environment initialized.")

# Reset the environment to get the initial observations and info
print("Resetting environment...")
observations = env.reset()
print("Environment reset.")
print("Initial observations:\n", observations)

# Run a few steps in the environment
num_steps = 1500
print(f"Running {num_steps} steps...")

for step in range(num_steps):
    # In a real RL scenario, you would use your agent's policy to get actions
    # For this simple example, we'll use random actions
    actions = {}
    for agent in env.possible_agents:
        # Get the action space for the current agent
        agent_action_space = env.action_space(agent)
        
        # For continuous action space (Box), sample a random value within the bounds
        actions[agent] = [0.1, 1.0, 1.0, 0.0] 
        

    # Ensure all agents have an action, even if it's None for unsupported types
    for agent in env.possible_agents:
        if agent not in actions:
             actions[agent] = [0.1, 1.0, 1.0, 0.0]  # Or a default action if applicable

    #print(f"Step {step+1}: Actions taken by agents: {actions}")

    # Take a step in the environment
    observations, rewards, terminations, truncations, info = env.step(actions)

    #print(f"Step {step+1}: Observations: {observations}")
    #print(f"Step {step+1}: Rewards: {rewards}")
    #print(f"Step {step+1}: Terminations: {terminations}")
    #print(f"Step {step+1}: Truncations: {truncations}")
    #print(f"Step {step+1}: Info: {info}")

    # Check if any agent has terminated or truncated
    if any(terminations.values()) or any(truncations.values()):
        print("Episode finished.")
        # In a real RL scenario, you would reset the environment here
        # observations, info = env.reset()
        break # Exit the loop for this example

# Close the environment
print("Closing environment...")
env.close()
print("Environment closed.")

print("Simple example script finished.")
