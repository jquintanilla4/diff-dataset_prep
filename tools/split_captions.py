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
    filename_pattern = r'\d+\.\s+(\d+\.png)'
    filenames = re.findall(filename_pattern, text)
    
    # Only print first 5 filenames
    print(f"First 5 filenames: {filenames[:5]}")
    
    # Split the text into image sections
    sections = text.split('**Image')[1:]  # Try first format
    if len(sections) <= 1:  # If first format didn't work
        sections = text.split('\n\n**')[1:]  # Try second format
    
    print(f"Number of sections found: {len(sections)}")
    
    for i, (filename, section) in enumerate(zip(filenames, sections)):
        base_name = filename.replace('.png', '')
        
        # Try different patterns for description
        description_patterns = [
            r'Description:\*\*\n\n(.*?)\n\n\*\*Prompt:',          # Format 1
            r'Description:\*\*\n.*?\n\s*(.*?)\n\n',               # Format 2
            r'\*\*Description:\*\*\n(.*?)\n\n\*\*Prompt:',        # Format 3
            r'Description:\*\*\n(.*?)\n\n(?:\d+\.)?\s*\*\*Prompt:', # Format 4
            r'\d\.\s*Description:\s*(.*?)\n\n\d\.',               # Format 5
            r'\*\*\d+\.\s*Description\*\*\n(.*?)\n\n\*\*\d+\.',   # Format 6
            r'\*\*\d+\.\s*Description:\*\*\n\n(.*?)\n\n\*\*Prompt:', # Format 7
        ]
        
        # Try different patterns for prompt
        prompt_patterns = [
            r'Prompt:\*\*\n\n(.*?)(?=\n\n|$)',                   # Format 1
            r'Prompt:\*\*\n.*?\n\s*(.*?)(?=\n\n|$)',             # Format 2
            r'\*\*Prompt:\*\*\n(.*?)(?=\n\n|$)',                 # Format 3
            r'Individual Prompt:\s*(.*?)(?=\n\n|$)',              # Format 4
            r'\d\.\s*\*\*Prompt:\*\*\n(.*?)(?=\n\n\d\.|$)',      # Format 5
            r'\*\*\d+\.\s*Prompt\*\*\n(.*?)(?=\n\n\*\*|$)',      # Format 6
            r'\*\*Prompt:\*\*\n\n(.*?)(?=\n\n\*\*|$)',          # Format 7
        ]
        
        # Try each description pattern until one works
        description = None
        for pattern in description_patterns:
            description = re.search(pattern, section, re.DOTALL)
            if description:
                break
                
        # Try each prompt pattern until one works
        prompt = None
        for pattern in prompt_patterns:
            prompt = re.search(pattern, section, re.DOTALL)
            if prompt:
                break
        
        # Debug prints only for first 5 files
        if i < 5:
            print(f"\nProcessing file {i+1}/5: {filename}")
            print(f"Description match: {bool(description)}")
            print(f"Prompt match: {bool(prompt)}")
            
            if not description or not prompt:
                print("Section content for debugging:")
                print(section[:200])
            
        if description and prompt:
            # Write description file
            desc_path = os.path.join(desc_dir, f'd_{base_name}.txt')
            with open(desc_path, 'w') as f:
                f.write(description.group(1).strip())
            
            # Write prompt file
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

    # Print only first 5 caption files found
    caption_files = [f for f in os.listdir(folder_path) 
                    if f.endswith('.txt') and not (f.startswith('d_') or f.startswith('p_'))]
    print(f"First 5 caption files found: {caption_files[:5]}")

    # Process all caption files in the user specified directory
    for file in caption_files:
        text = read_captions(os.path.join(folder_path, file))
        split_captions(text, folder_path)

if __name__ == '__main__':
    main()