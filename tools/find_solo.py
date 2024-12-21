import os
import shutil
from pathlib import Path


def find_unpaired_files(folder_path):
    # Convert to Path object for easier handling
    folder = Path(folder_path)

    # Get all files in the directory
    all_files = list(folder.glob('*'))

    # Separate files by extension
    png_files = {f.stem for f in all_files if f.suffix.lower() == '.png'}  # Create a set of file stems for all PNG files; f.stem gives the filename without the extension
    txt_files = {f.stem for f in all_files if f.suffix.lower() == '.txt'}  # Create a set of file stems for all TXT files

    # Find files without pairs
    png_without_txt = png_files - txt_files  # Find PNG files without corresponding TXT files (set difference)
    txt_without_png = txt_files - png_files  # Find TXT files without corresponding PNG files (set difference)

    # Return results
    unpaired = {
        'png_missing_txt': [f"{name}.png" for name in png_without_txt],
        'txt_missing_png': [f"{name}.txt" for name in txt_without_png]
    }

    return unpaired


def move_unpaired_files(folder_path, unpaired_files):
    """Move unpaired files to a new 'unpaired' folder"""
    source_folder = Path(folder_path)
    unpaired_folder = source_folder / 'unpaired'

    # Create unpaired folder if it doesn't exist
    unpaired_folder.mkdir(exist_ok=True)

    moved_files = []

    # Move all unpaired files
    for category in unpaired_files.values():
        for filename in category:
            source_file = source_folder / filename  # Source file path (using '/' to join paths)
            target_file = unpaired_folder / filename  # Target file path in 'unpaired' folder (using '/' to join paths)

            try:
                shutil.move(str(source_file), str(target_file))
                moved_files.append(filename)
            except Exception as e:
                print(f"Error moving {filename}: {str(e)}")

    return moved_files


def get_folder_path():
    """Get and validate folder path from user input"""
    folder_path = input(
        "Enter the path to the folder containing the files: ").strip()

    # Remove any quotes from the path
    folder_path = folder_path.replace(
        '"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return None

    return folder_path


def main():
    folder_path = get_folder_path()
    if folder_path is None:
        return

    # Find unpaired files
    results = find_unpaired_files(folder_path)

    # Print results
    if not any(results.values()):
        print("\nAll files are properly paired!")
        return

    print("\nUnpaired files found:")

    if results['png_missing_txt']:
        print("\nPNG files missing TXT pairs:")
        for file in sorted(results['png_missing_txt']):
            print(f"- {file}")

    if results['txt_missing_png']:
        print("\nTXT files missing PNG pairs:")
        for file in sorted(results['txt_missing_png']):
            print(f"- {file}")

    # Ask user if they want to move the files
    move_files = input(
        "\nDo you want to move unpaired files to an 'unpaired' folder? (y/n): ").lower().strip()

    if move_files == 'y':
        moved_files = move_unpaired_files(folder_path, results)
        if moved_files:
            print(
                f"\nMoved {len(moved_files)} files to the 'unpaired' folder:")
            for file in sorted(moved_files):
                print(f"- {file}")
        else:
            print("\nNo files were moved.")


if __name__ == "__main__":
    main()
