from dataclasses import astuple, dataclass, field
from enum import Enum

@dataclass
class ActionProbabilities:
    visit_house: list[float] # prob of choosing to visit each house (1-6)

    # turn_left: float
    # turn_right: float
    # stay_home: float

    swap_house: float
    swap_pet: float

    @property
    def visit_probs(self):
        return self.choose_house

    # no_swapping: float = field(init=False)  
    
    # def __post_init__(self):
    #     self.no_swapping = 1.0 - (self.swap_house + self.swap_pet)

    # @property
    # def movement_probs(self):
    #     return [self.turn_left, self.turn_right, self.stay_home]
    
    # @property
    # def swap_probs(self):
    #     return [self.swap_house, self.swap_pet, self.no_swapping]

property_to_idx_mapping = {
    'дом': 0,
    'цвет': 1,
    'национальность': 2,
    'напиток': 3, 
    'сигареты': 4, 
    'питомец': 5
}

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
    timestamp: int # day when the fact was true 

@dataclass
class StaticFact(Fact): # кто что ест, кто в каком доме живет - статический факт (о состоянии)
    person_id: int | None = None
    house: House | None = None
    # color: Color | None
    nationality: Nationality | None = None
    drink: Drink | None = None
    cigarettes: Cigarettes | None = None
    pet: Pet | None = None

class ActionType(Enum): 
    START_TRIP = 'start trip' # вышел из дома
    CONCLUDE_TRIP = 'conclude trip' # пришел в дом назначения
    HOUSE_SWAP = 'house swap'
    PET_SWAP = 'pet swap'
    INFORMATION_EXCHANGE = 'information exchange'

@dataclass
class ActionFact(Fact): # информация о действии 
    type: ActionType
    actors: list[int] # ids of people involved
    # TODO: how to know who did what exacly? is it necessary or can it be accounted for elsewhere? 

@dataclass(order=True)
class PendingVisit:
    visit_day: int
    person_id: int
    house_id: int

# class VisitDecision(Enum): 
#     TURN_LEFT = -1
#     STAY_HOME = 0
#     TURN_RIGHT = 1
    

# class VisitDecision(Enum): 
#     TURN_LEFT = -1
#     STAY_HOME = 0
#     TURN_RIGHT = 1


# class SwapDecision(Enum):
#     SWAP_HOUSE = 'swap house'
#     SWAP_PET = 'swap pet'
#     NO_SWAP = 'no swapping'