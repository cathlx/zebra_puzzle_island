from setting import create_island

people_csv = 'configs/island_schemas/people.csv'
actions_csv = 'configs/island_schemas/actions.csv'
distance_csv = 'configs/island_schemas/distances.csv'

island = create_island(people_csv, actions_csv, distance_csv, mandatory_return=True)

for _ in range(20):
    island.day()
