import subprocess
import pandas as pd
import time

hostler_numbers = [1, 2, 3, 4, 5, 6, 7]
crane_numbers = [1, 2, 3]
train_units = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

results = []

try:
    # Iterate through all parameter combinations
    for hn in hostler_numbers:
        for cn in crane_numbers:
            for tu in train_units:
                # Record start time
                start_time = time.time()

                # Run test.py and pass parameters
                process = subprocess.run(
                    ['python', 'baseline.py'],
                    input=f"{tu}\n{hn}\n{cn}\n",
                    text=True,
                    capture_output=True,
                    timeout=300  # Set timeout (seconds)
                )

                if process.returncode != 0:
                    print(f"Error running test.py with TRAIN_UNITS={tu}, HOSTLER_NUMBER={hn}, CRANE_NUMBER={cn}")
                    print(process.stderr)
                    continue

                try:
                    with open("avg_time_per_train.txt", "r") as f:
                        avg_time_per_train = float(f.read().strip())
                except FileNotFoundError:
                    print(f"File avg_time_per_train.txt not found for TRAIN_UNITS={tu}, HOSTLER_NUMBER={hn}, CRANE_NUMBER={cn}")
                    continue

                try:
                    with open("avg_container_times.txt", "r") as f:
                        avg_inbound_time, avg_outbound_time = map(float, f.readlines())
                except FileNotFoundError:
                    print(f"File avg_container_times.txt not found for TRAIN_UNITS={tu}, HOSTLER_NUMBER={hn}, CRANE_NUMBER={cn}")
                    continue

                end_time = time.time()
                duration = end_time - start_time

                results.append({
                    "HOSTLER_NUMBER": hn,
                    "CRANE_NUMBER": cn,
                    "TRAIN_UNITS": tu,
                    "avg_time_per_train": avg_time_per_train,
                    "avg_inbound_time": avg_inbound_time,
                    "avg_outbound_time": avg_outbound_time,
                    "duration": duration
                })
except KeyboardInterrupt:
    print("Simulation interrupted by user")

finally:
    df = pd.DataFrame(results)
    df.to_excel("simulation_results.xlsx", index=False)
    print("Done!")
