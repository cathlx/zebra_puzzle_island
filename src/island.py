import heapq
import numpy as np 
import random

from pathlib import Path
from typing import Generator

from src.agent import Agent
from src.schemas import * 

# TODO: main to run experiments 

# TODO: rewrite island to config (use DictConfig)
# TODO: add end trip facts for people in meeting 
# TODO: improve swap logic
# TODO: improve code for swap 

class Island:
    def __init__(self, 
                 agents: list[Agent], 
                 distance_matrix: np.ndarray, 
                 mandatory_return: bool = False,
                 verbose: bool = False) -> None:
        self.agents = agents # at i pos person with id i-1
        self.num_people = len(agents)
        self.distance_matrix = distance_matrix
        self.mandatory_return = mandatory_return

        self.timestamp = 0 # current day 
        self.meetings_today = 0

        self.facts: list[Fact] = [] 
        self.trips: list[Trip] = [] # heap

        # ACO 
        self.pheromones = np.zeros((len(agents), len(agents), len(agents)))
        self.exp_decay_time = 7 # time for pheromone to decay by factor e (in days)

        # num of known facts
        self.awareness = []
        self.agent_awareness = [[] for _ in range(len(agents))]

        self.verbose = verbose


    # FACTS HANDLING
    
    def add_facts(self, *facts: Fact) -> None:
        for fact in facts:
            self.facts.append(fact)
        
    def log_known_facts(self, filepath: Path = 'island_facts.txt') -> None:
        with open(filepath, 'w') as file:
            for fact in self.facts:
                file.write(repr(fact))
                file.write('\n')
    
    def log_knowledge(self, dir: Path = 'output') -> None:
        self.log_known_facts(dir / 'island_facts.txt')
        for i in range(self.num_people):
            self.agents[i].log_known_facts(dir / f'person{i + 1}_known_facts.txt')
    

    # VISIT HANDLING

    def plan_next_visits(self) -> None:
        for person_id in range(self.num_people):
            house_to_visit, eta = self.agents[person_id].visit_decision(self.distance_matrix, self.pheromones, self.mandatory_return)

            if not np.isnan(eta):
                cur_trip = Trip(self.timestamp + eta, self.timestamp, person_id, self.agents[person_id].at, house_to_visit)
                heapq.heappush(self.trips, cur_trip)

                self.agents[cur_trip.person_id].start_trip(cur_trip.house_to)
                self._handle_trip_fact(cur_trip, ActionType.START_TRIP)

    def get_day_visits(self) -> list[tuple[int, int]]:
        house_visitors = [[] for _ in range(self.num_people)]

        for person_id in range(self.num_people):
            if not self.agents[person_id].traveling:
                house_visitors[self.agents[person_id].at].append(person_id)

        while self.trips and self.trips[0].end_day == self.timestamp:
            cur_trip = heapq.heappop(self.trips)

            self.agents[cur_trip.person_id].end_trip(cur_trip.house_to)
            self.deposit_pheromone(cur_trip)

            house_visitors[cur_trip.house_to].append(cur_trip.person_id)

            self._handle_trip_fact(cur_trip, ActionType.END_TRIP)
            
        return house_visitors
    
    def _handle_trip_fact(self, trip: Trip, type: ActionType) -> None:
        fact_metadata = {'from': trip.house_from + 1, 'to': trip.house_to + 1, 'start': trip.start_day, 'end': trip.end_day}
        fact = ActionFact(self.timestamp, type, trip.person_id + 1, fact_metadata)

        self._add_facts_all((trip.person_id,), fact)

    def _add_facts_all(self, ids: tuple[int], *facts: ActionFact) -> None:
        '''add facts to island and agents' history'''
        self.add_facts(*facts)
        for id in ids:
            self.agents[id].update_knowledge(*facts)

    # ACO 

    def deposit_pheromone(self, trip: Trip):
        self.pheromones[trip.house_from, trip.house_to, trip.person_id] += self.agents[trip.person_id].pheromone_deposit

    # TODO understand this shit 
    def evaporate_pheromones(self):
        self.pheromones *= np.exp(-1 / self.exp_decay_time)

    def get_total_road_pheromone(self, house_from: int, house_to: int) -> float:
        return np.sum(self.pheromones[house_from, house_to, :])
    
    # HOUSE PROCESSING
    
    def _get_swap_id_pairs(self, *ids: int) -> Generator[tuple[int, int], None, None]:
        return zip(ids, ids[1:] + ids[:1])

        # take_from_ids = list(ids)
        # while True:
        #     random.shuffle(take_from_ids)
        #     if all(giver != receiver for receiver, giver in zip(ids, take_from_ids)):
        #         return zip(ids, take_from_ids)
            

    def process_house(self, house_id: int, *visitor_ids: int) -> None:
        if len(visitor_ids) < 2:
            return

        meeting_fact = ActionFact(self.timestamp, ActionType.MEETING, tuple(v + 1 for v in visitor_ids), metadata={'house_at': house_id + 1})
        self._add_facts_all(visitor_ids, meeting_fact)
        self.meetings_today += 1

        house_swappers = [v for v in visitor_ids if self.agents[v].swap_house]
        if len(house_swappers) > 1:
            self.swap(ActionType.HOUSE_SWAP, *house_swappers)

        pet_swappers = [v for v in visitor_ids if self.agents[v].swap_pet]
        if len(pet_swappers) > 1:
            self.swap(ActionType.PET_SWAP, *pet_swappers)

    def swap(self, type: ActionType, *ids: int) -> None:
        removed_items = dict()
        swap_facts = []

        for receiver_id, giver_id in self._get_swap_id_pairs(*ids):
            match type:
                case ActionType.HOUSE_SWAP:
                    prev_item = self.agents[receiver_id].state.house
                    new_item = removed_items[giver_id] if giver_id in removed_items else self.agents[giver_id].state.house
                case ActionType.PET_SWAP:
                    prev_item = self.agents[receiver_id].state.pet
                    new_item = removed_items[giver_id] if giver_id in removed_items else self.agents[giver_id].state.pet
                case _:
                    raise ValueError('Unknown swap type')
                
            removed_items[receiver_id] = prev_item
            self.agents[receiver_id].swap(type, new_item, self.timestamp)

            swap_facts.append(ActionFact(self.timestamp, type, (giver_id + 1, receiver_id + 1), {'from': giver_id + 1, 'to': receiver_id + 1, 'item': new_item}))

        self._add_facts_all(ids, *swap_facts)

    # AWARENESS

    def calc_awareness(self) -> None:
        self.awareness.append(len(self.facts))
        for i in range(self.num_people):
            self.agent_awareness[i].append(len(self.agents[i].known_facts))

    def print_awareness(self, timestamp: int = -1) -> None:
        print('Island:', self.awareness[timestamp])

        for i in range(len(self.agent_awareness)):
            print(f'Person {i + 1}:', self.agent_awareness[i][timestamp])

    
    def day(self) -> None:
        self.meetings_today = 0
        visits = self.get_day_visits() 

        if self.verbose:
            print(f'DAY {self.timestamp}')
            print('House visitors:', visits)

        for house_id in range(self.num_people):
            self.process_house(house_id, *visits[house_id])

        self.evaporate_pheromones()
        self.calc_awareness()

        # for agent in self.agents:
        #     self.add_facts(StaticFact(self.timestamp, *agent.state))
        self.log_known_facts()

        self.timestamp += 1
        self.plan_next_visits()

    # REPRESENTATION 
        
    def to_dict(self):
        return {
            'num_people': self.num_people,
            'agents': [agent.to_dict() for agent in self.agents],
            'mandatory_return': self.mandatory_return,
            'distance_matrix': '\n'.join(map(str, self.distance_matrix.tolist())),
            'aco': {
                'exp_decay_time': self.exp_decay_time,
            }
        }