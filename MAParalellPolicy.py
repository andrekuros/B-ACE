from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch

from tianshou.data import Batch, ReplayBuffer
from tianshou.policy import BasePolicy
from tianshou.env.pettingzoo_env_parallel import PettingZooParallelEnv

from tianshou.policy import PGPolicy

import numpy as np
import torch

class MAParalellPolicy(BasePolicy):
    def __init__(self, policies: List[BasePolicy], env: PettingZooParallelEnv, device = None, **kwargs):
        super().__init__(action_space=env.action_space(), **kwargs)
        assert len(policies) == len(env.agents), "One policy must be assigned for each agent."
        
        self.policies = {agent: policy for agent, policy in zip(env.agents, policies)}
        self.device = device if device is not None else "cpu"

        
        # for policy in policies:
        #     if isinstance(policy, PGPolicy):                
        #         policy.forward = _new_forward_PG 


    def forward(self, batch: Batch, state: Optional[Union[dict, Batch]] = None, **kwargs):
        action_dict = {}
                
        for agent_id, policy in self.policies.items():
            agent_data = Batch({key: value[agent_id] if agent_id in value else Batch() for key, value in batch.items()})

            action_dict[agent_id] = policy(agent_data, state)  # doesn't map to the target action range
            # act = policy.map_action(act, agent_data)
            
        return action_dict#Batch(action_dict, state=state)
    

    def update(self, sample_size: int, buffers: Dict[str, ReplayBuffer], **kwargs: Any) -> Dict[str, Any]:
        """Update the policy network for each agent."""
        results = {}
        self.updating = True

        # Compute joint Q-values for the next state for all agents
        # joint_next_q_values = self._compute_joint_next_q_values(sample_size, buffers)

        # Update each agent's policy
        for agent_id, buffer in buffers.items():
            # Sample data from the buffer
            batch, indices = buffer.sample(sample_size)
            
            batch = self.process_fn(batch, buffer, indices)

            # Add joint Q-values to the batch
            # batch.joint_next_q_values = joint_next_q_values
            
            batch = self.policies[agent_id].process_fn(batch, buffers[agent_id], indices)

            # Perform learning and store results
            # out = self.learn(batch, joint_next_q_values, self.policies[agent_id], **kwargs)
            out = self.policies[agent_id].learn(batch=batch, **kwargs)
                        
            for k, v in out.items():
                results[agent_id + "/" + k] = v

            # Post-process function
            self.post_process_fn(batch, buffer, indices)

        self.updating = False
        if self.lr_scheduler is not None:
            self.lr_scheduler.step()

        return results
    
    def learn(self, batch: Batch, joint_next_q_values_np, policy,  **kwargs: Any) -> Dict[str, Union[float, List[float]]]:
        """Learn from the batch data with joint Q-values."""
                                
        # Adjust the target Q-value using joint Q-values            
        #with torch.no_grad():               
        target_q_values = batch.rew #+ policy._gamma * joint_next_q_values_np * (1 - batch.done)

        # Modify the batch to include the computed target Q-values
        batch.returns = target_q_values  
       
        # Perform learning with the modified batch
        out = policy.learn(batch=batch, **kwargs)
        
        return out

        
    def exploration_noise(self, act: Union[np.ndarray, Batch],
                          batch: Batch) -> Union[np.ndarray, Batch]:
        """Add exploration noise from sub-policy onto act."""
        
        for agent_id, policy in self.policies.items():
            
            data_agent = Batch({ "obs"  : batch.obs[agent_id]})
            if hasattr(batch, "mask"):
                data_agent.mask = batch.mask[agent_id] 

            act[agent_id] = policy.exploration_noise(
                act[agent_id], data_agent )            
        return act
 

