import os
from PIL import Image
import ollama

def clean_caption(caption):
    return caption.replace("The image is", "").replace("The art style is ", "")\
        .replace("The overall style of the artwork is ", "")\
        .replace("an illustration featuring ", "").strip()

def process_image(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"
            
            # Check if a corresponding text file exists
            if os.path.exists(txt_path):
                # If the text file is empty, delete it and process the image
                if os.path.getsize(txt_path) == 0:
                    os.remove(txt_path)
                    print(f"Deleted empty file: {txt_path}")
                else:
                    # Skip this image if a non-empty text file exists
                    print(f"Skipping {filename}: Text file already exists")
                    continue
            
            # Get caption from Ollama
            response = ollama.chat(
                model='llama3.2-vision:11b-instruct-q8_0',
                messages=[{
                    'role': 'user',
                    'content': 'Describe this image and its art style.',
                    'images': [image_path]
                }]
            )
            
            # Extract caption from response
            caption = response['message']['content']
            
            # Clean the caption
            cleaned_caption = clean_caption(caption)

            # Write the caption to a text file
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_caption)

            print(f"{filename}: {cleaned_caption} -> {txt_path}")

def main():
    folder_path = input("Enter the path to the folder containing images: ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    process_image(folder_path)

if __name__ == '__main__':
    main()
