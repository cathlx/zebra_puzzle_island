import heapq
import numpy as np 
import random

from typing import Generator

from agent import Agent
from utils.schemas import * 

class Island:
    def __init__(self, agents: list[Agent], distance_matrix: np.ndarray) -> None:
        self.agents = agents # at i pos person with id i-1
        self.num_people = len(agents)
        self.distance_matrix = distance_matrix

        self.facts: list[Fact] = [] 
        self.timestamp = 0 # current day 
        self.trips: list[Trip] = [] # heap

        # num of known facts
        self.awareness = []
        self.agent_awareness = [[] for _ in range(len(agents))]

    def __getitem__(self, idx: int) -> Agent:
        return self.agents[idx]
    
    def add_facts(self, *facts: Fact) -> None:
        for fact in facts:
            self.facts.append(fact)
        
    def log_all_facts(self, filepath: str = 'output/island_facts.txt') -> None:
        with open(filepath, 'w') as file:
            for fact in self.facts:
                file.write(repr(fact))
                file.write('\n')

    def log_known_facts(self, filepath: str = f'output/') -> None:
        for i in range(len(self.agents)):
            with open(filepath + f'person{i}_known_facts.txt', 'w') as file:
                for fact in self.agents[i].known_facts:
                    file.write(repr(fact))
                    file.write('\n')

    def plan_visits(self) -> None:
        for person_id in range(self.num_people):
            house_to_visit, eta = self.agents[person_id].visit_decision(self.distance_matrix)
            if not np.isnan(eta):

                self.agents[person_id].start_trip(house_to_visit)
                heapq.heappush(self.trips, Trip(self.timestamp + eta, self.timestamp, person_id, self.agents[person_id].at, house_to_visit))
                
                fact_metadata = {'from': self.agents[person_id].at + 1, 'to': house_to_visit + 1, 'start': self.timestamp, 'end': self.timestamp + eta}
                start_trip_fact = ActionFact(self.timestamp, ActionType.START_TRIP, person_id + 1, fact_metadata)

                self.add_facts(start_trip_fact)
                self.agents[person_id].update_knowledge(start_trip_fact)

    def day_visits(self) -> list[tuple[int, int]]:
        house_visitors = [[] for _ in range(self.num_people)]

        for person_id in range(self.num_people):
            if not self.agents[person_id].traveling:
                house_visitors[self.agents[person_id].at].append(person_id)

        while self.trips and self.trips[0].end_day == self.timestamp:
            cur_trip = heapq.heappop(self.trips)

            self.agents[cur_trip.person_id].end_trip(cur_trip.house_to)
            house_visitors[cur_trip.house_to].append(cur_trip.person_id)

            fact_metadata = {'from': cur_trip.house_from + 1, 'to': cur_trip.house_to + 1, 'start': cur_trip.start_day, 'end': cur_trip.end_day}
            end_trip_fact = ActionFact(self.timestamp, ActionType.END_TRIP, cur_trip.person_id + 1, fact_metadata)

            self.add_facts(end_trip_fact)
            self.agents[cur_trip.person_id].update_knowledge(end_trip_fact)
            
        return house_visitors
    
    def _get_swap_id_pairs(self, *ids: int):
        return zip(ids, ids[1:] + ids[:1])

        # take_from_ids = list(ids)
        # while True:
        #     random.shuffle(take_from_ids)
        #     if all(giver != receiver for receiver, giver in zip(ids, take_from_ids)):
        #         return zip(ids, take_from_ids)
            
    def _add_swap_info(self, ids: tuple[int], swap_facts: list[ActionFact]) -> None:
        self.add_facts(*swap_facts)
        for id in ids:
            self.agents[id].update_knowledge(*swap_facts)

    def swap(self, type: ActionType, *ids):
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

        self._add_swap_info(ids, swap_facts)

    def process_house(self, house_id: int, *visitor_ids) -> None:

        self.add_facts(ActionFact(self.timestamp, ActionType.MEETING, tuple(v + 1 for v in visitor_ids), metadata={'house_at': house_id + 1}))

        house_swappers = [v for v in visitor_ids if self.agents[v].swap_house]
        if len(house_swappers) > 1:
            self.swap(ActionType.HOUSE_SWAP, *house_swappers)

        pet_swappers = [v for v in visitor_ids if self.agents[v].swap_pet]
        if len(pet_swappers) > 1:
            self.swap(ActionType.PET_SWAP, *pet_swappers)

        self.house_processed[house_id] = True

    def calc_awareness(self) -> None:
        self.awareness.append(len(self.facts))
        for i in range(self.num_people):
            self.agent_awareness[i].append(len(self.agents[i].known_facts))
    
    def day(self) -> None:
        visits = self.day_visits() 

        if visits:
            self.house_processed = [False] * self.num_people

            for house_id in range(self.num_people):

                if len(visits[house_id]) < 2:
                    self.house_processed[house_id] = True
                    continue 
                else:
                    self.process_house(house_id, *visits[house_id])

        self.calc_awareness()
        for agent in self.agents:
            self.add_facts(StaticFact(self.timestamp, *agent.state))

        self.timestamp += 1
        self.plan_visits()