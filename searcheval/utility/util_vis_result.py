import pandas as pd
import json
import ipywidgets as widgets
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from IPython.display import display, clear_output


def vis_search_eval_json(json_file: str):

    with open(json_file, "r") as f:
        data = json.load(f)

    # Transform the data into a DataFrame
    rows = []
    for query, details in data.items():
        row = {"query": query}
        for strategy, score_details in details["scores"].items():
            row[strategy] = score_details["ndgc"]
        rows.append(row)

    df = pd.DataFrame(rows)
    df.set_index("query", inplace=True)

    # Calculate the average scores and append as a new row
    average_scores = df.mean().to_dict()
    average_scores["query"] = "Average NDCG Score"
    average_df = pd.DataFrame([average_scores])
    average_df.set_index("query", inplace=True)
    df = pd.concat([df, average_df])

    # Sort columns by strategy name in ascending order
    df = df[sorted(df.columns)]

    # Create a custom colormap
    cmap = LinearSegmentedColormap.from_list("custom_cmap", ["red", "yellow", "green"])

    # Create a function to update the heatmap
    def update_heatmap():
        clear_output(wait=True)  # Clear the previous output
        
        plt.figure(figsize=(12, 8))
        ax = sns.heatmap(df, annot=True, cmap=cmap, cbar=True, vmin=0, vmax=1)
        plt.xlabel('Strategies')
        plt.ylabel('Queries')
        plt.title('Search Evaluation Heatmap', fontsize=20)  # Make the title bigger
        plt.xticks(rotation=45, ha='right')  # Angle the x-axis labels
        
        # Add a horizontal line to separate the average row
        ax.hlines(y=len(df)-1, xmin=0, xmax=len(df.columns), color='black', linewidth=2)
        
        # Make the average row text bolder
        for t in ax.texts:
            if t.get_text() == 'Average':
                t.set_weight('bold')
                t.set_fontsize(12)
        
        plt.show()

    # Create a button to update the heatmap
    update_button = widgets.Button(description="Update Heatmap")

    # Define the button click event
    def on_button_click(b):
        update_heatmap()

    # Attach the event to the button
    update_button.on_click(on_button_click)

    # Display the button and the initial heatmap
    display(update_button)
    update_heatmap()



def vis_deep_eval_correct_tests(json_file: str, title: str = "DeepEval Correctness Heatmap"):
    with open(json_file, "r") as f:
        data = json.load(f)

    # Transform the data into a DataFrame
    rows = []
    total_tokens = {strategy: 0 for strategy in list(data.values())[0]["strategies"].keys()}

    for query, details in data.items():
        row = {"query": details['query']}
        for strategy, strategy_details in details["strategies"].items():
            # row[strategy] = strategy_details["scores"]["Correctness (GEval)"]["score"]
            row[strategy] = strategy_details["scores"]["Citation Correctness (DAG)"]["score"]
            total_tokens[strategy] += strategy_details["tokens_used"]
        rows.append(row)

    df = pd.DataFrame(rows)
    df.set_index("query", inplace=True)

    # Calculate the average scores and append as a new row
    average_scores = df.mean().to_dict()
    average_scores["query"] = "Average Correctness Score"
    average_df = pd.DataFrame([average_scores])
    average_df.set_index("query", inplace=True)
    df = pd.concat([df, average_df])

    # Sort columns by strategy name in ascending order
    df = df[sorted(df.columns)]

    # Update column labels to include total tokens used
    updated_columns = [f"{strategy}\nTokens: {total_tokens[strategy]:,}" for strategy in df.columns]
    df.columns = updated_columns

    # Create a custom colormap
    cmap = LinearSegmentedColormap.from_list("custom_cmap", ["red", "yellow", "green"])

    # Create a function to update the heatmap
    def update_heatmap2():
        clear_output(wait=True)  # Clear the previous output
        
        plt.figure(figsize=(12, 8))
        ax = sns.heatmap(df, annot=True, cmap=cmap, cbar=True, vmin=0, vmax=1)
        plt.xlabel('Strategies / RAG LLM Tokens')
        plt.ylabel('Queries')
        plt.title(title, fontsize=20)  # Make the title bigger
        plt.xticks(rotation=45, ha='right')  # Angle the x-axis labels
        
        # Add a horizontal line to separate the average row
        ax.hlines(y=len(df)-1, xmin=0, xmax=len(df.columns), color='black', linewidth=2)
        
        # Make the average row text bolder
        for t in ax.texts:
            if t.get_text() == 'Average':
                t.set_weight('bold')
                t.set_fontsize(12)
        
        plt.show()

    # Create a button to update the heatmap
    update_button = widgets.Button(description="Update Heatmap")

    # Define the button click event
    def on_button_click(b):
        update_heatmap2()

    # Attach the event to the button
    update_button.on_click(on_button_click)

    # Display the button and the initial heatmap
    display(update_button)
    update_heatmap2()