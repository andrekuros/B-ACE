#%%%
import random
import numpy as np
from GodotExperimentWrapper import GodotExperimentWrapper
import json
import pandas as pd
import concurrent.futures
import wandb

# Define the parameters for the genetic algorithm
population_size = 30
enemies_size = 5
generations = 50
mutation_rate = 0.10
tournament_size = 3
elite_size = 2  # Number of best individuals to retain each generation
update_enemies_every = 1  # Frequency of updating the enemies list
max_enemies_update = 2
runs_per_case = 30

# Define the behavior parameter ranges
param_ranges = {
    "dShot": (0.1, 1.2),
    "lCrank": (0.1, 1.2),
    "lBreak": (0.1, 1.2)
}

config_dict_template = { "EnvConfig" : 
                {
                    "task": "b_ace_v1",
                    'env_path': 'BVR_AirCombat/bin/B_ACE_v10.exe',		
                    "port": 12500,
                    "renderize": 0,
                    "debug_view": 0,
                    "phy_fps": 20,
                    "speed_up": 50000,
                    "max_cycles": 36000,
                    "experiment_mode"  : 1,
                    "parallel_envs": 1,	
                    "seed": 1,	
                    "action_repeat": 20,	
                    "action_type": "Low_Level_Continuous", 
                    "stop_mission" : 0,                                           
                                        
                    "RewardsConfig" : {
                        "mission_factor": 0.001,				
                        "missile_fire_factor": -0.1,		
                        "missile_no_fire_factor": -0.001,
                        "missile_miss_factor": -0.5,
                        "detect_loss_factor": -0.1,
                        "keep_track_factor": 0.001,
                        "hit_enemy_factor": 3.0,
                        "hit_own_factor": -5.0,			
                        "mission_accomplished_factor": 10.0,			
                    }
                },

                "AgentsConfig" : 
                {
                    "blue_agents": { 
                        "num_agents" : 1,
                        
                        "base_behavior": "baseline1",
                        "mission"    : "DCA",
                        "beh_config" : {
                            "dShot" : 0.85,
                            "lCrank": 0.60,
                            "lBreak": 0.95
                        },                  
                        
                        "init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
                        "offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
                        "init_hdg": 0.0,                        
                        "target_position": {"x": 0.0,"y": 25000.0,"z": 0.0},
                        "rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},				
                        "rnd_shot_dist_var": 0.025,
                        "rnd_crank_var": 0.025,
                        "rnd_break_var": 0.025,
                        "wez_models" : "res://assets/wez/Default_Wez_params.json"
                    },	
                    "red_agents":
                    { 
                        "num_agents" : 1, 
                                    
                        "base_behavior": "baseline1",
                        "mission"    : "DCA",
                        "beh_config" : {
                            "dShot" : 0.85,
                            "lCrank": 0.60,
                            "lBreak": 0.95
                        },
                        "init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
                        "offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
                        "init_hdg" : 180.0,                        
                        "target_position": {"x": 0.0,"y": 25000.0,"z": 0.0},
                        "rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},				                        
                        "rnd_shot_dist_var": 0.025,
                        "rnd_crank_var": 0.025,
                        "rnd_break_var": 0.025,
                        "wez_models" : "res://assets/wez/Default_Wez_params.json"
                    }
                },
                
}


def insert_inv_sorted(sorted_list, ind):
    # Find the correct position to insert the value
    for i in range(len(sorted_list)):
        if ind.score[0] > sorted_list[i].score[0]:
            sorted_list.insert(i, ind)
            return True
    return False

def process_results(results):
    # Flatten the list of lists into a single list of dictionaries
    flat_data = [item for sublist in results for item in sublist]
        
    # Prepare a list to store the processed data
    processed_data = []

    # Process each simulation result
    for result in flat_data:
        entry = {
            'case_id': result['env_id'],
            'run_num': result['run_num']  
        }
        
        entry.update({
            'killed_blue': result['final_results'][0]['killed'],
            'missile_blue': result['final_results'][0]['missile'],
            'mission_blue': result['final_results'][0]['mission'],
            'reward_blue': result['final_results'][0]['reward'],
            
            'killed_red': result['final_results'][1]['killed'],
            'missile_red': result['final_results'][1]['missile'],
            'mission_red': result['final_results'][1]['mission'],
            'reward_red': result['final_results'][1]['reward']
        })

        processed_data.append(entry)

    # Create a DataFrame from the processed data
    df = pd.DataFrame(processed_data)
    
    # Group by 'case_id' and calculate the mean of each group
    df_grouped = df.groupby('case_id').agg({
        'run_num': 'max',
        'killed_blue': 'mean',
        'missile_blue': 'mean',
        'mission_blue': 'mean',
        'reward_blue': 'mean',
        'killed_red': 'mean',
        'missile_red': 'mean',
        'mission_red': 'mean',
        'reward_red': 'mean'
    }).reset_index()

    return df_grouped

class Individual:
    def __init__(self, port, dShot=None, lCrank=None, lBreak=None):
        self.beh_config = {
            "dShot": round(dShot if dShot is not None else random.uniform(*param_ranges["dShot"]), 2),
            "lCrank": round(lCrank if lCrank is not None else random.uniform(*param_ranges["lCrank"]), 2),
            "lBreak": round(lBreak if lBreak is not None else random.uniform(*param_ranges["lBreak"]), 2)
        }
        self.port = port
        self.env = self.initialize_env(port)
        self.score = [None,None,None]
    
    def initialize_env(self, port):
        config_dict = config_dict_template.copy()
        config_dict['EnvConfig']['port'] = port
        env = GodotExperimentWrapper(config_dict)
        return env
    
    #def generate_behavior_case(self, agent="blue_agents"):
    #    case = {                            
    #            "beh_config": self.beh_config
    #           }
    #    
    #    return case
    
    def evaluate_fitness(self, enemies):        
        
        cases = []
        for enemy in enemies:            
                                    
            case_config =   {"AgentsConfig" : 
                                {   "blue_agents" : { "beh_config" : self.beh_config  },
                                    "red_agents"  : { "beh_config" : enemy.beh_config}
                                }
                            }                        
            cases.append(case_config)
                
        experimentConfig = {'runs_per_case': runs_per_case, 'cases': cases}
        

        self.env.send_sim_config(experimentConfig)
        results = self.env.watch_experiment()
        results_df = process_results(results) 
        
        results_df["score"] = results_df["killed_red"] - results_df["killed_blue"]
        
        self.score = [np.mean(results_df["score"]),  np.mean(results_df["killed_red"]), np.mean(results_df["killed_blue"])]
        
        return self.score

    def reset(self, dShot=None, lCrank=None, lBreak=None):
        self.beh_config = {
            "dShot": round(dShot if dShot is not None else random.uniform(*param_ranges["dShot"]), 2),
            "lCrank": round(lCrank if lCrank is not None else random.uniform(*param_ranges["lCrank"]), 2),
            "lBreak": round(lBreak if lBreak is not None else random.uniform(*param_ranges["lBreak"]), 2)
        }
        self.score = [None,None,None]
    
    def update(self, beh_config, score):
        self.beh_config = {
            "dShot": round(beh_config["dShot"], 2),
            "lCrank": round(beh_config["lCrank"], 2),
            "lBreak": round(beh_config["lBreak"], 2)
        }
        self.score = score.copy()

def generate_initial_population(size, start_port):
    population = []
    for i in range(size):
        individual = Individual(port=start_port + i)
        population.append(individual)
    return population

def save_population(population, filename):
    pop_data = [{"beh_config": ind.beh_config, "score": ind.score} for ind in population]
    with open(filename, 'w') as file:
        json.dump(pop_data, file, indent=4)

def load_population(filename, start_port=12500, limitNum = 100):
    with open(filename, 'r') as file:
        pop_data = json.load(file)
    population = []
    for i, data in enumerate(pop_data[:limitNum]):
        ind = Individual(port=start_port + i, 
                         dShot=data["beh_config"]["dShot"], 
                         lCrank=data["beh_config"]["lCrank"], 
                         lBreak=data["beh_config"]["lBreak"])
        ind.score = data.get("score")
        population.append(ind)
    population.sort(key=lambda x: x.score[0], reverse=True)
    return population

def evaluate_loaded_populations(population1, population2):
    
    update_score_values(population1, population2)
        
    print_individuals_table(population1, title="Population 1")
    
    #print("\nPopulation 2 results:")
    #print_individuals_table(population2, title="Population 2")

# Select parents using tournament selection
def tournament_selection(population, scores, k=3):
    selected = random.sample(list(zip(population, scores)), k)    
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected[0][0]

# Perform crossover between two parents
def crossover(parent1, parent2):
    child_config = {}
    for param in param_ranges.keys():
        child_config[param] = round(random.choice([parent1.beh_config[param], parent2.beh_config[param]]), 2)
    return child_config

# Perform mutation on an individual
def mutate(individual_beh, mutation_rate):
    for param in param_ranges.keys():
        if random.random() < mutation_rate:
            individual_beh[param] = round(random.uniform(*param_ranges[param]), 2)
    return individual_beh

# Update enemies list
def update_enemies_list(enemies_list, population):
    population.sort(key=lambda x: x.score[0], reverse=True)
    
    new_enemies = []
    for new_enemy in population:
        if check_unique(new_enemy.beh_config, [ind.beh_config for ind in enemies_list]):
            new_enemies.append(new_enemy)
        if len(new_enemies) == max_enemies_update:
            break                
    
    enemies_list.sort(key=lambda x: x.score[0], reverse=True)
    num_changes = 0
    
    for ind in new_enemies:
        if ind.score[0] > enemies_list[-1].score[0]:                    
            enemies_list[-1].update(ind.beh_config.copy(), ind.score.copy())
            enemies_list.sort(key=lambda x: x.score[0], reverse=True)
            num_changes += 1
    return num_changes

def update_population(_population, new_beh):
    for i, inv in enumerate(_population):
        inv.update(new_beh[i], [None,None,None])
        

def update_score_values(population, enemies_list):
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ind = {executor.submit(ind.evaluate_fitness, enemies_list): ind for ind in population}
        for future in concurrent.futures.as_completed(future_to_ind):
            ind = future_to_ind[future]
            try:
                ind.score = future.result()
            except Exception as exc:
                print(f'Individual generated an exception: {exc}')

def print_individuals_table(individuals, title="Individuals", limit = 10):
    individuals.sort(key=lambda x: x.score[0], reverse=True)
    print(f"{title}:")
    headers = ["Port", "dShot", "lCrank", "lBreak", "Score"]
    row_format = "{:<10} {:<10} {:<10} {:<10} {:<10}"
    print(row_format.format(*headers))
    print("-" * (len(headers) * 11))

    for ind in individuals[:limit]:
        row = [
            ind.port,
            f"{ind.beh_config['dShot']:.2f}",
            f"{ind.beh_config['lCrank']:.2f}",
            f"{ind.beh_config['lBreak']:.2f}",
            f"{ind.score[0]:.2f} ({ind.score[1]:.2f},{ind.score[2]:.2f})" if ind.score[0] is not None else "None"
        ]
        print(row_format.format(*row))
        

def round_params(beh_config):
    return {
        "dShot": round(beh_config["dShot"], 2),
        "lCrank": round(beh_config["lCrank"], 2),
        "lBreak": round(beh_config["lBreak"], 2)
    }

def check_unique(individual_beh, population_dicts):
    rounded_beh = round_params(individual_beh)
    
    for ind_dict in population_dicts:
        ind_beh = round_params(ind_dict)        
        if (ind_beh['dShot'] == rounded_beh['dShot'] and
            ind_beh['lCrank'] == rounded_beh['lCrank'] and
            ind_beh['lBreak'] == rounded_beh['lBreak']):
            return False    
    return True

def elite_to_dicts(elite_population):
    return [ind.beh_config for ind in elite_population]

# Run the genetic algorithm
def genetic_algorithm(save_filename=None, enemies_load = None):
    start_port = 12500
    population = generate_initial_population(population_size, start_port)
    
    if enemies_load != None:
        enemies_list = load_population(enemies_load, start_port + 500)
    else:
        enemies_list = generate_initial_population(enemies_size, start_port + population_size)
    
    for generation in range(generations):
        update_score_values(population, enemies_list)
        
        # Log the best fitness score of the current generation to W&B
        mean_fitness = np.mean([ind.score[0] for ind in population])
        min_fitness = min([ind.score[0] for ind in population])
        best_fitness = max([ind.score[0] for ind in population])
        
        wandb.log({"Mean_Score_Population": mean_fitness, "Max_Score_Population": best_fitness, "Min_Score_Population": min_fitness})
        
        if save_filename != None:
            save_population(population, save_filename + str(generation) + "_agents.json")   

        print(f"Generation {generation}: Best fitness = {max([ind.score[0] for ind in population])}")
        print_individuals_table(population, title="Population", limit=population_size)
        
        if generation % update_enemies_every == 0 and update_enemies_every != -1:
            update_score_values(enemies_list, enemies_list)
            num_changes = update_enemies_list(enemies_list, population)
            
            if save_filename != None:
                save_population(enemies_list, save_filename + str(generation) + "_enemies.json")   
            
            print_individuals_table(enemies_list, title="Enemies", limit=enemies_size) 
            
            # Log the best fitness score of the current generation to W&B
            mean_fitness = np.mean([ind.score[0] for ind in enemies_list])
            min_fitness = min([ind.score[0] for ind in enemies_list])
            best_fitness = max([ind.score[0] for ind in enemies_list])
            
            wandb.log({"Mean_Score_Enemies": mean_fitness, 
                        "Max_Score_Enemies": best_fitness, 
                        "Min_Score_Enemies": min_fitness,
                        "Changes Best Group": num_changes}) 
        
        population.sort(key=lambda x: x.score[0], reverse=True)
        elite_population = population[:elite_size]
        elite_population_dicts = elite_to_dicts(elite_population)
        available_agents = population[elite_size:]
        
        new_individuals = []
        while len(new_individuals) < len(available_agents):
            parent1 = tournament_selection(population, [ind.score[0] for ind in population], tournament_size)
            parent2 = tournament_selection(population, [ind.score[0] for ind in population], tournament_size)
            child = mutate(crossover(parent1, parent2), mutation_rate=mutation_rate)
            
            if check_unique(child, elite_population_dicts + [ind for ind in new_individuals]):
                new_individuals.append(child)
                
        
        
        update_population(available_agents, new_individuals)
    
    return population

#%%% Run GA
load_dir = ".\\GA_Results\\"
enemiesLoad = load_dir + "Enemies_Gen95.json"
name = "GA2_Phase2_ChangeAll"+ enemiesLoad

#enemiesLoad = None

# Initialize W&B run
wandb.init(project="BaselineGA")
# Log hyperparameters
wandb.config.update({
    "population_size": population_size,
    "enemies_size": enemies_size,
    "generations": generations,
    "mutation_rate": mutation_rate,
    "tournament_size": tournament_size,
    "elite_size": elite_size,
    "update_enemies_every": update_enemies_every,
    "runs_per_case": runs_per_case,
    "name":name
})
# Running the genetic algorithm
best_population = genetic_algorithm(save_filename="GA_Results/Run_0623_", enemies_load=enemiesLoad)

# Save the best parameters found
best_params = [ind.beh_config for ind in best_population]
with open('best_parameters.json', 'w') as file:
    json.dump(best_params, file, indent=4)

# Finish the W&B run
wandb.finish()


# %% Test Population

# LOAD SAVED AGENTS
#best_population = genetic_algorithm(save_filename='best_population.json')

ref50 = '.\GA_Results\RefEnemies_50Gen.json'
refLast = '.\GA_Results\Run_0623_6_enemies.json'

population1 = []
for n in range(50):
    file = f'.\GA_Results\Run_0623_{n}_agents.json'
    pop_n = load_population(file, start_port=12500 + n * 20, limitNum=50)
    population1.extend(pop_n[:3])

# ELIMINATE DUPLICATES
eval_individuals = []
for agent in population1:        
    if check_unique(agent.beh_config, [ind.beh_config for ind in eval_individuals]):
        eval_individuals.append(agent)


#%% #EVALUATE AGENTS       
# Load two populations
#population1 = load_population(refLast, start_port=13000)
#population2 = load_population('.\GA_Results\Run_0621_15_enemies2.json', start_port=13500)

print_individuals_table(eval_individuals[22:])
#print_individuals_table(population2)

i = 75
for ind in eval_individuals[i:]:
    
    print(f'Eval Ind {i}')
    # Evaluate loaded populations against each other
    evaluate_loaded_populations([eval_individuals[i]], eval_individuals)
    print_individuals_table([eval_individuals[i]])
    i = i + 1


# %%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data from CSV
df = pd.read_csv('top_agents.csv')

# Function to select the top N agents based on the final score
def select_top_agents(df, num_agents):
    top_agents = df.nlargest(num_agents, 'final_score')
    return top_agents

# Function to generate graphs and statistics
def analyze_diversity(agents):
    # Scatter plot for the behavior parameters
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection='3d')
    ax.scatter3D(agents['dShot'], agents['lCrank'], agents['lBreak'], c=agents['blue_kills'], cmap='viridis')
    ax.set_xlabel('dShot')
    ax.set_ylabel('lCrank')
    ax.set_zlabel('lBreak')
    plt.title('3D Scatter Plot of Top Agents by Behavior Parameters')
    plt.colorbar(ax.scatter3D(agents['dShot'], agents['lCrank'], agents['lBreak'], c=agents['blue_kills'], cmap='viridis'))
    plt.show()

    # Statistics
    stats = agents.describe()
    print("Statistics of Top Agents:")
    print(stats)
    
    # Pairplot
    pd.plotting.scatter_matrix(agents[['dShot', 'lCrank', 'lBreak']], alpha=0.8, figsize=(12, 12), diagonal='hist', marker='o', c=agents['final_score'], cmap='viridis')
    plt.suptitle('Pairplot of Behavior Parameters')
    plt.show()

# Select the top N agents
num_agents = 87  # You can change this value to select a different number of top agents
top_agents = select_top_agents(df, num_agents)

# Analyze the diversity of the top agents
analyze_diversity(top_agents)

# Save the top agents to a new CSV file
#top_agents.to_csv('top_agents.csv', index=False)
#print(f"Top {num_agents} agents saved to 'top_agents.csv'.")

# %%
