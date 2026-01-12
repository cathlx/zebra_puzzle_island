import csv
import numpy as np 
import pandas as pd 

from src.agent import Agent
from src.island import Island
from src.schemas import * 

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
    house_visit = np.array([
        float(row['1']) / 100.0,
        float(row['2']) / 100.0, 
        float(row['3']) / 100.0,
        float(row['4']) / 100.0,
        float(row['5']) / 100.0,
        float(row['6']) / 100.0
    ])
        
    swap_house = float(row['PHouseExch']) / 100.0
    swap_pet = float(row['PPetExch']) / 100.0
    
    return ActionProbabilities(
        house_visit=house_visit,
        swap_house=swap_house,
        swap_pet=swap_pet
    )

def load_action_probabilities_from_csv(file_path: str) -> dict:
    """
    Load ActionProbabilities from CSV, keyed by nationality
    """
    probabilities = {}
    
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        
        for row in reader:
            nationality = Nationality(row['I'])
            action_probs = parse_action_probabilities_from_row(row)
            probabilities[nationality] = action_probs
    
    return probabilities

def load_distance_matrix_from_csv(csv_file: str) -> np.ndarray:
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


def agent_states_to_csv(person_states: list[PersonState], output_path: str = 'people_states.csv') -> None:
    """
    Convert list of PersonState objects to CSV with specific format.
    
    Format: H;C;I;D;S;P
    Where:
        H: House ID
        C: House Color
        I: Nationality
        D: Drink
        S: Cigarettes
        P: Pet
    
    Args:
        person_states: List of PersonState objects
        output_path: Path to save CSV file
    """
    
    header = ['H', 'C', 'I', 'D', 'S', 'P']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(header)
        
        for person in person_states:
            row = [
                str(person.house.id),              # H: House ID
                person.house.color.value,          # C: House Color
                person.nationality.value,          # I: Nationality
                person.drink.value,                # D: Drink
                person.cigarettes.value,           # S: Cigarettes
                person.pet.value                   # P: Pet
            ]
            writer.writerow(row)

def action_probs_to_csv(action_probs: dict[Nationality, ActionProbabilities], states: list[PersonState], output_path: str = 'actions.csv') -> None:
    header = ['ID','I','1','2','3','4','5','6','PHouseExch','PPetExch']

    id_to_nationality = {p.id:p.nationality for p in states}
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(header)
        
        for id in id_to_nationality:
            probs = action_probs[id_to_nationality[id]]

            house_visits = [round(p * 100, 2) for p in probs.house_visit]
            house_swap = round(probs.swap_house * 100, 2)
            pet_swap = round(probs.swap_pet * 100, 2)

            row = [
                id,                      # ID
                id_to_nationality[id].value,            # I (Nationality)
                *house_visits,                # 1-6 (House visit probabilities)
                house_swap,                   # PHouseExch
                pet_swap                      # PPetExch
            ]
            
            writer.writerow(row)

def distance_matrix_to_csv(distance_matrix: np.ndarray, states: list[PersonState], output_path: str = 'distances.csv') -> None:
    df = pd.DataFrame(distance_matrix, columns=range(1, len(distance_matrix) + 1))
    df.insert(0, 'Color', [p.house.color.value for p in states])
    
    def format_value(x):
        if pd.isna(x):
            return ''
        elif x == 0.0:
            return '0.0'
        else:
            return f'{x:.1f}' if x % 1 != 0 else f'{int(x)}.0'
    
    for col in df.columns[1:]:  
        df[col] = df[col].apply(format_value)
    
    df.to_csv(output_path, index=False)