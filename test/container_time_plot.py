import pandas as pd
import matplotlib.pyplot as plt

def plot_simulation_results(mode, train_units=None, crane=None, hostler=None):
    # Load the simulation results
    df = pd.read_excel('simulation_results.xlsx')

    if mode == 'combination':
        if train_units is None:
            raise ValueError("train_units must be provided for mode 'combination'")

        # Filter data for the given train units
        df_filtered = df[df['TRAIN_UNITS'] == train_units]

        # Create a combined column for crane-hostler combination
        df_filtered['Crane-Hostler'] = df_filtered['CRANE_NUMBER'].astype(str) + '-' + df_filtered[
            'HOSTLER_NUMBER'].astype(str)

        # Plot avg_inbound_time
        plt.figure(figsize=(10, 5))
        plt.plot(df_filtered['Crane-Hostler'], df_filtered['avg_inbound_time'], marker='o', label='Inbound containers')
        plt.plot(df_filtered['Crane-Hostler'], df_filtered['avg_outbound_time'], marker='o', label='Outbound containers')
        plt.xlabel('Crane-Hostler Combination', fontsize=18)
        plt.ylabel('Average Processing Time', fontsize=18)
        plt.title(f'Average Processing Time for TRAIN_UNITS = {train_units}')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif mode == 'units':
        if crane is None or hostler is None:
            raise ValueError("crane and hostler must be provided for mode 'units'")

        # Filter data for the given crane and hostler numbers
        df_filtered = df[(df['CRANE_NUMBER'] == crane) & (df['HOSTLER_NUMBER'] == hostler)]

        # Plot avg_inbound_time
        plt.figure(figsize=(10, 5))
        plt.plot(df_filtered['TRAIN_UNITS'], df_filtered['avg_inbound_time'], marker='o', label='Inbound containers')
        plt.plot(df_filtered['TRAIN_UNITS'], df_filtered['avg_outbound_time'], marker='o', label='Outbound containers')
        plt.xlabel('TRAIN_UNITS', fontsize=18)
        plt.ylabel('Average Processing Time', fontsize=18)
        plt.title(f'Average Processing Time for CRANE_NUMBER = {crane} and HOSTLER_NUMBER = {hostler}')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif mode == 'hostlers':
        if train_units is None:
            raise ValueError("train_units must be provided for mode 'hostlers'")

        # Filter data for the given train units
        df_filtered = df[df['TRAIN_UNITS'] == train_units]

        # Define specific colors for cranes
        colors = ['red', 'limegreen', 'blue']
        color_map = {crane_num: colors[i % len(colors)] for i, crane_num in enumerate(df_filtered['CRANE_NUMBER'].unique())}

        # Plot avg_inbound_time and avg_outbound_time for different cranes
        plt.figure(figsize=(12, 8))
        for crane_num in df_filtered['CRANE_NUMBER'].unique():
            df_crane = df_filtered[df_filtered['CRANE_NUMBER'] == crane_num]
            color = color_map.get(crane_num, 'black')  # Default to black if crane_num is not in color_map
            plt.plot(df_crane['HOSTLER_NUMBER'], df_crane['avg_inbound_time'], marker='o', label=f'Inbound Crane {crane_num}', color=color, linestyle='-')
            plt.plot(df_crane['HOSTLER_NUMBER'], df_crane['avg_outbound_time'], marker='x', label=f'Outbound Crane {crane_num}', color=color, linestyle='--')
        plt.xlabel('Hostler Numbers', fontsize=18)
        plt.ylabel('Average Processing Time', fontsize=18)
        plt.title(f'Average Processing Time for TRAIN_UNITS = {train_units}')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif mode == 'cranes':
        if train_units is None:
            raise ValueError("train_units must be provided for mode 'cranes'")

        # Filter data for the given train units
        df_filtered = df[df['TRAIN_UNITS'] == train_units]

        # Define specific colors for cranes
        colors = ['red', 'orange', 'blue']
        color_map = {crane_num: colors[i % len(colors)] for i, crane_num in enumerate(df_filtered['CRANE_NUMBER'].unique())}

        # Plot avg_inbound_time and avg_outbound_time
        plt.figure(figsize=(12, 8))
        for crane_num in df_filtered['CRANE_NUMBER'].unique():
            df_crane = df_filtered[df_filtered['CRANE_NUMBER'] == crane_num]
            color = color_map.get(crane_num, 'black')  # Default to black if crane_num is not in color_map
            plt.plot(df_crane['CRANE_NUMBER'], df_crane['avg_inbound_time'], marker='o', label=f'Inbound Crane {crane_num}', color=color, linestyle='-')
            plt.plot(df_crane['CRANE_NUMBER'], df_crane['avg_outbound_time'], marker='x', label=f'Outbound Crane {crane_num}', color=color, linestyle='--')
        plt.xlabel('Crane Numbers', fontsize=18)
        plt.ylabel('Average Processing Time', fontsize=18)
        plt.title(f'Average Processing Time for TRAIN_UNITS = {train_units}')
        plt.legend()
        plt.grid(True)
        plt.xticks(df_filtered['CRANE_NUMBER'].unique(), fontsize=12)  # Ensure x-ticks are integers
        plt.yticks(fontsize=12)
        plt.xlim(1, 3)  # Set x-axis limits to zoom in
        plt.tight_layout()
        plt.show()

    else:
        raise ValueError("Invalid mode. Choose either 'combination', 'units', 'hostlers', or 'cranes'.")

# For mode 'cranes'
plot_simulation_results(mode='cranes', train_units=6)

# For mode 'hostlers'
plot_simulation_results(mode='hostlers', train_units=6)

# For mode 'combination'
# plot_simulation_results(mode='combination', train_units=6)

# For mode 'units'
# plot_simulation_results(mode='units', crane=2, hostler=6)
