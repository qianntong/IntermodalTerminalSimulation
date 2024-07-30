import simpy
import random
import pandas as pd
from vehicle_performance import record_vehicle_event, save_average_times, save_vehicle_logs


# Simulation parameters
RANDOM_SEED = 42
SIM_TIME = 1000

# Yard setting
YARD_TYPE = 'parallel'  # choose 'perpendicular' or 'parallel'
YARD_VERT_WTH = 1
YARD_HORIZ_LTH = 1
BLOCK_COLUMN_NUM = 1
BLOCK_ROW_NUM = 1

# Trains
TRAIN_UNITS = int(input("Enter the number of train units: "))
TRAIN_SPOTS = TRAIN_UNITS
TRAIN_ARRIVAL_MEAN = 10
TRAIN_INSPECTION_TIME = 1
train_series = 0
time_per_train = []
train_departure_event = None
all_outbound_containers_dropped = None


# Containers
CONTAINERS_PER_CAR = 1
INBOUND_CONTAINER_NUMBER = TRAIN_UNITS * CONTAINERS_PER_CAR
OUTBOUND_CONTAINER_NUMBER = INBOUND_CONTAINER_NUMBER
container_events = {}   # Dictionary to store container event data

# Chassis
CHASSIS_NUMBER = TRAIN_UNITS
chassis_status = [-1] * CHASSIS_NUMBER  # -1 means empty, 1 means inbound container, 0 means outbound container

# Cranes
CRANE_NUMBER = int(input("Enter the number of crane: "))
CONTAINERS_PER_CRANE_MOVE = 1   # crane speed
CRANE_LOAD_CONTAINER_TIME = 1
CRANE_UNLOAD_CONTAINER_TIME = 2
CRANE_INITIALIZE_TIME = 2 * TRAIN_UNITS * CONTAINERS_PER_CAR * CONTAINERS_PER_CRANE_MOVE
outbound_containers_mapping = {}  # To keep track of outbound containers mapped to chassis

# Hostlers
HOSTLER_NUMBER = int(input("Enter the number of hostler: "))
CONTAINERS_PER_HOSTLER = 1  # hostler capacity
HOSTLER_SPEED_LIMIT = 30
HOSTLER_TRANSPORT_CONTAINER_TIME = 5
HOSTLER_FIND_CONTAINER_TIME = 1

# Trucks
TRUCK_PASS_GATE_TIME = 1
TRUCK_TO_PARKING = 2
TRUCK_TRANSPORT_CONTAINER_TIME = 2
TRUCK_SPEED_LIMIT = 30
TRUCK_NUMBERS = INBOUND_CONTAINER_NUMBER

# Counting vehicles
train_id_counter = 1
hostler_id_counter = 1
inbound_container_id_counter = 1
outbound_container_id_counter = 10001
truck_id_counter = 1
crane_id_counter = 1
batch_outbound_containers_processed = 0
outbound_containers_processed = 0


def record_event(container_id, event_type, timestamp):
    if container_id not in container_events:
        container_events[container_id] = {}
    container_events[container_id][event_type] = timestamp


def bring_all_outbound_containers(env, gate, outbound_containers_queue, train_processing, cranes, hostlers, chassis, truck_queue):
    global outbound_container_id_counter, batch_outbound_containers_processed, all_outbound_containers_dropped
    while batch_outbound_containers_processed < OUTBOUND_CONTAINER_NUMBER:
        for truck_id in range(1, TRUCK_NUMBERS + 1):
            yield env.process(truck_through_gate(env, gate, outbound_containers_queue, truck_id))
            if batch_outbound_containers_processed >= OUTBOUND_CONTAINER_NUMBER:
                print("All outbound containers are moved to the parking area")
                all_outbound_containers_dropped.succeed()
                return


def truck_through_gate(env, gate, outbound_containers_queue, truck_id):
    global outbound_container_id_counter, batch_outbound_containers_processed, outbound_containers_processed
    with gate.request() as request:
        yield request
        yield env.timeout(TRUCK_PASS_GATE_TIME)
        container_id = outbound_container_id_counter
        outbound_container_id_counter += 1
        record_event(container_id, 'truck_arrival', env.now)
        yield outbound_containers_queue.put(container_id)
        yield env.timeout(TRUCK_TRANSPORT_CONTAINER_TIME)
        record_event(container_id, 'truck_drop_off', env.now)
        batch_outbound_containers_processed += 1
        outbound_containers_processed += 1
        print(f"Truck {truck_id} drops outbound container {container_id} at {env.now}")


def train_arrival(env, train_processing, cranes, hostlers, chassis, gate, outbound_containers_queue, truck_queue):
    global train_id_counter, train_departure_event, all_outbound_containers_dropped
    while True:
        if train_departure_event is not None:
            yield train_departure_event

        yield all_outbound_containers_dropped

        yield env.timeout(random.expovariate(1 / TRAIN_ARRIVAL_MEAN))
        train_id = train_id_counter
        for container_id in range(inbound_container_id_counter, inbound_container_id_counter + INBOUND_CONTAINER_NUMBER):
            record_event(container_id, 'train_arrival', env.now)
        print(f"Train {train_id} arrives at {env.now}")

        with train_processing.request() as request:
            yield request

            all_chassis_filled_event = env.event()

            yield env.process(process_train(env, train_id, cranes, hostlers, chassis, gate, outbound_containers_queue, truck_queue,
                              train_processing, all_chassis_filled_event))
            train_id_counter += 1
            train_departure_event = None

def process_train(env, train_id, cranes, hostlers, chassis, gate, outbound_containers_queue, truck_queue, train_processing, all_chassis_filled_event):
    global time_per_train, train_series, INBOUND_CONTAINER_NUMBER, OUTBOUND_CONTAINER_NUMBER, outbound_container_id_counter

    start_time = env.now

    # Unload all inbound containers
    unload_processes = []
    for _ in range(INBOUND_CONTAINER_NUMBER):
        unload_process = env.process(crane_and_chassis(env, train_id, 'unload', cranes, hostlers, chassis, truck_queue, train_processing, outbound_containers_queue, gate, all_chassis_filled_event))
        unload_processes.append(unload_process)
    yield simpy.events.AllOf(env, unload_processes)

    # Ensure all outbound containers are moved to chassis
    move_processes = []
    for chassis_id in range(1, OUTBOUND_CONTAINER_NUMBER + 1):
        if chassis_status[chassis_id - 1] == 0:
            continue
        move_process = env.process(hostler_transfer(env, hostlers, 'outbound', chassis, chassis_id, None, truck_queue, cranes, train_processing, outbound_containers_queue, gate, all_chassis_filled_event))
        move_processes.append(move_process)
    yield simpy.events.AllOf(env, move_processes)

    # Wait until all chassis are filled with outbound containers
    yield all_chassis_filled_event

    # Load all outbound containers
    load_processes = []
    for chassis_id in range(1, OUTBOUND_CONTAINER_NUMBER + 1):
        load_process = env.process(crane_and_chassis(env, train_id, 'load', cranes, hostlers, chassis, truck_queue, train_processing, outbound_containers_queue, gate, all_chassis_filled_event, chassis_id=chassis_id))
        load_processes.append(load_process)
    yield simpy.events.AllOf(env, load_processes)

    end_time = env.now
    time_per_train.append(end_time - start_time)
    train_series += 1


def wait_for_all_chassis_filled(env):
    global chassis_status
    while any(status != 0 for status in chassis_status):
        yield env.timeout(1)
    print("All chassis filled with outbound containers")


def crane_and_chassis(env, train_id, action, cranes, hostlers, chassis, truck_queue, train_processing, outbound_containers_queue, gate, all_chassis_filled_event, chassis_id=None):
    global crane_id_counter, chassis_status, inbound_container_id_counter, outbound_containers_mapping, outbound_container_id_counter, INBOUND_CONTAINER_NUMBER, OUTBOUND_CONTAINER_NUMBER

    with cranes.request() as request:
        yield request


        start_time = env.now
        record_vehicle_event('crane', crane_id_counter, 'start', start_time)    # performance record: starting

        if action == 'unload':
            crane_id = crane_id_counter
            crane_id_counter = (crane_id_counter % CRANE_NUMBER) + 1

            chassis_id = ((inbound_container_id_counter - 1) % CHASSIS_NUMBER) + 1

            current_inbound_id = inbound_container_id_counter
            inbound_container_id_counter += 1
            yield env.timeout(CRANE_UNLOAD_CONTAINER_TIME)

            end_time = env.now
            record_vehicle_event('crane', crane_id_counter, 'end', end_time)     # performance record: ending

            chassis_status[chassis_id - 1] = 1
            record_event(current_inbound_id, 'crane_unload', env.now)
            print(f"Crane {crane_id} unloads inbound container {current_inbound_id} at chassis {chassis_id} from train {train_id} at {env.now}")
            env.process(hostler_transfer(env, hostlers, 'inbound', chassis, chassis_id, current_inbound_id, truck_queue, cranes, train_processing, outbound_containers_queue, gate, all_chassis_filled_event))

        elif action == 'load':
            if chassis_id not in outbound_containers_mapping:
                print(f"Error: No outbound container mapped to chassis {chassis_id} at {env.now}")
                return

            container_id = outbound_containers_mapping[chassis_id]  # Retrieve container ID from mapping

            if CRANE_NUMBER == 1:
                crane_id = 1
            else:
                crane_id = (chassis_id % CRANE_NUMBER) + 1

            yield env.timeout(CRANE_LOAD_CONTAINER_TIME)
            chassis_status[chassis_id - 1] = -1
            record_event(container_id, 'crane_load', env.now)
            print(f"Crane {crane_id} loads outbound container {container_id} from chassis {chassis_id} to train {train_id} at {env.now}")

            # Check if all outbound containers are loaded
            if all(status == -1 for status in chassis_status):
                env.process(train_departure(env, train_id, train_processing, cranes, hostlers, chassis, gate, outbound_containers_queue, truck_queue))


def hostler_transfer(env, hostlers, container_type, chassis, chassis_id, container_id, truck_queue, cranes, train_processing, outbound_containers_queue, gate, all_chassis_filled_event):
    global HOSTLER_TRANSPORT_CONTAINER_TIME, chassis_status, hostler_id_counter, HOSTLER_NUMBER, outbound_container_id_counter, outbound_containers_mapping, train_id_counter

    with hostlers.request() as request:
        yield request

        start_time = env.now
        record_vehicle_event('hostler', hostler_id_counter, 'start', start_time)    # performance record

        hostler_id = hostler_id_counter
        hostler_id_counter = (hostler_id_counter % HOSTLER_NUMBER) + 1

        with chassis.request() as chassis_request:
            yield chassis_request

            if container_type == 'inbound' and chassis_status[chassis_id - 1] == 1:
                yield env.timeout(HOSTLER_TRANSPORT_CONTAINER_TIME)
                chassis_status[chassis_id - 1] = -1
                record_event(container_id, 'hostler_pickup', env.now)
                print(f"Hostler {hostler_id} picks up inbound container {container_id} from chassis {chassis_id} to parking area at {env.now}")
                yield env.timeout(HOSTLER_TRANSPORT_CONTAINER_TIME)
                record_event(container_id, 'hostler_dropoff', env.now)
                print(f"Hostler {hostler_id} drops off inbound container {container_id} from chassis {chassis_id} to parking area at {env.now}")

                end_time = env.now
                record_vehicle_event('hostler', hostler_id_counter, 'end', end_time)    # performance record

                yield env.process(notify_truck(env, truck_queue, container_id))
                # Check and process outbound container
                yield env.process(handle_outbound_container(env, hostlers, chassis, chassis_id, truck_queue, cranes, train_processing,
                                              outbound_containers_queue, gate, all_chassis_filled_event))


def handle_outbound_container(env, hostlers, chassis, chassis_id, truck_queue, cranes, train_processing, outbound_containers_queue, gate, all_chassis_filled_event):
    global HOSTLER_FIND_CONTAINER_TIME, HOSTLER_TRANSPORT_CONTAINER_TIME, chassis_status, hostler_id_counter, outbound_container_id_counter, outbound_containers_mapping

    hostler_id = hostler_id_counter
    hostler_id_counter = (hostler_id_counter % HOSTLER_NUMBER) + 1

    outbound_container_id = yield outbound_containers_queue.get()

    if chassis_id not in outbound_containers_mapping:  # New mapping from outbound containers to chassis
        outbound_container_id = outbound_container_id
        outbound_containers_mapping[chassis_id] = outbound_container_id
        chassis_status[chassis_id - 1] = 0
        print(f"New mapping created: outbound container {outbound_container_id} to chassis {chassis_id} at {env.now}")

    outbound_container_id = outbound_containers_mapping[chassis_id]
    yield env.timeout(HOSTLER_FIND_CONTAINER_TIME)
    record_event(outbound_container_id, 'hostler_pickup', env.now)
    print(f"Hostler {hostler_id} brings back outbound container {outbound_container_id} from parking area to chassis {chassis_id} at {env.now}")
    yield env.timeout(HOSTLER_TRANSPORT_CONTAINER_TIME)
    record_event(outbound_container_id, 'hostler_dropoff', env.now)
    print(f"Hostler {hostler_id} drops off outbound container {outbound_container_id} from parking area to chassis {chassis_id} at {env.now}")

    # When all chassis are filled with outbound container, the cranes starts loading
    if all(status == 0 for status in chassis_status) and not all_chassis_filled_event.triggered:
        all_chassis_filled_event.succeed()
        # print("All chassis filled event triggered")

def notify_truck(env, truck_queue, container_id):
    truck_id = yield truck_queue.get()
    yield env.timeout(TRUCK_PASS_GATE_TIME)
    print(f"Truck {truck_id} arrives at parking area at {env.now}")
    yield env.process(truck_transfer(env, truck_id, container_id))


def truck_transfer(env, truck_id, container_id):
    global TRUCK_PASS_GATE_TIME, TRUCK_TRANSPORT_CONTAINER_TIME, outbound_container_id_counter

    start_time = env.now
    record_vehicle_event('truck', truck_id, 'start', start_time)    # performance record

    yield env.timeout(TRUCK_TO_PARKING)
    record_event(container_id, 'truck_pickup', env.now)
    print(f"Truck {truck_id} picks up inbound container {container_id} at {env.now}")
    yield env.timeout(TRUCK_TRANSPORT_CONTAINER_TIME)
    yield env.timeout(TRUCK_PASS_GATE_TIME)
    record_event(container_id, 'truck_exit', env.now)
    print(f"Truck {truck_id} exits gate with inbound container {container_id} at {env.now}")

    end_time = env.now
    record_vehicle_event('truck', truck_id, 'end', end_time)


def train_departure(env, train_id, train_processing, cranes, hostlers, chassis, gate, outbound_containers_queue,
                    truck_queue):
    global batch_outbound_containers_processed, train_departure_event
    yield env.timeout(TRAIN_INSPECTION_TIME)
    print(f"Train {train_id} departs at {env.now}")
    for container_id in range(outbound_container_id_counter - OUTBOUND_CONTAINER_NUMBER,
                              outbound_container_id_counter):
        record_event(container_id, 'train_depart', env.now)

    # Set the train_departure_event indicating the train has departed
    batch_outbound_containers_processed = 0
    train_departure_event = env.event()
    train_departure_event.succeed()

def check_container_status(env):
    while True:
        yield env.timeout(1)


def run_simulation():
    global all_outbound_containers_dropped
    print(f"Running simulation with TRAIN_UNITS={TRAIN_UNITS}, HOSTLER_NUMBER={HOSTLER_NUMBER}, CRANE_NUMBER={CRANE_NUMBER}")

    random.seed(RANDOM_SEED)
    env = simpy.Environment()

    train_processing = simpy.Resource(env, capacity=1)
    cranes = simpy.Resource(env, capacity=CRANE_NUMBER)
    hostlers = simpy.Resource(env, capacity=HOSTLER_NUMBER)
    gate = simpy.Resource(env, capacity=1)
    chassis = simpy.Resource(env, capacity=CHASSIS_NUMBER)
    outbound_containers_queue = simpy.Store(env, capacity=OUTBOUND_CONTAINER_NUMBER)
    truck_queue = simpy.Store(env, capacity=TRUCK_NUMBERS)

    # initialization
    all_outbound_containers_dropped = env.event()

    # Add initial trucks to truck_queue
    for truck_id in range(1, TRUCK_NUMBERS + 1):
        truck_queue.put(truck_id)

    env.process(bring_all_outbound_containers(env, gate, outbound_containers_queue, train_processing, cranes, hostlers, chassis, truck_queue))
    env.process(train_arrival(env, train_processing, cranes, hostlers, chassis, gate, outbound_containers_queue, truck_queue))
    env.process(check_container_status(env))

    env.run(until=SIM_TIME)

    # inbound and outbound container processing time
    inbound_times = []
    outbound_times = []

    for container_id, events in container_events.items():
        container_type = 'inbound' if container_id < 10001 else 'outbound'
        if container_type == 'inbound':
            if 'train_arrival' in events and 'truck_exit' in events:
                inbound_time = events['truck_exit'] - events['train_arrival']
                inbound_times.append(inbound_time)
        else:
            if 'truck_drop_off' in events and 'train_depart' in events:
                outbound_time = events['train_depart'] - events['truck_drop_off']
                outbound_times.append(outbound_time)

    avg_inbound_time = sum(inbound_times) / len(inbound_times) if inbound_times else 0
    avg_outbound_time = sum(outbound_times) / len(outbound_times) if outbound_times else 0

    print(f"Average processing time for inbound containers: {avg_inbound_time:.2f}")
    print(f"Average processing time for outbound containers: {avg_outbound_time:.2f}")

    # Save average processing times to a file
    with open("avg_container_times.txt", "w") as f:
        f.write(f"{avg_inbound_time}\n")
        f.write(f"{avg_outbound_time}\n")

    # Output average train processing time
    avg_time_per_train = sum(time_per_train) / len(time_per_train) if time_per_train else 0
    print(f"Processed {train_series} trains")
    print(f"Average processing time per train: {avg_time_per_train:.2f}")

    # Save average processing time to a file
    with open("avg_time_per_train.txt", "w") as f:
        f.write(str(avg_time_per_train))

    # Create DataFrame for container events
    container_data = []

    for container_id, events in sorted(container_events.items()):
        container_type = 'inbound' if container_id < 10001 else 'outbound'
        if container_type == 'inbound':
            container_process_time = events.get('truck_exit', '-') - events.get('train_arrival', '-') if 'truck_exit' in events and 'train_arrival' in events else '-'
        else:
            container_process_time = events.get('train_depart', '-') - events.get('truck_drop_off', '-') if 'train_depart' in events and 'truck_drop_off' in events else '-'

        container_data.append({
            'container_id': container_id,
            'container_type': container_type,
            'train_arrival': events.get('train_arrival', '-'),
            'truck_arrival': events.get('truck_arrival', '-'),
            'crane_unload': events.get('crane_unload', '-'),
            'hostler_pickup': events.get('hostler_pickup', '-'),
            'hostler_dropoff': events.get('hostler_dropoff', '-'),
            'truck_drop_off': events.get('truck_drop_off', '-'),
            'truck_pickup': events.get('truck_pickup', '-'),
            'truck_exit': events.get('truck_exit', '-'),
            'crane_load': events.get('crane_load', '-'),
            'train_depart': events.get('train_depart', '-'),
            'container_processing_time': container_process_time
        })

    df = pd.DataFrame(container_data)
    filename = f"C:/Users/Irena Tong/PycharmProjects/RailRoadSimul/results/simulation_hostler_{HOSTLER_NUMBER}_crane_{CRANE_NUMBER}.xlsx"
    df.to_excel(filename, index=False)

    # 调用 save_average_times 和 save_vehicle_logs 来保存车辆平均工作时间和详细日志
    save_average_times()
    save_vehicle_logs()

    print("Done!")

if __name__ == "__main__":
    run_simulation()
