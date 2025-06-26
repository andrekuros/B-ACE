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
        max_action : float              
    ):
        super().__init__(  
            state_shape=0,                      
            action_shape=action_shape,            
            device=device,
        )               
                           
        self.max_action = max_action                                  
        self.scene_encoder = nn.Sequential(
            nn.Linear(obs_shape, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 64)
        ).to(device)
        
        self.policy_fn = nn.Linear(64, action_shape)
        self.sigma_param = nn.Parameter(torch.zeros(action_shape, requires_grad=True))
        self.value_fn = nn.Linear(64, 1) # For critic output

    def forward(self, obs: Union[Dict[str, torch.Tensor], torch.Tensor], state: Optional[Any] = None, info: Optional[Any] = None, is_actor: bool = True):
        
        obs_tensor = torch.tensor(obs["obs"], dtype=torch.float32).to(self.device)
        
        output = self.scene_encoder(obs_tensor)
        
        
        mu = self.policy_fn(output)
        sigma = torch.exp(self.sigma_param).unsqueeze(0).expand_as(mu)
        return (mu, sigma), state
    
        value = self.value_fn(output)
        return value, state


    def value_function(self):
        # This method is likely not used by Tianshou's PPOPolicy directly
        # as the critic network is passed separately.
        # However, if it were, it would need to be updated to reflect the new structure.
        # For now, it can remain as is or be removed if confirmed unused.
        return self._value_out.flatten()
