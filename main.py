from utils.parsing import create_island

island = create_island()

NUM_DAYS = 10

for day in range(NUM_DAYS):
    island.day()

island.log_all_facts()
island.log_known_facts()