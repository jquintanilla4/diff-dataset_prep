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
image_path_1 = "/Users/jquintanilla/Library/CloudStorage/GoogleDrive-jorgeq@remko.io/My Drive/WSBBC/WSBBC_dataset/sample_image/0020.png"
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
    # Convert RGBA to RGB if necessary
    if image.mode == "RGBA":
        # Create a white background
        background = PIL.Image.new('RGB', image.size, (255, 255, 255))
        # Paste the image on the background using alpha channel as mask
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode == "RGB":
        # Convert any other mode to RGB
        image = image.convert("RGB")
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=quality)
    return base64.b64encode(buffered.getvalue()).decode()


# Resize and convert the sample image for the one-shot example
resized_sample_file_1 = resize_image(sample_file_1, max_dimension=512)
sample_file_1_jpeg = pil_to_base64_jpeg(resized_sample_file_1, quality=85)


# Define the prompt to be used for generating descriptions and prompts
prompt = """For each image, follow this two-step process:

1. First, internally analyze the image by creating a detailed description including:
- All characters and their expressions
- Actions and positioning
- Environmental elements
- Colors and lighting
- Objects and their relationships
- Overall scene composition

2. Then, based on your internal description, provide ONLY a comprehensive prompt for the generative image model Flux that includes:
- Character features and expressions (facial features, emotions, distinctive traits)
- Positioning and actions (pose, gestures, movement)
- Environmental details (surroundings, objects, terrain)
- Color information (palette, specific colors of elements)
- Spatial relationships (composition, placement of elements)
- Scene composition (framing, depth, perspective)
- Time of day lighting conditions (natural or artificial light sources)
- Shadow details (cast shadows, ambient occlusion)
- Atmospheric effects (air quality, mood, ambiance)
- Light interaction (how light affects different surfaces and materials)
- Weather implications (environmental conditions)
- Atmospheric perspective (depth, distance effects)

Important: Do not include your internal description in the output - only provide the final prompt."""

# Construct the one-shot example as a string (to be included in system instruction)
one_shot_example_str = f"""
**Prompt:** {prompt}

**Image:** (Base64 encoded JPEG image data below)
{sample_file_1_jpeg}

**Response:**
Mid-afternoon garden scene with character in center-left position, illuminated by bright natural daylight casting soft shadows. Character features: round yellow face with large round eyes showing skeptical expression, small red nose catching light, wide mouth with prominent pink tongue, distinctive black hair styled in "M" shape on forehead, face showing signs of exertion. Dynamic pose with body bent slightly forward, right hand gripping garden rake actively working soil, left hand raised holding white-yellow tinted towel wiping forehead sweat. Wearing red t-shirt with clear yellow Chinese characters reading "don't eat", fabric catching natural light, paired with blue shorts. Environment shows rich brown tilled soil in foreground with detailed furrows and ambient occlusion, small green plant with delicate white flower nearby, lifeless worm with "X" eyes and purple slug-like creature with matching "X" eyes adding environmental detail. Scene composition creates depth through layered elements: detailed soil texture in foreground, character at middle ground, large bare tree with snow-dusted branches and textured trunk anchoring right side of background, rolling green hill with gradient showing atmospheric perspective, white partly cloudy sky above, and blue clouded hills fading atmospherically in far distance. Warm color palette harmonizes yellows, reds, blues, browns, and varied greens throughout scene. Clear air quality with slight distance haze creates peaceful gardening atmosphere under mild weather conditions, natural light interacting distinctly with each surface from character's skin to soil texture.
"""

# Define the system instruction (including the one-shot example)
system_instruction = (
    "You're an illustrator, photographer, painter, and cinematographer. "
    "An expert in describing images and all of their details. "
    "Your task is to first internally analyze each image in detail, "
    "then provide only a comprehensive prompt based on that analysis. "
    "Never reference other images in your prompts. "
    "Each prompt must be completely self-contained. "
    "Here is an example of how to perform the task:\n\n"
) + one_shot_example_str


# Configure the generation settings for the Gemini model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the Gemini model with the specified configuration and system instructions
model = genai.GenerativeModel(
    # model_name="gemini-1.5-flash",
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    system_instruction=system_instruction,
)


def process_single_image(image_path, model, prompt):
    """Process a single image and generate analysis."""
    try:
        with PIL.Image.open(image_path) as image:  # File is automatically closed after the with block
            resized_image = resize_image(image, max_dimension=512)  # Resize the image to a max dimension of 512
            image_jpeg = pil_to_base64_jpeg(resized_image, quality=85)  # Convert the resized image to a base64 JPEG

            messages = [
                {
                    'mime_type': 'image/jpeg',  # Specify the MIME type as JPEG
                    'data': image_jpeg  # Include the base64 encoded image data
                },
                f"Analyze the image.\n{prompt}"  # Add the prompt for analysis
            ]

            response = generate_with_retry(model, messages)  # Generate content using the model with retry logic

            filename = os.path.basename(image_path)  # Extract the filename from the image path
            base_name = os.path.splitext(filename)[0]  # Get the base name without extension
            
            output_filename = f"p_{base_name}.txt"  # Create the output filename with "p_" prefix
            output_path = os.path.join(os.path.dirname(image_path), output_filename)  # Determine the full output path

            with open(output_path, 'w', encoding='utf-8') as f:  # Open the output file for writing
                f.write(response.text.strip())

            return True  # Return True to indicate successful processing

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False  # Return False to indicate failure


def process_folder(folder_path, model, prompt, max_images=3000):
    """
    Process all images in a folder one at a time.
    """
    image_files = [  # List comprehension to filter image files in the folder
        filename for filename in os.listdir(folder_path)  # Iterate over files in the specified folder
        if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.gif', '.bmp', '.tiff'))  # Check for valid image extensions
    ]
    image_files = image_files[:max_images]  # Limit the number of images to process

    with tqdm(total=len(image_files), desc="Processing images") as pbar:  # Progress bar for tracking processing
        for filename in image_files:  # Iterate over each image file
            image_path = os.path.join(folder_path, filename)  # Construct full path for the image
            
            # Check for existing processed file with p_ prefix
            base_name = os.path.splitext(filename)[0]  # Extract base name without extension
            processed_path = os.path.join(folder_path, f"p_{base_name}.txt")  # Path for processed output
            
            if os.path.exists(processed_path) and os.path.getsize(processed_path) > 0:  # Check if processed file exists and is not empty
                print(f"Skipping {filename}: Processed file already exists")  # Log skipping message
                pbar.update(1)  # Update progress bar
                continue  # Skip to the next file

            process_single_image(image_path, model, prompt)  # Process the image and check success
            print(f"Processed {filename}")
            
            pbar.update(1)  # Update progress bar


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
    base_delay = 10
    delay_multiplier = 2.5  # Multiplier for exponential backoff
    request_options = {"timeout": 120.0}  # Timeout for each API request

    while retry_count < max_retries:  # Loop until max retries reached
        try:
            start_time = time.time()  # Record start time for API call
            
            response = model.generate_content( # Generate content using the provided model and messages
                messages,
                request_options=request_options  # Options for the request
            )
            print(f" API call took {time.time() - start_time:.2f} seconds")  # Log API call duration

            # Return the raw response object
            return response  # Successful response returned

        except (ResourceExhausted, DeadlineExceeded) as e:  # Handle specific exceptions
            print(f"Attempt {retry_count + 1} failed. Error: {e}")  # Log failure and error
            retry_count += 1  # Increment retry counter

            if retry_count == max_retries:  # Check if max retries reached
                raise  # Raise exception if retries exhausted

            # Calculate delay with exponential backoff and random jitter
            delay = base_delay * (delay_multiplier ** retry_count) + \
                random.uniform(0, base_delay * retry_count)  # Calculate delay
            print(f"Retrying in {delay:.2f} seconds...")  # Log retry delay
            time.sleep(delay)  # Wait for the calculated delay before retrying


def main():
    # Get folder path from user
    folder_path = input("Enter the path to the folder containing images: ").strip()

    # Clean the input path
    folder_path = folder_path.replace('"', '').replace("'", '').replace('`', '')

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return
    
    # Get max images from user
    max_images_count = int(input("Enter the maximum number of images to process: "))
    if max_images_count > 3000:
        print("Warning: The maximum number of images to process is 3000. Setting to 3000.")
        max_images_count = 3000

    # Process the folder
    process_folder(folder_path, model, prompt, max_images=max_images_count)


if __name__ == "__main__":
    main()
