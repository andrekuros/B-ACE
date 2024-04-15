from ssl import get_default_verify_paths
from pettingzoo.sisl import pursuit_v4
from pettingzoo.utils import wrappers
import numpy as np
import torch
import time
import math
import random
from collections import deque


from gymnasium import spaces

import pandas as pd
from IPython.display import display, clear_output
from IPython.display import HTML

import pygame
from gymnasium.utils import EzPickle

from GodotRLPettingZooWrapper import GodotRLPettingZooWrapper



__all__ = ["ManualPolicy", "env", "parallel_env", "raw_env"]

# The above code defines a dictionary `TASK_TYPES` where each key represents a task type and the
# corresponding value is a list of binary values indicating the task type. Each binary value
# corresponds to a specific task feature. For example, the task type 'track_enemy' is represented by
# the list `[1, 0, 0, 0, 0, 0, 0, 0, 0, 0]` where the first element is 1 indicating tracking enemy is
# the task type and the rest are 0 indicating other task features. This setup allows for easy
# identification and

TASK_TYPES = {
    'track_enemy':  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'gimbal_enemy': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    'fire_missile': [0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'break':        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    'search':       [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    'fly_wpt':      [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    'turn':         [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    'level':        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    'stop_turn':    [0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    'stop_climb':   [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
}

class refPoint:
    def __init__(self, position):
        self.current_pos = position

class Task:
    _id_counter = 0  # Class variable for generating unique IDs

    def __init__(self, task_type, target_object, forced_action = 4, num_agents=0):
        self.id = Task._id_counter
        # print(self.id, " - ", task_type)
        Task._id_counter += 1
        self.type = task_type
        self.target_object = target_object                                
        

    def calculate_default_action(self):
        # Return a default action (e.g., stay)
        return 4  # Stay    


    def find_closest_point(self, my_position, points_array):
        
        # Calculate the differences between each point and your position
        differences = points_array - my_position
        
        # Calculate the Euclidean distance for each point
        distances = np.sqrt(np.sum(differences**2, axis=1))
        
        # Find the index of the minimum distance
        closest_point_index = np.argmin(distances)
        
        # Return the closest point
        return points_array[closest_point_index]
    
    def determine_desired_action(self, agent_position, slot, wall_channel):
        """
        Determine the action to take based on the task type and agent's position.
        """
        if self.type == 'chase_evader':
            # Task to chase an evader: Move towards the evader's position            
            action = self.calculate_direction_to_target(agent_position, self.target_object.current_pos + self.slot_offset[slot])
            
            if action != 4 and wall_channel[3 + self.slot_offset[action][1], 3 + self.slot_offset[action][0]] == 1 :
                slot = self.get_newSlot(agent_position, slot, exclusion = slot)
                action = self.calculate_direction_to_target(agent_position, self.target_object.current_pos + self.slot_offset[slot])

            return action
        
        elif self.type == 'coordinate':
            # Task to coordinate with another agent: Move towards the other agent's position
            return self.calculate_direction_to_target(agent_position, self.target_object.current_pos + self.slot_offset[slot])
        
        elif self.type == 'explore':
            
            exp_pos = None
            # Task to explore: This could be a predefined direction or a random action
            if agent_position[0] <= 3: 
                
                if agent_position[1] < 13:
                    exp_pos = np.array([3,13])
                else:
                    exp_pos = np.array([13,13])
            
            if agent_position[0] >= 13: 
                
                if agent_position[1] > 3:
                    exp_pos = np.array([13,3])
                else:
                    exp_pos = np.array([3,3])

            if exp_pos is None:
                if agent_position[0] > 3 and agent_position[1] <= 3: 
                    exp_pos = np.array([3,3])
                
                if agent_position[0] > 3 and agent_position[1] >= 13: 
                    exp_pos = np.array([13,13])


            if exp_pos is None:
                exp_pos = self.find_closest_point(agent_position, self.refExp)
            
            direction =  self.calculate_direction_to_target(agent_position, exp_pos)
            return direction
            # return self.calculate_direction_to_target(np.array([0,0]), self.target_object.current_pos[::-1] )
        
        else:
            # Default action (e.g., 'stay')
            return self.calculate_default_action()
    
    
    def calculate_direction_to_target(self, agent_position, target_position):
        """
        Calculate the direction from the agent's position to the target's position.
        """
        dx = target_position[0] - agent_position[0]
        dy = target_position[1] - agent_position[1]

        if dx == 0 and dy == 0:
            return 4 #self.random_direction()


        if abs(dx) > abs(dy):
            # Move in x direction
            return 0 if dx < 0 else 1  # Left (0) if dx is negative, Right (1) otherwise
        elif abs(dx) < abs(dy):
            # Move in y direction
            return 3 if dy < 0 else 2  # Up (2) if dy is negative, Down (3) otherwise
        else:
            #case the distances are the same random choice hor or vert move
            options = [0 if dx < 0 else 1 , 3 if dy < 0 else 2]
            return np.random.choice(options)

        
    def getDistSinCos(self, point_a, point_b):
        # Unpack the points
        x1, y1 = point_a
        x2, y2 = point_b
        
        # Calculate the differences
        dx = x2 - x1
        dy = y2 - y1

        # Euclidean distance
        distance = math.sqrt(dx**2 + dy**2)

        # Calculate the angle in radians
        angle = math.atan2(dy, dx)

        # Sine and Cosine of the angle
        sin_angle = math.sin(angle)
        cos_angle = math.cos(angle)

        return distance, sin_angle, cos_angle
    
    def get_dist(self, posA, posB):
        return math.sqrt((posB[0] - posA[0])**2 + (posB[1] - posA[1])**2)

    
    def distance_bearing(self, pos1, pos2):
        """Calculate Euclidean distance between two points."""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
    
    def random_direction(self):
        """
        Return a random direction.
        """
        # Assuming actions 0, 1, 2, 3 correspond to Up, Down, Left, Right
        return np.random.choice([0, 1, 2, 3])

class B_ACE_TaskEnv(GodotRLPettingZooWrapper):
    
    def __init__(self, *args, **kwargs):
                
        super.__init__(self, *args, **kwargs)
                
        self.agent_name_mapping = dict(zip(self.agents, list(range(self.num_agents))))                
        
        #Env modification for Task based policy
        self.max_tasks = 30  # Maximum number of tasks
        self.act_space = spaces.Discrete(self.max_tasks)
        self.action_space = [self.env.act_space for _ in range(self.env.n_pursuers)]
        self.action_spaces = dict(zip(self.agents, self.env.action_space))

        # Spaces                        
        self.refGeneric = refPoint([0,0])        
        self.exploreRefs = [refPoint(pos) for pos in  np.array([[-2,0], [2,0], [0,2], [0,-2]])]
                
        self.tasks_explore = [ Task("explore", self.refGeneric, forced_action = 4)] 
        
        self.tasks_basic = [Task('stay', self.refGeneric, forced_action = 4)] 

        self.tasks_enemies    = []
        self.tasks_allies     = []
        self.task_positioning = []
        
        self.last_tasks = {agent : [] for agent in self.agents}
        self.last_len_tasks = {agent : [] for agent in self.agents}

        self.task_historic = [0 for _ in self.agents]
        self.action_historic = [[0] * 5 for _ in self.agents]
        
        self.tasks = []

        self.last_actions = [(self.tasks_basic[0], self.tasks_basic[0].forced_action, -1, 1 ,0 ) for _ in self.agents]
        self.raw_observations = [None for _ in self.agents]

        # self.last_actions_memory = [ deque([0] * 5, maxlen=5) for _ in self.agents]

        self.tasks_map = {}
        self.allocation_table = []
    
    def reset(self, seed=0, options = None):
        # Call the base environment's reset
        super().reset(self, seed=seed, options=options)

        # tasks
        self.tasks_evaders = []
        self.tasks_allies = []
        self.tasks_map = {}
        self.allocation_table = []

        self.tasks = self.generate_tasks()
        self.update_tasks()
        
        self.last_tasks = {agent : [] for agent in self.agents}
        self.last_len_tasks = {agent : [] for agent in self.agents}

        self.task_historic = [0 for _ in self.agents]
        self.action_historic = [[0] * 5 for _ in self.agents]
        
        self.tasks = []

        self.last_actions = [(self.tasks_basic[0], self.tasks_basic[0].forced_action, -1, 1 ,0 ) for _ in self.agents]
        self.raw_observations = [None for _ in self.agents]
        
    def is_valid_explore_task(self,task, layer):
            
            # Calculate the target position for the explore task
            target_position = [3 + task.target_object.current_pos[0], 3 + task.target_object.current_pos[1]] 
            
            #print(layer[target_position[1], target_position[0]])

            # Check if the target position is a wall
            return layer[target_position[0], target_position[1]] == 0
    
    
    def observe(self, agent):
        
        current_obs = super().observe(agent)

    
        # print("Observation: ",current_obs)
        
        if np.sum(self.env.evaders_gone) != self.removed_evader:
            
            self.removed_evader = np.sum(self.env.evaders_gone)
            self.update_tasks() 
            # print("task_updated")


        pusuer_idx = agent.split("_")[-1]
        pusuer_idx = int(pusuer_idx)
        pursuer_obj = self.env.pursuers[pusuer_idx]

        self.raw_observations[pusuer_idx]  = current_obs

        #agent_positions = self.get_agent_positions()
        agent_position = self.env.pursuer_layer.get_position(pusuer_idx)

        # Calculate the bounds of the observation box
        range_ref = (self.env.obs_range-1)/2
        x_lower_bound = agent_position[0] - range_ref
        x_upper_bound = agent_position[0] + range_ref
        y_lower_bound = agent_position[1] - range_ref
        y_upper_bound = agent_position[1] + range_ref
        
        wall_channel = current_obs[..., 0]  # Assuming the first channel represents walls        
        allies_channel = current_obs[...,1]  # Assuming the first channel represents walls        
        enemies_channel = current_obs[...,2]  # Assuming the first channel represents walls        
               
        last_tasks = []               
        
        if self.last_actions[pusuer_idx][0].type == "explore" and sum(sum(enemies_channel)) == 0:
            
            current_task = self.last_actions[pusuer_idx][0]
            
            if self.task_historic[pusuer_idx] <= 1:
                if self.is_valid_explore_task(current_task, wall_channel):                    
                    last_tasks = [current_task]
                
                
        # Filter tasks within the observation box
        if last_tasks == []:
            tasks_in_range = [task for task in self.tasks if x_lower_bound <= task.target_object.current_pos[0] <= x_upper_bound and y_lower_bound <= task.target_object.current_pos[1] <= y_upper_bound and task.target_object != pursuer_obj]
            
            # Filter out explore tasks that lead to a wall
            tasks_to_explore = [task for task in self.tasks_explore if self.is_valid_explore_task(task, wall_channel)] 

            random.shuffle(tasks_to_explore)


            last_tasks = tasks_in_range + tasks_to_explore
        
        self.last_len_tasks[agent] = len(last_tasks)
        
        mask = [True for _ in last_tasks]
        mask.extend([False] * (self.max_tasks - len(last_tasks)))
                
        #Pad or truncate the task list to ensure a fixed number of tasks
        if len(last_tasks) < self.max_tasks:
            last_tasks.extend([self.tasks_basic[0] for _ in range( self.max_tasks - len(last_tasks) )])
            # last_tasks.extend([np.random.choice(self.tasks_explore) for _ in range( self.max_tasks - len(last_tasks) )])
        else:
            last_tasks = self.last_tasks[agent][:self.max_tasks]

        self.last_tasks[agent] = last_tasks
        # Convert tasks to tensor                             
        task_features = [self.get_feature_vector(pusuer_idx, current_obs,  agent_position, task) for task in last_tasks]
        
        # task_tensor = torch.tensor(task_features, dtype=torch.float32).to("cuda")
        
        self.infos[agent]["mask"] = mask
        observation = {"observation" : task_features, "action_mask" : mask, "info" : mask}
        
        
        return observation 
        
    def get_one_hot(self, task):
        return TASK_TYPES[task.type]
    
    def get_feature_vector(self, pusuer_idx, current_obs, agent_position, task):
        
        if task.type == "explore":
            channel = 0
        elif task.type == "coordinate":
            channel = 1        
        else:
            channel = 2

        # stats = self.calculate_statistics( current_obs, channel )
        
        #historic = 0 if self.last_actions[pusuer_idx][0] != task else self.task_historic[pusuer_idx] 

        task_type_one_hot = self.get_one_hot(task)  # One-hot encoding of task type
        
        if task.type != 'explore':
            task_pos = task.target_object.current_pos
        else:
            task_pos = np.array([ agent_position[0] + task.target_object.current_pos[1], agent_position[1] + task.target_object.current_pos[0]])
        
        feature_vector = task_type_one_hot +  list(task.getDistSinCos(agent_position, task_pos)) +\
                        [                             
                           agent_position[0]/15, 
                           agent_position[1]/15,
                           sum(task.slots)/4,
                           #historic / 5,
                           #aliies_in_sight,
                        ] #+ self.action_historic[pusuer_idx]#+ stats
        
        
        return feature_vector
    
    def step(self, actions):
        
        # Assuming the environment's step function can handle a dictionary of actions for each agent                                      
        if self.action_type == "Low_Level_Continuous":            
            godot_actions = [np.array([action]) for agent, action in actions.items()]        
            #godot_actions = [np.array(action) for agent, action in actions.items()]        
        elif self.action_type == "Low_Level_Discrete": 
            godot_actions = [ self.decode_action(action) for agent, action in actions.items()]
        else:
            print("GododtPZWrapper::Error:: Unknow Actions Type -> ", self.actions_type)
                                        
        obs, reward, dones, truncs, info = super().step(godot_actions, order_ij=True)
        
        
        # Assuming 'obs' is a list of dictionaries with 'obs' keys among others
        for agent, action in actions.items():
                                    
            
            action = self.convert_task2action(self.last_tasks[agent], action , agent_position, self.last_actions[pusuer_idx][2], wall_channel) 
            
            last_task_data = self.last_actions[pusuer_idx]                                          
        
            if task != self.last_actions[pusuer_idx][0]:                                                                                    
                                        
                last_task_data[0].slots[last_task_data[2]] -= 1

                slot = task.get_newSlot(agent_position, last_task_data[2])
                self.last_actions[pusuer_idx] = [task, action, slot, self.last_len_tasks[agent], 1]
                self.task_historic[pusuer_idx] = 1
            
            else:
                                                    
                #self.last_actions[pusuer_idx][2] = slot            
                self.task_historic[pusuer_idx] += 1
                self.last_actions[pusuer_idx][4] += 1
                
        
            # Convert observations, rewards, etc., to tensors
            # if dones[i] == True:
            #     continue
            # .to('cuda') moves the tensor to GPU if you're using CUDA; remove it if not using GPU
            self.observations[agent] =  obs[i]['obs']            
            self.rewards[agent] = reward[i]#torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            #self.terminations.append(dones[i])#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            #self.truncations.append(truncs[i])#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            
            self.terminations[agent] = dones[i]#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            self.truncations[agent] = truncs[i]#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            
            #self.terminations = self.terminations and dones[i]
            #self.truncations = self.truncations or truncs[i]
            #self.rewards += reward[i] #torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            
            
            
            
            
            # For 'info', it might not need to be a tensor depending on its use
            self.info[agent] = info[i]  # Assuming 'info' does not need tensor conversion            
                        
        #  # Update the list of active agents based on the 'dones' information
        #  for agent, done in dones.items():
        #      if done:
        # 
        
                                
        
        

        return self.observations, self.rewards, self.terminations, self.truncations, self.info 


    
    def generate_tasks(self):
                        
        for agent in self.agents:

            for i in range(self.envConfig["AgentsConfig"]["redAgents"]["numAgents"]):                
                
                self.enemies.append(i)
                
                new_task = Task('track_enemy', self.enemies[i])
                self.tasks_enemy.append(new_task)
                self.tasks_map[new_task.id] = new_task           
                                    

    def distance(self, pos1, pos2):
        """Calculate Euclidean distance between two points."""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
   
    def convert_task2action(self, last_tasks, task_num, agent_position, slot, wall_channel):
        # Get the selected task
        
        selected_task = last_tasks[task_num] if task_num < len(last_tasks) else None

        if selected_task is None:
            # Default action if no task is selected or if the task number is out of range
            return 4  # Assuming 4 is the default 'stay' action        

        # Determine the desired action based on the task type
        return selected_task.determine_desired_action(agent_position, slot, wall_channel)

    def update_tasks(self):
                
        active_evaders = [self.tasks_evaders[i] for i in range(len(self.tasks_evaders)) if not self.env.evaders_gone[i]]
        
        self.tasks = active_evaders + self.tasks_allies #+ self.tasks_basic 

        # self.tasks = active_evaders + self.tasks_basic 
        # self.tasks = self.tasks_basic.copy()

                
def env(**kwargs):
    environment = B_ACE_TaskEnv(**kwargs)
    environment = wrappers.AssertOutOfBoundsWrapper(environment)
    environment = wrappers.OrderEnforcingWrapper(environment)
    return environment

