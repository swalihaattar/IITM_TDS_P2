import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import openai
import sys
import os
import requests


# Set up API Key
openai.api_key = os.environ.get("AIPROXY_TOKEN")

import pandas as pd

def load_data(file_path):
    # Load dataset from a CSV file.
    try:
        # Attempt to read the file using UTF-8 encoding.
        # If the file contains non-UTF-8 encoded characters, the program will try a fallback encoding.
        data = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
        print(f"Data loaded successfully from {file_path}")  # Inform the user that the file is successfully loaded.
        return data  # Return the loaded data if successful.
    except UnicodeDecodeError:
        # If there is a UnicodeDecodeError (i.e., UTF-8 decoding fails), attempt to read the file using Latin1 encoding.
        try:
            data = pd.read_csv(file_path, encoding="latin1", on_bad_lines="skip")
            print(f"Data loaded successfully from {file_path}")  # Inform the user of successful load with Latin1 encoding.
            return data  # Return the data if loaded successfully with Latin1 encoding.
        except Exception as e:
            # If any other error occurs during loading (e.g., file not found), print the error message.
            print(f"Error loading data: {e}")
            return None  # Return None if the file cannot be loaded after both encoding attempts.
    except Exception as e:
        # Handle any other general exceptions (e.g., invalid file path).
        print(f"Error loading data: {e}")
        return None  # Return None if any general error occurs during loading.

def analyze_data(data):
    """Perform generic analysis on the dataset."""
    analysis = {}

    # Summary statistics
    analysis["summary_statistics"] = data.describe(include="all")

    # Missing values
    analysis["missing_values"] = data.isnull().sum()

    # Filter numeric columns for correlation
    numeric_data = data.select_dtypes(include=['number'])

    # Correlation matrix (only for numeric columns)
    if numeric_data.shape[1] > 1:
        analysis["correlation"] = numeric_data.corr()
    else:
        analysis["correlation"] = None

    return analysis

def visualize_data(data, output_dir):
    # Generate visualizations from the analysis.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a histogram for each numerical column
    for column in data.select_dtypes(include=["number"]).columns:
        plt.figure(figsize=(8, 6))
        sns.histplot(data[column], kde=True, bins=30)
        plt.title(f"Distribution of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")
        plt.savefig(f"{output_dir}/{column}_histogram.png")
        plt.close()

def generate_narrative(analysis, charts_dir):
    # Generate a narrative from the analysis using the AI Proxy.
    
    # Prepare the data for the LLM (Language Model) prompt.
    # Extract summary statistics and missing values from the analysis.
    summary_stats = analysis["summary_statistics"].to_string()
    missing_values = analysis["missing_values"].to_string()

    # Create the prompt for the LLM based on the extracted analysis.
    prompt = f"""
    Dataset Summary:
    {summary_stats}

    Missing Values:
    {missing_values}

    Create a narrative of the analysis and suggest insights from the data. Mention any charts provided as well.
    """
    
    try:
        # Retrieve the AI Proxy token from the environment variable.
        aip_proxy_token = os.getenv("AIPROXY_TOKEN")
        if not aip_proxy_token:
            # Raise an error if the token is not found.
            raise ValueError("AIPROXY_TOKEN environment variable is not set.")

        # Set up the request to the AI Proxy API.
        url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {aip_proxy_token}"  # Authorization header with the AI Proxy token
        }

        # Prepare the payload with the model and the message prompt.
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }

        # Make the POST request to the AI Proxy API.
        response = requests.post(url, headers=headers, json=payload)

        # If the response status is not successful, raise an exception.
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}, {response.text}")

        # Extract the generated narrative from the response.
        narrative = response.json()["choices"][0]["message"]["content"]
        print("Narrative generated successfully")  # Indicate that the narrative was generated
        return narrative

    except Exception as e:
        # Handle any exceptions during the process and print the error message.
        print(f"Error generating narrative: {e}")
        return "Error generating narrative."

def save_results(narrative, output_dir):
    # Save the generated narrative and charts to files.
    # Save narrative as README.md in the output directory
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(f"# Automated Data Analysis\n\n{narrative}\n")

        # Append the charts in the README
        for chart_file in os.listdir(output_dir):
            if chart_file.endswith(".png"):
                f.write(f"\n![{chart_file}]({chart_file})\n")

def main():
    # Check if the script was run with a CSV file as an argument
    if len(sys.argv) < 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)  # Exit if the dataset file is not provided

    filename = sys.argv[1]  # Get the filename from the command-line arguments
    dataset_name = os.path.splitext(os.path.basename(filename))[0]  # Extract the dataset name (e.g., "goodreads")
    output_folder = dataset_name  # Use the dataset name as the folder name

    # Load the data from the provided CSV file
    data = load_data(filename)
    if data is None:
        return

    # Perform data analysis
    analysis = analyze_data(data)

    # Create the output directory (e.g., "goodreads/")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Visualize the data and save charts in the output folder
    visualize_data(data, output_folder)

    # Generate the narrative from the analysis
    narrative = generate_narrative(analysis, output_folder)

    # Save results (narrative and charts)
    save_results(narrative, output_folder)


if __name__ == "__main__":  
    # This line ensures that the main() function is called when the script is executed directly.
    main()
