# from ray.rllib.algorithms.qmix import QMixConfig
from ray import tune
from RLLib_QMIX

config = QMixConfig()
config.environment(env="single_spread_v3")  # Specify your environment
config.framework("torch")  # Use PyTorch framework

# Example of setting some QMix specific configurations
config.training(mixer="qmix", mixing_embed_dim=32)

# Run the experiment
tune.run("QMIX", config=config.to_dict(), stop={"training_iteration": 100})
