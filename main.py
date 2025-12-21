from utils.parsing import create_island

island = create_island()

NUM_DAYS = 10

for day in range(NUM_DAYS):
    island.day()

print('Simulation done!')
island.print_facts()