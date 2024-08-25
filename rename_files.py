import os
import re

# function to get the next available number
def get_next_number(folder_path):
    pattern = re.compile(r'image_(\d{4})\..*') # pattern to match the image files
    max_number = 0 # initialize the max number to 0
    for filename in os.listdir(folder_path): # loop through all the files in the folder
        match = pattern.match(filename) # match the filename to the pattern
        if match:
            number = int(match.group(1)) # get the number from the filename
            max_number = max(max_number, number) # update the max number
    return max_number + 1 if max_number > 0 else 1 # return the next available number, starting from 1 if no files are found

def rename_files(folder_path):
    # get all files in the folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    # sort files
    files.sort()

    # Get the next available number
    next_number = get_next_number(folder_path)

    # rename files
    for filename in files:
        if not re.match(r'image_\d{4}\..*', filename):
            # create new file name
            new_filename = f"image_{next_number:04d}{os.path.splitext(filename)[1]}"

            # construct old file path and new file path
            old_file_path = os.path.join(folder_path, filename)
            new_file_path = os.path.join(folder_path, new_filename)

            # rename file
            os.rename(old_file_path, new_file_path)
            print(f"Renamed {filename} -> {new_filename}")

            next_number += 1

def main():
    folder_path = input("Enter the path to the folder containing the files to be renamed: ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return
    
    rename_files(folder_path)

if __name__ == "__main__":
    main()