import numpy as np 

from dataclasses import astuple, dataclass
from enum import Enum
from typing import Any

@dataclass
class ActionProbabilities:
    house_visit: np.ndarray # prob of choosing to visit each house (1-6)

    swap_house: float
    swap_pet: float

class Color(Enum):
    RED = 'Red'
    BLUE = 'Blue'
    YELLOW = 'Yellow'
    GREEN = 'Green'
    WHITE = 'White'
    BLACK = 'Black'

@dataclass
class House:
    id: int
    color: Color

class Nationality(Enum):
    RUSSIAN = 'Russian'
    ENGLISH = 'English'
    CHINESE = 'Chinese'
    GERMAN = 'German'
    FRENCH = 'French'
    AMERICAN = 'American'

class Drink(Enum):
    WATER = 'Water'
    BEER = 'Beer'
    JUICE = 'Juice'
    WHISKEY = 'Whiskey'  
    VODKA = 'Vodka'
    WINE = 'Wine'

class Cigarettes(Enum):
    MARLBORO = 'Marlboro'
    PALL_MALL = 'Pall Mall'
    DUNHILL = 'Dunhill'
    KENT = 'Kent'
    CAMEL = 'Camel'
    PARLAMENT = 'Parlament'

class Pet(Enum):
    DOG = 'Dog'
    CAT = 'Cat'
    ZEBRA = 'Zebra'
    FISH = 'Fish'
    HAMSTER = 'Hamster'  
    BEAR = 'Bear'

@dataclass
class PersonState:
    id: int
    house: House 
    nationality: Nationality 
    drink: Drink 
    cigarettes: Cigarettes 
    pet: Pet 

    def __iter__(self):
        return iter(astuple(self))

@dataclass
class Fact:
    timestamp: int 

@dataclass
class StaticFact(Fact): 
    person_id: int | None = None
    house: House | None = None
    nationality: Nationality | None = None
    drink: Drink | None = None
    cigarettes: Cigarettes | None = None
    pet: Pet | None = None

class ActionType(Enum): 
    START_TRIP = 'start trip' 
    END_TRIP = 'end trip' 
    MEETING = 'meeting'
    HOUSE_SWAP = 'house swap'
    PET_SWAP = 'pet swap'
    INFORMATION_EXCHANGE = 'information exchange'

@dataclass
class ActionFact(Fact): 
    type: ActionType
    actors: list[int] # ids of people involved
    metadata: dict[str, Any] | None = None

@dataclass(order=True)
class Trip:
    end_day: int
    start_day: int
    person_id: int
    house_from: int
    house_to: int

class VisitStrategy(Enum):
    RANDOM = 'Random'
    ACO = 'ACO'
    