import torch
import torch.nn as nn
from typing import Optional, Any, List, Dict, Union
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
            nn.Linear(obs_shape, 64),
            nn.ReLU(),
            nn.Linear(64, 256),
            nn.ReLU(), 
            nn.Linear(256, 256),
            nn.ReLU(),                   
            nn.Linear(256, 64)
        ).to(device)
        
        self.policy_fn = nn.Linear(64, 1)        
        

    def forward(self, obs: Union[Dict[str, torch.Tensor], torch.Tensor], state: Optional[Any] = None, info: Optional[Any] = None):
        if isinstance(obs, np.ndarray):
            observation = torch.tensor(np.array(obs), dtype=torch.float32).to(self.device)                       
        else:                                   
            observation = torch.tensor(np.array(obs["obs"]), dtype=torch.float32).to(self.device)

        #obs_tensor = torch.tensor(obs, dtype=torch.float32).to(self.device)
        
        output = self.scene_encoder(observation)
        output = self.policy_fn(output).squeeze(-1)

        return output


    def value_function(self):
        return self._value_out.flatten()
