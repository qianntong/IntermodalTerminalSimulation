import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
mode = 'filter'  # choose filter or total
file_path = 'simulation_results.xlsx'
data = pd.read_excel(file_path)

# Define a function to get a color map for a given crane
def get_shades_of_color(base_color, num_shades):
    base_color = np.array(base_color)
    return [base_color * (1 - i * 0.1) for i in range(num_shades)]

# Base colors for cranes
base_colors = {
    1: [1, 0, 0],  # red
    2: [0, 1, 0],  # green
    3: [0, 0, 1],  # blue
}

# Additional colors for filter mode
filter_colors = [
    [1, 0, 0],  # red
    [0, 1, 0],  # green
    [0, 0, 1],  # blue
    [1, 1, 0],  # yellow
    [1, 0, 1],  # magenta
    [0, 1, 1],  # cyan
    [0.5, 0.5, 0.5]  # gray
]

if mode == 'total':
    pivot_table = data.pivot_table(
        values='avg_time_per_train',
        index='TRAIN_UNITS',
        columns=['HOSTLER_NUMBER', 'CRANE_NUMBER'],
        aggfunc='mean'
    )

    fig, ax = plt.subplots(figsize=(14, 10))

    for (hostler, crane) in pivot_table.columns:
        shades = get_shades_of_color(base_colors[crane], 7)
        ax.plot(pivot_table.index, pivot_table[(hostler, crane)], label=f'Hostler {hostler} & Crane {crane}', color=shades[hostler-1])

    ax.set_title('Average Processing Time per Train Unit for Different Hostler & Crane Combinations')
    ax.set_xlabel('Train Units', fontsize=18)
    ax.set_ylabel('Average Processing Time', fontsize=18)
    ax.legend(title='Hostler & Crane Combinations')
    ax.tick_params(axis='both', which='major')  # Adjust font size of major ticks
    plt.xticks(range(6, 16),fontsize=15)  # Set x-axis to show integers from 6 to 15
    plt.yticks(fontsize=15)
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.15)
    plt.show()

if mode == 'filter':
    filtered_data = data[(data['HOSTLER_NUMBER'].isin([1, 2, 3, 4, 5, 6, 7])) & (data['CRANE_NUMBER'].isin([2]))]

    pivot_table = filtered_data.pivot_table(
        values='avg_time_per_train',
        index='TRAIN_UNITS',
        columns=['HOSTLER_NUMBER', 'CRANE_NUMBER'],
        aggfunc='mean'
    )

    pivot_table = pivot_table.loc[6:15]

    fig, ax = plt.subplots(figsize=(14, 10))

    for (hostler, crane) in pivot_table.columns:
        color = filter_colors[hostler - 1]
        ax.plot(pivot_table.index, pivot_table[(hostler, crane)], label=f'Hostler {hostler} & Crane {crane}', color=color)

    ax.set_title('Average Processing Time per Train Unit for Hostlers 1-7 and Cranes 2',fontsize=18)
    ax.set_xlabel('Train Units',fontsize=18)
    ax.set_ylabel('Average Processing Time',fontsize=18)
    ax.legend(title='Hostler & Crane Combinations')
    ax.tick_params(axis='both', which='major', labelsize=14)  # Adjust font size of major ticks
    plt.xticks(range(6, 16),fontsize=15)  # Set x-axis to show integers from 6 to 15
    plt.yticks(fontsize=15)
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.15)
    plt.show()
