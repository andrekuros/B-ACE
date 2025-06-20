# B-ACE: Beyond Visual Range Air Combat Environment

B-ACE is an open-source, lightweight simulation environment designed to facilitate the experimentation and evaluation of autonomous agents in Beyond Visual Range (BVR) air combat scenarios. Built on the Godot game engine, B-ACE leverages Multi-Agent Reinforcement Learning (MARL) to explore advanced techniques in autonomous air combat agent development. The environment provides a flexible and accessible platform for the research community, enabling the rapid prototyping and evaluation of AI-based tactics and strategies in complex air combat settings.

## Features
- **Open-source and easily extensible:** Researchers can easily modify and extend the environment to suit their specific needs.
- **Integration with MARL frameworks:** Compatible with popular reinforcement learning libraries such as Gymnasium and PettingZoo.
- **Simplified yet representative BVR combat dynamics:** Focuses on key aspects of air combat, offering a balance between realism and accessibility.
- **Supports single and multi-agent learning scenarios:** Ideal for exploring both individual and cooperative agent behaviors.

# Documentation

## Project Structure

The project is organized as follows:

-   `b_ace_py/`: Contains the core Python code for the B-ACE environment, including the PettingZoo wrapper (`B_ACE_GodotPettingZooWrapper.py`) and other utility functions.
-   `Examples/`: Contains example scripts for running the simulation with different reinforcement learning frameworks, such as Tianshou and BenchMARL.
-   `Godot_Air_Combat/`: Contains the Godot project files for the simulation environment.
-   `Data/`: Contains data files used for experiments and evaluation.
-   `bin/`: Contains the executable binaries for the Godot simulation.
-   `minimum_requirements.txt`: Lists the minimum Python packages required to run the examples.
-   `Readme.md`: The documentation file you are currently reading.

## How to use?

The B-ACE adopt the pettingZoo standard (link to pettinzoo site) and leverage GodotRL Agents (link do godotRL Agnets project) to simplify the interction with the simulation using standarlized tools.

The B_ACE_PettingZoo_Wrapper (link to file) is responsible to offer a peeting zoo enviroment connected with the Godot simulation. You just need to send action and process observation to evaluate your solution.

Following the Gym/PettingZoo protocols, the `B_ACE_GodotPettingZooWrapper` class provides the following standard functions:

-   `__init__`: Initializes the environment, including launching the Godot simulation, setting up the observation and action spaces, and defining the agents.
-   `reset`: Resets the environment to its initial state, returning a dictionary of observations for each agent.
-   `step`: Takes a dictionary of actions from each agent and steps the environment forward, returning the next observations, rewards, terminations, truncations, and info dictionaries.
-   `observation_space(agent)`: Returns the observation space for a given agent.
-   `action_space(agent)`: Returns the action space for a given agent.

These functions ensure that the B-ACE environment can be used with any reinforcement learning framework that is compatible with the PettingZoo API.


## Examples

#Simple Test

The fisrt exemple is a simple test to check the integration of the python code with godot and observe the simulaion running.

To run the simple test (sugest the creation of a venv):

code:
pip install minimum_requirements.txt
git clone https://github.com/andrekuros/B-ACE.git
python ./B-ACE/Examples/run_simple_example.py

# Tianshou Example

Tianshou is an open-source reinforcement learning framework that provides a clean and efficient implementation of various reinforcement learning algorithms.

To understand the Tianshou example, you should:

-   Install Tianshou and its dependencies.
-   Understand how to define a policy and a collector in Tianshou.
-   Understand how to train an agent using the `tianshou.trainer.onpolicy.OnpolicyTrainer` class.

# BenchMARL Example

BenchMARL is a framework for benchmarking multi-agent reinforcement learning algorithms.

To understand the BenchMARL example, you should:

-   Install BenchMARL and its dependencies.
-   Understand how to define a task and an agent in BenchMARL.
-   Understand how to train and evaluate agents using the BenchMARL training and evaluation scripts.

## Citation
If you use B-ACE in your research, please cite the following paper:

```bibtex
@inproceedings{kuroswiski2024bace,
  author    = {Andre R. Kuroswiski and Annie S. Wu and Angelo Passaro},
  title     = {B-ACE: An Open Lightweight Beyond Visual Range Air Combat Simulation Environment for Multi-Agent Reinforcement Learning},
  booktitle = {Interservice/Industry Training, Simulation, and Education Conference (I/ITSEC) 2024},
  year      = {2024},
  note      = {Presented in December 2024},
  paper     = {24464}
}
````

## Acknowledgements
This work was supported by the Brazilian Air Force Postgraduate Program in Operational Applications (PPGAO).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
