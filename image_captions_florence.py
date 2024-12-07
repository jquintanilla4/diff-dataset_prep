import os
from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AutoModelForCausalLM.from_pretrained("gokaygokay/Florence-2-Flux-Large", trust_remote_code=True).to(device).eval()
processor = AutoProcessor.from_pretrained("gokaygokay/Florence-2-Flux-Large", trust_remote_code=True)

def run_example(task_prompt, text_input, image):
    prompt = task_prompt + text_input

    # Ensure the image is in RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")

    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        num_beams=3,
        repetition_penalty=1.10,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(generated_text, task=task_prompt, image_size=(image.width, image.height))
    return parsed_answer

def clean_caption(caption):
    return caption.replace(
        "The image is", "").replace(
        "The art style is ", "").replace(
        "The overall style of the artwork is ", "").replace(
        "an illustration featuring ", "").strip()

def process_image(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"
            
            # Check if a corresponding text file exists
            if os.path.exists(txt_path):
                if os.path.getsize(txt_path) == 0: # if the text file is empty
                    os.remove(txt_path) # delete the text file
                    print(f"Deleted empty file: {txt_path}")
                else:
                    print(f"Skipping {filename}: Text file already exists")
                    continue
            
            image = Image.open(image_path)
            answer = run_example("<DESCRIPTION>", "Describe this image and art style.", image)
            caption = answer["<DESCRIPTION>"]

            # clean the caption
            cleaned_caption = clean_caption(caption)

            # Write the caption to a text file in the same directory
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