import os
import lmstudio as lms


def initialize_model():
    # Connect to LM Studio and get the VLM model
    model = lms.llm("mlx-community/qwen2.5-vl-7b-instruct")
    return model


def run_example(model, image_path):
    # Prepare the image using LM Studio's prepare_image function
    image_handle = lms.prepare_image(image_path)

    # Create a chat and add the user message with image
    chat = lms.Chat()
    chat.add_user_message("Describe this image.", images=[image_handle])

    # Generate response using the model
    prediction = model.respond(chat)

    # Extract the text content from the PredictionResult
    return prediction.content


def clean_caption(caption):
    return caption.replace(
        "The image is", "").replace(
        "The image depicts", "").replace(
        "The image shows", "").replace(
        "The image features", "").replace(
        "The image contains", "").replace(
        "The art style is ", "").replace(
        "The overall style of the artwork is ", "").replace(
        "an illustration featuring ", "").strip()


def process_image(folder_path, model):
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

            # No need to manually open/convert image - LM Studio handles this
            caption = run_example(model, image_path)
            cleaned_caption = clean_caption(caption)

            # Write the caption to a text file
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_caption)

            print(f"{filename}: {cleaned_caption} -> {txt_path}")


def main():
    folder_path = input(
        "Enter the path to the folder containing images: ").strip()

    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    model = initialize_model()
    process_image(folder_path, model)


if __name__ == '__main__':
    main()
