import torch
import torch.nn as nn
from typing import Optional, Any, List, Dict
from tianshou.utils.net.common import Net
import numpy as np

class DNN_B_ACE_CRITIC(Net):
    def __init__(
        self,
        obs_shape: int,        
        action_shape: int,        
        device: str,               
    ):
        super().__init__(  
            state_shape=0,                      
            action_shape=action_shape,            
            device=device,
        )               
                           
                                                
        self.scene_encoder = nn.Sequential(
            nn.Linear(17, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(), 
            nn.Linear(128, 128),
            nn.ReLU(),                   
            nn.Linear(128, 64)
        ).to(device)
        
        self.policy_fn = nn.Linear(64, 1)        
        

    def forward(self, obs: Dict[str, torch.Tensor], state: Optional[Any] = None, info: Optional[Any] = None):
        obs_sequence = obs['obs']
        output = self.scene_encoder(torch.tensor(obs_sequence, dtype=torch.float32).to(self.device))
                
        output = self.policy_fn(output)
        
        # Split the combined action output into means and std devs
        # Assuming the first half are means and the second half are std devs
        # means, std_devs = combined_action.split(combined_action.size(-1) // 2, dim=-1)
        
        # Optionally, apply an activation function to std_devs to ensure they are positive
        # For example, you could use the softplus function
        # std_devs = torch.nn.functional.softplus(std_devs)
        
        # print("Means: ", means)
        # print("Std Devs: ", std_devs)
        
        return output, state


    def value_function(self):
        return self._value_out.flatten()
        
     

    
