import argparse

from ray import air, tune
from ray.tune.registry import register_env
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.algorithms.dqn import DQNConfig
from ray.rllib.env.wrappers.pettingzoo_env import PettingZooEnv
from pettingzoo.mpe import simple_spread_v3

# Based on code from github.com/parametersharingmadrl/parametersharingmadrl

parser = argparse.ArgumentParser()
parser.add_argument(
    "--num-gpus",
    type=int,
    default=1,
    help="Number of GPUs to use for training.",
)
parser.add_argument(
    "--as-test",
    action="store_true",
    help="Whether this script should be run as a test: Only one episode will be "
    "sampled.",
)

if __name__ == "__main__":
    args = parser.parse_args()

    def env_creator(args):
        return PettingZooEnv(simple_spread_v3.env(continuous_actions = False))

    env = env_creator({})
    register_env("simple_spread", env_creator)

    config = (
        DQNConfig()
        .environment("simple_spread")
        .resources(num_gpus=args.num_gpus)
        .rollouts(num_rollout_workers=2)
        .multi_agent(
            policies=env.get_agent_ids(),
            policy_mapping_fn=(lambda agent_id, *args, **kwargs: agent_id),
        )
    )

    if args.as_test:
        # Only a compilation test of running waterworld / independent learning.
        stop = {"training_iteration": 1}
    else:
        stop = {"episodes_total": 60000}

    tune.Tuner(
        "DQN",
        run_config=air.RunConfig(
            stop=stop,
            checkpoint_config=air.CheckpointConfig(
                checkpoint_frequency=10,
            ),
        ),
        param_space=config,
    ).fit()