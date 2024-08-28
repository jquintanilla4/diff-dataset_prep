import os
import glob
from ollama import Client

# function to clean up phrases from the caption. Because LLMs/VLMs are not perfect
def process_caption(caption):
    client = Client()
    prompt = f"Remove any descriptions of art mediums, digital tools, or creation processes from the following caption. Remove any quotation marks. Return only the cleaned caption: {caption}"
    
    response = client.chat(model='llama3.1:8b-instruct-fp16', messages=[
        {
            'role': 'user', 'content': prompt,
        }
    ])
    
    return response['message']['content'].strip()

# function to process the files
def process_files(folder_path, prepend_text):
    for filename in glob.glob(os.path.join(folder_path, '*.txt')):
        with open(filename, 'r') as file:
            original_caption = file.read().strip()
        
        cleaned_caption = process_caption(original_caption)

        # use cleaned_caption if prepend_text is 'n', otherwise use full_caption
        final_caption = cleaned_caption if prepend_text.lower() == 'n' else f"{prepend_text}, {cleaned_caption}"

        # write the caption to a text file in the same directory
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(final_caption)
        
        print(f"Processed: {filename}")

def main():
    folder_path = input("Enter the path to the folder containing images: ").strip()
    prepend_text = input("Enter the prepend text/token (e.g., 'arcane oil') or 'n' to skip: ").strip()

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return
    
    process_files(folder_path, prepend_text)

if __name__ == "__main__":
    main()