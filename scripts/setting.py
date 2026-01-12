import numpy as np
import random

from configs.config_manager import Config 

from scripts.csv_handling import (
    load_action_probabilities_from_csv, 
    load_person_states_from_csv, 
    load_distance_matrix_from_csv, 
    agent_states_to_csv,
    action_probs_to_csv,
    distance_matrix_to_csv
)

from src.agent import Agent
from src.island import Island
from src.schemas import * 

NUM_PEOPLE = 6

def get_distance_matrix(filepath: str | None = None, low: int = 1, high: int = 5, num_people: int = 6, nan_probability: float = 0.1):
    if filepath:
        return load_distance_matrix_from_csv(filepath)
    
    distance_matrix = np.random.randint(1, 5, size=(NUM_PEOPLE, NUM_PEOPLE))
    np.fill_diagonal(distance_matrix, 0)
    distance_matrix = ((distance_matrix + distance_matrix.T) / 2).astype(int).astype(float)

    set_to_nan = (np.random.random(size=(NUM_PEOPLE, NUM_PEOPLE)) < nan_probability) & ~np.eye(NUM_PEOPLE, dtype=bool)
    set_to_nan = ((set_to_nan + set_to_nan.T) / 2).astype(bool)

    distance_matrix[set_to_nan] = np.nan
    return distance_matrix

def get_agent_states(filepath: str | None = None) -> list[PersonState]:
    if filepath:
        return load_person_states_from_csv(filepath)
    
    HOUSE_COLORS = list(Color)
    NATIONALITIES = list(Nationality)
    DRINKS = list(Drink)
    CIGARETTES = list(Cigarettes)
    PETS = list(Pet)

    properties = [HOUSE_COLORS, NATIONALITIES, DRINKS, CIGARETTES, PETS]
    for property_lst in properties:
        random.shuffle(property_lst)

    states = []
    for i, (house_color, nationality, drink, cigarette, pet) in enumerate(
        zip(HOUSE_COLORS, NATIONALITIES, DRINKS, CIGARETTES, PETS)
    ):
        person_state = PersonState(
            id=i+1,
            house=House(i+1, house_color),
            nationality=nationality,
            drink=drink,
            cigarettes=cigarette,
            pet=pet
        )
        states.append(person_state)

    return states

def get_action_probs(filepath: str | None = None) -> dict[Nationality, ActionProbabilities]:
    if filepath:
        return load_action_probabilities_from_csv(filepath)
    
    return {nationality: ActionProbabilities(
    house_visit=np.random.dirichlet(np.ones(NUM_PEOPLE)),
    swap_house = np.random.rand(),
    swap_pet=np.random.rand()) for nationality in Nationality}

def get_visit_strategies(strategies: dict[int, str]) -> list[VisitStrategy]:
    visit_strategies = []
    for strategy in strategies.values():
        match strategy:
            case 'random':
                visit_strategies.append(VisitStrategy.RANDOM)
            case 'aco':
                visit_strategies.append(VisitStrategy.ACO)
            case _:
                raise ValueError('Unknown visit strategy')
    return visit_strategies

def create_agents(person_states: list[PersonState], 
                  action_probabilities: dict[Nationality, ActionProbabilities],
                  strategies: list[VisitStrategy]) -> list[Agent]:
    agents = []
    
    for i, person_state in enumerate(person_states):
        agent = Agent(
            state=person_state,
            action_probs=action_probabilities.get(person_state.nationality),
            strategy=strategies[i]
        )
        agents.append(agent)
    
    return agents

def create_island(people_csv: str | None = None, 
                  actions_csv: str | None = None, 
                  distance_csv: str | None = None, 
                  strategy: str = 'random',
                  mandatory_return: bool = False) -> Island:
    states = get_agent_states(people_csv)
    probs = get_action_probs(actions_csv)
    strategies = get_visit_strategies(strategy)
    agents = create_agents(states, probs, strategies)
    distance_matrix = get_distance_matrix(distance_csv)
    return Island(agents, distance_matrix, mandatory_return)

def get_island_from_cfg(cfg: Config, save_csv: bool = False) -> Island:
    states = get_agent_states(cfg.input.people_states)
    probs = get_action_probs(cfg.input.action_probs)
    strategies = get_visit_strategies(cfg.strategies.visit_strategies)
    agents = create_agents(states, probs, strategies)

    distance_matrix = get_distance_matrix(cfg.input.distance_matrix)

    if save_csv: 
        island_schema_path = cfg.get_output_directory() / 'island_schemas'
        island_schema_path.mkdir(exist_ok=True)

        agent_states_to_csv(states, island_schema_path / 'people.csv')
        action_probs_to_csv(probs, states, island_schema_path / 'actions.csv')
        distance_matrix_to_csv(distance_matrix, states, island_schema_path / 'distances.csv')

    return Island(agents, distance_matrix, mandatory_return=cfg.strategies.mandatory_return, verbose=cfg.simulation.verbose)