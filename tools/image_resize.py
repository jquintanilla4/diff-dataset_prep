from PIL import Image
import os

def resize_image(image_path, target_size=1024):
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Check if the image already meets the criteria
        if width <= target_size and height <= target_size:
            print(f"Skipped: {os.path.basename(image_path)} (already fits criteria)")
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

def process_directory(directory):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_path = os.path.join(directory, filename)
            if resize_image(image_path):
                print(f"Resized: {filename}")

def main():
    directory = input("Enter the directory path containing the images: ").strip()

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return

    process_directory(directory)
    
if __name__ == "__main__":
    main()