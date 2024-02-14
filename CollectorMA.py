from tianshou.data.collector import Collector

import time
import warnings
from typing import Any, Callable, Dict, List, Optional, Union

import gymnasium as gym
import numpy as np
import torch

from tianshou.data import (
    Batch,
    ReplayBuffer,
     to_numpy,
)
from tianshou.data.batch import _alloc_by_keys_diff
from tianshou.env import BaseVectorEnv, DummyVectorEnv
from tianshou.policy import BasePolicy

class CollectorMA(Collector):
    def __init__(
        self,
        policy: BasePolicy,
        env: Union[gym.Env, BaseVectorEnv],
        buffer: Dict[str, ReplayBuffer],
        preprocess_fn: Optional[Callable[..., Batch]] = None,
        exploration_noise: bool = False,
    ):
        super().__init__(policy, env, None, preprocess_fn, exploration_noise)
        self._assign_buffers(buffer)
    
    def _assign_buffers(self, buffer: Dict[str, ReplayBuffer]):
        if buffer is None:
            raise ValueError("Buffers cannot be None for CollectorMA")        
        self.buffer = buffer
        

    def collect(
        self,
        n_step: Optional[int] = None,
        n_episode: Optional[int] = None,
        random: bool = False,
        render: Optional[float] = None,
        no_grad: bool = True,
        gym_reset_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        
        assert not self.env.is_async, "Please use AsyncCollector if using async venv."
        if n_step is not None:
            assert n_episode is None, (
                f"Only one of n_step or n_episode is allowed in Collector."
                f"collect, got n_step={n_step}, n_episode={n_episode}."
            )
            assert n_step > 0
            if not n_step % self.env_num == 0:
                warnings.warn(
                    f"n_step={n_step} is not a multiple of #env ({self.env_num}), "
                    "which may cause extra transitions collected into the buffer."
                )
            ready_env_ids = np.arange(self.env_num)
        elif n_episode is not None:
            assert n_episode > 0
            ready_env_ids = np.arange(min(self.env_num, n_episode))
            self.data = self.data[:min(self.env_num, n_episode)]
        else:
            raise TypeError(
                "Please specify at least one (either n_step or n_episode) "
                "in AsyncCollector.collect()."
            )

        start_time = time.time()

        step_count = 0
        episode_count = 0
        episode_rews = []
        episode_lens = []
        episode_start_indices = []

        # Initialize a collective 'done' array for all agents
        collective_done = np.zeros(self.env_num, dtype=bool)

        while True:
            assert len(self.data) == len(ready_env_ids)
            # restore the state: if the last state is None, it won't store
            last_state = self.data.policy.pop("hidden_state", None)

            # get the next action
            if random:
                try:
                    act_sample = [
                        self._action_space[i].sample() for i in ready_env_ids
                    ]
                except TypeError:  # envpool's action space is not for per-env
                    act_sample = [self._action_space.sample() for _ in ready_env_ids]
                act_sample = self.policy.map_action_inverse(act_sample)  # type: ignore
                self.data.update(act=act_sample)
            else:
                if no_grad:
                    with torch.no_grad():  # faster than retain_grad version
                        # self.data.obs will be used by agent to get result
                        result = self.policy(self.data, last_state)
                else:
                    result = self.policy(self.data, last_state)
                # update state / act / policy into self.data
                policy = result.get("policy", Batch())
                assert isinstance(policy, Batch)
                state = result.get("state", None)
                if state is not None:
                    policy.hidden_state = state  # save state into buffer
                act = to_numpy(result.act)
                if self.exploration_noise:
                    act = self.policy.exploration_noise(act, self.data)
                self.data.update(policy=policy, act=act)

            # get bounded and remapped actions first (not saved into buffer)
            action_remap = self.policy.map_action(self.data.act)
            
            # Step in the environment
            # step in env
            obs_next, rew, terminated, truncated, info = self.env.step(
                action_remap,  # type: ignore
                ready_env_ids
            )
            
            self.data.update(
                obs_next=obs_next,
                rew=rew,
                terminated=terminated,
                truncated=truncated,
                #done=done,
                info=info
            )
                        
            # Initialize containers for episode statistics
            ep_rews = {agent_id: [] for agent_id in self.buffer.keys()}
            ep_lens = {agent_id: [] for agent_id in self.buffer.keys()}
            ep_idxs = {agent_id: [] for agent_id in self.buffer.keys()}

            # Process step data for each agent
            for i, agent_id in enumerate(self.buffer.keys()):
                
                # Extract and process data for the current agent across all environments                                            
                agent_step_data = {
                    key: self.extract_agent_data(self.data[key], agent_id)
                    for key in self.data.keys()
                }


                # Update the collective 'done' array for all environments
                collective_done |= self.check_done_states(agent_step_data)

                # Apply preprocessing if defined
                if self.preprocess_fn:
                    preprocessed_data = self.preprocess_fn(agent_step_data)
                    agent_step_data.update(preprocessed_data)

                # Add data to the agent's buffer
                ptr, ep_rew, ep_len, ep_idx = self.buffer[agent_id].add(agent_step_data)
                
                # if i == 0:
                #Since agents act in sincrony, just take 1
                ep_rews[agent_id].append(ep_rew)
                ep_lens[agent_id].append(ep_len)
                ep_idxs[agent_id].append(ep_idx)                                                     
                        
            # collect statistics
            step_count += len(ready_env_ids)

            # Check and handle if any environment is done
            if np.any(collective_done):
                
                env_ind_local = np.where(collective_done)[0]
                collective_done[env_ind_local] = False
                env_ind_global = ready_env_ids[env_ind_local]
                episode_count += len(env_ind_local)

                episode_lens.append(ep_len[env_ind_local])
                episode_rews.append(ep_rew[env_ind_local])
                episode_start_indices.append(ep_idx[env_ind_local])                

                # Reset finished environments
                self._reset_env_with_ids(env_ind_local, env_ind_global, gym_reset_kwargs)
                
                for i in env_ind_local:
                    self._reset_state(i)

                # Remove surplus environment IDs
                if n_episode:
                    surplus_env_num = len(ready_env_ids) - (n_episode - episode_count)
                    if surplus_env_num > 0:
                        mask = np.ones_like(ready_env_ids, dtype=bool)
                        mask[env_ind_local[:surplus_env_num]] = False
                        ready_env_ids = ready_env_ids[mask]
                        self.data = self.data[mask]

            self.data.obs = self.data.obs_next

            # Check termination conditions
            if (n_step and step_count >= n_step) or (n_episode and episode_count >= n_episode):
                break

        # Generate statistics
        self.collect_step += step_count
        self.collect_episode += episode_count
        self.collect_time += max(time.time() - start_time, 1e-9)

        if n_episode:
            self.data = Batch(
                obs={}, act={}, rew={}, terminated={}, truncated={}, done={}, obs_next={}, info={}, policy={}
            )
            self.reset_env()

        
        if episode_count > 0:
            rews, lens, idxs = list(
                map(
                    np.concatenate,
                    [episode_rews, episode_lens, episode_start_indices]
                )
            )
            rew_mean, rew_std = rews.mean(), rews.std()
            len_mean, len_std = lens.mean(), lens.std()
        else:
            rews, lens, idxs = np.array([]), np.array([], int), np.array([], int)
            rew_mean = rew_std = len_mean = len_std = 0

        return {
            "n/ep": episode_count,
            "n/st": step_count,
            "rews": rews,
            "lens": lens,
            "idxs": idxs,
            "rew": rew_mean,
            "len": len_mean,
            "rew_std": rew_std,
            "len_std": len_std,
        }

        # # Aggregate episode statistics
        # aggregated_rews = [np.concatenate(ep_rews[agent_id]) for agent_id in ep_rews]
        # aggregated_lens = [np.concatenate(ep_lens[agent_id]) for agent_id in ep_lens]
        # aggregated_idxs = np.concatenate([ep_idxs[agent_id][0] for agent_id in ep_idxs])

        # # Return aggregated statistics
        # return {
        #     "n/ep": episode_count,
        #     "n/st": step_count,
        #     "rews": aggregated_rews,
        #     "lens": aggregated_lens,
        #     "idxs": aggregated_idxs,
        #     "rew": aggregated_rews,
        #     "len": aggregated_lens,
        #     "rew_std": aggregated_rews,
        #     "len_std": aggregated_lens,
        # }


    def reset_buffer(self, keep_statistics: bool = False) -> None:
        """Reset the data buffers for all agents."""

        for agent_id, buffer in self.buffer.items():
            buffer.reset(keep_statistics=keep_statistics)

    
    
    def extract_agent_data(self, batch_data, agent_id):
        """
        Extract the relevant data for a specific agent from the batched environment data.
        """
        agent_data = Batch()        

        for key, value in batch_data.items():
            # Check if the key is the specific agent's data
            if key == agent_id:
                # Extract data specific to the agent
                agent_data = value
                break

        return agent_data


    def check_done_states(self, agent_data):
        """
        Check whether any of the environments have finished an episode for a specific agent.
        This function will return an array where each element corresponds to an environment,
        indicating whether the episode has finished in that environment.
        """
        terminated = agent_data.get('terminated', np.array([False] * self.env_num))
        truncated = agent_data.get('truncated', np.array([False] * self.env_num))
        return np.logical_or(terminated, truncated)


