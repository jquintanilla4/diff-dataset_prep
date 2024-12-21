import os
import glob


def remove_trigger_word(file_path, trigger_word):
    try:
        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if the trigger word exists in the content
        if trigger_word in content:
            # Replace only the first occurrence of the trigger word
            new_content = content.replace(trigger_word, '', 1)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Processed: {file_path}")
        else:
            print(
                f"Skipped: {file_path} (trigger word '{trigger_word}' not found)")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def process_directory(directory_path):
    # Get all .txt files in the directory
    txt_files = glob.glob(os.path.join(directory_path, "*.txt"))

    print(f"\nProcessing directory: {directory_path}")

    # Define trigger words to check
    trigger_words = ["BBCDFL, ", "WSBBC, "]
    print(f"Looking for trigger words: {trigger_words}")

    # Process each file
    for file_path in txt_files:
        for trigger_word in trigger_words:
            remove_trigger_word(file_path, trigger_word)


def main():
    # Get directory path from user input
    directory = input(
        "Enter the path to the folder containing the prompt text files: ").strip()

    # if the input from the user has backquotes, single quotes, or double quotes, remove them
    directory = directory.replace(
        '"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return

    process_directory(directory)


if __name__ == "__main__":
    main()
