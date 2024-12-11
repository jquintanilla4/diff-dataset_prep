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
import json

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Define the path for an initial sample image used in the one-shot example
image_path_1 = "/Users/jquintanilla/Library/CloudStorage/GoogleDrive-jorgeq@remko.io/My Drive/WSBBC_PSDs/WSBBC_dataset/small_set_ch01/0020.png"
sample_file_1 = PIL.Image.open(image_path_1)


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

# Configure the generation settings for the Gemini model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# Define the prompt to be used for generating descriptions and prompts
prompt = """Please describe what's in this image, and if there's a character, also describe its expression. The character is not an anthropomorphic food, it's a cartoon character. 

After that, please create a new paragraph titled "Prompt", in which you will create a comprehensive prompt for the generative image model Flux. Include all of these elements:
1. Character features and expressions (facial features, emotions, distinctive traits)
2. Positioning and actions (pose, gestures, movement)
3. Environmental details (surroundings, objects, terrain)
4. Color information (palette, specific colors of elements)
5. Spatial relationships (composition, placement of elements)
6. Scene composition (framing, depth, perspective)
7. Time of day lighting conditions (natural or artificial light sources)
8. Shadow details (cast shadows, ambient occlusion)
9. Atmospheric effects (air quality, mood, ambiance)
10. Light interaction (how light affects different surfaces and materials)
11. Weather implications (environmental conditions)
12. Atmospheric perspective (depth, distance effects)

The prompt should be detailed but stay under 512 tokens. This prompt will be used for training a LoRA."""

# Construct the one-shot example as a string (to be included in system instruction)
one_shot_example_str = f"""
**Prompt:** {prompt}

**Image:** (Base64 encoded JPEG image data below)
{sample_file_1_jpeg}

**Response:**
**Description:**
This is a cartoon illustration, depicting a character engaged in gardening on a sloped landscape under a partly cloudy sky.

The character, positioned in the center-left of the frame, has a round, yellow face with exaggerated features, including large, round eyes with a skeptical expression, a small red nose, and a wide mouth with a prominent, pink tongue. It has a mop of black hair styled into an "M" shape on its forehead. It's dressed in a red t-shirt with yellow Chinese characters that translate to "Don't eat" and blue shorts. It is holding a garden rake in its right hand and a white towel with a yellow tint in its left hand, seemingly wiping sweat off his forehead.

The character appears to be working on the soil, which is a rich brown color. The rake is in the soil, suggesting recent tilling. Nearby, there are a few notable elements: a worm lying on the ground, appearing lifeless with "X" marks for eyes; a purple, slug-like creature with similar "X" eyes; and a small green plant with a white flower to the left.

The background features a hill with a gradient of green hues, suggesting grass, and a large, bare tree with snow on some of its branches to the right. The tree's branches are spread out, and it has a textured trunk. The sky is white, with a blue, clouded hill in the distance. The overall color palette is warm, with the use of yellows, browns, and greens dominating the scene.

**Individual Prompt:**
Mid-afternoon garden scene with character in center-left position, illuminated by bright natural daylight casting soft shadows. Character features: round yellow face with large round eyes showing skeptical expression, small red nose catching light, wide mouth with prominent pink tongue, distinctive black hair styled in "M" shape on forehead, face showing signs of exertion. Dynamic pose with body bent slightly forward, right hand gripping garden rake actively working soil, left hand raised holding white-yellow tinted towel wiping forehead sweat. Wearing red t-shirt with clear yellow Chinese characters reading "don't eat", fabric catching natural light, paired with blue shorts. Environment shows rich brown tilled soil in foreground with detailed furrows and ambient occlusion, small green plant with delicate white flower nearby, lifeless worm with "X" eyes and purple slug-like creature with matching "X" eyes adding environmental detail. Scene composition creates depth through layered elements: detailed soil texture in foreground, character at middle ground, large bare tree with snow-dusted branches and textured trunk anchoring right side of background, rolling green hill with gradient showing atmospheric perspective, white partly cloudy sky above, and blue clouded hills fading atmospherically in far distance. Warm color palette harmonizes yellows, reds, blues, browns, and varied greens throughout scene. Clear air quality with slight distance haze creates peaceful gardening atmosphere under mild weather conditions, natural light interacting distinctly with each surface from character's skin to soil texture.
"""

# Define the system instruction (including the one-shot example)
system_instruction = (
    "You're an illustrator, photographer, painter, and cinematographer. "
    "An expert in describing images and all of its details. "
    "For each image, provide a detailed description followed by an individual prompt "
    "that captures all the specific details of that particular image. "
    "Each image should have its own description and prompt, clearly separated. "
    "Here is an example of how to perform the task:\n\n"
) + one_shot_example_str

# Initialize the Gemini model with the specified configuration and system instructions
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction,
)


def process_folder(folder_path, model, prompt, batch_size=5, max_images=3000):
    """Process images in batches, analyzing all images in each batch together."""
    image_files = [filename for filename in os.listdir(folder_path)
                   if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff'))]
    image_files = image_files[:max_images]

    with tqdm(total=len(image_files), desc="Processing images") as pbar:
        for i in range(0, len(image_files), batch_size):
            batch_files = image_files[i:i + batch_size]
            batch_messages = []
            batch_output_path = os.path.join(folder_path, f"batch_{i}_analysis.txt")

            # Skip if this batch has already been processed
            if os.path.exists(batch_output_path) and os.path.getsize(batch_output_path) > 0:
                print(f"Skipping batch {i}: Analysis file already exists")
                pbar.update(len(batch_files))
                continue

            try:
                # Prepare all images in the batch
                for filename in batch_files:
                    image_path = os.path.join(folder_path, filename)
                    new_image = PIL.Image.open(image_path)
                    resized_new_image = resize_image(new_image, max_dimension=512)
                    new_image_jpeg = pil_to_base64_jpeg(resized_new_image, quality=85)

                    batch_messages.append({
                        'mime_type': 'image/jpeg', 
                        'data': new_image_jpeg
                    })

                # Add prompt after all images
                messages = batch_messages + [f"Analyze the following {len(batch_messages)} images.\n{prompt}"]

                # Generate content for all images in batch
                response = generate_with_retry(model, messages)

                # Save the raw response
                raw_response_path = os.path.join(folder_path, f"raw_response_batch_{i}.json")
                with open(raw_response_path, 'w', encoding='utf-8') as f:
                    json.dump(response.to_dict(), f, indent=4)

                # Save the batch analysis
                with open(batch_output_path, 'w', encoding='utf-8') as f:
                    f.write(response.text.strip())
                print(f"Processed batch {i} -> {batch_output_path}")

            except Exception as e:
                print(f"Error processing batch {i}: {e}")

            pbar.update(len(batch_files))


def generate_with_retry(model, messages, max_retries=5):
    """
    Generates content using the provided generative model, with retry logic for handling exceptions.

    Args:
        model: The generative model to use for generating content.
        messages: The input messages for content generation, including image data and text prompt.
        max_retries: The maximum number of retries in case of exceptions.

    Returns:
        The raw response object, or raises an exception after retries.
    """
    retry_count = 0
    base_delay = 10  # Initial delay in seconds
    delay_multiplier = 2.5  # Multiplier for exponential backoff
    request_options = {"timeout": 120.0}  # Timeout for each API request

    while retry_count < max_retries:
        try:
            start_time = time.time()
            # Generate content using the provided model and messages
            response = model.generate_content(
                messages,
                request_options=request_options
            )
            print(f" API call took {time.time() - start_time:.2f} seconds")

            # Return the raw response object
            return response

        except (ResourceExhausted, DeadlineExceeded) as e:
            print(f"Attempt {retry_count + 1} failed. Error: {e}")
            retry_count += 1

            if retry_count == max_retries:
                raise

            # Calculate delay with exponential backoff and random jitter
            delay = base_delay * (delay_multiplier ** retry_count) + random.uniform(0, base_delay * retry_count)
            print(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)  # Wait for the calculated delay before retrying


def main():
    # Get folder path from user
    folder_path = input("Enter the path to the folder containing images: ").strip()

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    # Process the folder using the module-level one_shot_example
    process_folder(folder_path, model, prompt, batch_size=5, max_images=30)


if __name__ == "__main__":
    main()