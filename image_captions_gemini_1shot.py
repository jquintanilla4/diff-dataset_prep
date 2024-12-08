import os
import time
import random
import base64
from dotenv import load_dotenv
import PIL.Image
import io
import google.generativeai as genai
import os.path

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

image_path_1 = "/home/jquintanilla/Diffusion/image_datasets/WSBBC_dataset/small_set_ch01/0020.png"
image_path_2 = "/home/jquintanilla/Diffusion/image_datasets/WSBBC_dataset/small_set_ch01/0022.png"

sample_file_1 = PIL.Image.open(image_path_1)
new_image = PIL.Image.open(image_path_2)

# Function to convert PIL image to base64
def pil_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# Choose a Gemini model.
# generation_config = { # Generation config for Gemini Exp 1206
#   "temperature": 1,
#   "top_p": 0.95,
#   "top_k": 64,
#   "max_output_tokens": 8192,
#   "response_mime_type": "text/plain",
# }

generation_config = { # Generation config for Gemini 1.5 Flash
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
#   model_name="gemini-exp-1206",
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="You're an illustrator, photographer, painter, and cinematographer. An expert in describing images and all of its details.",
)

prompt = "Please describe what's in this image, and if there's a character, also describe its expression. After that, please create a new paragraph title \"Prompt\", in which you will reformat the image description and any additional details you mentioned  into a verbose prompt for the generative image model Flux. This prompt will be used for training a LoRA."

# Create the one-shot example message with just the response
one_shot_example = [{
    "role": "user",
    "parts": [prompt, pil_to_base64(sample_file_1)]
}, {
    "role": "model",
    "parts": [
        "This is a cartoon illustration, depicting a character engaged in gardening on a sloped landscape under a partly cloudy sky.\n\nThe character, positioned in the center-left of the frame, has a round, yellow face with exaggerated features, including large, round eyes with a skeptical expression, a small red nose, and a wide mouth with a prominent, pink tongue. It has a mop of black hair styled into an \"M\" shape on its forehead. It's dressed in a red t-shirt with yellow Chinese characters that translate to \"Don't eat\" and blue shorts. It is holding a garden rake in its right hand and a white towel with a yellow tint in its left hand, seemingly wiping sweat off its forehead.\n\nThe character appears to be working on the soil, which is a rich brown color. The rake is in the soil, suggesting recent tilling. Nearby, there are a few notable elements: a worm lying on the ground, appearing lifeless with \"X\" marks for eyes; a purple, slug-like creature with similar \"X\" eyes; and a small green plant with a white flower to the left.\n\nThe background features a hill with a gradient of green hues, suggesting grass, and a large, bare tree with snow on some of its branches to the right. The tree's branches are spread out, and it has a textured trunk. The sky is white, with a blue, clouded hill in the distance. The overall color palette is warm, with the use of yellows, browns, and greens dominating the scene.\n\n**Prompt**\n\n```\n(masterpiece, best quality:1.2), absurdres, highres, original, extremely detailed, perfect lighting, cinematic lighting, Cartoon illustration of a character gardening on a sloped landscape under a partly cloudy sky. The character has a round yellow face, large round eyes with a skeptical expression, a small red nose, a wide mouth with a prominent pink tongue, black hair in an \"M\" shape. Wearing a red t-shirt with yellow Chinese characters \"Don't eat\", blue shorts. Holding a garden rake in the right hand and a white towel with a yellow tint in the left, wiping sweat. Rich brown soil, a lifeless worm with \"X\" eyes, a purple slug-like creature with \"X\" eyes, a small green plant with a white flower. Background with a green gradient hill, a large bare tree with snow on branches to the right, textured trunk. White sky, blue clouded hill in the distance. Warm color palette with yellows, browns, and greens.\n```\n"
    ]
}]

# Create a message for the new image
new_image_message = {
    "role": "user",
    "parts": [prompt, pil_to_base64(new_image)]
}

# Add timeout to request options
request_options = { "timeout": 120.0 }  # 120 seconds timeout

# Generate content with timeout and exponential backoff
max_retries = 5
retry_count = 0
base_delay = 1  # Initial delay in seconds

while retry_count < max_retries:
    try:
        messages = one_shot_example + [new_image_message]
        response = model.generate_content(
            messages,
            request_options=request_options
        )
        
        # Get the base filename without extension
        base_filename = os.path.splitext(image_path_2)[0]
        output_path = f"{base_filename}.txt"
        
        # Write the response to a text file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"Response saved to: {output_path}")
        print("New image response:")
        print(response.text)
        break
        
    except Exception as e:
        retry_count += 1
        if retry_count == max_retries:
            print(f"Failed after {max_retries} attempts. Error: {str(e)}")
            raise

        delay = base_delay * (2 ** retry_count) + random.uniform(0, base_delay) # Exponential backoff formula
        print(f"Attempt {retry_count} failed. Retrying in {delay:.2f} seconds... Error: {str(e)}")
        time.sleep(delay)