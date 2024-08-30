import pandas as pd
import os

print(os.getcwd())
dir = os.path.dirname(os.path.abspath(__file__))

# Load the CSV into a DataFrame
df = pd.read_csv(os.path.join(dir, 'chexpert_demo_df_labels.csv'))

# Update the image path to use 'updated_path'
df['Path'] = df['updated_path']

# Remove the specific prefix from the 'Path' column
prefix = '/home/joseph/datasets/chexpertchestxrays-u20210408/'
df['Path'] = df['Path'].str.replace(prefix, '', regex=False)

# Replace blank labels with 0
labels = ['No Finding', 'Enlarged Cardiomediastinum', 'Cardiomegaly', 'Lung Opacity', 'Lung Lesion', 'Edema', 'Consolidation', 'Pneumonia', 'Atelectasis', 'Pneumothorax', 'Pleural Effusion', 'Pleural Other', 'Fracture', 'Support Devices']
for label in labels:
    df[label] = df[label].apply(lambda x: 0 if x != 1 else x)

# Select only the columns of interest and reorder them
output_columns = ['Path'] + labels
df = df[output_columns]

df.columns = df.columns.str.replace(' ', '_')


out = os.path.join(dir, 'demo.csv')
# Save the transformed DataFrame to a new CSV file
# Write the DataFrame to CSV without a header for the Path column only
with open(out, 'w', newline='') as file:
    df.to_csv(file, index=False, header=True)
    # Read the file and rewrite it to remove the header for the Path column
    with open(out, 'r') as file:
        lines = file.readlines()
    # Modify the header to remove the 'Path' column header
    lines[0] = lines[0].replace('Path', '')
    with open(out, 'w') as file:
        file.writelines(lines)