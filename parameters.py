import random

class SimulationParameters:
    def __init__(self):
        self.random_seed = 42
        # simulation
        self.sim_time = 1000
        self.total_container_volume = 500
        self.docks = 1
        # container
        self.container_mode = 'loaded' # choose from 'loaded' or 'random'
        # trains
        self.train_series = 0
        self.num_train_cars = 6
        self.train_id = list(range(1, self.num_train_cars + 1))
        self.train_arrival_time = 1000
        self.train_arrival_min = 100
        self.train_arrival_max = 300
        self.train_inspection_time = 15
        self.train_load_time = 10
        self.train_unload_time = 10
        self.containers_for_a_train = 100
        # rail_crane
        self.RC_numbers = 3
        self.RC_horiz_speed = 10
        self.RC_verti_speed = 10
        self.RC_verti_dist = 10
        self.RC_horiz_dist = 10
        self.RC_capacity_container_volume = 50
        self.RC_waiting_container_time = 10
        self.RC_moving_time = 10
        self.RC_waiting_truck_time = 10
        self.RC_loading_time = 10
        self.RC_unloading_time = 10
        # chassis
        self.chassis_inspection_time = 10
        self.chassis_numbers = 20
        # hostler
        self.loading_hostler_numbers = 5
        self.stacking_hostler_numbers = 5
        self.total_hostler_numbers = self.loading_hostler_numbers + self.stacking_hostler_numbers
        self.hostler_speed = 30 # mph
        self.stacking_to_train_time = random.uniform(0, 1)
        self.loading_to_train_time = random.uniform(0, 1)
        # truck
        self.truck_numbers = 3
        self.truck_capacity_container_volume = 50   # also need consider empty load
        self.truck_waiting_container_time = 10
        self.truck_inspiration_time = 10
        self.truck_turnover_time = 100  # should be function regarding time and distance, and consider queuing
        self.truck_moving_to_loading = 10
        self.truck_moving_to_unloading = 10
        self.truck_waiting_loading_equipment = 10
        self.truck_waiting_unloading_equipment = 10
        self.truck_receiving_loading_equipment = 10
        self.truck_receiving_unloading_equipment = 10

    def get(self):
        return vars(self)