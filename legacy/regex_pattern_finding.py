import json
import os
import re
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
import time
import random
from tqdm import tqdm

# Load environment variables
load_dotenv()

prompt = """Analyze the given text and identify regex patterns specifically for splitting caption files into description and prompt sections. Return only a JSON object with two arrays:
1. 'description_patterns': Patterns that match text between a Description header and the next Prompt section
2. 'prompt_patterns': Patterns that match text between a Prompt header and the next section or end of file

The patterns should handle variations of:
- "**Description:**" or "Description:**" headers
- "**Prompt:**" or "Prompt:**" headers
- Numbered sections (e.g., "**1. Description:**")
- Various whitespace and newline combinations

Example response format:
{
    "description_patterns": [
        ["r'Description:\\*\\*\\n\\n(.*?)\\n\\n\\*\\*Prompt:'", "Matches basic Description-to-Prompt format"],
        ["r'\\*\\*\\d+\\.\\s*Description:\\*\\*\\n\\n(.*?)\\n\\n'", "Matches numbered Description sections"]
    ],
    "prompt_patterns": [
        ["r'Prompt:\\*\\*\\n\\n(.*?)(?=\\n\\n|$)'", "Matches basic Prompt-to-end format"],
        ["r'\\*\\*\\d+\\.\\s*Prompt:\\*\\*\\n\\n(.*?)(?=\\n\\n\\*\\*|$)'", "Matches numbered Prompt sections"]
    ]
}

Use proper regex syntax with capture groups and ensure patterns work with re.DOTALL flag."""


def analyze_with_llm(text, max_retries=5):
    """Use LLM to discover patterns in the text."""
    retry_count = 0
    base_delay = 10
    delay_multiplier = 2.5

    while retry_count < max_retries:
        try:
            client = OpenAI(
                api_key=os.getenv("GEMINI_API_KEY"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )

            response = client.chat.completions.create(
                model="gemini-1.5-flash",
                # model="gemini-2.0-flash-exp",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing text patterns and creating regex expressions. You must ONLY return valid JSON with no additional formatting or text."},
                    {"role": "user",
                        "content": f"{prompt}\n\nText to analyze:\n{text[:2000]}"}
                ],
                timeout=120.0
            )
            try:
                # Extract and clean the response text from the LLM
                response_text = response.choices[0].message.content.strip()

                # Handle markdown code blocks by extracting JSON content
                if "```" in response_text:
                    parts = response_text.split("```")
                    # Check for proper markdown code block structure (content before, between, and after ``` marks)
                    if len(parts) >= 3:
                        response_text = parts[1]
                        # Remove "json" language identifier if present
                        if response_text.startswith("json"):
                            response_text = response_text[4:]

                response_text = response_text.strip()

                # Attempt to parse the cleaned text as JSON
                patterns = json.loads(response_text)

                # Validate the JSON has the expected structure with description and prompt patterns
                if isinstance(patterns, dict) and \
                   'description_patterns' in patterns and \
                   'prompt_patterns' in patterns:
                    return patterns
                else:
                    print(f"Invalid response format: {response_text}")
                    retry_count += 1
                    continue

            except json.JSONDecodeError as e:
                # Handle JSON parsing failures by logging and retrying
                print(f"JSON parsing error: {e}")
                print(f"Raw response: {response_text}")
                retry_count += 1
                continue

        except Exception as e:
            # Handle any other API or processing errors
            print(f"API call failed. Error: {e}")
            retry_count += 1

        # Implement exponential backoff with jitter for retries
        if retry_count < max_retries:
            # Calculate delay using exponential backoff formula with random jitter
            delay = base_delay * (delay_multiplier ** retry_count) + \
                random.uniform(0, base_delay * retry_count)
            print(f"Retrying in {delay:.2f} seconds...")
            try:
                time.sleep(delay)
            except KeyboardInterrupt:
                # Allow graceful cancellation of retries
                print("\nOperation cancelled by user")
                return None

    # If all retries are exhausted, fall back to default patterns
    print("Max retries reached, falling back to regex patterns")
    return None


def analyze_file_patterns(file_path):
    """Analyze a single file for potential description and prompt patterns."""
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    patterns_found = {
        'description': [],
        'prompt': []
    }

    # Use LLM-based pattern discovery
    llm_patterns = analyze_with_llm(text)
    if llm_patterns:
        patterns_found['description'].extend(llm_patterns['description_patterns'])
        patterns_found['prompt'].extend(llm_patterns['prompt_patterns'])

    return patterns_found


def find_patterns_in_folder(folder_path):
    """Analyze all txt files in a folder and collect unique patterns."""
    pattern_frequency = {
        'description': defaultdict(int),
        'prompt': defaultdict(int)
    }

    # Get all txt files in the folder
    txt_files = [f for f in os.listdir(folder_path)
                 if f.endswith('.txt') and not (f.startswith('d_') or f.startswith('p_'))]

    print(f"Found {len(txt_files)} text files to analyze.")

    # Analyze each file with progress bar
    for file in tqdm(txt_files, desc="Analyzing files", unit="file"):
        file_path = os.path.join(folder_path, file)
        try:
            patterns = analyze_file_patterns(file_path)

            # Count pattern frequencies
            for pattern, desc in patterns['description']:
                pattern_frequency['description'][(pattern, desc)] += 1
            for pattern, desc in patterns['prompt']:
                pattern_frequency['prompt'][(pattern, desc)] += 1

        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            continue

    return pattern_frequency


def main():
    folder_path = input("Enter the path to the folder containing the caption files: ").strip()
    folder_path = folder_path.replace('"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    print("\nAnalyzing files for caption splitting patterns...")
    with tqdm(total=1, desc="Overall Progress") as pbar:
        pattern_frequency = find_patterns_in_folder(folder_path)
        pbar.update(1)

    # Update the output format to be more focused
    patterns_file = os.path.join(folder_path, 'caption_patterns.txt')
    
    with open(patterns_file, 'w', encoding='utf-8') as f:
        f.write("# Caption Splitting Patterns\n\n")
        
        f.write("## Description Patterns\n")
        f.write("Add these to description_patterns in split_captions.py:\n```python\n")
        for (pattern, desc), count in sorted(pattern_frequency['description'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"    {pattern},  # {desc} ({count} occurrences)\n")
        f.write("```\n\n")
        
        f.write("## Prompt Patterns\n")
        f.write("Add these to prompt_patterns in split_captions.py:\n```python\n")
        for (pattern, desc), count in sorted(pattern_frequency['prompt'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"    {pattern},  # {desc} ({count} occurrences)\n")
        f.write("```\n")

    print(f"\nCaption splitting patterns have been written to: {patterns_file}")


if __name__ == '__main__':
    main()
