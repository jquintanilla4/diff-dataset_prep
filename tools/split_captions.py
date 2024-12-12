import os
import re

def read_captions(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def split_captions(text, folder_path):
    # Create description and prompt directories if they don't exist
    desc_dir = os.path.join(folder_path, 'descriptions')
    prompt_dir = os.path.join(folder_path, 'prompts')
    os.makedirs(desc_dir, exist_ok=True)
    os.makedirs(prompt_dir, exist_ok=True)

    # Extract filenames from the header
    filename_pattern = r'\d+\.\s+(\d+\.png)' # regex to extract the filename from the header
    filenames = re.findall(filename_pattern, text) # find all the filenames in the header
    
    # Split the text into image sections
    sections = text.split('**Image')[1:]  # Skip the header
    
    for filename, section in zip(filenames, sections): # pair the filenames with the sections; zip is used to pair the filenames with the sections
        base_name = filename.replace('.png', '') # remove the .png extension from the filename
        
        # Extract description and prompt
        description = re.search(r'Description:\*\*\n\n(.*?)\n\n\*\*Prompt:', section, re.DOTALL) # regex to extract the description from the section
        prompt = re.search(r'Prompt:\*\*\n\n(.*?)(?=\n\n|$)', section, re.DOTALL) # regex to extract the prompt from the section
        
        if description and prompt:
            # Write description file to descriptions folder
            desc_path = os.path.join(desc_dir, f'd_{base_name}.txt')
            with open(desc_path, 'w') as f:
                f.write(description.group(1).strip())
            
            # Write prompt file to prompts folder
            prompt_path = os.path.join(prompt_dir, f'p_{base_name}.txt')
            with open(prompt_path, 'w') as f:
                f.write(prompt.group(1).strip())

def main():
    folder_path = input("Enter the path to the folder containing the captions: ").strip()
    
    # if the input from the user has backquotes, single quotes, or double quotes, remove them
    folder_path = folder_path.replace('"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    # Process all caption files in the user specified directory
    for file in os.listdir(folder_path):
        if file.endswith('.txt') and not (file.startswith('d_') or file.startswith('p_')): # check if the file is a caption file and not already split
            text = read_captions(os.path.join(folder_path, file))
            split_captions(text, folder_path)

if __name__ == '__main__':
    main()