import os
import torch
import torch.backends.mps
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image


def get_device():
    """Determine the appropriate device (CUDA, MPS, or CPU)."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def initialize_model(device):
    """Initialize the model and tokenizer."""
    model_id = "vikhyatk/moondream2"
    revision = "2024-08-26"

    # For MPS, we load to CPU first then transfer to MPS
    if device == "mps":
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision=revision).to('cpu')
        model = model.to(device)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, revision=revision).to(device)

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    return model, tokenizer

# function to clean up phrases from the caption. Because LLMs/VLMs
def clean_caption(caption):
    """Clean up common phrases from the caption."""
    replacements = [
        "The image is",
        "The art style is ",
        "The overall style of the artwork is ",
        "an illustration featuring "
    ]

    for phrase in replacements:
        caption = caption.replace(phrase, "")
    return caption.strip()


def process_image(folder_path, model, tokenizer):
    """Process images in the given folder and generate captions."""
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"

            # Skip if non-empty text file exists
            if os.path.exists(txt_path):
                if os.path.getsize(txt_path) == 0:
                    os.remove(txt_path)
                    print(f"Deleted empty file: {txt_path}")
                else:
                    print(f"Skipping {filename}: Text file already exists")
                    continue

            # process the image
            try:
                image = Image.open(image_path)
                enc_image = model.encode_image(image)
                caption = model.answer_question(
                    enc_image, "Describe this image and art style.", tokenizer)

                cleaned_caption = clean_caption(caption)

                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_caption)

                print(f"{filename}: {cleaned_caption} -> {txt_path}")

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")


def main():
    folder_path = input(
        "Enter the path to the folder containing images: ").strip()

    # if the input from the user has backquotes, single quotes, or double quotes, remove them
    folder_path = folder_path.replace(
        '"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    device = get_device()
    print(f"Using device: {device}")

    try:
        model, tokenizer = initialize_model(device)
        process_image(folder_path, model, tokenizer)
    except Exception as e:
        print(f"Error initializing model: {str(e)}")


if __name__ == '__main__':
    main()
