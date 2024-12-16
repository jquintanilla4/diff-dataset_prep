import os
import glob
import time
import random
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from tools.caption_starters import clean_caption

# Load environment variables from .env file
load_dotenv()

# function to clean up phrases from the caption. Because LLMs/VLMs are not perfect
def process_caption(caption, max_retries=5):
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
                n=1,
                messages=[
                    {"role": "system", "content": "You are an expert prompt editor and crafter, and a helpful assistant. You are an expert at cleaning up prompts from image captions."},
                    {
                        "role": "user",
                        "content": f"Please remove any descriptions of art mediums, such as illustration, cartoon; art style, such as watercolor; digital tools such as paper; or creation processes from the following caption. Please remove any caption starters such as 'An illustration featuring ', 'The image is ', 'The scene is ', 'An illustration of ', and any like them. Please also remove any quotation marks, parethesis, and other non-text characters. Rephrase any sentences that contain colons, such as 'Expression: Surprise or astonishment' to something like 'The expression is surprise or astonishment'. If the sentence has none in it such as 'Atmospheric effects: None', remove that sentence. Any references to a black M, black M shape, M shaped, styled M, or black hair styled as M should be rephrased to a 'black M eyebrow'. If any caption has more than one paragaph, please reformat it to only be one paragraph. The caption is meant to used by a T5 text encoder, so we have 512 tokens to use, please be descriptive enough when editing the caption, but not overly verbose or overly consice. Please only return a cleaned caption: {caption}"
                    }
                ],
                timeout=120.0  # Add timeout parameter
            )
            return response.choices[0].message.content.strip()

        except Exception as e: # if there is an error, print the error and retry
            print(f"Attempt {retry_count + 1} failed. Error: {e}")
            retry_count += 1

            if retry_count == max_retries:
                raise

            delay = base_delay * (delay_multiplier ** retry_count) + random.uniform(0, base_delay * retry_count) # calculate the delay
            print(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)

# function to process the files


def process_files(folder_path, prepend_text):
    # Create a 'cleaned' subdirectory if it doesn't exist
    cleaned_folder = os.path.join(folder_path, "cleaned")
    os.makedirs(cleaned_folder, exist_ok=True)

    # Get a list of of all txt files for tqdm
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))

    # Create a progress bar for the files processing progress
    for filename in tqdm(txt_files, desc="Processing captions", unit="file"):
        try:
            # Create new filename for cleaned caption
            base_name = os.path.basename(filename)
            name_without_p = base_name[2:] if base_name.startswith('p_') else base_name
            name_without_ext = os.path.splitext(name_without_p)[0]
            new_filename = os.path.join(cleaned_folder, f"{name_without_ext}_c.txt")

            # Skip if already processed
            if os.path.exists(new_filename) and os.path.getsize(new_filename) > 0: # checks if the pathfile exists and is not empty
                print(f"Skipping {filename}: Already processed")
                continue

            # Process the caption
            with open(filename, 'r') as file:
                original_caption = file.read().strip()
            
            # clean the caption
            cleaned_caption = clean_caption(original_caption)

            # process the caption
            processed_caption = process_caption(cleaned_caption)

            # use cleaned_caption if prepend_text is 'n', otherwise use full_caption
            final_caption = processed_caption if prepend_text.lower() == 'n' else f"{prepend_text}, {processed_caption}"

            # Write the caption
            with open(new_filename, 'w', encoding='utf-8') as file:
                file.write(final_caption)

            print(f"Processed: {base_name} -> {name_without_ext}_c.txt") # basename -> name_without_ext_c.txt

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue  # Continue with next file if there's an error


def main():
    folder_path = input("Enter the path to the folder containing the prompt text files: ").strip()

    # if the input from the user has backquotes, single quotes, or double quotes, remove them
    folder_path = folder_path.replace('"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    prepend_text = input("Enter the prepend text/token (e.g., 'arcane oil') or 'n' to skip: ").strip()

    process_files(folder_path, prepend_text)


if __name__ == "__main__":
    main()
