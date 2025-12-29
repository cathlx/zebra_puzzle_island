from utils.parsing import create_island

island = create_island()

NUM_DAYS = 10

for day in range(NUM_DAYS):
    island.day()

island.print_facts()
island.print_facts_for_log()