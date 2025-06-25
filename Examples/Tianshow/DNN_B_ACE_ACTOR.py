import torch
import torch.nn as nn
from typing import Optional, Any, List, Dict, Union
from tianshou.utils.net.common import Net
import numpy as np

class DNN_B_ACE_ACTOR(Net):
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
            nn.LayerNorm(64), # Add LayerNorm
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.LayerNorm(128), # Add LayerNorm
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.LayerNorm(128), # Add LayerNorm
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.LayerNorm(64) # Add LayerNorm to the final output of the encoder before heads
        ).to(device)
        
        self.policy_fn = nn.Linear(64, action_shape)
        
        self.sigma_param = nn.Parameter(torch.full((action_shape,), -0.5, requires_grad=True))
        self.value_fn = nn.Linear(64, 1) # For critic output

    def forward(self, obs: Union[Dict[str, torch.Tensor], torch.Tensor], state: Optional[Any] = None, info: Optional[Any] = None, is_actor: bool = True):
        
        if 'obs' in obs:
            observation = torch.tensor(np.array(obs.obs), dtype=torch.float32).to(self.device)          
        else:          
            # When obs is a Batch from MultiAgentPolicyManager, it's nested under 'agent_0'
            #TODO add agent info to allow MARL
            observation = torch.tensor(np.array(obs["agent_0"].obs), dtype=torch.float32).to(self.device)
            
        
        output = self.scene_encoder(observation)
        
        
        mu = self.max_action * self.policy_fn(output)
        sigma = torch.exp(self.sigma_param).unsqueeze(0).expand_as(mu)
        
        #if observation.dim() > 1 and observation.size(1) != input_dim: # If not already flattened for linear
        #     observation = observation.view(observation.size(0), -1)
        
        return mu, sigma
