import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image

model_id = "vikhyatk/moondream2"
revision = "2024-07-23"
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision=revision).to("cuda")
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)

# function to clean up phrases from the caption. Because LLMs/VLMs
def  clean_caption(caption):
    return caption.replace("The image is", "").replace("The art style is ", "").replace("The overall style of the artwork is ", "").strip()

# function to process the images
def process_image(folder_path):
    for filename in  os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"

            image = Image.open(image_path)
            enc_image = model.encode_image(image)
            caption = model.answer_question(enc_image, "Describe this image and art style. Please do not use the words 'The image is'.", tokenizer)

            # clean the caption
            cleaned_caption = clean_caption(caption)

            prepend_text = "oil painting, expressive oil painting, " # change or add more art styles here
            full_caption = prepend_text + cleaned_caption

            
            # Write the caption to a text file in the same directory
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_caption)

            print(f"{filename}: {full_caption} -> {txt_path}")


def main():
    folder_path = 'dataset/images_originals' # change this to the path of the folder containing the images
    process_image(folder_path)

if __name__ == '__main__':
    main()

# TODO:
# - [ ] add code to check if there's pre-existing text files in the folder. If there are any that match the image name, skip the image.
# - [ ] add code to check if the text file is empty. If it is, delete the text file and process the image.
# - [ ] add code to make it so that the script can be run from the command line.