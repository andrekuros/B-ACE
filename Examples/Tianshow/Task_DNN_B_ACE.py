import torch
import torch.nn as nn
import numpy as np

class Task_DNN_B_ACE(nn.Module):
    def __init__(
        self,
        num_tasks: int = 10,
        num_features_per_task: int = 8,
        device: str = "cpu",
        nhead: int = 4,
    ):
        super().__init__()

        self.device = device
        self.num_tasks = num_tasks  # Number of max tasks (e.g., 20)
        self.embedding_size = 128  # Customizable

        # Task encoder: Fully connected layers
        # Each task has num_features_per_task feature      

        self.task_encoder = nn.Sequential(
            nn.Linear(num_features_per_task * num_tasks, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, 1024),
        ).to(device)



        # ).to(device)

        self.output = nn.Sequential(
            nn.Linear(1024, 1024),
            nn.ReLU(),           
            nn.Linear(1024, num_tasks)  # Ensure this matches the action space

        ).to(device)
      

    def forward(self, obs, state=None, info=None):
        # obs shape is expected to be [batch_size, num_tasks, num_features_per_task]
                
        

        if isinstance(obs, np.ndarray):
            observation = torch.tensor(np.array(obs), dtype=torch.float32).to(self.device)            
            mask = info.mask
        else:            
            observation = torch.tensor(np.array(obs[info].obs), dtype=torch.float32).to(self.device)
            mask =  obs[info].mask
                    
            
        
        
        mask = ~mask #for pythorch
        mask = torch.tensor(mask, dtype=torch.bool).to(self.device)
        # Process each task independently through the task encoder
        batch_size, num_tasks, num_features = observation.shape
                
        
        obs_reshaped = observation.view(-1, num_features * num_tasks)  # [batch_size * num_tasks, num_features]
        task_embeddings = self.task_encoder(obs_reshaped)  # [batch_size * num_tasks, embedding_size]        
        task_q_values = self.output(task_embeddings)                   
        task_q_values = torch.squeeze(task_q_values, -1).to(self.device)           

        
        return task_q_values, state
