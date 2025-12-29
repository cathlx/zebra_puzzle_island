import numpy as np 
import random

from utils.schemas import * 

class Agent:
    def __init__(self, 
                 state: PersonState,
                 action_probs: ActionProbabilities) -> None:
        self.state = state
        self.action_probs = action_probs

        self.known_facts: list[Fact] = []

        self.at: int = self.state.house.id - 1 # which house stays in 
        self.traveling: bool = False # is traveling between houses
        self.destination: int = -1 # if traveling, where to

        # self.update_knowledge(StaticFact(0, *self.state))

    @property
    def house_id(self) -> int:
        '''house id in range [0, 5]'''
        return self.state.house.id - 1

    def visit_decision(self, distance_matrix: np.ndarray) -> tuple[int, int]:
        '''choose which house (0 - 5) to visit, give eta in days'''
        if self.traveling:
            return -1, np.nan
        
        reachable_indices = np.where((~np.isnan(distance_matrix[self.at])) & (self.action_probs.house_visit > 0))[0]

        if len(reachable_indices) > 0:
            house_to_visit = int(random.choices(reachable_indices, self.action_probs.house_visit[reachable_indices])[0])
            eta = int(distance_matrix[self.at][house_to_visit])
            return house_to_visit, eta if house_to_visit != self.at else np.nan
        else:
            return -1, np.nan
        
    def start_trip(self, house_to: int):
        self.traveling = True
        self.destination = house_to
    
    def end_trip(self, house_to: int) -> None:
        self.at = house_to
        self.traveling = False
        self.destination = -1
    
    @property
    def swap_pet(self) -> bool:
        '''choose whether to swap pet'''
        return random.random() < self.action_probs.swap_pet
    
    @property
    def swap_house(self) -> bool:
        '''choose whether to swap house'''
        return random.random() < self.action_probs.swap_house
    
    def swap(self, type: ActionType, item, timestamp):
        match type:
            case ActionType.HOUSE_SWAP:
                self.change_house(item, timestamp)
            case ActionType.PET_SWAP:
                self.change_pet(item, timestamp)
            case _:
                raise ValueError('Unknown swap type')

    def change_house(self, house: House, timestamp: int):
        self.state.house = house
        # self.update_knowledge(StaticFact(timestamp, *self.state))

    def change_pet(self, pet: Pet, timestamp: int):
        self.state.pet = pet
        # self.update_knowledge(StaticFact(timestamp, *self.state))

    def update_knowledge(self, *facts: Fact):
        for fact in facts:
            self.known_facts.append(fact)

    def print_facts(self) -> None:
        for fact in self.known_facts:
            print(fact)

    @property
    def dynamic_state_repr(self):
        return f'staying at house {self.at + 1}' * (not self.traveling) + f'traveling from house {self.at + 1} to house {self.destination + 1}' * self.traveling

    def __str__(self):
        return (f'{self.state.nationality.value} lives in {self.state.house.color.value} house {self.state.house.id}, '
                f'drinks {self.state.drink.value}, smokes {self.state.cigarettes.value}, has a {self.state.pet.value} '
                f'swaps house with probabilty {self.action_probs.swap_house}, swaps pet with probability {self.action_probs.swap_pet}')
    
    def to_dict(self):
        return {
            'house': self.state.house.id,
            'color': self.state.house.color.value,
            'nationality': self.state.nationality.value,
            'drink': self.state.drink.value,
            'cigarettes': self.state.cigarettes.value,
            'pet': self.state.pet.value
        }