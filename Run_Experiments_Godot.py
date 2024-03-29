from GodotExperimentWrapper import GodotExperimentWrapper
import pandas as pd
import json
import math

def clamp_HdgD(hdg):      
    if hdg > 180:
        return -(360 - hdg)        
    
    if hdg < -180:
        return (360 + hdg )    
    return hdg

def generate_cases(blue_altitude, red_altitude, angle_off, aspect_angle, min_dist=50, max_dist=60, dist_step=0.5):
    
    cases = []
    dist_cases = [x / 10 for x in range(min_dist * 10, max_dist * 10, 5)]    
       
    for distance in dist_cases:
        
        blue_hdg = clamp_HdgD(aspect_angle)
        red_hdg = clamp_HdgD(blue_hdg + angle_off)                 
        
        case = {
            'agents_config': {
                'blue_agents': {
                    'init_position': {'x': 0.0, 'y': blue_altitude, 'z': 30.0},                    
                    'init_hdg': blue_hdg,                    
                },    
                'red_agents': {
                    'init_position': {'x': 0.0, 'y': red_altitude, 'z': 30.0 - distance},                    
                    'init_hdg': red_hdg,                    
                }                
            }
        }
        cases.append(case)

    return cases

config_dict =   { 'EnvConfig' : {
                            'task': 'b_ace_v1',
                            'env_path': 'BVR_AirCombat/bin/B_ACE_v4.exe',
                            'renderize': 1,
                            'experiment_mode'  : 1,
                            'parallel_envs': 1,
                            'max_cycles': 2400,
                            'seed': 1,
                            'port': 12500,
                            'action_repeat': 20,
                            'speedup': 2000,
                            'action_type': 'Low_Level_Continuous',                        
                            'full_observation': 1,
                            'actions_2d': 0
                            },
                        'SimConfig' : {                        
                            'num_allies': 1,
                            'num_enemies': 1,
                            'enemies_behavior': 'wez_eval_target_max',
                            'agents_behavior' : 'wez_eval_shooter',
                            'agents_config' : { 
                                'blue_agents': 
                                    {                        
                                        'init_position': {'x': 0.0, 'y': 25000.0,'z': 30.0},
                                        'offset_pos': {	'x': 0.0, 'y': 0.0, 'z': 0.0},
                                        'init_hdg': 0.0,                        
                                        'target_position': {'x': 0.0,'y': 25000.0,'z': -30.0},                                        
                                        'rnd_offset_range':{'x': 0.0,'y': 0.0,'z': 0.0},
                                        'rnd_shot_dist_var': 0.0 																						
                                    },                            
                                'red_agents':
                                    { 
                                        'init_position': {'x': 0.0,'y': 25000.0,'z': -30.0},
                                        'offset_pos': {'x': 0.0,'y': 0.0,'z': 0.0},
                                        'init_hdg' : 180.0,                        
                                        'target_position': {'x': 0.0,'y': 25000.0,'z': 30.0},                                        
                                        'rnd_offset_range':{'x': 0.0,'y': 0.0,'z': 0.0},
                                        'rnd_shot_dist_var': 0.0					
                                    }   
                            } 
                            
                        }
                }

                    
cases =  generate_cases(20000, 10000, 180, 0)       

experimentConfig = { 'runs_per_case': 5, 'cases' : cases }

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
print(df)
