import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image

model_id = "vikhyatk/moondream2"
revision = "2024-07-23"
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision=revision).to("cuda")
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)

# function to clean up phrases from the caption. Because LLMs/VLMs
def  clean_caption(caption):
    return caption.replace("The image is", "").replace("The art style is ", "").replace("The overall style of the artwork is ", "").replace("an illustration featuring ", "").strip()

# function to process the images
def process_image(folder_path, prepend_text):
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
            
            image = Image.open(image_path)
            enc_image = model.encode_image(image)
            caption = model.answer_question(enc_image, "Describe this image and art style. Please do not describe the art medium.", tokenizer)

            # clean the caption
            cleaned_caption = clean_caption(caption)

            full_caption = prepend_text + ", " + cleaned_caption

            
            # Write the caption to a text file in the same directory
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_caption)

            print(f"{filename}: {full_caption} -> {txt_path}")


def main():
    folder_path = input("Enter the path to the folder containing images: ").strip()
    prepend_text = input("Enter the prepend text/token (e.g., 'arcane oil'): ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    process_image(folder_path, prepend_text)

if __name__ == '__main__':
    main()