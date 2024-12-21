import os
import glob


def remove_trigger_word(file_path, search_word, replacement_word):
    try:
        # Read the content of the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if the search word exists in the content
        if search_word in content:
            # Replace all occurrences of the search word
            new_content = content.replace(search_word, replacement_word)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Processed: {file_path}")
        else:
            print(f"Skipped: {file_path} (word '{search_word}' not found)")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def process_directory(directory_path, search_word, replacement_word):
    # Get all .txt files in the directory
    txt_files = glob.glob(os.path.join(directory_path, "*.txt"))

    print(f"\nProcessing directory: {directory_path}")
    print(f"Replacing '{search_word}' with '{replacement_word}'")

    # Process each file
    for file_path in txt_files:
        remove_trigger_word(file_path, search_word, replacement_word)


def main():
    # Get directory path from user input
    directory = input(
        "Enter the path to the folder containing the text files: ").strip()
    search_word = input("Enter the word to search for: ").strip()
    replacement_word = input("Enter the replacement word: ").strip()

    # Remove quotes if present
    directory = directory.replace('"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return

    process_directory(directory, search_word, replacement_word)


if __name__ == "__main__":
    main()
