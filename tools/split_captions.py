import os
import re

def read_captions(file_path):
    """Reads the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def split_captions(text, folder_path, file_path, log_file):
    """Splits the captions text into descriptions and prompts, and saves them into separate files.

    Args:
        text (str): The text content of the captions file.
        folder_path (str): The path to the folder where the captions file is located.
        file_path (str): The full path to the captions file.
        log_file (str): The path to the log file.
    """
    # Initialize counters
    processed_count = 0
    error_count = 0

    # Create description and prompt directories if they don't exist
    desc_dir = os.path.join(folder_path, 'descriptions')
    prompt_dir = os.path.join(folder_path, 'prompts')
    os.makedirs(desc_dir, exist_ok=True)
    os.makedirs(prompt_dir, exist_ok=True)

    # Updated section splitting to handle "Files processed..." sections
    sections = re.split(r'(?:\n\s*|^)(\*\*\d+\.\*\*|Prompt:\n|Files processed in this batch)', text)
    sections = [s.strip() for s in sections if s.strip()]

    # Combine section headers with their content
    new_sections = []
    i = 0
    while i < len(sections):
        if i + 1 < len(sections):
            if sections[i] == 'Files processed in this batch':
                # Find the end of the "Files processed" section
                end_index = i + 2
                while end_index < len(sections) and not re.match(r'(\*\*\d+\.\*\*|Prompt:)', sections[end_index]):
                    end_index += 1
                
                # Combine the header and content for the "Files processed" section
                new_sections.append(' '.join(sections[i:end_index]))
                
                # Skip the already processed parts
                i = end_index
            else:
                new_sections.append(sections[i] + "\n" + sections[i+1])
                i += 2
        else:
            i += 1
    
    sections = new_sections

    log_message(log_file, f"Number of sections found: {len(sections)}")
    if sections:
        log_message(log_file, "First section preview:")
        log_message(log_file, sections[0][:200])

    # Extract filenames from the header section
    filename_pattern = r'^\d+\.\s+(\d+\.png)'
    filenames = []
    if 'Files processed in this batch' in text:
        file_list = text.split('=== Analysis ===')[0]
        filenames = re.findall(filename_pattern, file_list, re.MULTILINE)

    log_message(log_file, f"Number of filenames found: {len(filenames)}")
    log_message(log_file, "Filenames found: " + str(filenames))

    # Updated patterns for this specific format
    description_patterns = [
        r'\*\*\d+\.\*\*\n\*\*Description:\*\*\n(.*?)(?=\n\n\*\*Prompt:|\n$)',  # Pattern for numbered sections
        r'\*\*Description:\*\*\n(.*?)(?=\n\n\*\*Prompt:|\n$)',  # Pattern when numbers are missing but structure is maintained
        r'Description:\*\*\n(.*?)(?=\n\nPrompt:|\n$)', # Pattern for unformatted start
        r'\*\*Description:\*\*(.*?)(?=\n\n\*\*|$)', # Pattern for edge cases
        r'Files processed in this batch.*?\b{filename}\b.*?=== Analysis ===\s*(?:.*\n)*?\*\*Description:\*\*\s*(.*?)(?=\*\*Prompt:|\n$)',  # For "Files processed..." sections
    ]

    prompt_patterns = [
        r'\*\*\d+\.\*\*\n\*\*Prompt:\*\*\n(.*?)(?=\n\n\*\*\d+\.\*\*|\n$)',  # Pattern for numbered sections
        r'\*\*Prompt:\*\*\n(.*?)(?=\n\n\*\*Description:|\n$)',  # Pattern when numbers are missing but structure is maintained
        r'Prompt:\*\*\n(.*?)(?=\n\n\*\*|\n$)',  # Pattern for unformatted start
        r'\*\*Prompt:\*\*(.*?)(?=\n\n\*\*|$)',  # Pattern for edge cases
        r'Files processed in this batch.*?\b{filename}\b.*?=== Analysis ===\s*((?:.*\n)*?)\*\*Prompt:\*\*\s*(.*?)(?=\*\*Description:|\n$)',  # For "Files processed..." sections
    ]

    # Ensure that we process the correct number of sections corresponding to filenames
    for i in range(min(len(filenames), len(sections))):
        filename = filenames[i]
        section = sections[i]

        try:
            base_name = filename.replace('.png', '')
            log_message(log_file, f"\nProcessing file {base_name}")
            log_message(log_file, f"Section preview: {section[:200]}...")

            # Try to find description and prompt
            description = None
            prompt = None

            # Find description
            for pattern in description_patterns:
                description_match = find_match(section, pattern, filename)
                if description_match:
                    description = description_match
                    log_message(log_file, f"Found description: {description[:50]}...")
                    break

            # Find prompt
            for pattern in prompt_patterns:
                prompt_match = find_match(section, pattern, filename)
                if prompt_match:
                    prompt = prompt_match
                    log_message(log_file, f"Found prompt: {prompt[:50]}...")
                    break

            if not description:
                log_message(log_file, "DEBUG: Could not find description. Section content:")
                log_message(log_file, section)
            if not prompt:
                log_message(log_file, "DEBUG: Could not find prompt. Section content:")
                log_message(log_file, section)
            
            # Save files if found
            if description:
                desc_file = os.path.join(desc_dir, f"{base_name}.txt")
                save_to_file(desc_file, description)
                log_message(log_file, f"Saved description to {desc_file}")

            if prompt:
                prompt_file = os.path.join(prompt_dir, f"{base_name}.txt")
                save_to_file(prompt_file, prompt)
                log_message(log_file, f"Saved prompt to {prompt_file}")

            if description and prompt:
                processed_count += 1
            else:
                error_count += 1
                log_message(log_file, f"WARNING: Missing {'description' if not description else 'prompt'} for {filename}")

        except Exception as e:
            log_message(log_file, f"Error processing section {i+1} ({filename}): {str(e)}")
            error_count += 1

    log_message(log_file, f"\nProcessed: {processed_count} (with both description and prompt)")
    log_message(log_file, f"Errors: {error_count} (missing either description or prompt)")

    # If nothing was processed, log the file name
    if processed_count == 0:
        log_message(log_file, f"Zero items processed in file: {os.path.basename(folder_path)}")

def find_match(section, pattern, filename):
    """
    Searches for a match in the section using the given pattern and filename.
    Handles special replacement of {filename} in the pattern.

    Args:
        section (str): The section text to search within.
        pattern (str): The regex pattern to use for searching.
        filename (str): The filename to replace {filename} in the pattern.

    Returns:
        str or None: The matched text if found, otherwise None.
    """
    # Replace {filename} with the actual filename, escaping regex special characters
    pattern = pattern.replace('{filename}', re.escape(filename))
    match = re.search(pattern, section, re.DOTALL)
    return match.group(1).strip() if match else None

def save_to_file(file_path, content):
    """
    Saves the given content to a file.

    Args:
        file_path (str): The path to the file.
        content (str): The content to save.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def log_message(log_file, message):
    """
    Logs a message to the specified log file.

    Args:
        log_file (str): The path to the log file.
        message (str): The message to log.
    """
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def main():
    try:
        folder_path = input("Enter the path to the folder containing the captions: ").strip()

        # Remove surrounding quotes if present
        folder_path = folder_path.strip('\'"`')

        if not os.path.isdir(folder_path):
            print(f"Error: '{folder_path}' is not a valid directory.")
            return

        # Clear and initialize the log file
        log_file = os.path.join(folder_path, 'zero_processed_files.txt')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Log file for processed files:\n\n")

        caption_files = [f for f in os.listdir(folder_path)
                         if f.endswith('.txt') and not (f.startswith('d_') or f.startswith('p_'))]

        if not caption_files:
            print("No caption files found in the specified directory.")
            return

        for file in caption_files:
            try:
                file_path = os.path.join(folder_path, file)
                text = read_captions(file_path)
                split_captions(text, folder_path, file_path, log_file)
            except Exception as e:
                log_message(log_file, f"Error processing file {file}: {str(e)}")

        print(f"\nProcessing complete. Check {log_file} for more information.")

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    main()