import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    # Initialize the parser
    parser = argparse.ArgumentParser(description="Experiment script.")
    # Adding the arguments
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        default="UCMerced",
        help="The dataset to use",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=False,
        default="Gemini1.5",
        help="The model to use",
    )
    parser.add_argument(
        "--location",
        type=str,
        required=False,
        default="us-central1",
        help="The location for the experiment",
    )
    parser.add_argument(
        "--num_shot_per_class",
        type=int,
        required=True,
        help="The number of shots per class",
    )
    parser.add_argument(
        "--num_qns_per_round",
        type=int,
        required=False,
        default=1,
        help="The number of questions asked each time",
    )
    parser.add_argument(
        "--black_race_split",
        type=float,
        required=False,
        default=0.5,
        help="What ratio of demo example are 'black'. Default to 0.5. 1 correlates with 100 percent black demo examples",
    )

    # Parsing the arguments
    args = parser.parse_args()

    # Using the arguments
    dataset_name = args.dataset
    model = args.model
    num_qns_per_round = args.num_qns_per_round

    results_csv_path = os.path.join(os.getcwd(), f"{dataset_name}_{model}_{num_qns_per_round}_results.csv")

    df = results_df = pd.read_csv(results_csv_path)
    zero_shot = df[df['num_shots_per_class'] == 0]
    df_0 = pd.concat([zero_shot, df[(df['black_race_split'] == 0) & (df['num_shots_per_class'] > 0)]]).sort_values('num_shots_per_class')
    df_1 = pd.concat([zero_shot, df[(df['black_race_split'] == 1) & (df['num_shots_per_class'] > 0)]]).sort_values('num_shots_per_class')
    df_05 = pd.concat([zero_shot, df[(df['black_race_split'] == 0.5) & (df['num_shots_per_class'] > 0)]]).sort_values('num_shots_per_class')
    fig, axes = plt.subplots(ncols=3, figsize=(18, 6), sharey=True)
    axes[0].errorbar(df_0['num_shots_per_class'], df_0['accuracy'], yerr=df_0['acc_error'], color='blue', capsize=3)
    axes[0].set_title('Black Race Split = 0%')
    axes[0].set_xlabel('Num Demo Examples')
    axes[0].set_ylabel('Accuracy')
    axes[0].set_ylim(0, 100)
    axes[2].errorbar(df_1['num_shots_per_class'], df_1['accuracy'], yerr=df_1['acc_error'], color='green', capsize=3)
    axes[2].set_title('Black Race Split = 100%')
    axes[2].set_xlabel('Num Demo Examples')
    axes[2].set_ylim(0, 100)
    axes[1].errorbar(df_05['num_shots_per_class'], df_05['accuracy'], yerr=df_05['acc_error'], color='red', capsize=3)
    axes[1].set_title('Black Race Split = 50%')
    axes[1].set_xlabel('Num Demo Examples')
    axes[1].set_ylim(0, 100)
    fig.suptitle('Accuracy vs. Number of Demo Examples by Black Race Split', y=0.95)
    plt.subplots_adjust(top=0.85)
    plt.show()


    
    df['bias'] = df['black_accuracy'] - df['white_accuracy']
    zero_shot = df[df['num_shots_per_class'] == 0]
    bias_data = {
        '0': pd.concat([zero_shot[['num_shots_per_class', 'bias']], df[df['black_race_split'] == 0][df['num_shots_per_class'] > 0][['num_shots_per_class', 'bias']]]).set_index('num_shots_per_class')['bias'],
        '0.5': pd.concat([zero_shot[['num_shots_per_class', 'bias']], df[df['black_race_split'] == 0.5][df['num_shots_per_class'] > 0][['num_shots_per_class', 'bias']]]).set_index('num_shots_per_class')['bias'],
        '1': pd.concat([zero_shot[['num_shots_per_class', 'bias']], df[df['black_race_split'] == 1][df['num_shots_per_class'] > 0][['num_shots_per_class', 'bias']]]).set_index('num_shots_per_class')['bias']
    }
    bias_df = pd.DataFrame(bias_data)
    bias_df = bias_df.sort_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.25
    x = np.arange(len(bias_df))
    ax.bar(x - bar_width, bias_df['0'], width=bar_width, label='Black Race Split = 0', color='blue')
    ax.bar(x, bias_df['0.5'], width=bar_width, label='Black Race Split = 0.5', color='red')
    ax.bar(x + bar_width, bias_df['1'], width=bar_width, label='Black Race Split = 1', color='green')
    ax.set_xlabel('Num Shots per Class')
    ax.set_ylabel('Bias (Black Accuracy - White Accuracy)')
    ax.set_title('Bias by Num Shots per Class and Black Race Split')
    ax.set_xticks(x)
    ax.set_xticklabels(bias_df.index)
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.8)
    ax.legend()
    plt.tight_layout()
    plt.show()