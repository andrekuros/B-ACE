from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch

from tianshou.data import Batch, ReplayBuffer
from tianshou.policy import BasePolicy
from tianshou.env.pettingzoo_env_parallel import PettingZooParallelEnv
import numpy as np
import torch

class MAParalellPolicy(BasePolicy):
    def __init__(self, policies: List[BasePolicy], env: PettingZooParallelEnv, device = None, **kwargs):
        super().__init__(action_space=env.action_space, **kwargs)
        assert len(policies) == len(env.agents), "One policy must be assigned for each agent."
        
        self.policies = {agent: policy for agent, policy in zip(env.agents, policies)}
        self.device = device if device is not None else "cpu"


    def forward(self, batch: Batch, state: Optional[Union[dict, Batch]] = None, **kwargs):
        action_dict = {}
        
        
        for agent_id, policy in self.policies.items():
            agent_data = Batch({key: value[agent_id] if agent_id in value else Batch() for key, value in batch.items()})
                                    
            action = policy(agent_data).act
            action_dict[agent_id] = action
        
        return Batch(act=action_dict)
    
    # def _compute_joint_next_q_values(self, sample_size: int, buffers: Dict[str, ReplayBuffer]) -> torch.Tensor:
    #     # Compute joint Q-values for the next state for all agents
    #     with torch.no_grad():
    #         all_batches = [buffer.sample(sample_size)[0] for buffer in buffers.values()]
    #         all_next_q_values = [policy(batch).logits.max(dim=1, keepdim=True)[0] 
    #                              for policy, batch in zip(self.policies.values(), all_batches)]
    #         joint_next_q_values = sum(all_next_q_values)
        
    #     joint_next_q_values_np = joint_next_q_values.squeeze(-1).cpu().numpy() / 3

    #     # if np.mean(joint_next_q_values_np) <  0:
    #     #     print(np.mean(joint_next_q_values_np))
                 
    #     return joint_next_q_values_np  # Remove the last dimension if necessary

       
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

    # def compute_joint_nstep_return(self, batch, buffer, indices, gamma, n_step):
    #     # Initialize containers for n-step returns and rewards
    #     n_step_returns = np.zeros(len(indices), dtype=np.float32)
    #     n_step_rewards = np.zeros(len(indices), dtype=np.float32)

    #     # Loop over each step to accumulate rewards and calculate returns
    #     for n in range(n_step):
    #         # Get indices for the nth step
    #         nth_indices = buffer.next(indices, n)

    #         # Compute and accumulate rewards
    #         n_step_rewards += (gamma ** n) * buffer.rew[nth_indices]

    #         # Check if nth step is terminal
    #         is_terminal = buffer.done[nth_indices] | buffer.terminated[nth_indices]
    #         if n == n_step - 1 or np.any(is_terminal):
    #             # For the last step or terminal step, compute the joint Q-values
    #             joint_q_values = self._compute_joint_next_q_values(1, {k: buffer for k in self.policies.keys()})
    #             # Calculate the n-step return
    #             n_step_returns[indices] = n_step_rewards + (gamma ** n_step) * joint_q_values * (~is_terminal)
    #             break

    #     return n_step_returns


    
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
 

