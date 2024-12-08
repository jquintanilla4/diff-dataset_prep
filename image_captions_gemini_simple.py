import os
import time
import base64
from dotenv import load_dotenv
import PIL.Image
from PIL import Image
import io
import google.generativeai as genai
import os.path

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Test with a single image
image_path = "/home/jquintanilla/Diffusion/image_datasets/WSBBC_dataset/small_set_ch01/0022.png"
image = PIL.Image.open(image_path)


# Function to convert PIL image to base64
def pil_to_base64_jpeg(image, quality=75):
    """Converts a PIL image to a base64 encoded JPEG string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=quality)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def resize_image(image_path, max_dimension=512):
    """Resizes an image, maintaining aspect ratio, so the largest dimension is no more than max_dimension."""
    image = Image.open(image_path)
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


# Simplified generation config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # Using more stable model for testing
    generation_config=generation_config,
    system_instruction="You're an illustrator, photographer, painter, and cinematographer. An expert in describing images and all of its details.",
)

prompt = "Please describe what's in this image, and if there's a character, also describe its expression. After that, please create a new paragraph title \"Prompt\", in which you will reformat the image description into a verbose prompt for image generation."

new_image = resize_image(image_path, max_dimension=512)
new_image_jpeg_base64 = pil_to_base64_jpeg(new_image, quality=85)

# Simple message without one-shot example
message = {
    "role": "user",
    "parts": [prompt, new_image_jpeg_base64]
}

try:
    start_time = time.time()
    response = model.generate_content(message)
    end_time = time.time()
    duration = end_time - start_time
    print(f"API call took {duration:.2f} seconds")
    
    # Save response to file
    base_filename = os.path.splitext(image_path)[0]
    output_path = f"{base_filename}_test.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"Response saved to: {output_path}")
    print("\nGenerated response:")
    print(response.text)

except Exception as e:
    print(f"Error occurred: {str(e)}")