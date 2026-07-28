from typing import Any
import numpy as np
import torch

from tianshou.data import Batch, ReplayBuffer, to_torch_as
from tianshou.policy.modelfree.dqn import DQNPolicy, DQNTrainingStats, TDQNTrainingStats


class CustomDQNPolicy(DQNPolicy[TDQNTrainingStats]):
    """
    A custom DQNPolicy that modifies the info parameter in _target_q.
    """

    def _target_q(self, buffer: ReplayBuffer, indices: np.ndarray) -> torch.Tensor:
        obs_next_batch = Batch(
            obs=buffer[indices].obs_next,
            info=buffer.agent_ref  # Your desired change here
        )
        result = self(obs_next_batch)
        if self._target:
            target_q = self(obs_next_batch, model="model_old").logits
        else:
            target_q = result.logits
        if self.is_double:
            return target_q[np.arange(len(result.act)), result.act]
        return target_q.max(dim=1)[0]

    # If you need to override the learn method to return your custom training stats,
    # you can do so here. Otherwise, the base class's learn method will work.
    def learn(self, batch: Any, *args: Any, **kwargs: Any) -> TDQNTrainingStats:
        # Call the parent's learn method or implement custom logic
        return super().learn(batch, *args, **kwargs)
