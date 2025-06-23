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
                    "renderize": 1
             }
}
# Define desired agents configuration
agents_config = {
                    "AgentsConfig":{
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

#Update de default configuration with the desired changes
B_ACE_config.update(env_config)
B_ACE_config.update(agents_config)

# Create an instance of the GodotRLPettingZooWrapper
# Pass the environment and agents configurations
print("Initializing Godot environment...")
env = B_ACE_GodotPettingZooWrapper(device = 'cpu', **B_ACE_config)

# Reset the environment to get the initial observations and info
observations = env.reset()
print("Environment reset.")
print("Initial observations:\n", observations)

# Run a few steps in the environment
num_steps = 3000
print(f"Running {num_steps} steps...")

for step in range(num_steps):
    # In a real RL scenario, you would use your agent's policy to get actions
    # For this simple example, we'll use fixed actions
    actions = {}
    turn_side = 1
    for agent in env.possible_agents:
        # Get the action space for the current agent
        agent_action_space = env.action_space(agent)
        
        # For continuous action space (Box), sample a random value within the bounds
        # Action [hdg, level, g_force, fire] 
        # [hdg]     -> Desired heading is 180 * hdg to the right side (-0.1 to the left)
        # [level]   -> 25000ft * level + 25000ft  	
		# [g_force] -> (g_force * (max_g  - 1.0) + (max_g + 1.0))/2.0	
		# [fire]    -> 0 if last_fire_input <= 0 else 1 (1 is fire missile)
   
        actions[agent] = [0.1 * turn_side, 0.5, 2.0, 0.0] 
        turn_side *= -1


    # Take a step in the environment
    observations, rewards, terminations, truncations, info = env.step(actions)

    # Check if any agent has terminated or truncated
    if all(terminations.values()) or all(truncations.values()):
        print("Episode finished.")
        # In a real RL scenario, you would reset the environment here
        # observations, info = env.reset()
        break # Exit the loop for this example

# Close the environment
env.close()
print("Environment closed.")
print("Simple example script finished.")
