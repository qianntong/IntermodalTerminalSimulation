import simpy
import random
import numpy as np

RANDOM_SEED = 42
SIM_TIME = 100  # Simulation time in seconds

# Parameters
train_arrival_mean = 10  # Mean arrival time for trains
train_inspection_time = 1
crane_load_container_time = 2
crane_unload_container_time = 2

# Constants
CARS_PER_TRAIN = 6
CONTAINERS_PER_CAR = 1
CONTAINERS_PER_CRANE_MOVE = 1

# Global counters for IDs
train_id_counter = 1
crane_id_counter = 1
hostler_id_counter = 1
chassis_id_counter = 1
container_id_counter = 1

train_series = 0
time_per_train = []

# Define events
def train_arrival(env, stacking_area, container_mode, train_inspection_time):
    global train_id_counter
    while True:
        # Train arrival follows a normal distribution
        yield env.timeout(random.normalvariate(train_arrival_mean, 1))
        train_id = train_id_counter
        train_id_counter += 1
        print(f"Train {train_id} arrives at {env.now}")
        yield env.process(process_train(env, stacking_area, train_id))

def process_train(env, stacking_area, train_id):
    global container_id_counter
    for car_id in range(1, CARS_PER_TRAIN + 1):
        for container_batch in range(0, CONTAINERS_PER_CAR, CONTAINERS_PER_CRANE_MOVE):
            container_ids = list(range(container_id_counter, container_id_counter + min(CONTAINERS_PER_CRANE_MOVE, CONTAINERS_PER_CAR - container_batch)))
            container_id_counter += len(container_ids)
            yield env.process(crane_to_chassis(env, stacking_area, train_id, car_id, container_ids))
    yield env.process(train_departure(env, stacking_area, train_id))

def crane_to_chassis(env, stacking_area, train_id, car_id, container_ids):
    global crane_id_counter, chassis_id_counter
    crane_id = crane_id_counter

    chassis_id = chassis_id_counter
    chassis_id_counter += 1
    yield env.timeout(crane_load_container_time)
    for container_id in container_ids:
        print(f"Crane {crane_id} loads container {container_id} from car {car_id} of Train {train_id} to chassis {chassis_id} at {env.now}")
    yield env.process(chassis_to_hostler(env, stacking_area, train_id, crane_id, chassis_id, car_id, container_ids))

def chassis_to_hostler(env, stacking_area, train_id, crane_id, chassis_id, car_id, container_ids):
    global hostler_id_counter
    hostler_id = hostler_id_counter
    hostler_id_counter += 1
    yield env.timeout(crane_unload_container_time)
    for container_id in container_ids:
        print(f"Hostler {hostler_id} picks up container {container_id} from chassis {chassis_id} to stacking area for Train {train_id} at {env.now}")
        stacking_area.put(1)
    yield env.process(hostler_to_chassis(env, stacking_area, train_id, crane_id, chassis_id, hostler_id, car_id, container_ids))

def hostler_to_chassis(env, stacking_area, train_id, crane_id, chassis_id, hostler_id, car_id, container_ids):
    while stacking_area.level > 0:
        yield env.timeout(crane_unload_container_time)
        stacking_area.get(1)
        for container_id in container_ids:
            print(f"Hostler {hostler_id} brings back container {container_id} from stacking area to chassis {chassis_id} for Train {train_id} at {env.now}")
        yield env.process(chassis_to_crane(env, stacking_area, train_id, crane_id, chassis_id, hostler_id, car_id, container_ids))

def chassis_to_crane(env, stacking_area, train_id, crane_id, chassis_id, hostler_id, car_id, container_ids):
    yield env.timeout(crane_load_container_time)
    for container_id in container_ids:
        print(f"Crane {crane_id} loads container {container_id} from chassis {chassis_id} to car {car_id} for Train {train_id} at {env.now}")

def train_departure(env, stacking_area, train_id):
    global train_series
    yield env.timeout(1)
    print(f"Train {train_id} departs at {env.now}")
    train_series += 1
    time_per_train.append(env.now)

def check_container_status(env):
    while True:
        # Logic to check the status of the container and update the loop
        yield env.timeout(1)

# Setup and start the simulation
def run_simulation():
    print('Train Loading and Unloading Simulation')
    random.seed(RANDOM_SEED)

    env = simpy.Environment()

    stacking_area = simpy.Container(env, capacity=1000, init=0)

    env.process(train_arrival(env, stacking_area, 'random', train_inspection_time))
    env.process(check_container_status(env))

    env.run(until=SIM_TIME)

    print('Number of trains processed: ', train_series)
    print('Average time per train: ', np.mean(time_per_train))

run_simulation()