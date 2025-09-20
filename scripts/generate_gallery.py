from pathlib import Path

IMAGE_SIZE = 200
CATS_PER_ROW = 3

IMAGE_FOLDER_NAME = "cats"
IMAGE_FOLDER_PATH = Path(__file__).parent.parent.resolve() / IMAGE_FOLDER_NAME

IMAGE_PREFIX = "cat_sitting_"
PNG_EXTENSION = ".png"
CENTER_JUSTIFICATION_ELEMENT = ":--:"

def group_list(ungrouped_list: list[str], 
                elements_per_group: int) -> list[list[str]]:
    return [
        ungrouped_list[i : i + elements_per_group]
        for i in range(0, len(ungrouped_list), elements_per_group)
    ]

def get_image_html(filename: str) -> str:
    return f'<img src="{IMAGE_FOLDER_NAME}/{filename}" width="{IMAGE_SIZE}" />'

def get_cat_name(filename: str) -> str:
    # This assumes that filename contains IMAGE_PREFIX, no check done for this
    return Path(filename).stem[len(IMAGE_PREFIX):]

def get_caption_markdown(filename: str) -> str:
    return f"[{get_cat_name(filename)}]({IMAGE_FOLDER_NAME}/{filename})"

def generate_gallery_table(filenames: list[str]) -> str:
    if len(filenames) == 0:
        return ""
    
    image_row = f"|{
        "|".join([get_image_html(filename) for filename in filenames])}|\n"
    
    center_justification_row = f"|{"|".join(
        [CENTER_JUSTIFICATION_ELEMENT for _ in range(len(filenames))])}|\n"

    caption_row = f"|{
        "|".join(
            [get_caption_markdown(filename) for filename in filenames])}|\n"

    return image_row + center_justification_row + caption_row

def main() -> None:
    image_filenames = [
        file_path.name
        for file_path in sorted(IMAGE_FOLDER_PATH.iterdir())
        if (file_path.is_file() and (file_path.suffix == PNG_EXTENSION))
    ]
    print(f"Detected {len(image_filenames)}\n")

    grouped_filenames = group_list(ungrouped_list=image_filenames,
                                    elements_per_group=CATS_PER_ROW)

    table_markdown = "\n".join(
        [generate_gallery_table(
            image_filenames) for image_filenames in grouped_filenames])


    print("Paste the following in the Cat Gallery Section of the README:\n")

    print(table_markdown)

if __name__ == "__main__":
    main()
