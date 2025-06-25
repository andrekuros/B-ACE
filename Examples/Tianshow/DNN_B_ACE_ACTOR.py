import torch
import torch.nn as nn
from typing import Any, Dict, Optional, Sequence, Tuple, Type, Union
from tianshou.utils.net.common import Net
import numpy as np
import warnings

"""Simple actor network (output with a Gauss distribution).

:param preprocess_net: a self-defined preprocess_net which output a
    flattened hidden state.
:param action_shape: a sequence of int for the shape of action.
:param hidden_sizes: a sequence of int for constructing the MLP after
    preprocess_net. Default to empty sequence (where the MLP now contains
    only a single linear layer).
:param float max_action: the scale for the final action logits. Default to
    1.
:param bool unbounded: whether to apply tanh activation on final logits.
    Default to False.
:param bool conditioned_sigma: True when sigma is calculated from the
    input, False when sigma is an independent parameter. Default to False.
:param int preprocess_net_output_dim: the output dimension of
    preprocess_net.

For advanced usage (how to customize the network), please refer to
:ref:`build_the_network`.

.. seealso::

    Please refer to :class:`~tianshou.utils.net.common.Net` as an instance
    of how preprocess_net is suggested to be defined.
    """


SIGMA_MIN = -20
SIGMA_MAX = 2

class DNN_B_ACE_ACTOR(Net):
        def __init__(
        self,        
        action_shape: Sequence[int],
        obs_shape: int,  
        device: str,        
        max_action: float = 1.0,        
        unbounded: bool = False,
        conditioned_sigma: bool = False,
        preprocess_net_output_dim: Optional[int] = None,
    ) -> None:
        
            super().__init__(  
                    state_shape=0,                      
                    action_shape=action_shape,            
                    device=device,
            )   
    
            if unbounded and not np.isclose(max_action, 1.0):
                warnings.warn(
                    "Note that max_action input will be discarded when unbounded is True."
                )
                max_action = 1.0            
            self.device = device
            self.output_dim = int(np.prod(action_shape))
            input_dim = obs_shape
            self.mu = nn.Sequential(
                        nn.Linear(input_dim, 64),
                        nn.ReLU(),
                        nn.Linear(64, 256),
                        nn.ReLU(), 
                        nn.Linear(256, 256),
                        nn.ReLU(),                   
                        nn.Linear(256, self.output_dim)
                    ).to(device)
            
            self._c_sigma = conditioned_sigma
            if conditioned_sigma:
                self.sigma = nn.Sequential(
                        nn.Linear(input_dim, 64),
                        nn.ReLU(),
                        nn.Linear(64, 256),
                        nn.ReLU(), 
                        nn.Linear(256, 256),
                        nn.ReLU(),                   
                        nn.Linear(256, self.output_dim)
                    ).to(device)
            else:
                self.sigma_param = nn.Parameter(torch.zeros(self.output_dim, 1))
            self.max_action = max_action
            self._unbounded = unbounded

        def forward(
            self,
            obs: Union[np.ndarray, torch.Tensor],
            state: Any = None,
            info: Dict[str, Any] = {},
        ) -> Tuple[torch.Tensor, Any]:
            """Mapping: obs -> logits -> action."""
                                   
            # logits, hidden = self.preprocess(obs, state)
            if isinstance(obs, np.ndarray):
                obs_tensor = torch.tensor(np.array(obs), dtype=torch.float32).to(self.device)            
            else:            
            # When obs is a Batch from MultiAgentPolicyManager, it's nested under 'obs' key
                obs_tensor = torch.tensor(np.array(obs["obs"]), dtype=torch.float32).to(self.device)
            
            mu = self.mu(obs_tensor)
            if not self._unbounded:
                mu = self.max_action * torch.tanh(mu)

            # For DDPG, the actor returns a deterministic action.
            return mu, state
