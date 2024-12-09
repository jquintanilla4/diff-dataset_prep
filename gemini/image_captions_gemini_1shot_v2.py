import os
import time
import random
import base64
from dotenv import load_dotenv
import PIL.Image
from PIL import Image
import io
import google.generativeai as genai
import os.path
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# image_path_1 = "/home/jquintanilla/Diffusion/image_datasets/WSBBC_dataset/small_set_ch01/0020.png"
image_path_1 = "/Users/jquintanilla/Library/CloudStorage/GoogleDrive-jorgeq@remko.io/My Drive/WSBBC_PSDs/WSBBC_dataset/small_set_ch01/0020.png"
sample_file_1 = PIL.Image.open(image_path_1)

# Choose a Gemini model.
# Gemini 1.5 Flash
# generation_config = {
#   "temperature": 1,
#   "top_p": 0.95,
#   "top_k": 40,
#   "max_output_tokens": 8192,
#   "response_mime_type": "text/plain",
# }

# model = genai.GenerativeModel(
#   model_name="gemini-1.5-flash",
#   generation_config=generation_config,
#   system_instruction="You're an illustrator, photographer, painter, and cinematographer. An expert in describing images and all of its details.",
# )

# Gemini-exp-1206
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-exp-1206",
  generation_config=generation_config,
  system_instruction="You're an illustrator, photographer, painter, and cinematographer. An expert in describing images and all of its details.",
)

prompt = "Please describe what's in this image, and if there's a character, also describe its expression. The character is not an anthropomorphic food, it's a cartoon character. After that, please create a new paragraph title \"Prompt\", in which you will reformat the image description and any additional details you mentioned into a verbose prompt for the generative image model Flux. This prompt will be used for training a LoRA."


# Function to resize image while maintaining aspect ratio
def resize_image(image, max_dimension=512):
    """Resizes an image, maintaining aspect ratio, so the largest dimension is no more than max_dimension."""
    width, height = image.size

    if max(width, height) <= max_dimension:
        return image  # No need to resize

    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))

    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    return resized_image

# Function to convert PIL image to base64 encoded JPEG
def pil_to_base64_jpeg(image, quality=85):
    """Converts a PIL image to a base64 encoded JPEG string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=quality)
    return base64.b64encode(buffered.getvalue()).decode()

# Resize and convert the sample image for the one-shot example
resized_sample_file_1 = resize_image(sample_file_1, max_dimension=512)
sample_file_1_jpeg = pil_to_base64_jpeg(resized_sample_file_1, quality=85)

# Define the one-shot example once, at the module level
one_shot_example = [{
    "role": "user",
    "parts": [prompt, sample_file_1_jpeg]  # Using the base64 JPEG string for the example
}, {
    "role": "model",
    "parts": [
        "This is a cartoon illustration, depicting a character engaged in gardening on a sloped landscape under a partly cloudy sky.\n\nThe character, positioned in the center-left of the frame, has a round, yellow face with exaggerated features, including large, round eyes with a skeptical expression, a small red nose, and a wide mouth with a prominent, pink tongue. It has a mop of black hair styled into an \"M\" shape on its forehead. It's dressed in a red t-shirt with yellow Chinese characters that translate to \"Don't eat\" and blue shorts. It is holding a garden rake in its right hand and a white towel with a yellow tint in its left hand, seemingly wiping sweat off its forehead.\n\nThe character appears to be working on the soil, which is a rich brown color. The rake is in the soil, suggesting recent tilling. Nearby, there are a few notable elements: a worm lying on the ground, appearing lifeless with \"X\" marks for eyes; a purple, slug-like creature with similar \"X\" eyes; and a small green plant with a white flower to the left.\n\nThe background features a hill with a gradient of green hues, suggesting grass, and a large, bare tree with snow on some of its branches to the right. The tree's branches are spread out, and it has a textured trunk. The sky is white, with a blue, clouded hill in the distance. The overall color palette is warm, with the use of yellows, browns, and greens dominating the scene.\n\n**Prompt**\n\n```\n(masterpiece, best quality:1.2), absurdres, highres, original, extremely detailed, perfect lighting, cinematic lighting, Cartoon illustration of a character gardening on a sloped landscape under a partly cloudy sky. The character has a round yellow face, large round eyes with a skeptical expression, a small red nose, a wide mouth with a prominent pink tongue, black hair in an \"M\" shape. Wearing a red t-shirt with yellow Chinese characters \"Don't eat\", blue shorts. Holding a garden rake in the right hand and a white towel with a yellow tint in the left, wiping sweat. Rich brown soil, a lifeless worm with \"X\" eyes, a purple slug-like creature with \"X\" eyes, a small green plant with a white flower. Background with a green gradient hill, a large bare tree with snow on branches to the right, textured trunk. White sky, blue clouded hill in the distance. Warm color palette with yellows, browns, and greens.\n```\n"
    ]
}]

def process_folder(folder_path, model, one_shot_example, prompt):
    """Process all images in the given folder."""
    # Get list of image files first
    image_files = [filename for filename in os.listdir(folder_path) 
                   if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff'))]
    
    # Create progress bar
    with tqdm(total=len(image_files), desc="Processing images") as pbar:
        for filename in image_files:
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"
            
            # Skip if text file already exists and is not empty
            if os.path.exists(txt_path):
                if os.path.getsize(txt_path) == 0:
                    os.remove(txt_path)
                    print(f"Deleted empty file: {txt_path}")
                else:
                    print(f"Skipping {filename}: Text file already exists")
                    pbar.update(1)
                    continue

            try:
                # Process the new image
                new_image = PIL.Image.open(image_path)
                resized_new_image = resize_image(new_image, max_dimension=512)
                new_image_jpeg = pil_to_base64_jpeg(resized_new_image, quality=85)

                # Create message for the new image
                new_image_message = {
                    "role": "user",
                    "parts": [prompt, new_image_jpeg]
                }

                # Generate content with retry logic
                response = generate_with_retry(model, one_shot_example + [new_image_message])

                # Write response to text file
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)

                print(f"Processed {filename} -> {txt_path}")
                print(f"Response:\n{response.text}\n")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
            
            pbar.update(1)

def generate_with_retry(model, messages, max_retries=5):
    """Generate content with retry logic."""
    retry_count = 0
    base_delay = 10
    delay_multiplier = 2.5
    request_options = {"timeout": 120.0}

    while retry_count < max_retries:
        try:
            start_time = time.time()
            response = model.generate_content(
                messages,
                request_options=request_options
            )
            print(f"API call took {time.time() - start_time:.2f} seconds")
            return response

        except (ResourceExhausted, DeadlineExceeded) as e:
            print(f"Attempt {retry_count + 1} failed. Error: {e}")
            retry_count += 1
            
            if retry_count == max_retries:
                raise

            delay = base_delay * (delay_multiplier ** retry_count) + random.uniform(0, base_delay * retry_count)
            print(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)

def main():
    # Get folder path from user
    folder_path = input("Enter the path to the folder containing images: ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    # Process the folder using the module-level one_shot_example
    process_folder(folder_path, model, one_shot_example, prompt)

if __name__ == "__main__":
    main()