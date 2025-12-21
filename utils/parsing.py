import csv
import numpy as np 
import pandas as pd 

from agent import Agent
from island import Island
from utils.schemas import * 

def parse_person_state_from_row(id: int, row: dict) -> PersonState:
    """
    Parse a CSV row dictionary into PersonState
    Expected columns: H, C, I, D, S, P
    """
    house_id = int(row['H'])
    color = Color(row['C'])
    
    house = House(id=house_id, color=color)
    
    return PersonState(
        id=id, 
        house=house,
        nationality=Nationality(row['I']),
        drink=Drink(row['D']),
        cigarettes=Cigarettes(row['S']),
        pet=Pet(row['P'])
    )

def load_person_states_from_csv(file_path: str) -> list[PersonState]:
    """
    Load PersonState objects from CSV file
    """
    person_states = []
    
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        
        for i, row in enumerate(reader):
            person_state = parse_person_state_from_row(i, row)
            person_states.append(person_state)
    
    return person_states

def parse_csv_to_action_probs(csv_file: str) -> list[ActionProbabilities]:
    """
    Parse CSV file into ActionProbabilities objects
    
    Args:
        csv_file: Path to the CSV file
    
    Returns:
        List of ActionProbabilities objects
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # If ID was saved as index, it will be the first column without a name
    # Let's handle both cases (with and without index)
    if 'ID' not in df.columns and df.columns[0] == 'Unnamed: 0':
        df = df.rename(columns={'Unnamed: 0': 'ID'})
    
    action_probs_list = []
    
    for _, row in df.iterrows():
        # Extract house visit probabilities (columns 1-6)
        choose_house = [
            float(row['1']),
            float(row['2']), 
            float(row['3']),
            float(row['4']),
            float(row['5']),
            float(row['6'])
        ]
        
        # Extract swap probabilities
        swap_house = float(row['PHouseExch']) / 100.0
        swap_pet = float(row['PPetExch']) / 100.0
        
        # Create ActionProbabilities object
        action_probs = ActionProbabilities(
            choose_house=choose_house,
            swap_house=swap_house,
            swap_pet=swap_pet
        )
        
        action_probs_list.append(action_probs)
    
    return action_probs_list

def parse_action_probabilities_from_row(row: dict) -> ActionProbabilities:
    """
    Parse a CSV row into ActionProbabilities
    """
    visit_house = [
        float(row['1']) / 100.0,
        float(row['2']) / 100.0, 
        float(row['3']) / 100.0,
        float(row['4']) / 100.0,
        float(row['5']) / 100.0,
        float(row['6']) / 100.0
    ]
        
    swap_house = float(row['PHouseExch']) / 100.0
    swap_pet = float(row['PPetExch']) / 100.0
    
    return  ActionProbabilities(
        visit_house=visit_house,
        swap_house=swap_house,
        swap_pet=swap_pet
    )

# def parse_action_probabilities_from_row(row: dict) -> ActionProbabilities:
#     """
#     Parse a CSV row into ActionProbabilities
#     Expected columns: ID;I;PLeft;PRight;PHome;PHouseExch;PPetExch
#     """
#     return ActionProbabilities(
#         turn_left=float(row['PLeft']) / 100.0,
#         turn_right=float(row['PRight']) / 100.0,
#         stay_home=float(row['PHome']) / 100.0,
#         swap_house=float(row['PHouseExch']) / 100.0,
#         swap_pet=float(row['PPetExch']) / 100.0
#     )

def load_action_probabilities_from_csv(file_path: str) -> dict:
    """
    Load ActionProbabilities from CSV, keyed by nationality
    """
    probabilities = {}
    
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        
        for row in reader:
            nationality = Nationality(row['I'])
            action_probs = parse_action_probabilities_from_row(row)
            probabilities[nationality] = action_probs
    
    return probabilities

def create_agents(person_states: list[PersonState], 
                  action_probabilities: dict[Nationality, ActionProbabilities]) -> list[Agent]:
    agents = []
    
    for person_state in person_states:
        agent = Agent(
            state=person_state,
            action_probs=action_probabilities.get(person_state.nationality)
        )
        agents.append(agent)
    
    return agents

def parse_distance_csv(csv_file: str) -> np.ndarray:
    """
    Parse CSV file into a symmetric distance matrix where position [i,j] 
    represents the distance between house i+1 and house j+1
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        numpy array of shape (6, 6) with distances between houses
    """

    df = pd.read_csv(csv_file)
    distance_matrix = np.full((6, 6), np.nan)
    
    for idx, row in df.iterrows():
        color = row['Color']
        for house_num in range(1, 7):
            distance = row[str(house_num)]
            if not pd.isna(distance):
                house_idx = house_num - 1

                distance_matrix[idx, house_idx] = distance
                distance_matrix[house_idx, idx] = distance
    
    np.fill_diagonal(distance_matrix, 0)
    return distance_matrix

def create_island(people_csv: str = 'data/zebra-people.csv', strategies_csv: str = 'data/zebra-strategies.csv', distance_csv: str = 'data/house-distances.csv'):
    states = load_person_states_from_csv(people_csv)
    probs = load_action_probabilities_from_csv(strategies_csv)
    agent_states = create_agents(states, probs)
    distance_matrix = parse_distance_csv(distance_csv)
    return Island(agent_states, distance_matrix)