#%%%
# Get the absolute path of the directory where the current script resides and
#add to the system root
import os
import sys
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)
project_root = script_dir.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from b_ace_py.B_ACE_ExperimentWrapper import  B_ACE_GodotExperimentWrapper

import pandas as pd
import json
import math
import numpy as np
#from scipy.stats import bootstrap


def bootstrap_ci(data, metric, n_bootstrap=10000, confidence=0.95):
    data_values = data[metric]
    data_mean = np.mean(data_values)

    bootstrap_samples = []
    for _ in range(n_bootstrap):
        bootstrap_sample = np.random.choice(data_values, size=len(data_values), replace=True)
        bootstrap_samples.append(np.mean(bootstrap_sample))

    alpha = (1 - confidence) / 2
    ci_low = np.percentile(bootstrap_samples, alpha * 100)
    ci_high = np.percentile(bootstrap_samples, (1 - alpha) * 100)

    return data_mean, ci_low, ci_high

def clamp_HdgD(hdg):      
    if hdg > 180:
        return -(360 - hdg)        
    
    if hdg < -180:
        return (360 + hdg )    
    return hdg

def generate_wez_cases(blue_altitude, red_altitude, angle_off, aspect_angle, wez_file = "res://assets/Default_Wez_params.json", min_dist=50, max_dist=60, dist_step=0.5):
    
    cases = []
    dist_cases = [x / 10 for x in range(min_dist * 10, max_dist * 10, 5)]    
       
    for i in range(10):
        
        blue_hdg = clamp_HdgD(aspect_angle)
        red_hdg = clamp_HdgD(blue_hdg + angle_off)                 
        
        case = {
            'AgentsConfig': {
                'blue_agents': {
                    'init_position': {'x': 30.0, 'y': blue_altitude, 'z': 0.0},                    
                    'init_hdg': blue_hdg,
                    "wez_models" : wez_file                    
                },    
                'red_agents': {
                    'init_position': {'x': -30.0, 'y': red_altitude, 'z': 0.0},                    
                    'init_hdg': red_hdg, 
                    "wez_models" : "res://assets//Wez_paramsPR3_MAE_074_046.json"                
                }                
            }
        }
        cases.append(case)

    return cases

def generate_behavior_case(dShot = 0.85, lCrank = 0.60, lBreak = 0.95 ):
    
    case = { "AgentsConfig" : 
                {
                "blue_agents": { 
                        "num_agents" : 1,
                        "beh_config" : 
                        {
                            "dShot" : dShot,
                            "lCrank": lCrank,
                            "lBreak": lBreak
                        },
                },
                "red_agents": { 
                        "num_agents" : 1,
                        "beh_config" : 
                        {
                            "dShot" : dShot,
                            "lCrank": lCrank,
                            "lBreak": lBreak
                        },
                }
            }            
    }
    
    return case

#TASK Config    
config_dict = { "EnvConfig" : 
                {
                    "task": "b_ace_v1",
                    'env_path': 'BVR_AirCombat/bin/B_ACE_v10.exe',		
                    "port": 12500,
                    "renderize": 1,
                    "debug_view": 0,
                    "phy_fps": 20,
                    "speed_up": 50000,
                    "max_cycles": 36000,
                    "experiment_mode"  : 1,
                    "parallel_envs": 1,	
                    "seed": 1,	
                    "action_repeat": 20,	
                    "action_type": "Low_Level_Continuous",                                            
                                        
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
                        "num_agents" : 1,
                        
                        "base_behavior": "baseline1",
                        "beh_config" : {
                            "dShot" : 0.85,
                            "lCrank": 0.60,
                            "lBreak": 0.95
                        },                  
                        
                        "init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
                        "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                        "init_hdg": 0.0,                        
                        "target_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
                        "rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},				
                        "rnd_shot_dist_var": 0.025,
                        "rnd_crank_var": 0.025,
                        "rnd_break_var": 0.025,
                        "wez_models" : "res://assets/wez/Default_Wez_params.json"
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
                        "rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},				                        
                        "rnd_shot_dist_var": 0.025,
                        "rnd_crank_var": 0.025,
                        "rnd_break_var": 0.025,
                        "wez_models" : "res://assets/wez/Default_Wez_params.json"
                    }
                },
                
}
    

                    
#%%% RUN Experiments
#wezFile = "res://assets//Default_Wez_params.json"

cases = []
for case in range(5):
    
    dict_beh = generate_behavior_case(dShot = 0.85, 
                                lCrank = 0.60, 
                                lBreak = 0.95 )
    dict_beh["EnvConfig"] = { "seed" : case}
    cases.append(dict_beh) 
#print(cases)
experimentConfig = { 'runs_per_case': 30, 'cases' : cases }

config_dict['ExperimentConfig'] = experimentConfig

# Create the GodotExperimentWrapper
env = B_ACE_GodotExperimentWrapper(config_dict)

# Run the experiment
env.send_sim_config(experimentConfig)
results = env.watch_experiment()

# Save the experiment results to a file
with open('experiment_results.json' , "w") as file:
    json.dump(results, file, indent=4)

# Flatten the list of lists into a single list of dictionaries
flat_data = [item for sublist in results for item in sublist]
# Create the DataFrame
df = pd.DataFrame(flat_data)
#print(df)

#%%%
_results = []

team_stats = {}
teams = ["Blue", "Red"]
team_stats[teams[0]] = {"killed":[], "missile" : []}
team_stats[teams[1]] ={"killed":[], "missile" : []}

for sim_result in flat_data:
    if True:#sim_result["run_num"] != 1: 
        for i, final_result in enumerate(sim_result["final_results"]): 
                        
            team_stats[teams[i]]["killed"].append(final_result["killed"])
            team_stats[teams[i]]["missile"].append(final_result["missile"])

merged_result = []

for team_name, stats in team_stats.items():
    #killed_data = np.array(stats["killed"])
    #missile_data = np.array(stats["missile"])
    
    killed_mean, killed_ci_low, killed_ci_high = bootstrap_ci(stats, "killed" )
    missile_mean, missile_ci_low, missile_ci_high = bootstrap_ci(stats, "missile" )

    merged_result.append({
        "team": team_name,
        "killed": f'{killed_mean:.2f}',
        "ci_killed": f'({killed_ci_low:.2f},{killed_ci_high:.2f})',
        "missiles": f'{missile_mean:.2f}',
        "ci_missiles": f'({missile_ci_low:.2f},{missile_ci_high:.2f})',        
    })    

_results.append(merged_result)

df_results = pd.DataFrame(_results[0])

print(df_results)

# %%
import pandas as pd

# Data for the reward and penalty factors table
reward_data = {
    "Factor": [
        "mission_accomplished_factor", "mission_factor", 
        "missile_fire_factor", "missile_no_fire_factor", "missile_miss_factor", 
        "detect_loss_factor", "keep_track_factor", 
        "hit_enemy_factor", "hit_own_factor"
    ],
    "Default Value": [
        10.0, 0.001, 
        -0.1, -0.001, -0.5, 
        -0.1, 0.001, 
        3.0, -5.0
    ],
    "Explanation": [
        "Reward for successfully completing a mission", "Shaping reward related to mission objectives", 
        "Penalty for firing a missile", "Shaping penalty for firing when not possible", "Penalty for missing a target with a missile", 
        "Shaping penalty for losing track of an enemy", "Shaping reward for maintaining track of an enemy", 
        "Reward for hitting an enemy", "Penalty for being hit"
    ]
}

# Create DataFrame
reward_df = pd.DataFrame(reward_data)

# Save to Excel file
reward_df.to_excel("Reward_Penalty_Factors_B_ACE_Environment.xlsx", index=False)


# %%
