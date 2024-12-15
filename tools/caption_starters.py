def clean_caption(caption):
    return caption.replace(
        "The image is ", "").replace(
        "The art style is ", "").replace(
        "The overall style of the artwork is ", "").replace(
        "The scene is a ", "").replace(
        "A mid-shot illustration featuring a ", "").replace(
        "A cartoon illustration with ", "").replace(
        "Cartoon illustration featuring ", "").replace(
        "An illustration featuring ", "").strip()