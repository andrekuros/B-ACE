import torch
import torch.nn as nn
from typing import Optional, Any, List, Dict, Union
from tianshou.utils.net.common import Net
import numpy as np

class DNN_B_ACE(Net):
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
            nn.Linear(20, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(), 
            nn.Linear(128, 128),
            nn.ReLU(),                   
            nn.Linear(128, 64)
        ).to(device)
        
        self.policy_fn = nn.Linear(64, action_shape)        
        

    def forward(self, obs: Union[Dict[str, torch.Tensor], torch.Tensor], state: Optional[Any] = None, info: Optional[Any] = None):
        
        # print("CRITIC:", len(obs))
        # if isinstance(obs, dict):
        #     # Concatenate the tensors in the dictionary along a new dimension
        #     obs_tensor = torch.cat(list(obs.values()), dim=0)
        # else:
        #     obs_tensor = obs

        obs_tensor = torch.tensor(obs, dtype=torch.float32).to(self.device)
        
        output = self.scene_encoder(obs_tensor)
        output = self.policy_fn(output)
        
        print(output)

        return output


    def value_function(self):
        return self._value_out.flatten()
        
     

    
