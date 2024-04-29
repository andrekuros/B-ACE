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
    'null'         :  [0, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'track_enemy'  :  [1, 0, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'fly_direction':  [0, 1, 0, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'fire_missile' :  [0, 0, 1, 0],#, 0, 0, 0, 0, 0, 0, 0],
    'missile_support':[0, 0, 0, 1]#, 0, 0, 0, 0, 0, 0],
#     'search':       [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
#     'fly_direction':[0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
#     'turn':         [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
#     'level':        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
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
                                    current_obs[self.obs_map["track_alt_diff"]],     #1
                                    current_obs[self.obs_map["track_dist"]],         #2   
                                    current_obs[self.obs_map["track_aspect_angle"]], #3
                                    current_obs[self.obs_map["track_angle_off"]],    #4                                
                                    
                                    current_obs[self.obs_map["track_threat_factor"]],       #5
                                    current_obs[self.obs_map["track_offensive_factor"]],    #6
                                    current_obs[self.obs_map["track_is_missile_support"]],  #7
                                    current_obs[self.obs_map["track_detected"]]             #8
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
            
        elif self.type == "fire_missile":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["track_alt_diff"]],              #1                            
                            current_obs[self.obs_map["track_aspect_angle"]],          #2
                            current_obs[self.obs_map["track_angle_off"]],             #3
                            current_obs[self.obs_map["track_dist"]],                  #4
                            
                            current_obs[self.obs_map["track_own_missile_RMax"]],      #5
                            current_obs[self.obs_map["track_own_missile_Nez"]],       #6
                            current_obs[self.obs_map["track_enemy_missile_RMax"]],    #7
                            current_obs[self.obs_map["track_enemy_missile_Nez"]]     #8                                                    #8                      

                        ] #+ self.action_historic[pusuer_idx]#+ stats
            
        elif self.type == "missile_support":  
                        
            task_specific_info =[                            
                            current_obs[self.obs_map["track_alt_diff"]],              #1                            
                            current_obs[self.obs_map["track_aspect_angle"]],          #2
                            current_obs[self.obs_map["track_angle_off"]],             #3
                            current_obs[self.obs_map["track_dist"]],                  #4
                            
                            current_obs[self.obs_map["own_in_flight_missile"]],       #5
                            current_obs[self.obs_map["own_missiles"]],                #6
                            current_obs[self.obs_map["own_in_flight_missile"]],       #7
                            current_obs[self.obs_map["track_is_missile_support"]]     #8                                                    #8                      

                        ] #
            
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
            
        else:
            print(f'Error: Unknown selected task type ({self.type})')
        
                        
        return task_type_one_hot + task_specific_info
    
    def get_one_hot(self):                   
        return TASK_TYPES[self.type]
    

class B_ACE_TaskEnv(GodotRLPettingZooWrapper):
    
    def __init__(self, *args, **kwargs):
                        
        super().__init__(*args, **kwargs)
                
        self.agent_name_mapping = dict(zip(self.agents, list(range(self.num_agents))))                
        
        #Env modification for Task based policy
        self.max_tasks = 6  # Maximum number of tasks
        self.act_space = spaces.Discrete(self.max_tasks)
        self.action_space = spaces.Discrete(self.max_tasks)
        #self.action_spaces = dict(zip(self.agents, self.action_space))

        # Spaces                                                
        self.task_null = Task('null', -1, self.obs_map)

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
        self.infos = {agent : [] for agent in self.agents}
        
        self.task_historic = [0 for _ in self.agents]
        self.action_historic = [[0] * 5 for _ in self.agents]
        
        self.tasks = []

        #self.last_actions = [(self.tc[0], self.tasks_basic[0].forced_action, -1, 1 ,0 ) for _ in self.agents]
        

        # self.last_actions_memory = [ deque([0] * 5, maxlen=5) for _ in self.agents]

        self.tasks_map = {}
        self.allocation_table = []
    
    def reset(self, seed=0, options = None):
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
        self.infos = {agent : [] for agent in self.agents}
        
        self.tasks_enemies    = {agent : [] for agent in self.agents}
        self.tasks_allies     = {agent : [] for agent in self.agents}
        self.tasks_positioning = {agent : [] for agent in self.agents}
        
        self.tasks = self.generate_tasks()
        self.prepare_next_tasks()
                        
        return self.observations, self.infos  

    
    def step(self, task_actions):

        godot_actions = {}
        actions = {}
                
        for agent, action_selected in task_actions.items():
                                                            
            task = self.last_tasks[agent][action_selected]            
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
        
        self.prepare_next_tasks()
                
        
        self.terminations = False
        self.truncations = False        
        self.rewards = 0.0
        
        for i, agent in enumerate(self.possible_agents):
                       
            # Convert observations, rewards, etc., to tensors
            # if dones[i] == True:
            #     continue
            # .to('cuda') moves the tensor to GPU if you're using CUDA; remove it if not using GPU
            
            self.raw_observations[agent] =  obs[agent]['obs']            
            #self.rewards[agent] = reward[i]#torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            #self.terminations.append(dones[i])#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            #self.truncations.append(truncs[i])#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            
            #self.terminations[agent] = dones[i]#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            #self.truncations[agent] = truncs[i]#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            
            self.terminations = self.terminations and dones[agent]
            self.truncations = self.truncations or truncs[agent]            
            self.rewards += reward[agent] #torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
 
            # For 'info', it might not need to be a tensor depending on its use
            #self.info[agent] = info[i]  # Assuming 'info' does not need tensor conversion            
                        
        
                                
        return self.observations, self.rewards, self.terminations, self.truncations, self.infos 


    def prepare_next_tasks(self):
                
                        
        for agent in self.possible_agents:
            
            agent_observation = self.raw_observations[agent]

            last_tasks = self.tasks_enemies[agent] + self.tasks_positioning[agent]            
            self.last_len_tasks[agent] = len(last_tasks)
            
            mask = [True for _ in last_tasks]
            mask.extend([False] * (self.max_tasks - len(last_tasks)))
                    
            #Pad or truncate the task list to ensure a fixed number of tasks
            if len(last_tasks) < self.max_tasks:
                last_tasks.extend([self.task_null for _ in range( self.max_tasks - len(last_tasks) )])            
            else:
                last_tasks = self.last_tasks[agent][:self.max_tasks]

            self.last_tasks[agent] = last_tasks
            
            # Convert tasks to tensor            
            task_features = [task.get_feature_vector(agent_observation) for task in last_tasks] 
            
            
            # task_tensor = torch.tensor(task_features, dtype=torch.float32).to("cuda")
                        
            self.observations[agent] = {"obs" : task_features, "mask" : mask}#, "agent_id" : agent }
            self.infos[agent] = {"info" : {"agent_id" : agent, "mask": mask}}
            
                
    
    
    def generate_tasks(self):
                        
        for agent in self.agents:

            for i in range(self.agents_config["red_agents"]["num_agents"]):                
                                                
                new_task = Task('track_enemy', i, self.obs_map)
                self.tasks_enemies[agent].append(new_task)
                self.tasks_map[new_task.id] = new_task  
                
                new_task = Task('fire_missile', i, self.obs_map)
                self.tasks_enemies[agent].append(new_task)
                self.tasks_map[new_task.id] = new_task    

                new_task = Task('missile_support', i, self.obs_map)            
                self.tasks_enemies[agent].append(new_task)
                self.tasks_map[new_task.id] = new_task        
            
            #Main Target-based Task            
            new_task = Task('fly_direction', 101, self.obs_map)            
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task      
            
    
            
            #Main null Task            
            new_task = Task('null', 100, self.obs_map)            
            self.tasks_positioning[agent].append(new_task)
            self.tasks_map[new_task.id] = new_task                         

   
    def convert_task2action(self, agent, task, agent_observation):
                                
        """
        Determine the action to take based on the task type and agent's data.
        """            
        #task.type = 'missile_support'
        
        if task.type == 'track_enemy':
            
            # Task to             
            hdg2target  =   agent_observation[self.obs_map["track_aspect_angle"]]
            level       =   agent_observation[self.obs_map["own_altitude"]]
            turn_g      =   2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire        =   0 
                        
            action = [hdg2target, level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        
        elif task.type == 'missile_support':
            
            # Task to             
            hdg2target  =   agent_observation[self.obs_map["track_aspect_angle"]] - (50.0/180.0) * np.sign(agent_observation[self.obs_map["track_aspect_angle"]])            
            level       =   agent_observation[self.obs_map["own_altitude"]]
            turn_g      =   2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire        =   0 
                        
            action = [hdg2target, level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
                            
        elif task.type == 'fly_direction':
            
            # Task to 
            hdg2target = agent_observation[self.obs_map["own_aspect_angle_target"]]
            level  = agent_observation[self.obs_map["own_altitude"]]
            turn_g = 2.5 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0 
                        
            action = [hdg2target, level, turn_g, fire]                
            self.last_actions[agent] = action                    
            return action
        
        elif task.type == 'fire_missile':
            
            # Task to 
            hdg2target = agent_observation[self.obs_map["own_aspect_angle_target"]]
            level  = agent_observation[self.obs_map["own_altitude"]]
            turn_g = 1.0 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 1 
                        
            action = [hdg2target, level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        
        elif task.type == 'null':
            
            # Task to 
            hdg2target = agent_observation[self.obs_map["own_current_hdg"]]
            level  = agent_observation[self.obs_map["own_altitude"]]
            turn_g = 1.0 * (-1.0/8.0) #result is 2.5g input for max_g = 9
            fire = 0                     
            
            action = [hdg2target, level, turn_g, fire]            
            self.last_actions[agent] = action
            return action
        else:
            print(f'Error: Unknown task type {task.type} when converting to action')
            exit(-1)
        
        

    def update_tasks(self):
                
        return#active_evaders = [self.tasks_evaders[i] for i in range(len(self.tasks_evaders)) if not self.env.evaders_gone[i]]
        
        #self.tasks = active_evaders + self.tasks_allies #+ self.tasks_basic 

        # self.tasks = active_evaders + self.tasks_basic 
        # self.tasks = self.tasks_basic.copy()

                
def env(**kwargs):
    environment = B_ACE_TaskEnv(**kwargs)
    environment = wrappers.AssertOutOfBoundsWrapper(environment)
    environment = wrappers.OrderEnforcingWrapper(environment)
    return environment

