import heapq
import logging 
import numpy as np 
import random

from agent import Agent
from utils.schemas import * 

logging.basicConfig(
    level=logging.INFO,  
    format='%(message)s', 
    filename='simulation.log',
)

class Island:
    def __init__(self, agent_states: list[Agent], distance_matrix: np.ndarray) -> None:
        self.agent_states = agent_states # at i pos person with id i-1
        self.house_processed = [False] * 6 # whether the house has been processed during the day
        self.facts: list[Fact] = [] 
        self.timestamp = 1 # current day 
        self.distance_matrix = distance_matrix
        self.pending_visits: list[PendingVisit] = [] # heap

        logging.info('Initialized island with agents:')
        for agent in self.agent_states:
            logging.info(str(agent))
        logging.info('')

    # def log(self, ):
        # logging.info(f'DAY {self.timestamp}: ')

    def __getitem__(self, idx: int) -> Agent:
        return self.agent_states[idx]
        
    def print_facts(self):
        for fact in self.facts:
            print(fact)

    def add_facts(self, *facts: Fact) -> None:
        for fact in facts:
            self.facts.append(fact)
    
    def plan_visits(self) -> None:
        '''people plan their visits'''
        for person_id in range(6):
            # which house to visit and how many days until visit happens 
            house_to_visit, eta = self.agent_states[person_id].visit_decision(self.distance_matrix)

            if not np.isnan(eta):
                heapq.heappush(self.pending_visits, PendingVisit(self.timestamp + eta, person_id, house_to_visit))
                logging.info(f'DAY {self.timestamp}: Pending visit added: arrival: {self.timestamp + eta}, person: {person_id + 1}, house: {house_to_visit + 1}')
                
                start_trip_fact = ActionFact(self.timestamp, ActionType.START_TRIP, person_id + 1)

                self.add_facts(start_trip_fact)
                self.agent_states[person_id].update_knowledge(start_trip_fact)
                self.agent_states[person_id].traveling = True

    
    def day_visits(self) -> list[tuple[int, int]]:
        # returns house people will be in (at i pos i house visitors)
        house_visitors = []
        for _ in range(6):
            house_visitors.append([])

        for person_id in range(6):
            if not self.agent_states[person_id].traveling:
                house_visitors[self.agent_states[person_id].at].append(person_id)
                logging.info(f'DAY {self.timestamp}: Person {person_id + 1} stays at house {self.agent_states[person_id].at + 1}')

        while self.pending_visits and self.pending_visits[0].visit_day == self.timestamp:
            cur_visit = heapq.heappop(self.pending_visits)
            house_visitors[cur_visit.house_id].append(cur_visit.person_id)

            logging.info(f'DAY {self.timestamp}: Person {cur_visit.person_id + 1} came to house {cur_visit.house_id + 1}')
            
            end_trip_fact = ActionFact(self.timestamp, ActionType.CONCLUDE_TRIP, person_id)
            self.add_facts(end_trip_fact)
            self.agent_states[person_id].update_knowledge(end_trip_fact)

            self.agent_states[cur_visit.person_id].traveling = False
            self.agent_states[cur_visit.person_id].destination = -1
            self.agent_states[cur_visit.person_id].at = cur_visit.house_id
            
        return house_visitors

    
    def swap_house(self, person_1: int, person_2: int, person_3: int | None = None) -> tuple[int, int, int | None]:
        # returns houses of id_1, id_2, id_3 after the swap
        if not person_3:
            house_temp = self.agent_states[person_1].state.house
            self.agent_states[person_1].change_house(self.agent_states[person_2].state.house, self.timestamp)
            self.agent_states[person_2].change_house(house_temp, self.timestamp)

            self.add_swap_information(ActionType.HOUSE_SWAP, person_1, person_2)

        else:
            # NOTE: how do 3 people choose who to swap with?
            # clockwise or counterclockwise with equal probability 

            if random.random() < 0.5: # clockwise (houses: 2 -> 0, 0 -> 1, 1 -> 2)
                house_temp = self.agent_states[person_1].state.house # 0
                self.agent_states[person_1].change_house(self.agent_states[person_3].state.house, self.timestamp) # 2 -> 0
                self.agent_states[person_3].change_house(self.agent_states[person_2].state.house, self.timestamp) # 1 -> 2
                self.agent_states[person_2].change_house(house_temp, self.timestamp) # 0 -> 1

            else: # counterclockwise (houses: 1 -> 0, 2 -> 1, 0 -> 2)
                house_temp = self.agent_states[person_1].state.house # 0
                self.agent_states[person_1].change_house(self.agent_states[person_2].state.house, self.timestamp) # 1 -> 0
                self.agent_states[person_2].change_house(self.agent_states[person_3].state.house, self.timestamp) # 2 -> 1
                self.agent_states[person_3].change_house(house_temp, self.timestamp) # 0 -> 1

            self.add_swap_information(ActionType.HOUSE_SWAP, person_1, person_2, person_3)


    def add_swap_information(self, type: ActionType, person_1: int, person_2: int, person_3: int | None = None) -> None:
        if not person_3:
            swap_fact = ActionFact(self.timestamp, type, [person_1, person_2])

            if type == ActionType.HOUSE_SWAP:
                person1_fact = StaticFact(self.timestamp, person_id=person_1, house=self.agent_states[person_1].state.house)
                person2_fact = StaticFact(self.timestamp, person_id=person_2, house=self.agent_states[person_2].state.house)
            elif type == ActionType.PET_SWAP:
                person1_fact = StaticFact(self.timestamp, person_id=person_1, pet=self.agent_states[person_1].state.pet)
                person2_fact = StaticFact(self.timestamp, person_id=person_2, pet=self.agent_states[person_2].state.pet)

            self.agent_states[person_1].update_knowledge(swap_fact, person1_fact, person2_fact)
            self.agent_states[person_2].update_knowledge(swap_fact, person1_fact, person2_fact)

            self.add_facts(swap_fact, person1_fact, person2_fact)

        else:
            swap_fact = ActionFact(self.timestamp, type, [person_1, person_2, person_3])

            if type == ActionType.HOUSE_SWAP:
                person1_fact = StaticFact(self.timestamp, person_id=person_1, house=self.agent_states[person_1].state.house)
                person2_fact = StaticFact(self.timestamp, person_id=person_2, house=self.agent_states[person_2].state.house)
                person3_fact = StaticFact(self.timestamp, person_id=person_3, house=self.agent_states[person_3].state.house)
            elif type == ActionType.PET_SWAP:
                person1_fact = StaticFact(self.timestamp, person_id=person_1, pet=self.agent_states[person_1].state.pet)
                person2_fact = StaticFact(self.timestamp, person_id=person_2, pet=self.agent_states[person_2].state.pet)
                person3_fact = StaticFact(self.timestamp, person_id=person_3, pet=self.agent_states[person_3].state.pet)

            person1_fact = StaticFact(self.timestamp, person_id=person_1, house=self.agent_states[person_1].state.house)
            person2_fact = StaticFact(self.timestamp, person_id=person_2, house=self.agent_states[person_2].state.house)
            person3_fact = StaticFact(self.timestamp, person_id=person_3, house=self.agent_states[person_3].state.house)

            self.agent_states[person_1].update_knowledge(swap_fact, person1_fact, person2_fact, person3_fact)
            self.agent_states[person_2].update_knowledge(swap_fact, person1_fact, person2_fact, person3_fact)
            self.agent_states[person_3].update_knowledge(swap_fact, person1_fact, person2_fact, person3_fact)

            self.add_facts(swap_fact, person1_fact, person2_fact, person3_fact)

        logging.info(f'DAY {self.timestamp}: {type.value} between {person_1, person_2, person_3}')
            

    def swap_pet(self, person_1: int, person_2: int, person_3: int | None = None) -> tuple[int, int, int | None]:
        if not person_3:
            pet_temp = self.agent_states[person_1].state.pet
            self.agent_states[person_1].change_pet(self.agent_states[person_2].state.pet, self.timestamp)
            self.agent_states[person_2].change_pet(pet_temp, self.timestamp)

            self.add_swap_information(ActionType.PET_SWAP, person_1, person_2)
        else:
            # NOTE: how do 3 people choose who to swap with?
            # clockwise or counterclockwise with equal probability 

            if random.random() < 0.5: # clockwise (pets: 2 -> 0, 0 -> 1, 1 -> 2)
                pet_temp = self.agent_states[person_1].state.pet # 0
                self.agent_states[person_1].change_pet(self.agent_states[person_3].state.pet, self.timestamp) # 2 -> 0
                self.agent_states[person_3].change_pet(self.agent_states[person_2].state.pet, self.timestamp) # 1 -> 2
                self.agent_states[person_2].change_pet(pet_temp, self.timestamp) # 0 -> 1

            else: # counterclockwise (pets: 1 -> 0, 2 -> 1, 0 -> 2)
                pet_temp = self.agent_states[person_1].state.pet # 0
                self.agent_states[person_1].change_pet(self.agent_states[person_2].state.pet, self.timestamp) # 1 -> 0
                self.agent_states[person_2].change_pet(self.agent_states[person_3].state.pet, self.timestamp) # 2 -> 1
                self.agent_states[person_3].change_pet(pet_temp, self.timestamp) # 0 -> 1

            self.add_swap_information(ActionType.PET_SWAP, person_1, person_2, person_3)

    def process_house(self, house_id: int, *visitor_ids) -> None:
        house_swappers = []
        pet_swappers = []

        for visitor in visitor_ids:
            if self.agent_states[visitor].swap_pet:
                pet_swappers.append(visitor)

            if self.agent_states[visitor].swap_house:
                house_swappers.append(visitor)

        logging.info(f'DAY {self.timestamp}: Processing house {house_id + 1}')
        logging.info(f'DAY {self.timestamp}: Pet swappers at house {house_id + 1}: {[x + 1 for x in pet_swappers]}')
        logging.info(f'DAY {self.timestamp}: House swappers at house {house_id + 1}: {[x + 1 for x in house_swappers]}')

        if len(house_swappers) > 1:
            self.swap_house(*house_swappers)
        if len(pet_swappers) > 1:
            self.swap_pet(*pet_swappers)

        self.house_processed[house_id] = True
    
    def day(self) -> None:
        logging.info(f'DAY {self.timestamp} BEGAN')

        visits = self.day_visits() # who will be in which house

        if visits:
            self.house_processed = [False] * 6

            for house_id in range(6):
                logging.info(f'DAY {self.timestamp}: people {[v + 1 for v in visits[house_id]]} at house {house_id + 1}')

                if len(visits[house_id]) < 2:
                    self.house_processed[house_id] = True
                    continue # 0 or 1 person in house
                else:
                    self.process_house(house_id, *visits[house_id])

        logging.info(f'BY THE END OF DAY {self.timestamp}')
        for person_id in range(6):
            logging.info(f'Person {person_id + 1} ' + self.agent_states[person_id].dynamic_state_repr)
        logging.info(f'DAY {self.timestamp} ENDED')
        logging.info('')

        self.timestamp += 1
        self.plan_visits()