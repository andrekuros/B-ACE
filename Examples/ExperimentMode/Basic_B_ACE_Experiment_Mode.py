#%%%
# Get the absolute path of the directory where the current script resides and
#add to the system root
import os
import sys
from pathlib import Path
import pandas as pd
import json
import math
import numpy as np

script_dir = Path(__file__).parent.resolve()
os.chdir(script_dir)
project_root = script_dir.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from b_ace_py.B_ACE_ExperimentWrapper import  B_ACE_ExperimentWrapper
from b_ace_py.utils import load_b_ace_config

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


# Define the environment configuration
B_ACE_config = load_b_ace_config('../../b_ace_py/Default_B_ACE_config.json')

# Define desired environment configuration
env_config = { 
                "EnvConfig":{
                    'task': 'basic_experiment_01',
                    "env_path": "../../bin/B_ACE_v0.1.exe", # Path to the Godot executable
                    'experiment_mode'  : 1,
                    "renderize": 0
                }
}
# Define desired agents configuration
agents_config = {"AgentsConfig" : 
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
                            "rnd_shot_dist_var": 0.025,
                            "rnd_crank_var": 0.025,
                            "rnd_break_var": 0.025,                       
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
                        }
                    }
                }
B_ACE_config.update(env_config)
B_ACE_config.update(agents_config)    

                    
#%%% Config and RUN Experiments
cases = []

#Each case will run in a parallel viewport in godot with different seed
for case in range(1):   
    dict_beh = generate_behavior_case(dShot = 0.85, 
                                lCrank = 0.60, 
                                lBreak = 0.95 )
    dict_beh["EnvConfig"] = { "seed" : case}
    cases.append(dict_beh) 

experimentConfig = { 'runs_per_case': 30, 'cases' : cases }

# Create the GodotExperimentWrapper
env = B_ACE_ExperimentWrapper(B_ACE_config)

# Run the experiment
env.send_sim_config(experimentConfig)
results = env.watch_experiment()
env.close()

# Save the experiment results to a file
with open('experiment_results.json' , "w") as file:
    json.dump(results, file, indent=4)

# Flatten the list of lists into a single list of dictionaries
flat_data = [item for sublist in results for item in sublist]
# Create the DataFrame
df = pd.DataFrame(flat_data)

#%%%
_results = []

team_stats = {}
teams = ["Blue", "Red"]
team_stats[teams[0]] = {"killed":[], "missile" : []}
team_stats[teams[1]] ={"killed":[], "missile" : []}

for sim_result in flat_data:
        for i, final_result in enumerate(sim_result["final_results"]): 
                        
            team_stats[teams[i]]["killed"].append(final_result["killed"])
            team_stats[teams[i]]["missile"].append(final_result["missile"])

merged_result = []

for team_name, stats in team_stats.items():
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