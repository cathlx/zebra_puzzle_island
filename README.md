# Dynamic Zebra Puzzle Island Simulation

A simulation of agents (people) living on an island with houses, traveling between locations, and interacting through meetings and exchanges.

## Project Structure

```
configs/
├── example_files/                 # Configuration files for experiments with schema files 
│   ├── aco_1_rational.yaml        # ACO agent with rational behavior
│   └── random_baseline.yaml       # Random baseline configuration
├── generated/                     # Configurations for experiments without schema files 
├── island_schemas/                # Island schema data
│   ├── actions.csv                # Agents action probabilities
│   ├── distances.csv              # Distance matrix
│   └── people.csv                 # People/agent states
└── config_manager.py              # Configuration management

scripts/
├── csv_handling.py                # CSV file utilities (input/output)
├── experiments.py                 # Experiment management
├── main.py                        # Main entry point (WIP)
├── setting.py                     # Simulation setup
└── src/                           # Core simulation modules
    ├── agent.py                   # Agent implementation
    ├── island.py                  # Island environment
    └── schemas.py                 # Data schemas

notebooks/
├── tryouts.ipynb                  # Experimental notebooks
└── example.ipynb                  # Usage examples

results/                           # Experiment outputs (auto-generated)

.gitignore
README.md
requirements.txt
```

## Usage

### Running an Experiment

```python
from scripts.experiments import ExperimentManager

# Initialize with configuration file
experiment = ExperimentManager('configs/example_files/aco_1_rational.yaml')

# Run the experiment
output_dir = experiment.run_experiment(
    yaml_representation=True,
    save_results=True,
    save_island_csv=False
)

# Plot results
experiment.plot_results(figsize=(12, 8))
```

### Creating Custom Configurations

```python
from configs.config_manager import Config

# Create a new configuration
config = Config(
    experiment_name="my_experiment",
    description="Testing mixed strategies",
    simulation=SimulationConfig(
        num_agents=10,
        num_days=1000,
        random_seed=123
    ),
    strategies=StrategiesConfig(
        mandatory_return=True,
        visit_strategies={0: 'aco', 1: 'aco', **{i: 'random' for i in range(2, 10)}}
    )
)

# Save to YAML
config.to_yaml('configs/generated/my_experiment.yaml')
```

Or use YAML configuration file (see examples in `configs/`)

### Using the Command Line (WIP)

## Input Data Requirements

### 1. People CSV (`people.csv`)
Contains initial states of agents/people on the island.

### 2. Actions CSV (`actions.csv`)
Probability distributions for different actions agents can take.

### 3. Distances CSV (`distances.csv`)
Distance matrix between different locations on the island.

If not specified, will be generated automatically. For reuse set `manager.run_experiment(save_island_csv=True)`

For accepted format see examples in `configs/island_schemas/`

## Outputs

Each experiment generates:
- `results/<experiment_name>_<timestamp>/`
  - `metrics.csv`: Tracked metrics (saving interval is configurable)
  - `setting.yaml`: Complete experiment configuration in human-readable format
  - `facts/`: Final state knowledge per agent and for island as a whole (if enabled)
  - `island_schemas/`: 3 csv files specifying an island (see above) (if enabled)
  - Visualizations (when using `plot_results()`)

## Available Strategies

1. **ACO (Ant Colony Optimization)**: Agents deposit and follow pheromone trails
2. **Random**: Agents explore randomly (according to spicified probabilities) without memory
3. **Mixed**: Different strategies per agent (configurable)
4. **Mandatory return home after every visit**: WIP
5. TBC

## Metrics Tracked

- `total_awareness`: Total unique facts known by all agents
- `agentX_awareness`: Number of facts known by agent X
- Custom metrics can be added via configuration (TBC)

## Core Components

### Agent Class (`agent.py`)

The `Agent` class represents individuals in the simulation with:

**Key Attributes:**
- `state`: Current state (house, nationality, drink, cigarettes, pet)
- `action_probs`: Probabilities for different actions (swapping house/pet, choosing each house to travel to)
- `known_facts`: List of facts the agent knows
- `traveling`: Whether the agent is currently traveling
- `destination`: Target house when traveling

**Main Methods:**
- `visit_decision()`: Decides which house to visit based on reachability and speicified strategy
- `start_trip()`: Begins travel to a destination (sets flags)
- `end_trip()`: Completes travel (sets flags)
- `swap()`: Handles house or pet swaps
- `update_knowledge()`: Adds new facts to agent's knowledge


### Island Class (`island.py`)

The `Island` class manages the simulation environment:

**Key Features:**
- Manages multiple agents and their interactions
- Tracks time and events
- Handles travel scheduling using a priority queue
- Manages fact propagation
- Processes daily interactions

**Main Methods:**
- `plan_visits()`: Plans future trips for all agents
- `day_visits()`: Processes visits for the current day
- `process_house()`: Handles interactions at a specific house
- `swap()`: Executes house or pet swaps between agents
- `day()`: Advances simulation by one day

**Example:**
```python
from island import Island

# Initialize island with agents and distance matrix
island = Island(agents, distance_matrix)

# Run multiple days
for _ in range(100):
    island.day()
```

## Simulation Flow

1. **Initialization**: Create agents with initial states and probabilities
2. **Daily Cycle**:
   - Process completed trips
   - Handle house meetings and interactions
   - Execute swaps based on probabilities
   - Update knowledge bases
   - Plan future trips
3. **Time Advancement**: Increment timestamp and repeat