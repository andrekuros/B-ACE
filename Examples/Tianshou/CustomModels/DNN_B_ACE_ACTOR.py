import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Any, Tuple, Union, Dict

from tianshou.utils.net.common import Net

class DNN_B_ACE_ACTOR(Net):
    """
    A standard Actor network for the DDPG algorithm.

    :param int obs_shape: The dimensionality of the observation space.
    :param int action_shape: The dimensionality of the action space.
    :param float max_action: The maximum absolute value for each action component.
    :param str device: The device to run the network on ('cpu' or 'cuda').
    :param List[int] hidden_sizes: A list of integers specifying the size of each hidden layer.
    """
    def __init__(
        self,
        obs_shape: int,
        action_shape: int,
        max_action: float,
        device: str = "cpu",
        hidden_sizes: list[int] = [256, 256],
    ):
        super().__init__(
            state_shape=obs_shape,  # More conventional to use obs_shape
            action_shape=action_shape,
            device=device,
        )

        self.max_action = max_action
        
        layers = [nn.Linear(obs_shape, hidden_sizes[0]), nn.ReLU()]
        for i in range(len(hidden_sizes) - 1):
            layers.extend([nn.Linear(hidden_sizes[i], hidden_sizes[i+1]), nn.ReLU()])
        
        # Keep the final layer separate to initialize it
        self.output_layer = nn.Linear(hidden_sizes[-1], action_shape)
                
        # Initialize the final layer weights and biases to a small uniform range
        # This is a key technique from the original DDPG paper
        torch.nn.init.uniform_(self.output_layer.weight, -3e-3, 3e-3)
        torch.nn.init.uniform_(self.output_layer.bias, -3e-3, 3e-3)
        
        # Combine all layers into the model
        layers.append(self.output_layer)
        self.model = nn.Sequential(*layers).to(device)

    def forward(
        self,
        obs: Union[np.ndarray, torch.Tensor],
        state: Optional[Any] = None,
        info: Dict[str, Any] = {},
    ) -> Tuple[torch.Tensor, Optional[Any]]:
        """
        Defines the forward pass of the actor network.
        
        Returns a tuple of (action, state), where state is None for this network.
        """
        # Ensure the input is a torch tensor on the correct device
        # if not isinstance(obs, torch.Tensor):
        #     obs = torch.as_tensor(obs, dtype=torch.float32, device=self.device)
        
        if 'obs' in obs:
            observation = torch.tensor(np.array(obs.obs), dtype=torch.float32).to(self.device)          
        else:          
            # When obs is a Batch from MultiAgentPolicyManager, it's nested under 'agent_0'
            #TODO add agent info to allow MARL
            observation = torch.tensor(np.array(obs["agent_0"].obs), dtype=torch.float32).to(self.device)
        
        logits = self.model(observation)
        
        # Apply tanh activation and scale by max_action
        action = self.max_action * torch.tanh(logits)
        
        
        return action, state
