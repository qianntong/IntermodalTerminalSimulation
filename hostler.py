import simpy
from parameters import *

class Hostler:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.status = 1  # inactive(wait): 1

    def move_from_loading(self):
        self.status = 0  # active (move): 0
        print(f"{self.name} is moving to loading area at time {self.env.now}")
        yield self.env.timeout(random.randint(1, 5))  # simulate moving time
        print(f"{self.name} has arrived at loading area at time {self.env.now}")

    def move_from_stacking(self):
        self.status = 0  # active (move): 0
        print(f"{self.name} is moving to stacking area at time {self.env.now}")
        yield self.env.timeout(random.randint(1, 5))  # simulate moving time
        print(f"{self.name} has arrived at stacking area at time {self.env.now}")

def loading_area(env, hostlers):
    while True:
        yield env.timeout(10) # loading area hostler handling time
        for hostler in hostlers:
            env.process(hostler.move_from_loading())
            # queuing time module connection
            hostler.status = 1  # back to loading area

def stacking_area(env, hostlers):
    while True:
        yield env.timeout(15)   # stacking area hostler handling time
        for hostler in hostlers:
            env.process(hostler.move_from_stacking())
            # queuing time module connection
            hostler.status = 1  # back to stacking area

env = simpy.Environment()

# parameter setting
parameters = SimulationParameters()
loading_hostler_numbers = parameters.get()["loading_hostler_numbers"]
stacking_hostler_numbers = parameters.get()["stacking_hostler_numbers"]

loading_hostlers = [Hostler(env, f"Loading Hostler {i+1}") for i in range(loading_hostler_numbers)]
stacking_hostlers = [Hostler(env, f"Stacking Hostler {i+1}") for i in range(stacking_hostler_numbers)]
env.process(loading_area(env, loading_hostlers))
env.process(stacking_area(env, stacking_hostlers))

env.run(until=parameters.sim_time)

for hostler in loading_hostlers + stacking_hostlers:
    print(f"{hostler.name} status: {'Active' if hostler.status == 1 else 'Waiting'}")