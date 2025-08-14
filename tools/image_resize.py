from PIL import Image
import os


def resize_image(image_path, target_size=1024, resize_largest=False, resize_height=False, resize_width=False):
    with Image.open(image_path) as img:
        width, height = img.size

        # Resize the largest dimension
        if resize_largest:
            if width <= target_size and height <= target_size:
                print(
                    f"Skipped: {os.path.basename(image_path)} (already fits criteria)")
                return False

            # Determine the new size
            if width > height:
                new_size = (target_size, int(height * (target_size / width)))
            else:
                new_size = (int(width * (target_size / height)), target_size)

            # Resize the image
            resized_img = img.resize(new_size, Image.LANCZOS)
            resized_img.save(image_path)
            return True

        # Resize the height
        if not resize_largest and resize_height:
            new_size = (int(width * (target_size / height)), target_size)
            resized_img = img.resize(new_size, Image.LANCZOS)
            resized_img.save(image_path)
            return True

        # Resize the width
        if not resize_largest and resize_width:
            new_size = (target_size, int(height * (target_size / width)))
            resized_img = img.resize(new_size, Image.LANCZOS)
            resized_img.save(image_path)
            return True


def process_directory(directory, target_size=1024, resize_largest=False, resize_height=False, resize_width=False):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_path = os.path.join(directory, filename)
            if resize_image(image_path, target_size, resize_largest, resize_height, resize_width):
                print(f"Resized: {filename}")


def main():
    directory = input("Enter the directory path containing the images: ").strip()

    # Remove quotes if present
    directory = directory.replace('"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return

    # Choose resize mode
    resize_largest = input("Would you like to resize the largest dimension? (y/n): ").strip().lower() == 'y'

    resize_height = False
    resize_width = False

    if not resize_largest:  # if false
        resize_height = input("Would you like to resize the height? (y/n): ").strip().lower() == 'y'
        if not resize_height:  # if false
            resize_width = input("Would you like to resize the width? (y/n): ").strip().lower() == 'y'

        if not resize_height and not resize_width:
            print("No resize option selected. Exiting.")
            return

    # Ask for the target size based on chosen option
    while True:
        try:
            if resize_largest:
                target_size = int(input("Enter the target size (in pixels) for the largest dimension (e.g., 1024): ").strip())
            elif resize_height:
                target_size = int(input("Enter the target height (in pixels) (e.g., 1024): ").strip())
            else:
                target_size = int(input("Enter the target width (in pixels) (e.g., 1024): ").strip())

            if target_size <= 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid positive integer.")

    process_directory(directory, target_size, resize_largest,
                      resize_height, resize_width)


if __name__ == "__main__":
    main()
