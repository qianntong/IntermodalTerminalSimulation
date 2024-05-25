import simpy
import random
import numpy as np

RANDOM_SEED = 42
SIM_TIME = 50  # Simulation time in seconds

# Parameters
train_arrival_mean = 10  # Mean arrival time for trains
train_inspection_time = 1
crane_load_container_time = 2
crane_unload_container_time = 2

# Global counters for IDs
train_id_counter = 0
crane_id_counter = 0
hostler_id_counter = 0

# train container setting
CARS_PER_TRAIN = 6
CONTAINERS_PER_CAR = 10
CONTAINERS_PER_CRANE_MOVE = 2

train_series = 0
time_per_train = []

# Define events
def train_arrival(env, container_mode, train_inspection_time):
    global train_id_counter
    while True:
        # Train arrival follows a normal distribution
        yield env.timeout(random.normalvariate(train_arrival_mean, 1))
        train_id = train_id_counter
        train_id_counter += 1
        print(f"Train {train_id} arrives at {env.now}")
        env.process(crane_to_chassis(env, train_id))

def crane_to_chassis(env, train_id):
    global crane_id_counter
    crane_id = crane_id_counter
    crane_id_counter += 1
    yield env.timeout(crane_load_container_time)
    print(f"Crane {crane_id} loads containers from railcar to chassis for Train {train_id} at {env.now}")
    env.process(chassis_to_hostler(env, train_id, crane_id))

def chassis_to_hostler(env, train_id, crane_id):
    global hostler_id_counter
    hostler_id = hostler_id_counter
    hostler_id_counter += 1
    yield env.timeout(crane_unload_container_time)
    print(f"Hostler {hostler_id} picks up containers from chassis to stacking area for Train {train_id} at {env.now}")
    env.process(hostler_to_chassis(env, train_id, crane_id, hostler_id))

def hostler_to_chassis(env, train_id, crane_id, hostler_id):
    yield env.timeout(crane_unload_container_time)
    print(f"Hostler {hostler_id} brings back containers from stacking area to railway loading area for Train {train_id} at {env.now}")
    env.process(chassis_to_crane(env, train_id, crane_id, hostler_id))

def chassis_to_crane(env, train_id, crane_id, hostler_id):
    yield env.timeout(crane_load_container_time)
    print(f"Crane {crane_id} loads containers from chassis to railcar for Train {train_id} at {env.now}")
    env.process(train_departure(env, train_id, crane_id, hostler_id))

def train_departure(env, train_id, crane_id, hostler_id):
    global train_series
    yield env.timeout(1)
    print(f"Train {train_id} departs at {env.now}")
    train_series += 1
    time_per_train.append(env.now)
    env.process(train_arrival(env, 'random', train_inspection_time))

def check_container_status(env):
    while True:
        # Logic to check the status of the container and update the loop
        yield env.timeout(1)

# Setup and start the simulation
def run_simulation():
    print('Train Loading and Unloading Simulation')
    random.seed(RANDOM_SEED)

    env = simpy.Environment()

    env.process(train_arrival(env, 'random', train_inspection_time))
    env.process(check_container_status(env))

    env.run(until=SIM_TIME)

    print('Number of trains processed: ', train_series)
    print('Average time per train: ', np.mean(time_per_train))

run_simulation()
