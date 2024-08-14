import os
import argparse


def rename_files(folder_path):
    # get all files in the folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    # sort files
    files.sort()

    # rename files
    for index, filename in enumerate(files, start=1):
        # create new file name
        new_filename = f"image_{index:04d}{os.path.splitext(filename)[1]}"

        # construct old file path and new file path
        old_file_path = os.path.join(folder_path, filename)
        new_file_path = os.path.join(folder_path, new_filename)

        # rename file
        os.rename(old_file_path, new_file_path)
        print(f"Renamed {filename} -> {new_filename}")

def main():
    parser = argparse.ArgumentParser(description="Rename files in a folder to a sequential numbering system")
    parser.add_argument("folder_path", type=str, help="Path to the folder containing the files to be renamed")
    args = parser.parse_args()

    rename_files(args.folder_path)

if __name__ == "__main__":
    main()

# TODO:
# - [ ] add code to check if the folder already has files in the numbering system. If it does, do not rename those and rename those without but starting from the next number