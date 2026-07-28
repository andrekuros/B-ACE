import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Any, Tuple, Union, Dict, List

from tianshou.utils.net.common import Net

class DNN_B_ACE_CRITIC(Net):
    """
    A standard Critic network for the DDPG algorithm.

    This network takes an observation (state) and an action as input and
    outputs a single Q-value.

    :param int obs_shape: The dimensionality of the observation space.
    :param int action_shape: The dimensionality of the action space.
    :param str device: The device to run the network on ('cpu' or 'cuda').
    :param List[int] hidden_sizes: A list of integers specifying the size of each hidden layer.
    """
    def __init__(
        self,
        obs_shape: int,
        action_shape: int,
        device: str = "cpu",
        hidden_sizes: List[int] = [256, 256],
    ):
        super().__init__(
            state_shape=obs_shape,  # More conventional to use obs_shape
            action_shape=action_shape,
            device=device,
        )


        # The input to the critic is the concatenation of observation and action
        input_size = obs_shape + action_shape
        
        layers = [nn.Linear(input_size, hidden_sizes[0]), nn.ReLU()]
        for i in range(len(hidden_sizes) - 1):
            layers.extend([nn.Linear(hidden_sizes[i], hidden_sizes[i+1]), nn.ReLU()])
        
        # The final layer outputs a single Q-value
        layers.append(nn.Linear(hidden_sizes[-1], 1))
        
        self.model = nn.Sequential(*layers).to(device)

    def forward(
        self,
        obs: Union[np.ndarray, torch.Tensor],
        act: Optional[Union[np.ndarray, torch.Tensor]] = None,
        state: Optional[Any] = None,
        info: Dict[str, Any] = {},
    ) -> Tuple[torch.Tensor, Optional[Any]]:
        """
        Defines the forward pass of the critic network.
        
        Concatenates the observation and action and returns the estimated Q-value.
        """
        # Ensure obs is a torch tensor
#        if not isinstance(obs, torch.Tensor):
#            obs = torch.as_tensor(obs, dtype=torch.float32, device=self.device)
            
        if 'obs' in obs:
            observation = torch.tensor(np.array(obs.obs), dtype=torch.float32).to(self.device)          
        else:          
            # When obs is a Batch from MultiAgentPolicyManager, it's nested under 'agent_0'
            #TODO add agent info to allow MARL
            observation = torch.tensor(np.array(obs["agent_0"].obs), dtype=torch.float32).to(self.device)
        
        
        # Tianshou may pass actions during the update step
        if act is not None:
            if not isinstance(act, torch.Tensor):
                act = torch.as_tensor(act, dtype=torch.float32, device=self.device)
            # Concatenate obs and act along the feature dimension
            observation = torch.cat([observation, act], dim=1)
        
        q_value = self.model(observation)
        
        return q_value