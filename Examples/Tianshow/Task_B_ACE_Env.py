import numpy as np
import torch
import time
import math
import random
from collections import deque

from gymnasium import spaces
from GodotRLPettingZooWrapper import GodotRLPettingZooWrapper
from godot_rl.core.godot_env import GodotEnv



__all__ = ["ManualPolicy", "env", "parallel_env", "raw_env"]

# The above code defines a dictionary `TASK_TYPES` where each key represents a task type and the
# corresponding value is a list of binary values indicating the task type. Each binary value
# corresponds to a specific task feature. For example, the task type 'track_enemy' is represented by
# the list `[1, 0, 0, 0, 0, 0, 0, 0, 0, 0]` where the first element is 1 indicating tracking enemy is
# the task type and the rest are 0 indicating other task features. This setup allows for easy
# identification and

TASK_TYPES = {
    'null'              :  [0, 0, 0, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'track_enemy'       :  [1, 0, 0, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],    
    'fire_missile'      :  [0, 1, 0, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'missile_support'   :  [1, 1, 0, 0, 0, 0],#, 0, 0, 0, 0, 0, 0],
    'fly_direction'     :  [0, 0, 1, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'straight_ahead'    :  [1, 1, 1, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],'     :  [0, 0, 1, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'turn_left'         :  [1, 0, 1, 0, 0, 0],#, 0, 0, 0, 0, 0],
    'turn_right'        :  [0, 1, 1, 0, 0, 0],#, 0, 0, 0, 0, 0],
    'level_up'          :  [1, 0, 0, 1, 0, 0],#, 0, 0, 0, 0],
    'level_down'        :  [0, 0, 0, 1, 0, 0],#, 0, 0, 0, 0],    
    'follow_ally'       :  [0, 0, 0, 0, 1, 0],#
    'hdg_ally'          :  [1, 0, 0, 0, 1, 0],#    
    'diverge_ally_right':  [0, 1, 0, 0, 1, 0],
    'diverge_ally_left' :  [0, 0, 1, 0, 1, 0],
#     'stop_turn':    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
#     'stop_climb':   [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
     }


class refPoint:
    def __init__(self, position):
        self.current_pos = position

class Task:
    _id_counter = 0  # Class variable for generating unique IDs

    def __init__(self, task_type, target_id, obs_map):
        self.id = Task._id_counter
        # print(self.id, " - ", task_type)
        
        Task._id_counter += 1
        self.type = task_type
        self.target_object = target_id 
        self.obs_map = obs_map                               
        
    def get_feature_vector(self, current_obs):
                        
        task_type_one_hot = self.get_one_hot()  # One-hot encoding of task type
                
        if self.type == "track_enemy":                        
            task_specific_info =[  
                                    current_obs[self.obs_map["track_alt_diff_" + self.target_object]],     #1
                                    current_obs[self.obs_map["track_dist_" + self.target_object]],         #2   
                                    current_obs[self.obs_map["track_aspect_angle_" + self.target_object]], #3
                                    current_obs[self.obs_map["track_angle_off_" + self.target_object]],    #4                                
                                    
                                    current_obs[self.obs_map["track_threat_factor_" + self.target_object]],       #5
                                    current_obs[self.obs_map["track_offensive_factor_" + self.target_object]],    #6
                                    current_obs[self.obs_map["track_is_missile_support_" + self.target_object]],  #7
                                    current_obs[self.obs_map["track_detected_" + self.target_object]]             #8
                                ]
            
        elif self.type == "fly_direction":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            current_obs[self.obs_map["own_dist_target"]],           #2
                            current_obs[self.obs_map["own_aspect_angle_target"]],   #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
            
        elif self.type == "turn_left":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            0.0,           #2
                            -30.0/180.0,   #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
            
        elif self.type == "turn_right":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            0.0,           #2
                            30.0/180.0,    #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
        elif self.type == "level_up":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            0.0,           #2
                            0.0,   #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
            
        elif self.type == "level_down":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            0.0,           #2
                            0.0,    #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
                         
        
        elif self.type == "fire_missile":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["track_alt_diff_" + self.target_object]],              #1                            
                            current_obs[self.obs_map["track_aspect_angle_" + self.target_object]],          #2
                            current_obs[self.obs_map["track_angle_off_" + self.target_object]],             #3
                            current_obs[self.obs_map["track_dist_" + self.target_object]],                  #4
                            
                            current_obs[self.obs_map["track_own_missile_RMax_" + self.target_object]],      #5
                            current_obs[self.obs_map["track_own_missile_Nez_" + self.target_object]],       #6
                            current_obs[self.obs_map["track_enemy_missile_RMax_" + self.target_object]],    #7
                            current_obs[self.obs_map["track_enemy_missile_Nez_" + self.target_object]]     #8                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
            
        elif self.type == "missile_support":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["track_alt_diff_" + self.target_object]],              #1                            
                            current_obs[self.obs_map["track_aspect_angle_" + self.target_object]],          #2
                            current_obs[self.obs_map["track_angle_off_" + self.target_object]],             #3
                            current_obs[self.obs_map["track_dist_" + self.target_object]],                  #4
                            
                            current_obs[self.obs_map["own_in_flight_missile"]],       #5
                            current_obs[self.obs_map["own_missiles"]],                #6
                            current_obs[self.obs_map["own_in_flight_missile"]],       #7
                            current_obs[self.obs_map["track_is_missile_support_" + self.target_object]]     #8                                                    #8                      

                        ] #
            
        elif self.type == "follow_ally":                        
            task_specific_info =[  
                                    current_obs[self.obs_map["allied_track_alt_diff_" + self.target_object]],     #1
                                    current_obs[self.obs_map["allied_track_aspect_angle_" + self.target_object]],         #2   
                                    current_obs[self.obs_map["allied_track_angle_off_" + self.target_object]], #3
                                    current_obs[self.obs_map["allied_track_dist_" + self.target_object]],    #4                                
                                    
                                    current_obs[self.obs_map["allied_track_dist2go_" + self.target_object]],       #5
                                    current_obs[self.obs_map["allied_track_detected_" + self.target_object]],    #6
                                    current_obs[self.obs_map["own_in_flight_missile"]],  #7
                                    current_obs[self.obs_map["own_current_hdg"]]             #8
                                ]
        
        elif self.type == "hdg_ally":                        
            task_specific_info =[  
                                    current_obs[self.obs_map["allied_track_alt_diff_" + self.target_object]],     #1
                                    current_obs[self.obs_map["allied_track_aspect_angle_" + self.target_object]],         #2   
                                    current_obs[self.obs_map["allied_track_angle_off_" + self.target_object]], #3
                                    current_obs[self.obs_map["allied_track_dist_" + self.target_object]],    #4                                
                                    
                                    current_obs[self.obs_map["allied_track_dist2go_" + self.target_object]],       #5
                                    current_obs[self.obs_map["allied_track_detected_" + self.target_object]],    #6
                                    current_obs[self.obs_map["own_in_flight_missile"]],  #7
                                    current_obs[self.obs_map["own_current_hdg"]]             #8
                                ]
        
        elif self.type == "diverge_ally_right" or self.type == "diverge_ally_left":                        
            
            task_specific_info =[  
                                    
                                    current_obs[self.obs_map["allied_track_alt_diff_" + self.target_object]],     #1
                                    current_obs[self.obs_map["allied_track_aspect_angle_" + self.target_object]],         #2   
                                    current_obs[self.obs_map["allied_track_angle_off_" + self.target_object]], #3
                                    current_obs[self.obs_map["allied_track_dist_" + self.target_object]],    #4                                
                                    
                                    current_obs[self.obs_map["allied_track_dist2go_" + self.target_object]],       #5
                                    current_obs[self.obs_map["allied_track_detected_" + self.target_object]],    #6
                                    current_obs[self.obs_map["own_in_flight_missile"]],  #7
                                    current_obs[self.obs_map["own_current_hdg"]]             #8
                                ]
            
            
        elif self.type == "null":
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            current_obs[self.obs_map["own_dist_target"]],           #2
                            current_obs[self.obs_map["own_aspect_angle_target"]],   #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
        
        elif self.type == "straight":
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["own_altitude"]],              #1                            
                            current_obs[self.obs_map["own_dist_target"]],           #2
                            current_obs[self.obs_map["own_aspect_angle_target"]],   #3
                            current_obs[self.obs_map["own_current_hdg"]],           #4
                            
                            current_obs[self.obs_map["own_current_speed"]],         #5
                            current_obs[self.obs_map["own_missiles"]],              #6
                            current_obs[self.obs_map["own_in_flight_missile"]],     #7
                            0.0                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
            
        else:
            print(f'Error: Unknown selected task type ({self.type})')
        
                        
        return task_type_one_hot + task_specific_info
    
    def check_track_valid(self, current_obs, ref):
        
        if ref == "enemy":
            return current_obs[self.obs_map["track_dist_" + self.target_object]] >= 0.0
        elif ref == "ally":
            return current_obs[self.obs_map["allied_track_dist_" + self.target_object]] >= 0.0
        else:
            return False
    
        
    def get_one_hot(self):                   
        return TASK_TYPES[self.type]
    

class B_ACE_TaskEnv(GodotRLPettingZooWrapper):
    
    def __init__(self, *args, **kwargs):
                        
        super().__init__(*args, **kwargs)
                
        self.agent_name_mapping = dict(zip(self.agents, list(range(self.num_agents))))                
        
        #Env modification for Task based policy
        self.max_tasks = 30  # Maximum number of tasks
        self.act_space = spaces.Discrete(self.max_tasks)
        self.action_space = spaces.Discrete(self.max_tasks)
        #self.action_spaces = dict(zip(self.agents, self.action_space))

        # Spaces                                                
        self.task_null = Task('null', -1, self.obs_map[self.agents[0]])

        self.tasks_enemies    = {agent : [] for agent in self.agents}
        self.tasks_allies     = {agent : [] for agent in self.agents}
        self.tasks_positioning = {agent : [] for agent in self.agents}
        
        # The above code is creating a dictionary called `last_tasks` with keys as each agent in the
        # list `self.agents` and initializing the value for each key as an empty list.
        self.last_tasks     = {agent : [] for agent in self.agents}
        self.last_len_tasks = {agent : [] for agent in self.agents}
        self.last_actions   = {agent : [] for agent in self.agents}
        
        self.observations = {agent : [] for agent in self.agents}
        self.raw_observations = {agent : [] for agent in self.agents}
        self.rewards = {agent : [] for agent in self.agents}        
        self.infos = {agent : [] for agent in self.agents}
        
        self.task_historic = [0 for _ in self.agents]
        self.action_historic = [[0] * 5 for _ in self.agents]
        
        self.tasks = []
        
        self.desired_hdg   = 0.0 # 0 deg
        self.desired_level = 0.0 # 25000ft

        #self.last_actions = [(self.tc[0], self.tasks_basic[0].forced_action, -1, 1 ,0 ) for _ in self.agents]
        

        # self.last_actions_memory = [ deque([0] * 5, maxlen=5) for _ in self.agents]

        self.tasks_map = {}
        self.allocation_table = []
        
        # Track task selection statistics
        self.task_selection_count = {task_type: 0 for task_type in TASK_TYPES}
        self.task_usage_log = []  # To log (task, step)

        # Configuration for outputs
        self.enable_summary_output = "log_tasks_summary" in self.additional_config
        self.enable_log_output = "log_all_tasks" in self.additional_config
        
        if self.enable_summary_output or self.enable_log_output:
            # Create a directory with a timestamp
            self.output_dir = f'./Logs/Tasks/{self.num_agents}_shares_{self.share_states}_{self.share_tracks}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.makedirs(self.output_dir, exist_ok=True)
                
    def reset(self, seed=0, options = None):
        
        if self.enable_summary_output and self.task_usage_log != []:
            self.write_summary_file()
        
        if not all(value == 0 for value in self.task_selection_count.values()):        
            if self.enable_log_output and self.task_selection_count:
                self.write_log_file()
            
        # Call the base environment's reset
        self.raw_observations, self.info  = super().reset(self, options=options)

        # tasks
        self.tasks_evaders = []
        self.tasks_allies = []
        self.tasks_map = {}
        self.allocation_table = []

        self.last_tasks = {agent : [self.task_null] for agent in self.agents}
        self.last_len_tasks = {agent : 1 for agent in self.agents}  
        self.last_actions   = {agent : [] for agent in self.agents}      
        
        self.task_historic = [0 for _ in self.agents]
        self.action_historic = [[0] * 5 for _ in self.agents]
        
        self.observations = {agent : [] for agent in self.agents}   
        self.rewards = {agent : [] for agent in self.agents}             
        self.infos = {agent : [] for agent in self.agents}
        
        self.tasks_enemies    = {agent : [] for agent in self.agents}
        self.tasks_allies     = {agent : [] for agent in self.agents}
        self.tasks_positioning = {agent : [] for agent in self.agents}
        
        self.tasks = self.generate_tasks()
        self.prepare_next_tasks()
        
        self.desired_hdg   = 0.0 # 0 deg
        self.desired_level = 0.0 # 25000ft
                        
        return self.observations, self.infos  

    
    def step(self, task_actions):

        godot_actions = {}
        actions = {}
                
        for agent, action_selected in task_actions.items():
                                                                        
            task = self.last_tasks[agent][action_selected]            
            #if agent == "agent_0":
            #    task = self.tasks_allies[agent][3]
            
            #last_task_data = self.last_actions[agent]                             
            actions[agent] = self.convert_task2action( agent, task, self.raw_observations[agent]) 
                                    
            
        # Assuming the environment's step function can handle a dictionary of actions for each agent                                      
        if self.action_type == "Low_Level_Continuous":            
            godot_actions = [np.array([action]) for agent, action in actions.items()]        
            #godot_actions = [np.array(action) for agent, action in actions.items()]        
        elif self.action_type == "Low_Level_Discrete": 
            godot_actions = [ self.decode_action(action) for agent, action in actions.items()]
        else:
            print("GododtPZWrapper::Error:: Unknow Actions Type -> ", self.actions_type)     
            
        
        obs, reward, dones, truncs, info = GodotEnv.step(self, godot_actions, order_ij=True)
        
        #print(["obs_task_bace: ", obs, reward, len(obs)])
        
        self.prepare_next_tasks()
                
        
        
        self.terminations = False
        self.truncations = False        
        self.rewards = 0.0
        
        for i, agent in enumerate(self.possible_agents):

            # Convert observations, rewards, etc., to tensors
            #if dones[agent] == True:
            #    continue
            # .to('cuda') moves the tensor to GPU if you're using CUDA; remove it if not using GPU
            
            self.raw_observations[agent] =  obs[agent]['obs']            
            #self.rewards[agent] = reward[i]#torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            #self.terminations.append(dones[i])#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            #self.truncations.append(truncs[i])#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            
            #self.terminations[agent] = dones[agent]#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            #self.truncations[agent] = truncs[agent]#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            
            #Stop 1 died
            #self.terminations = self.terminations or dones[agent]
            #self.truncations = self.truncations and truncs[agent]  
            
            self.terminations = self.terminations or dones[agent]
            self.truncations = self.truncations and truncs[agent]           
            
            
            self.rewards += reward[agent] #torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            #self.rewards[agent] = reward[agent]
            
            # For 'info', it might not need to be a tensor depending on its use
            #self.info[agent] = info[i]  # Assuming 'info' does not need tensor conversion            
                        
        self.rewards = self.rewards 
        
        return self.observations, self.rewards, self.terminations, self.truncations, self.infos 


    def prepare_next_tasks(self):
                
                        
        for agent in self.possible_agents:
            
            agent_observation = self.raw_observations[agent]
            
            last_tasks = []
            last_tasks.extend( [task for task in self.tasks_enemies[agent] if task.check_track_valid(agent_observation, "enemy")])
            last_tasks.extend( [task for task in self.tasks_allies[agent]  if task.check_track_valid(agent_observation, "ally")])
            last_tasks.extend( [task for task in self.tasks_positioning[agent]])
            
            #print(len(last_tasks))
            
            self.last_len_tasks[agent] = len(last_tasks)
            
            mask = [True for _ in last_tasks]
            mask.extend([False] * (self.max_tasks - len(last_tasks)))
                    
            #Pad or truncate the task list to ensure a fixed number of tasks
            if len(last_tasks) < self.max_tasks:
                last_tasks.extend([self.task_null for _ in range( self.max_tasks - len(last_tasks) )])            
            else:
                last_tasks = self.last_tasks[agent][:self.max_tasks]
                print (f'Tasks Over Limit: {len(last_tasks)} /{self.max_tasks}' )

            self.last_tasks[agent] = last_tasks
            
            # Convert tasks to tensor            
            task_features = [task.get_feature_vector(agent_observation) for task in last_tasks] 
            
            
            # task_tensor = torch.tensor(task_features, dtype=torch.float32).to("cuda")
                        
            self.observations[agent] = {"obs" : task_features, "mask" : mask}#, "agent_id" : agent }
            self.infos[agent] = {"agent_id" : agent, "mask": mask}
                            
    
    
    def generate_tasks(self):
                        
        
        agents_id = [i + 101 for i in range(self.agents_config["blue_agents"]["num_agents"])]
        for agent_idx,agent in enumerate(self.agents):
            
            agent_id = agents_id[agent_idx]
                        
            for i in range(self.agents_config["red_agents"]["num_agents"]):                
                                                
                new_task = Task('track_enemy', str(i + 200 + 1), self.obs_map[agent])
                self.tasks_enemies[agent].append(new_task)
                self.tasks_map[new_task.id] = new_task  
                
                new_task = Task('fire_missile', str(i + 200 + 1), self.obs_map[agent])
                self.tasks_enemies[agent].append(new_task)
                self.tasks_map[new_task.id] = new_task    

                new_task = Task('missile_support', str(i + 200 + 1), self.obs_map[agent])            
                self.tasks_enemies[agent].append(new_task)
                self.tasks_map[new_task.id] = new_task 
                
            if self.share_states == 1:
                for id in [idx for idx in agents_id if idx != agent_id]:                
                                                                    
                    new_task = Task('follow_ally', str(id), self.obs_map[agent])
                    self.tasks_allies[agent].append(new_task)
                    self.tasks_map[new_task.id] = new_task  
                    
                    new_task = Task('hdg_ally', str(id), self.obs_map[agent])
                    self.tasks_allies[agent].append(new_task)
                    self.tasks_allies[new_task.id] = new_task    

                    new_task = Task('diverge_ally_right', str(id), self.obs_map[agent])            
                    self.tasks_allies[agent].append(new_task)
                    self.tasks_map[new_task.id] = new_task    
                    
                    new_task = Task('diverge_ally_left', str(id), self.obs_map[agent])            
                    self.tasks_allies[agent].append(new_task)
                    self.tasks_map[new_task.id] = new_task                      
                        
            #Main Target-based Task            
            new_task = Task('fly_direction', "101", self.obs_map[agent])            
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task  
                        
            
            new_task = Task('turn_left', "102", self.obs_map[agent])
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task    
            
            new_task = Task('turn_right', "103", self.obs_map[agent])
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task      
            
            new_task = Task('level_up', "104", self.obs_map[agent])
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task      
            
            new_task = Task('level_down', "105", self.obs_map[agent])
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task        
            
            Task('straight', "106", self.obs_map[agent])            
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task  
            
            #Main null Task            
            new_task = Task('null', "100", self.obs_map[agent])            
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task                         

   
    def convert_task2action(self, agent, task, agent_observation):
                                
        """
        Determine the action to take based on the task type and agent's data.
        """            
        #task.type = 'trail_ally'
        
        if task.type == 'fly_direction':
            
            # Task to 
            hdg2target = agent_observation[task.obs_map["own_aspect_angle_target"]]
            level  = agent_observation[task.obs_map["own_altitude"]]
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
                        
            action = [hdg2target, level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action
        
        elif task.type == 'track_enemy':
            
            # Task to             
            hdg2target  =   agent_observation[task.obs_map["track_aspect_angle_" + task.target_object]]
            level       =   agent_observation[task.obs_map["own_altitude"]]
            turn_g      =   2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire        =   0 
                        
            action = [hdg2target, self.desired_level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        
        elif task.type == 'missile_support':
            
            # Task to             
            hdg2target  =   agent_observation[task.obs_map["track_aspect_angle_" + task.target_object]] - (50.0/180.0) * np.sign(agent_observation[task.obs_map["track_aspect_angle_" + task.target_object]])            
            level       =   agent_observation[task.obs_map["own_altitude"]]
            turn_g      =   2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire        =   0 
                        
            action = [hdg2target, self.desired_level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        
                            
        elif task.type == 'follow_ally':
                        
            hdg2target  =   agent_observation[task.obs_map["allied_track_aspect_angle_" + task.target_object]]
            self.desired_hdg = hdg2target
            
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
            
            action = [hdg2target, self.desired_level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action

        elif task.type == 'hdg_ally':
            
            # Position the aircraft 6 miles on the closed side of the ally            
            ally_hdg = agent_observation[task.obs_map["allied_track_aspect_angle_" + task.target_object]] + agent_observation[task.obs_map["own_current_hdg"]]
            
            hdg2target  =   ally_hdg
            self.desired_hdg = hdg2target
            
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
            
            action = [hdg2target, self.desired_level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action

        elif task.type == 'diverge_ally_right':
           # Position the aircraft 6 miles on the closed side of the ally            
            hdg2target = 0.5 - agent_observation[task.obs_map["allied_track_angle_off_" + task.target_object]] 
            
            if hdg2target > 1.0:
                hdg2target = 1.0 - hdg2target 
            elif hdg2target < -1.0:
                hdg2target = 2.0 + hdg2target 
            
            self.desired_hdg = hdg2target
                        
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
            
            action = [hdg2target, self.desired_level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action
        
        elif task.type == 'diverge_ally_left':
            # Position the aircraft 6 miles on the closed side of the ally            
            hdg2target = -0.5 - agent_observation[task.obs_map["allied_track_angle_off_" + task.target_object]] 
            
            if hdg2target > 1.0:
                hdg2target = 1.0 - hdg2target 
            elif hdg2target < -1.0:
                hdg2target = 2.0 + hdg2target 
            
            self.desired_hdg = hdg2target
                                    
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
            
            action = [hdg2target, self.desired_level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action

        elif task.type == 'turn_left':
            
            # Task to 
            hdg2target = task.obs_map["own_current_hdg"] - 30.0/ 180.0
            self.desired_hdg = hdg2target
                        
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
                        
            action = [hdg2target, self.desired_level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action
        
        elif task.type == 'turn_right':
            
            # Task to 
            hdg2target = task.obs_map["own_current_hdg"] + 30.0/ 180.0
            self.desired_hdg = hdg2target
            
            level  = agent_observation[task.obs_map["own_altitude"]]
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9

                        
            action = [hdg2target, self.desired_level, turn_g, 0]                
            self.last_actions[agent] = action                    
            return action

        elif task.type == 'level_up':

            level  = agent_observation[task.obs_map["own_altitude"]] + 5000.0 / 25000.0
            self.desired_level = level
            
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
                        
            action = [self.desired_hdg, level, turn_g, 0]                
            self.last_actions[agent] = action                    
            return action

        elif task.type == 'level_down':
                                    
            level  = agent_observation[task.obs_map["own_altitude"]] - 5000.0 / 25000.0
            self.desired_level = level
            
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
                        
            action = [self.desired_hdg, level, turn_g, 0]                
            self.last_actions[agent] = action                    
            return action
        
        elif task.type == 'straight':
                        
            hdg2target = agent_observation[task.obs_map["own_current_hdg"]]
            self.desired_hdg = hdg2target            
            level  = agent_observation[task.obs_map["own_altitude"]]
            self.desired_level = level
            
            turn_g = 1.0 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0                     
            
            action = [hdg2target, level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        
        elif task.type == 'fire_missile':
            
            # Task to             
            turn_g = 1.0 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 1 
                        
            action = [self.desired_hdg, self.desired_level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        
        elif task.type == 'null':
            
            # Task to 
            hdg2target = agent_observation[task.obs_map["own_current_hdg"]]
            level  = agent_observation[task.obs_map["own_altitude"]]
            turn_g = 1.0 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0                     
            
            action = [hdg2target, level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        else:
            print(f'Error: Unknown task type {task.type} when converting to action')
            exit(-1)
    
    def write_summary_file(self):
        if not self.enable_summary_output:
            return
        save_path = self.output_dir + "task_summary_{self.resets}.csv"
        
        with open(filename=save_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Task Type", "Selection Count"])
            for task_type, count in self.task_selection_count.items():
                writer.writerow([task_type, count])

    def write_log_file(self, filename="task_log.csv"):
        if not self.enable_log_output:
            return
        
        save_path = self.output_dir + "all_tasks_{self.resets}.csv"
        with open(save_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow("Task Type")
            for task_type, step in self.task_usage_log:
                writer.writerow(task_type)    
        
    def call_results(self):
        resp = self.call("last")       
        return resp
                
def env(**kwargs):
    environment = B_ACE_TaskEnv(**kwargs)
    environment = wrappers.AssertOutOfBoundsWrapper(environment)
    environment = wrappers.OrderEnforcingWrapper(environment)
    return environment

