import os
import re

def read_captions(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def split_captions(text, folder_path, file_path):
    # Initialize counters
    processed_count = 0
    error_count = 0

    # Create description and prompt directories if they don't exist
    desc_dir = os.path.join(folder_path, 'descriptions')
    prompt_dir = os.path.join(folder_path, 'prompts')
    os.makedirs(desc_dir, exist_ok=True)
    os.makedirs(prompt_dir, exist_ok=True)

    # Create or open a log file for zero-processed files
    log_file = os.path.join(folder_path, 'zero_processed_files.txt')

    # Updated section splitting to handle "Files processed..." sections
    sections = re.split(r'(?:\n\s*|^)(\*\*\d+\.\*\*|Prompt:\n|Files processed in this batch)', text)
    sections = [s.strip() for s in sections if s.strip()]

    # Combine section headers with their content
    new_sections = []
    for i in range(0, len(sections), 2):
        if i + 1 < len(sections):
            if sections[i] == 'Files processed in this batch':
                # Find the end of the "Files processed" section
                end_index = i + 2
                while end_index < len(sections) and not re.match(r'(\*\*\d+\.\*\*|Prompt:)', sections[end_index]):
                    end_index += 1
                
                # Combine the header and content for the "Files processed" section
                new_sections.append(' '.join(sections[i:end_index]))
                
                # Skip the already processed parts
                i = end_index - 2
            else:
                new_sections.append(sections[i] + "\n" + sections[i+1])
    
    sections = new_sections
            
    print(f"Number of sections found: {len(sections)}")
    if sections:
        print("First section preview:")
        print(sections[0][:200])

    # Extract filenames from the header section
    filename_pattern = r'^\d+\.\s+(\d+\.png)'
    filenames = []
    if 'Files processed in this batch' in text:
        file_list = text.split('=== Analysis ===')[0]
        filenames = re.findall(filename_pattern, file_list, re.MULTILINE)

    print(f"Number of filenames found: {len(filenames)}")
    print("Filenames found:", filenames)

    # Updated patterns for this specific format
    description_patterns = [
        r'\*\*\d+\.\*\*\n\*\*Description:\*\*\n(.*?)(?=\n\n\*\*Prompt:|\n$)',  # Pattern for numbered sections
        r'\*\*Description:\*\*\n(.*?)(?=\n\n\*\*Prompt:|\n$)',  # Pattern when numbers are missing but structure is maintained
        r'Description:\*\*\n(.*?)(?=\n\nPrompt:|\n$)', # Pattern for unformatted start
        r'\*\*Description:\*\*(.*?)(?=\n\n\*\*|$)', # Pattern for edge cases
        r'Files processed in this batch.*?(\d+\.png).*?=== Analysis ===\s*(?:.*\n)*?\*\*Description:\*\*\s*(.*?)(?=\*\*Prompt:|\n$)',  # For "Files processed..." sections
    ]

    prompt_patterns = [
        r'\*\*\d+\.\*\*\n\*\*Prompt:\*\*\n(.*?)(?=\n\n\*\*\d+\.\*\*|\n$)',  # Pattern for numbered sections
        r'\*\*Prompt:\*\*\n(.*?)(?=\n\n\*\*Description:|\n$)',  # Pattern when numbers are missing but structure is maintained
        r'Prompt:\*\*\n(.*?)(?=\n\n\*\*|\n$)',  # Pattern for unformatted start
        r'\*\*Prompt:\*\*(.*?)(?=\n\n\*\*|$)',  # Pattern for edge cases
        r'Files processed in this batch.*?(\d+\.png).*?=== Analysis ===\s*(?:.*\n)*?\*\*Prompt:\*\*\s*(.*?)(?=\*\*Description:|\n$)',  # For "Files processed..." sections
    ]
    
    # Ensure that we process the correct number of sections corresponding to filenames
    for i in range(min(len(filenames), len(sections))):
        filename = filenames[i]
        section = sections[i]

        try:
            base_name = filename.replace('.png', '')
            print(f"\nProcessing file {base_name}")
            print(f"Section preview: {section[:200]}...")

            # Try to find description and prompt
            description = None
            prompt = None

            # First try to find description
            for pattern in description_patterns:
                # Special handling for "Files processed..." sections
                if "Files processed in this batch" in section:
                    match = re.search(pattern, section, re.DOTALL)
                    if match and match.group(1) == filename:
                        description = match.group(2).strip()
                        print(f"Found description: {description[:50]}...")
                        break
                else:
                    match = re.search(pattern, section, re.DOTALL)
                    if match:
                        description = match.group(1).strip()
                        print(f"Found description: {description[:50]}...")
                        break

            # Then try to find prompt
            for pattern in prompt_patterns:
                # Special handling for "Files processed..." sections
                if "Files processed in this batch" in section:
                    match = re.search(pattern, section, re.DOTALL)
                    if match and match.group(1) == filename:
                        prompt = match.group(2).strip()
                        print(f"Found prompt: {prompt[:50]}...")
                        break
                else:
                    match = re.search(pattern, section, re.DOTALL)
                    if match:
                        prompt = match.group(1).strip()
                        print(f"Found prompt: {prompt[:50]}...")
                        break

            if not description:
                print("DEBUG: Could not find description. Section content:")
                print(section)
            if not prompt:
                print("DEBUG: Could not find prompt. Section content:")
                print(section)

            # Save files if found
            try:
                if description:
                    desc_file = os.path.join(desc_dir, f"{base_name}.txt")
                    with open(desc_file, 'w', encoding='utf-8') as f:
                        f.write(description)
                    print(f"Saved description to {desc_file}")

                if prompt:
                    prompt_file = os.path.join(prompt_dir, f"{base_name}.txt")
                    with open(prompt_file, 'w', encoding='utf-8') as f:
                        f.write(prompt)
                    print(f"Saved prompt to {prompt_file}")

                if description and prompt:
                    processed_count += 1
                else:
                    error_count += 1
                    print(f"WARNING: Missing {'description' if not description else 'prompt'} for {filename}")

            except IOError as e:
                print(f"Error writing files for {filename}: {str(e)}")
                error_count += 1

        except Exception as e:
            print(f"Error processing section {i+1} ({filename}): {str(e)}")
            error_count += 1

    print(f"\nProcessed: {processed_count} (with both description and prompt)")
    print(f"Errors: {error_count} (missing either description or prompt)")

    # If nothing was processed, log the file name
    if processed_count == 0:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"Zero items processed in file: {os.path.basename(folder_path)}\n")

def main():
    try:
        folder_path = input("Enter the path to the folder containing the captions: ").strip()

        # if the input from the user has backquotes, single quotes, or double quotes, remove them
        folder_path = folder_path.replace('"', '').replace("'", '').replace('`', '')

        if not os.path.isdir(folder_path):
            print(f"Error: '{folder_path}' is not a valid directory.")
            return

        # Clear the log file at the start
        log_file = os.path.join(folder_path, 'zero_processed_files.txt')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Files with zero successful processes:\n\n")

        caption_files = [f for f in os.listdir(folder_path)
                         if f.endswith('.txt') and not (f.startswith('d_') or f.startswith('p_'))]

        if not caption_files:
            print("No caption files found in the specified directory.")
            return

        for file in caption_files:
            try:
                file_path = os.path.join(folder_path, file)
                text = read_captions(file_path)
                split_captions(text, folder_path, file_path)
            except Exception as e:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"Error processing file {file}: {str(e)}\n")

        print(f"\nProcessing complete. Check {log_file} for files with zero successful processes.")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    main()