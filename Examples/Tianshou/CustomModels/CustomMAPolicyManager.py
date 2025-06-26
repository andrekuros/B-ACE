from typing import Any, Literal, Protocol, Self, cast, overload

import numpy as np
from overrides import override

from tianshou.data import Batch, ReplayBuffer
from tianshou.data.batch import BatchProtocol, IndexType
from tianshou.data.types import RolloutBatchProtocol
from tianshou.policy import BasePolicy
from tianshou.policy.base import TLearningRateScheduler, TrainingStats

import gymnasium as gym
import numpy as np
import torch
from gymnasium.spaces import Box, Discrete, MultiBinary, MultiDiscrete

try:
    from tianshou.env.pettingzoo_env import PettingZooEnv
except ImportError:
    PettingZooEnv = None  # type: ignore


class MapTrainingStats(TrainingStats):
    def __init__(
        self,
        agent_id_to_stats: dict[str | int, TrainingStats],
        train_time_aggregator: Literal["min", "max", "mean"] = "max",
    ) -> None:
        self._agent_id_to_stats = agent_id_to_stats
        train_times = [agent_stats.train_time for agent_stats in agent_id_to_stats.values()]
        match train_time_aggregator:
            case "max":
                aggr_function = max
            case "min":
                aggr_function = min
            case "mean":
                aggr_function = np.mean  # type: ignore
            case _:
                raise ValueError(
                    f"Unknown {train_time_aggregator=}",
                )
        self.train_time = aggr_function(train_times)
        self.smoothed_loss = {}

    @override
    def get_loss_stats_dict(self) -> dict[str, float]:
        """Collects loss_stats_dicts from all agents, prepends agent_id to all keys, and joins results."""
        result_dict = {}
        for agent_id, stats in self._agent_id_to_stats.items():
            agent_loss_stats_dict = stats.get_loss_stats_dict()
            for k, v in agent_loss_stats_dict.items():
                result_dict[f"{agent_id}/" + k] = v
        return result_dict


class MAPRolloutBatchProtocol(RolloutBatchProtocol, Protocol):
    # TODO: this might not be entirely correct.
    #  The whole MAP data processing pipeline needs more documentation and possibly some refactoring
    @overload
    def __getitem__(self, index: str) -> RolloutBatchProtocol:
        ...

    @overload
    def __getitem__(self, index: IndexType) -> Self:
        ...

    def __getitem__(self, index: str | IndexType) -> Any:
        ...


class CustomMAPolicyManager(BasePolicy):
    """Multi-agent policy manager for MARL.

    This multi-agent policy manager accepts a list of
    :class:`~tianshou.policy.BasePolicy`. It dispatches the batch data to each
    of these policies when the "forward" is called. The same as "process_fn"
    and "learn": it splits the data and feeds them to each policy. A figure in
    :ref:`marl_example` can help you better understand this procedure.

    :param policies: a list of policies.
    :param env: a PettingZooEnv.
    :param action_scaling: if True, scale the action from [-1, 1] to the range
        of action_space. Only used if the action_space is continuous.
    :param action_bound_method: method to bound action to range [-1, 1].
        Only used if the action_space is continuous.
    :param lr_scheduler: if not None, will be called in `policy.update()`.
    """

    def __init__(
        self,
        *,
        policies: list[BasePolicy],
        # TODO: 1 why restrict to PettingZooEnv?
        # TODO: 2 This is the only policy that takes an env in init, is it really needed?
        env: PettingZooEnv,
        action_scaling: bool = False,
        action_bound_method: Literal["clip", "tanh"] | None = "clip",
        lr_scheduler: TLearningRateScheduler | None = None,
    ) -> None:
        super().__init__(
            action_space=env.action_space,
            observation_space=env.observation_space,
            action_scaling=action_scaling,
            action_bound_method=action_bound_method,
            lr_scheduler=lr_scheduler,
        )
        assert len(policies) == len(env.agents), "One policy must be assigned for each agent."

        self.agent_idx = env.agent_idx
        for i, policy in enumerate(policies):
            # agent_id 0 is reserved for the environment proxy
            # (this MultiAgentPolicyManager)
            policy.set_agent_id(env.agents[i])

        self.policies: dict[str | int, BasePolicy] = dict(zip(env.agents, policies, strict=True))
        """Maps agent_id to policy."""

    # TODO: unused - remove it?
    def replace_policy(self, policy: BasePolicy, agent_id: int) -> None:
        """Replace the "agent_id"th policy in this manager."""
        policy.set_agent_id(agent_id)
        self.policies[agent_id] = policy


    def process_fn(  # type: ignore
        self,
        batch: MAPRolloutBatchProtocol,
        buffer: ReplayBuffer,
        indice: np.ndarray,
    ) -> MAPRolloutBatchProtocol:
        """Dispatch batch data to every policy's process_fn.

        Save original multi-dimensional rew in "save_rew", set rew to the reward
        of each agent during their "process_fn", and restore the original reward afterwards.
        """
                    
        results: dict[str | int, RolloutBatchProtocol] = {}
        assert isinstance(
            batch.obs,
            BatchProtocol,
        ), f"here only observations of type Batch are permitted, but got {type(batch.obs)}"

        # Function to filter buffer for a specific agent

        for agent_id, policy in self.policies.items():
                                

            
            # Extract relevant data for the agent
            agent_batch = Batch(
                obs=batch.obs[agent_id], 
                obs_next=batch.obs_next[agent_id], 
                info=batch.info[agent_id],
                act=batch.act[agent_id],
                mask=batch.obs[agent_id].mask,
                #weight=batch.weight,
                #rew=batch.rew[:, agent_id] if batch.rew.ndim > 1 else batch.rew,
                rew=batch.rew,
                terminated=batch.terminated,
                truncated=batch.truncated
            )
        
            if not hasattr(agent_batch, "info"):
                agent_batch.info = Batch()  # Create an empty info attribute if missing
            
            buffer.agent_ref = agent_id
                     
            results[agent_id] = policy.process_fn(agent_batch, buffer, indice)

        return Batch(results)

    # def exploration_noise(
    #     self,
    #     act: np.ndarray | BatchProtocol,
    #     batch: RolloutBatchProtocol,
    # ) -> np.ndarray | BatchProtocol:
    #     """Add exploration noise from sub-policy onto act."""
    #     assert isinstance(
    #         batch.obs,
    #         BatchProtocol,
    #     ), f"here only observations of type Batch are Batch, but got {type(batch.obs)}"
        
    #     for agent_id, policy in self.policies.items():
    #         act[agent_id] = policy.exploration_noise(act[agent_id], batch.obs[agent_id])
    #     return act

    def forward(  # type: ignore
        self,
        batch: Batch,
        state: dict | Batch | None = None,
        **kwargs: Any,
    ) -> Batch:
        """Dispatch batch data to every policy's forward and return actions for all agents.

        :param batch: a Batch object containing observations for all agents
        :param state: if None, it means all agents have no state. If not
            None, it should contain keys of "agent_1", "agent_2", ...

        :return: a Batch with the following contents:
            {
                "act": a dictionary mapping agent_id to its corresponding action
                "state": a dictionary mapping agent_id to its corresponding state (if any)
            }
        """
        act_dict, state_dict = {}, {}
        for agent_id, policy in self.policies.items():                  
            agent_batch = Batch( obs=batch.obs[agent_id], mask=batch.obs[agent_id].mask, info=batch.info[agent_id])            
            if not hasattr(agent_batch, "info"):
                agent_batch.info = Batch()  # Create an empty info attribute if missing
            
            out = policy(
                batch=agent_batch,
                state=None if (state is None or state.shape == []) else state[agent_id],
                **kwargs,
            )
            act_dict[agent_id] = out.act#.detach()  # Detach the action tensor
            if hasattr(out, "state") and out.state is not None:
                if isinstance(out.state, torch.Tensor):
                    state_dict[agent_id] = out.state.detach()
                elif isinstance(out.state, Batch):
                    # Recursively detach tensors within the state Batch
                    detached_state_batch = Batch()
                    for k, v in out.state.items():
                        if isinstance(v, torch.Tensor):
                            detached_state_batch[k] = v.detach()
                        else:
                            detached_state_batch[k] = v # Keep non-tensor items as is
                    state_dict[agent_id] = detached_state_batch
                else:
                    state_dict[agent_id] = out.state

        if not state_dict: # If no agent returned a state, return None for the overall state
            return Batch(act=act_dict, state=None)
        
        return Batch(act=act_dict, state=state_dict)

    def learn(  # type: ignore
        self,
        batch: MAPRolloutBatchProtocol,
        *args: Any,
        **kwargs: Any,
    ) -> MapTrainingStats:
        """Dispatch the data to all policies for learning.

        :param batch: must map agent_ids to rollout batches
        """
        
        agent_id_to_stats = {}
        for agent_id, policy in self.policies.items():            
            data = batch[agent_id]
            if data: # Changed from not data.is_empty()
                train_stats = policy.learn(batch=data, **kwargs)
                agent_id_to_stats[agent_id] = train_stats
        return MapTrainingStats(agent_id_to_stats)

    def train(self, mode: bool = True) -> Self:
        """Set each internal policy in training mode."""
        for policy in self.policies.values():
            policy.train(mode)
        return self
    
    def map_action(self, act: Batch) -> list:
        """
        Map raw network output to action range in gym's env.action_space.
        This function is called in :meth:`~tianshou.data.Collector.collect` and only affects action sending to env.
        Remapped action will not be stored in buffer and thus can be viewed as a part of env (a black box action transformation).
        Action mapping includes 2 standard procedures: bounding and scaling.
        Bounding procedure expects original action range is (-inf, inf) and maps it to [-1, 1],
        while scaling procedure expects original action range is (-1, 1) and maps it to [action_space.low, action_space.high].
        Bounding procedure is applied first.

        :param act: a data batch or numpy.ndarray which is the action taken by policy.forward.
        :return: action in the form of a list where each position represents an environment and contains a dictionary with the agent ID and the corresponding action data.
        """
        processed_act = {}        

        for agent_id, policy in self.policies.items():
            agent_act = self._action_to_numpy(act[agent_id])
            if isinstance(self.action_space, gym.spaces.Box):
                if self.action_bound_method == "clip":
                    agent_act = np.clip(agent_act, -1.0, 1.0)
                elif self.action_bound_method == "tanh":
                    agent_act = np.tanh(agent_act)

                if self.action_scaling:
                    assert (
                        np.min(agent_act) >= -1.0 and np.max(agent_act) <= 1.0
                    ), f"action scaling only accepts raw action range = [-1, 1], but got: {act}"
                    low, high = self.action_space.low, self.action_space.high
                    agent_act = low + (high - low) * (agent_act + 1.0) / 2.0

            processed_act[agent_id] = agent_act

        # Get the number of environments
        num_envs = len(processed_act['agent_0'])

        # Initialize the remapped action list
        remapped_action = [None] * num_envs

        # Iterate over each environment
        for env_id in range(num_envs):
            # Create a dictionary to store the action for each agent in the current environment
            env_action = {}

            # Iterate over each agent
            for agent_id, agent_action in processed_act.items():
                # Add the agent's action to the environment's action dictionary
                env_action[agent_id] = agent_action[env_id]

            # Assign the environment's action dictionary to the corresponding position in the remapped action list
            remapped_action[env_id] = env_action

        return remapped_action
