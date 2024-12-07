import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """
  Uploads the given file to Gemini.
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def get_image_caption(image_path):
    """
    Gets caption for a single image using Gemini API.
    """
    # Create the model with configuration
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

    # Upload and process the image
    file = upload_to_gemini(image_path, mime_type="image/png")
    
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    "Please describe what's in this image, and if there's a character, also describe its expression. After that, please create a new paragraph title \"Prompt\", in which you will reformat the image description and any additional details you mentioned into a verbose prompt for the generative image model Flux. This prompt will be used for training a LoRA.",
                ],
            },
            {
                "role": "model",
                "parts": [
                    "This is a cartoon illustration, depicting a character engaged in gardening on a sloped landscape under a partly cloudy sky.\n\nThe character, positioned in the center-left of the frame, has a round, yellow face with exaggerated features, including large, round eyes with a skeptical expression, a small red nose, and a wide mouth with a prominent, pink tongue. It has a mop of black hair styled into an \"M\" shape on its forehead. It's dressed in a red t-shirt with yellow Chinese characters that translate to \"Don't eat\" and blue shorts. It is holding a garden rake in its right hand and a white towel with a yellow tint in its left hand, seemingly wiping sweat off its forehead.\n\nThe character appears to be working on the soil, which is a rich brown color. The rake is in the soil, suggesting recent tilling. Nearby, there are a few notable elements: a worm lying on the ground, appearing lifeless with \"X\" marks for eyes; a purple, slug-like creature with similar \"X\" eyes; and a small green plant with a white flower to the left.\n\nThe background features a hill with a gradient of green hues, suggesting grass, and a large, bare tree with snow on some of its branches to the right. The tree's branches are spread out, and it has a textured trunk. The sky is white, with a blue, clouded hill in the distance. The overall color palette is warm, with the use of yellows, browns, and greens dominating the scene.\n\n**Prompt**\n\n```\n(masterpiece, best quality:1.2), absurdres, highres, original, extremely detailed, perfect lighting, cinematic lighting, Cartoon illustration of a character gardening on a sloped landscape under a partly cloudy sky. The character has a round yellow face, large round eyes with a skeptical expression, a small red nose, a wide mouth with a prominent pink tongue, black hair in an \"M\" shape. Wearing a red t-shirt with yellow Chinese characters \"Don't eat\", blue shorts. Holding a garden rake in the right hand and a white towel with a yellow tint in the left, wiping sweat. Rich brown soil, a lifeless worm with \"X\" eyes, a purple slug-like creature with \"X\" eyes, a small green plant with a white flower. Background with a green gradient hill, a large bare tree with snow on branches to the right, textured trunk. White sky, blue clouded hill in the distance. Warm color palette with yellows, browns, and greens.\n```\n",
                ],
            },
            {
                "role": "user",
                "parts": [
                    file,
                    "Please describe what's in this image, and if there's a character, also describe its expression. After that, please create a new paragraph title \"Prompt\", in which you will reformat the image description and any additional details you mentioned into a verbose prompt for the generative image model Flux. This prompt will be used for training a LoRA.",
                ],
            }
        ]
    )
    
    return chat_session.last.text

def process_images(folder_path):
    """
    Process all images in the specified folder.
    """
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_path = os.path.join(folder_path, filename)
            txt_path = os.path.splitext(image_path)[0] + ".txt"
            
            # Skip if caption file already exists and is not empty
            if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
                print(f"Skipping {filename}: Text file already exists")
                continue
                
            try:
                # Get caption from Gemini
                caption = get_image_caption(image_path)
                
                # Write the caption to a text file
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(caption)
                
                print(f"Processed {filename} -> {txt_path}")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

def main():
    folder_path = input("Enter the path to the folder containing images: ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    process_images(folder_path)

if __name__ == '__main__':
    main()