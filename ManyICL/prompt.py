import traceback
import os
from tqdm import tqdm
import random
import pickle
import numpy as np
from LMM import GPT4VAPI, GeminiAPI
import pandas as pd

PATH_TO_OG_CHEXPERT_CSV = os.path.join(os.getcwd(), 'ManyICL', 'dataset', 'CheXpert', 'chexpert_binaryPNA_demo_df_labels.csv')

def work(
    model,
    num_shot_per_class,
    location,
    num_qns_per_round,
    test_df,
    demo_df,
    classes,
    class_desp,
    SAVE_FOLDER,
    dataset_name,
    black_race_split,
    detail="auto",
    file_suffix="",
):
    """
    Run queries for each test case in the test_df dataframe using demonstrating examples sampled from demo_df dataframe.

    model[str]: the specific model checkpoint to use e.g. "Gemini1.5", "gpt-4-turbo-2024-04-09"
    num_shot_per_class[int]: number of demonstrating examples to include for each class, so the total number of demo examples equals num_shot_per_class*len(classes)
    location[str]: Vertex AI location e.g. "us-central1","us-west1", not used for GPT-series models
    num_qns_per_round[int]: number of queries to be batched in one API call
    test_df, demo_df [pandas dataframe]: dataframe for test cases and demo cases, see dataset/UCMerced/demo.csv as an example
    classes[list of str]: names of categories for classification, and this should match tbe columns of test_df and demo_df.
    class_desp[list of str]: category descriptions for classification, and these are the actual options sent to the model
    SAVE_FOLDER[str]: path for the images
    dataset_name[str]: name of the dataset used
    detail[str]: resolution level for GPT4(V)-series models, not used for Gemini models
    file_suffix[str]: suffix for image filenames if not included in indexes of test_df and demo_df. e.g. ".png"
    """

    class_to_idx = {class_name: idx for idx, class_name in enumerate(classes)}
    EXP_NAME = f"{dataset_name}_{num_shot_per_class*len(classes)}shot_{model}_{num_qns_per_round}_{black_race_split:.2f}split"

    if model.startswith("gpt"):
        api = GPT4VAPI(model=model, detail=detail)
    else:
        assert model == "Gemini1.5"
        api = GeminiAPI(location=location)
    print(EXP_NAME, f"test size = {len(test_df)}")

    # Prepare the demonstrating examples
    # Relies on same number of demo examples per class -- need to change for many shot experiment
    num_black_shots_per_class = int(num_shot_per_class * black_race_split)
    num_white_shots_per_class = num_shot_per_class - num_black_shots_per_class
    df = pd.read_csv(PATH_TO_OG_CHEXPERT_CSV)
    assert num_shot_per_class <= df.shape[0], f"Custom error message: More shots than demo examples available. {num_shot_per_class} requested and {df.shape[0]} available."
    assert num_black_shots_per_class <= df[df['binary_race'] == 'Black'].shape[0], f"Custom error message: More black shots than demo examples available. {num_black_shots_per_class} requested and {df[df['binary_race'] == 'Black'].shape[0]} available."
    assert num_black_shots_per_class <= df[df['binary_race'] == 'White'].shape[0], f"Custom error message: More white shots than demo examples available. {num_white_shots_per_class} requested and {df[df['binary_race'] == 'White'].shape[0]} available."

    demo_examples = []
    for class_name in classes:
        num_cases_class = 0
        num_cases_black = 0
        num_cases_white = 0
        for j in demo_df[demo_df[class_name] == 1].itertuples():
            row = df[df['updated_path'].str.endswith(j.Index)]
            if num_cases_class == num_shot_per_class:
                break
            if row['binary_race'].values[0] == 'Black':
                if num_cases_black == num_black_shots_per_class:
                    continue
                num_cases_black += 1
            elif row['binary_race'].values[0] == 'White':
                if num_cases_white == num_white_shots_per_class:
                    continue
                num_cases_white += 1
            demo_examples.append((j.Index, class_desp[class_to_idx[class_name]]))
            num_cases_class += 1
    assert len(demo_examples) == num_shot_per_class * len(classes)
    assert(num_cases_black == num_black_shots_per_class)
    assert(num_cases_white == num_white_shots_per_class)

    # Load existing results
    if os.path.isfile(f"{EXP_NAME}.pkl"):
        with open(f"{EXP_NAME}.pkl", "rb") as f:
            results = pickle.load(f)
    else:
        results = {}

    test_df = test_df.sample(frac=1, random_state=66)  # Shuffle the test set
    for start_idx in tqdm(range(0, len(test_df), num_qns_per_round), desc=EXP_NAME):
        end_idx = min(len(test_df), start_idx + num_qns_per_round)

        random.shuffle(demo_examples)
        if len(demo_examples) > 0:
            prompt = f"Below are {len(demo_examples)} demonstrating examples:\n\n"
        else:
            prompt = ""
        image_paths = [os.path.join(os.getcwd(), SAVE_FOLDER, 'chexpert_binary_PNA_demo_df',i[0]+file_suffix) for i in demo_examples]
        for demo in demo_examples:
            prompt += f"""<<IMG>>Given the image above, answer the following question using the specified format.
Question: What is in the image above? Note that this is a binary classification problem, so there will only be one choice.
Choices: {str(class_desp)}
Answer Choice: {demo[1]}
"""
        qns_idx = []
        prompt += "\n\n\nBelow is the actual question:\n"
        for idx, i in enumerate(test_df.iloc[start_idx:end_idx].itertuples()):
            qns_idx.append(i.Index)
            image_paths.append(os.path.join(os.getcwd(), SAVE_FOLDER, 'chexpert_binary_PNA_test_df',i.Index+file_suffix))
            qn_idx = idx+1
           
            prompt += f"""<<IMG>>Given the image above, answer the following question using the specified format.
Question {qn_idx}: What is in the image above? Note that this is a binary classification problem, so there will only be one choice.
Choices {qn_idx}: {str(class_desp)}


"""
        for i in range(start_idx, end_idx):
            qn_idx = i-start_idx+1
            prompt += f"""
Please respond with the following format for each question:
---BEGIN FORMAT TEMPLATE FOR QUESTION {qn_idx}---
Answer Choice {qn_idx}: [Your Answer Choice Here for Question {qn_idx}. If the choice is not present in the image, put an empty list]
Confidence Score {qn_idx}: [Your Numerical Prediction Confidence Score Here From 0 To 1 for Question {qn_idx}]
---END FORMAT TEMPLATE FOR QUESTION {qn_idx}---


Do not deviate from the above format. Repeat the format template for the answer."""
            
        # print(prompt)
        qns_id = str(qns_idx)
        for retry in range(3):
            if (
                (qns_id in results)
                and (not results[qns_id].startswith("ERROR"))
                and (
                    f"END FORMAT TEMPLATE FOR QUESTION {end_idx-start_idx}"
                    in results[qns_id]
                )
            ):  # Skip if results exist and successful
                continue

            try:
                res = api(
                    prompt,
                    image_paths=image_paths,
                    real_call=True,
                    max_tokens=60 * num_qns_per_round,
                )
            except Exception as e:
                res = f"ERROR!!!! {traceback.format_exc()}"
            except KeyboardInterrupt:
                previous_usage = results.get("token_usage", (0, 0, 0))
                total_usage = tuple(
                    a + b for a, b in zip(previous_usage, api.token_usage)
                )
                results["token_usage"] = total_usage
                with open(f"{EXP_NAME}.pkl", "wb") as f:
                    pickle.dump(results, f)
                exit()

            print(res)
            results[qns_id] = res

    # Update token usage and save the results
    previous_usage = results.get("token_usage", (0, 0, 0))
    total_usage = tuple(a + b for a, b in zip(previous_usage, api.token_usage))
    results["token_usage"] = total_usage
    with open(f"{EXP_NAME}.pkl", "wb") as f:
        pickle.dump(results, f)

    results_csv_path = os.path.join(os.getcwd(), f"{dataset_name}_{model}_{num_qns_per_round}_results.csv")
    if not os.path.isfile(results_csv_path):
        columns = ['num_shots_per_class', 'black_race_split', 'accuracy', 'acc_error', 'f1', 'f1_error', 'black_accuracy', 'black_acc_error', 'black_f1', 'black_f1_error', 'white_accuracy', 'white_acc_error', 'white_f1', 'white_f1_error']
        df = pd.DataFrame(columns=columns)
        df.to_csv(results_csv_path, index=False)
