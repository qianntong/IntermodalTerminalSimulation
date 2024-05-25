from hostler import *
from parameters import *
from parameters import SimulationParameters

class RailRoadSimulation:
    def __init__(self, env, parameters):
        self.env = env
        self.parameters = parameters
        self.train_queue = simpy.Resource(env, capacity=parameters.docks)
        self.chassis = simpy.Resource(env, capacity=parameters.chassis_numbers)
        self.hostler = simpy.Resource(env, capacity=parameters.total_hostler_numbers)
        self.RC = simpy.Resource(env, capacity=parameters.RC_numbers)
        self.trucks = simpy.Resource(env, capacity=parameters.truck_numbers)
        self.random_seed = parameters.random_seed
        random.seed(self.random_seed)
        # asynchronous processes
        self.pipe0 = simpy.Store(env)
        self.pipe1 = simpy.Store(env)
        self.pipe2 = simpy.Store(env)
        self.pipe3 = simpy.Store(env)
        self.pipe4 = simpy.Store(env)
        self.pipe5 = simpy.Store(env)
        # containers
        self.containers = {}
        # train
        self.train_status = [0] * self.parameters.num_train_cars    # initialize with all 0 as no railcar
        # hostler
        self.container_to_stacking_distance = self.parameters.stacking_to_train_time * self.parameters.hostler_speed
        self.container_to_loading_distance = self.parameters.loading_to_train_time * self.parameters.hostler_speed
        self.hostler_loading = []
        self.hostler_stacking = []
        # output parameter
        self.crane_load_container_time = 0
        self.crane_upload_container_time = 0
        self.container_transport_time = []
        self.hostler_upload_transshipment_time = 0
        self.hostler_load_transshipment_time = 0
        self.hostler_upload_time = 0
        self.hostler_load_time = 0
        self.total_truck_movements = 0
        self.total_transported_containers = 0   # total transported containers
        self.train_id = parameters.train_id
        self.time_per_train = 0

    # Status 0-1: Containers are fully loaded on the train
    def train_arrival(self):
        while True:
            if self.parameters.container_mode == 'random':
                for i in range(len(self.train_status)):
                    if self.train_status[i] == 0:
                        self.train_status[i] = random.choice([0, 1])  # randomly assign 0 or 1
            elif self.parameters.container_mode == 'loaded':
                self.train_status = [1] * len(self.train_status)    # fully loaded
            print(self.train_status)
            yield self.env.timeout(random.expovariate(1.0 / self.parameters.train_arrival_time))

            with self.train_queue.request() as request:
                print(f"Train arrives at time {self.env.now}")
                yield self.env.timeout(self.parameters.train_inspection_time)
                print(f"Train inspection completed at time {self.env.now}")
                self.check_container_status()   # status check
            print(self.train_status)

    # status 1-2: Rail cranes lift containers from railcar to chassis
    def crane_to_chassis(self):
        with self.chassis.request() as request:
            yield request
            self.check_container_status()
            processing_time = 2 * (self.parameters.RC_verti_dist / self.parameters.RC_verti_speed) \
                              + (self.parameters.RC_horiz_dist / self.parameters.RC_horiz_speed)
            self.crane_load_container_time += processing_time
            yield self.env.timeout(self.crane_load_container_time)

    # Status 2-3: Rail spots are empty, while hostlers are delivering containers from railcars to stacking area
    def chassis_to_hostler(self):
        with self.hostler.request() as request:
            yield request
            unload_start_time = self.env.now
            self.check_container_status()
            yield self.env.timeout(self.hostler_load_time)
            unload_end_time = self.env.now
            self.hostler_load_transshipment_time = unload_end_time - unload_start_time
            yield self.env.timeout(self.hostler_load_transshipment_time)

    # status 3-4: Hostlers bring back containers from stacking area to railway loading area
    def hostler_to_chassis(self):
        with self.hostler.request() as request:
            yield request
            unload_start_time = self.env.now  # container unload start time
            self.check_container_status()
            yield self.env.timeout(self.hostler_upload_time)  # every iteration, the transshipment time of hostler
            unload_end_time = self.env.now
            self.hostler_upload_transshipment_time = unload_end_time - unload_start_time
            yield self.env.timeout(self.hostler_upload_transshipment_time)

    # status 4-5: Rail cranes lift containers from chassis to railcar
    def chassis_to_crane(self):
        with self.chassis.request() as request:
            yield request
            self.check_container_status()
            processing_time = 2 * (self.parameters.RC_verti_dist / self.parameters.RC_verti_speed) \
                          + (self.parameters.RC_horiz_dist / self.parameters.RC_horiz_speed)
            self.crane_upload_container_time += processing_time
            yield self.env.timeout(self.crane_load_container_time)

    # status 5-6: The train is fully uploaded and ready to departure
    def train_departure(self):
        if all(status == 5 for status in self.train_status):
            self.train_sreies += 1
            print("All containers are unloaded from the train.")
            self.time_per_train = self.crane_load_container_time \
                                  + self.crane_upload_container_time \
                                  + self.container_transport_time \
                                  + self.hostler_upload_transshipment_time \
                                  + self.hostler_load_transshipment_time \
                                  + self.hostler_upload_time \
                                  + self.hostler_load_time \
                                  + self.total_truck_movements \
                                  + self.total_transported_containers
            print(f"It costs {self.time_per_train} to load and upload containers for train #{self.train_sreies}")
            print(f"Train #{self.train_sreies} are preparing to depart.")

    def check_container_status(self):
        for c_id, status in zip(range(len(self.train_id)), range(len(self.train_status))):
            if self.train_status[c_id] == 1:
                self.crane_to_chassis()
                self.train_status[c_id] = 2
                c_id += 1
                status += 1
                print(self.train_status)
                continue
            elif self.train_status[c_id] == 2:
                if self.container_to_stacking_distance <= self.container_to_loading_distance:
                    print(
                        f"Shortest distance from hostler {c_id} to railroad: {self.container_to_stacking_distance:.2f} mile")
                    self.hostler_stacking.append(c_id)
                    self.hostler_stacking = list(set(self.train_id) - set(self.hostler_stacking))
                else:
                    print(
                        f"Shortest distance from hostler {c_id} to railroad: {self.container_to_loading_distance:.2f} mile")
                    self.hostler_loading.append(c_id)
                    self.hostler_stacking = list(set(self.train_id) - set(self.hostler_loading))
                self.chassis_to_hostler()
                self.train_status[c_id] = 3
                c_id += 1
                status += 1
                print(self.train_status)
                continue
            elif self.train_status[c_id] == 3:
                if self.container_to_stacking_distance <= self.container_to_loading_distance:
                    print(
                        f"Shortest distance from hostler {c_id} to railroad: {self.container_to_stacking_distance :.2f} mile")
                    self.hostler_stacking.append(c_id)
                    self.hostler_stacking = list(set(self.train_id) - set(self.hostler_stacking))
                else:
                    print(
                        f"Shortest distance from hostler {c_id} to railroad: {self.container_to_loading_distance:.2f} mile")
                    self.hostler_loading.append(c_id)
                    self.hostler_stacking = list(set(self.train_id) - set(self.hostler_loading))
                self.hostler_to_chassis()
                self.train_status[c_id] = 4
                c_id += 1
                status += 1
                print(self.train_status)
                continue
            elif self.train_status[c_id] == 4:
                self.chassis_to_crane()
                self.train_status[c_id] = 5
                c_id += 1
                status += 1
                print(self.train_status)
                continue
            elif self.train_status[c_id] == 5:
                print(self.train_status)
                c_id += 1
                status += 1
                continue
            elif all(status == 5 for status in self.train_status):
                self.train_departure()
                continue

def main():
    parameters = SimulationParameters()
    env = simpy.Environment()
    simulation = RailRoadSimulation(env, parameters)
    env.process(simulation.train_arrival())
    env.process(simulation.crane_to_chassis())
    env.process(simulation.chassis_to_hostler())
    env.process(simulation.hostler_to_chassis())
    env.process(simulation.chassis_to_crane())
    simulation.train_departure()
    env.run(until=parameters.sim_time)

if __name__ == "__main__":
    main()