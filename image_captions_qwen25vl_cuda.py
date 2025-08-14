# CUDA only because of qwen2vl utils.

import os
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image

def initialize_model():
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-7B-Instruct", 
        torch_dtype="auto", 
        device_map="auto"
    )
    
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
    
    return model, processor


def run_example(processor, model, image):
    # Prepare messages in Qwen2-VL format
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image","image": image,
                    # "resized_height": 1008,
                    # "resized_width": 1008,
                },
                {"type": "text", "text": "Describe this image."},
            ],
        }
    ]
    
    # Process inputs
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda" if torch.cuda.is_available() else "cpu")
    
    # Generate response
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=128,
    )
    
    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    
    generated_text = processor.batch_decode(
        generated_ids_trimmed, 
        skip_special_tokens=True, 
        clean_up_tokenization_spaces=False
    )[0]
    
    return generated_text


def clean_caption(caption):
    return caption.replace(
        "The image is", "").replace(
        "The art style is ", "").replace(
        "The overall style of the artwork is ", "").replace(
        "an illustration featuring ", "").strip()


def process_image(folder_path, model, processor):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"
            
            # Check if a corresponding text file exists
            if os.path.exists(txt_path):
                if os.path.getsize(txt_path) == 0:
                    os.remove(txt_path)
                    print(f"Deleted empty file: {txt_path}")
                else:
                    print(f"Skipping {filename}: Text file already exists")
                    continue
            
            image = Image.open(image_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
                
            caption = run_example(processor, model, image)
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
    
    model, processor = initialize_model()
    process_image(folder_path, model, processor)


if __name__ == '__main__':
    main()