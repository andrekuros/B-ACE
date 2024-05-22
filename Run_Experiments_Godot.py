#%%%
from GodotExperimentWrapper import GodotExperimentWrapper
import pandas as pd
import json
import math
import numpy as np
from scipy.stats import bootstrap


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

def generate_cases(blue_altitude, red_altitude, angle_off, aspect_angle, wez_file = "res://assets/Default_Wez_params.json", min_dist=50, max_dist=60, dist_step=0.5):
    
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
#TASK Config    
config_dict = { 	
            "EnvConfig" : 
            {
                "task": "b_ace_v1",
                "env_path": "BVR_AirCombat/bin/B_ACE_v8.exe",
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
                "full_observation": 0,
                
                "RewardsConfig" : {
                    "mission_factor": 0.001,
                    "missile_fire_factor": -0.1,
                    "missile_no_fire_factor": -0.001,
                    "missile_miss_factor": -0.5,
                    "detect_loss_factor": -0.1,
                    "keep_track_factor": 0.001,
                    "hit_enemy_factor": 3.0,
                    "hit_own_factor": -5.0,                            
                    "mission_accomplished_factor": 10.0
                }
            },

            "AgentsConfig" : 
            {
                "blue_agents": { 
                    "num_agents" : 2,
                    "beh_config" : {
                        "dShot" : 0.50,
                        "lCrank": 0.40,
                        "lBreak": 0.8
                    },
                    "base_behavior": "baseline1",                  
                    "init_position": {"x": 0.0, "y": 25000.0,"z": -30.0},
                    "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                    "init_hdg": 180.0,                        
                    "target_position": {"x": 0.0,"y": 25000.0,"z": 0.0},
                    "rnd_offset_range":{"x": 10.0,"y": 20000.0,"z": 10.0},				
                    "rnd_shot_dist_var": 0.0,
                    "wez_models" : "res://assets/Default_Wez_params.json"
                },	
                "red_agents":
                { 
                    "num_agents" : 2, 
                    "base_behavior": "baseline1",
                    "beh_config" : {
                        "dShot" : 0.50,
                        "lCrank": 0.40,
                        "lBreak": 0.8
                    },
                    "init_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
                    "offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
                    "init_hdg" : 0.0,                        
                    "target_position": {"x": 0.0,"y": 25000.0,"z": 0.0},
                    "rnd_offset_range":{"x": 10.0,"y": 20000.0,"z": 10.0},
                    "rnd_shot_dist_var": 0.0,
                    "wez_models" : "res://assets/Default_Wez_params.json"
                }
            }	
}                   


                    
#%%%

#wezFile = "res://assets//Wez_paramsPR2_MAE_121_060.json"
#wezFile =  "res://assets//Wez_paramsPR3_MAE_074_046.json"
wezFile = "res://assets//Wez_paramsPR4_MAE_044_037.json"
#wezFile = "res://assets//Default_Wez_params.json"

cases =  generate_cases(20000, 20000, 180, 90, wez_file=wezFile)       
#print(cases)
experimentConfig = { 'runs_per_case': 200, 'cases' : cases }

config_dict['ExperimentConfig'] = experimentConfig

# Create the GodotExperimentWrapper
env = GodotExperimentWrapper(config_dict)

# Run the experiment
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
        "team_name": team_name,
        "mean_killed": killed_mean,
        "killed_ci_low": killed_ci_low,
        "killed_ci_high": killed_ci_high,
        "mean_missile": missile_mean,
        "missile_ci_low": missile_ci_low,
        "missile_ci_high": missile_ci_high,
    })

_results.append(merged_result)

df_results = pd.DataFrame(_results[0])

print(df_results)
# %%
