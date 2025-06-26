from typing import Any, Callable, Dict, List, Optional, Union
import warnings
import time
import numpy as np
import torch
from tianshou.data.collector import Collector
from tianshou.data import Batch, ReplayBuffer
from tianshou.env import BaseVectorEnv
from tianshou.policy import BasePolicy
from tianshou.utils.print import DataclassPPrintMixin
from tianshou.data.types import RolloutBatchProtocol

from tianshou.data import (
    Batch,
    CachedReplayBuffer,
    PrioritizedReplayBuffer,
    ReplayBuffer,
    ReplayBufferManager,
    SequenceSummaryStats,
    VectorReplayBuffer,
    to_numpy,
)

#@dataclass(kw_only=True)
class CollectStatsBase(DataclassPPrintMixin):
    """The most basic stats, often used for offline learning."""

    n_collected_episodes: int = 0
    """The number of collected episodes."""
    n_collected_steps: int = 0
    """The number of collected steps."""

class CollectStats(CollectStatsBase):
    """A data structure for storing the statistics of rollouts."""

    def __init__(self, agent_stats: Dict[str, Dict[str, Any]]) -> None:
        self.agent_stats = agent_stats

class CollectorMA(Collector):
    def __init__(
        self,
        policy: BasePolicy,
        env: BaseVectorEnv,
        buffer: Dict[str, ReplayBuffer],
        agents: List[str],
        preprocess_fn: Optional[Callable[..., Batch]] = None,
        exploration_noise: bool = False,
    ):
        super().__init__(policy, env, None, preprocess_fn, exploration_noise)
        self.agents = agents
        self._assign_buffers(buffer)
        
        self.data: RolloutBatchProtocol
        
        #self.data = Batch()
        #for agent_id in self.agents:
        #    self.data[agent_id] = Batch(
        #        obs={}, act={}, rew={}, terminated={}, truncated={}, done={}, obs_next={}, info={}, policy={}
        #    )
        # self.data = Batch()
        # for agent_id in self.agents:
        #     self.data[agent_id] = Batch(
        #         obs={}, act={}, rew={}, terminated={}, truncated={}, done={}, obs_next={}, info={}, policy={}
        #     )
        #     for key in self.data[agent_id].keys():
        #         self.data[agent_id][key] = [None] * self.env_num

    def _assign_buffers(self, buffer: Dict[str, ReplayBuffer]):
        if buffer is None:
            raise ValueError("Buffers cannot be None for CollectorMA")
        agent_ids = set(buffer.keys())
        env_agent_ids = set(self.agents)
        if agent_ids != env_agent_ids:
            raise ValueError(
                f"Buffer agent IDs {agent_ids} do not match environment agent IDs {env_agent_ids}"
            )
        self.buffer = buffer

    def collect(
        self,
        n_step: Optional[int] = None,
        n_episode: Optional[int] = None,
        random: bool = False,
        render: Optional[float] = None,
        no_grad: bool = True,
        gym_reset_kwargs: Optional[Dict[str, Any]] = None,
    ) -> CollectStats:
        assert not self.env.is_async, "Please use AsyncCollector if using async venv."
        if n_step is not None:
            assert n_episode is None, (
                f"Only one of n_step or n_episode is allowed in Collector."
                f"collect, got n_step={n_step}, n_episode={n_episode}."
            )
            assert n_step > 0
            if n_step % self.env_num != 0:
                warnings.warn(
                    f"n_step={n_step} is not a multiple of #env ({self.env_num}), "
                    "which may cause extra transitions collected into the buffer.",
                )
            ready_env_ids = np.arange(self.env_num)
        elif n_episode is not None:
            assert n_episode > 0
            ready_env_ids = np.arange(min(self.env_num, n_episode))
            self.data = self.data[: min(self.env_num, n_episode)]
        else:
            raise TypeError(
                "Please specify at least one (either n_step or n_episode) "
                "in AsyncCollector.collect().",
            )

        start_time = time.time()

        step_count = 0
        episode_count = 0
        episode_rews = {agent_id: [] for agent_id in self.agents}
        episode_lens = {agent_id: [] for agent_id in self.agents}
        episode_start_indices = {agent_id: [] for agent_id in self.agents}

        collective_done = np.zeros(self.env_num, dtype=bool)

        while True:
            # restore the state for each agent           
            
            # last_state = {
            #     agent_id: self.data[agent_id].policy.pop("hidden_state", None)
            #     for agent_id in self.agents
            # }
            for agent_id, agent_obs in self.data.obs.items():                
                    # Process the observation for the current agent and environment                   
                    last_state = {agent_id : self.data.policy.agent_id.pop("hidden_state", None) if agent_id in self.data.policy else None}

            # get the next action for each agent
            agent_data = {}
            for agent_id in self.agents:
                if random:
                    act_sample = self._action_space[agent_id].sample()
                    act_sample = self.policy.map_action_inverse(act_sample)
                    agent_data[agent_id] = Batch(act=act_sample)
                else:
                    if no_grad:
                        with torch.no_grad():
                            
                            result = self.policy.policies[agent_id](Batch({"obs": self.data.obs[agent_id], "info" : None}), last_state[agent_id])
                    else:
                        result = self.policy.policies[agent_id](self.data.obs[agent_id], last_state[agent_id])

                    policy = result.get("policy", Batch())
                    assert isinstance(policy, Batch)
                    state = result.get("state", None)
                    if state is not None:
                        policy.hidden_state = state  # save state into buffer
                    act = to_numpy(result.act)
                    if self.exploration_noise:
                        act = self.policy.policies[agent_id].exploration_noise(act, Batch({"obs": self.data.obs[agent_id], "info" : None}))
                    agent_data[agent_id] = Batch(policy=policy, act=act)

            # combine actions for all agents          
            self.data.update({
                agent_id: Batch({
                    key: value
                    for key, value in agent_data[agent_id].items()
                })
                for agent_id in self.agents
            })

            # get bounded and remapped actions first (not saved into buffer)
            action_remap = {
                agent_id: self.policy.map_action(self.data[agent_id].act)
                for agent_id in self.agents
            }

            # step in env
            obs_next, rew, terminated, truncated, info = self.env.step(action_remap, ready_env_ids)

            # update data for each agent
            for agent_id in self.agents:
                self.data[agent_id].update(
                    obs_next=obs_next[agent_id],
                    rew=rew[agent_id],
                    terminated=terminated[agent_id],
                    truncated=truncated[agent_id],
                    info=info[agent_id],
                )
                done = np.logical_or(terminated[agent_id], truncated[agent_id])
                collective_done = np.logical_or(collective_done, done)

                if self.preprocess_fn:
                    self.data[agent_id].update(
                        self.preprocess_fn(
                            obs_next=self.data[agent_id].obs_next,
                            rew=self.data[agent_id].rew,
                            done=done,
                            info=self.data[agent_id].info,
                            policy=self.data[agent_id].policy,
                            env_id=ready_env_ids,
                            act=self.data[agent_id].act,
                        ),
                    )

                # add data into the buffer
                ptr, ep_rew, ep_len, ep_idx = self.buffer[agent_id].add(
                    self.data[agent_id], buffer_ids=ready_env_ids
                )

                episode_rews[agent_id].extend(ep_rew)
                episode_lens[agent_id].extend(ep_len)
                episode_start_indices[agent_id].extend(ep_idx)

            # collect statistics
            step_count += len(ready_env_ids)

            if render:
                self.env.render()
                if render > 0 and not np.isclose(render, 0):
                    time.sleep(render)

            if np.any(collective_done):
                env_ind_local = np.where(collective_done)[0]
                env_ind_global = ready_env_ids[env_ind_local]
                episode_count += len(env_ind_local)

                self._reset_env_with_ids(env_ind_local, env_ind_global, gym_reset_kwargs)

                for i in env_ind_local:
                    for agent_id in self.agents:
                        self.data[agent_id].obs[i] = self.data[agent_id].obs_next[i]
                        self._reset_state(i)

                if n_episode:
                    surplus_env_num = len(ready_env_ids) - (n_episode - episode_count)
                    if surplus_env_num > 0:
                        mask = np.ones_like(ready_env_ids, dtype=bool)
                        mask[env_ind_local[:surplus_env_num]] = False
                        ready_env_ids = ready_env_ids[mask]
                        for agent_id in self.agents:
                            self.data[agent_id] = self.data[agent_id][mask]

                collective_done[env_ind_local] = False

            if (n_step and step_count >= n_step) or (n_episode and episode_count >= n_episode):
                break

        self.collect_step += step_count
        self.collect_episode += episode_count
        collect_time = max(time.time() - start_time, 1e-9)
        self.collect_time += collect_time

        agent_stats = {}
        for agent_id in self.agents:
            rews = np.array(episode_rews[agent_id])
            lens = np.array(episode_lens[agent_id], int)
            agent_stats[agent_id] = {
                "n_collected_episodes": len(rews),
                "n_collected_steps": sum(lens),
                "collect_time": collect_time,
                "collect_speed": sum(lens) / collect_time,
                "returns": rews,
                "returns_stat": SequenceSummaryStats.from_sequence(rews) if len(rews) > 0 else None,
                "lens": lens,
                "lens_stat": SequenceSummaryStats.from_sequence(lens) if len(lens) > 0 else None,
            }

        return CollectStats(agent_stats)

