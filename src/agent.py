import numpy as np 
import random

from src.schemas import * 

class Agent:
    def __init__(self, 
                 state: PersonState,
                 action_probs: ActionProbabilities,
                 strategy: VisitStrategy = VisitStrategy.RANDOM) -> None:
        self.state = state
        self.action_probs = action_probs
        self.strategy = strategy

        self.known_facts: list[Fact] = []

        self.at: int = self.state.house.id - 1 # which house stays in 
        self.traveling: bool = False # is traveling between houses
        self.destination: int = -1 # if traveling, where to
        self.must_return = False # must return home 

        self.pheromone_deposit = 1.0 # strength of pheromone left 

        # self.update_knowledge(StaticFact(0, *self.state))

    @property
    def house_id(self) -> int:
        '''house id in range [0, NUM_PEOPLE]'''
        return self.state.house.id - 1

    def visit_decision(self, distance_matrix: np.ndarray, pheromone_matrix: np.ndarray | None, mandatory_return: bool = False) -> tuple[int, int]:
        '''choose which house (0 - NUM_PEOPLE) to visit, give eta in days'''
        if self.traveling:
            return -1, np.nan
        
        if mandatory_return and self.must_return:
            self.must_return = False
            return self.house_id, int(distance_matrix[self.at][self.house_id])
        
        # reachable_indices = np.where((~np.isnan(distance_matrix[self.at])) & (self.action_probs.house_visit > 0))[0]
        # reachable_indices = reachable_indices[reachable_indices != self.at]

        reachable_indices = [h for h in range(6) if h != self.at and not np.isnan(distance_matrix[self.at, h])]

        if not reachable_indices:
            return -1, np.nan
        
        visit_probabilities = None
        
        match self.strategy:
            case VisitStrategy.RANDOM:
                visit_probabilities = self.action_probs.house_visit[reachable_indices]
                if not np.sum(visit_probabilities) > 0:
                    return -1, np.nan
            case VisitStrategy.ACO:
                attractiveness = np.array([np.sum(pheromone_matrix[self.at, pos_next_house, :]) for pos_next_house in reachable_indices])
                if sum(attractiveness) > 0:
                    visit_probabilities = attractiveness / sum(attractiveness)
                else:
                    visit_probabilities = np.ones_like(reachable_indices) / len(reachable_indices)
            case _:
                raise ValueError('Unknown strategy type')
        
        house_to_visit = int(random.choices(reachable_indices, visit_probabilities)[0])
        eta = int(distance_matrix[self.at][house_to_visit])
        self.must_return = True
        return house_to_visit, eta
        
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
        self.must_return = True
        # self.update_knowledge(StaticFact(timestamp, *self.state))

    def change_pet(self, pet: Pet, timestamp: int):
        self.state.pet = pet
        # self.update_knowledge(StaticFact(timestamp, *self.state))

    def update_knowledge(self, *facts: Fact):
        for fact in facts:
            self.known_facts.append(fact)

    def log_known_facts(self, filepath: str = 'output/'):
        with open(filepath, 'w') as file:
            for fact in self.known_facts:
                file.write(repr(fact))
                file.write('\n')

    def __str__(self):
        return (f'''
                Person {self.state.id}

                NON-PERMANENT PROPERTIES:
                House: {self.state.house.color.value} (ID: {self.state.house.id})
                Pet: {self.state.pet.value}

                PERMANENT PROPERTIES:
                Nationality: {self.state.nationality.value}
                Drink: {self.state.drink.value}
                Cigarettes: {self.state.cigarettes.value}

                ACTION PROBABILITIES:
                House visits:\n    {'\n    '.join(str(house + 1) + ' - ' + str(prob) for house, prob in enumerate(self.action_probs.house_visit))}
                Probability of house swap: {self.action_probs.swap_house}
                Probability of pet swap:  {self.action_probs.swap_pet}

                DYNAMIC STATE:
                {f'At: {self.at + 1}' * (not self.traveling) + f'Traveling from house {self.at + 1} to house {self.destination + 1}' * self.traveling}

                STRATEGIES:
                Visit: {self.strategy.value}

                ''')
    
        # return f'{self.id}: {self.house.color.value}|{self.nationality.value}|{self.drink.value}|{self.cigarettes.value}|{self.pet.value}'
    
    def to_dict(self):
        return {
            'id': self.state.house.id,
            'house_color': self.state.house.color.value,
            'nationality': self.state.nationality.value,
            'drink': self.state.drink.value,
            'cigarettes': self.state.cigarettes.value,
            'pet': self.state.pet.value,
            'action_probs': {
                'house_visit': dict(zip(range(1, len(self.action_probs.house_visit) + 1), self.action_probs.house_visit.round(2).tolist())),
                'swap_house': round(self.action_probs.swap_house, 2),
                'swap_pet': round(self.action_probs.swap_pet, 2)
            },
            'strategy': self.strategy.value,
            'pheromone_deposit': self.pheromone_deposit
        }
    
