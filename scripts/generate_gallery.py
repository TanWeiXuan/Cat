from pathlib import Path

IMAGE_SIZE = 200
CATS_PER_ROW = 3

SITTING_CATS_IMAGE_FOLDER_NAME = "cats"
STANDING_CATS_IMAGE_FOLDER_NAME = "cats_2"

SITTING_CATS_IMAGE_FOLDER_PATH = Path(__file__).parent.parent.resolve() / SITTING_CATS_IMAGE_FOLDER_NAME
STANDING_CATS_IMAGE_FOLDER_PATH = Path(__file__).parent.parent.resolve() / STANDING_CATS_IMAGE_FOLDER_NAME
README_FILE_PATH = Path(__file__).parent.parent.resolve() / "README.md"

SITTING_CATS_IMAGE_PREFIX = "cat_sitting_"
STANDING_CATS_IMAGE_PREFIX = "cat_standing_"
PNG_EXTENSION = ".png"
CENTER_JUSTIFICATION_ELEMENT = ":--:"

def group_list(ungrouped_list: list[str], elements_per_group: int) -> list[list[str]]:
    return [
        ungrouped_list[i : i + elements_per_group]
        for i in range(0, len(ungrouped_list), elements_per_group)
    ]

def get_image_html(image_folder_name: str, filename: str) -> str:
    return f'<img loading="lazy" src="{image_folder_name}/{filename}" width="{IMAGE_SIZE}" />'

def get_cat_name(image_prefix: str, filename: str) -> str:
    # This assumes that filename contains image_prefix, no check done for this
    return Path(filename).stem[len(image_prefix):]

def get_caption_markdown(image_prefix: str, image_folder_name: str, filename: str) -> str:
    return f"[{get_cat_name(image_prefix, filename)}]({image_folder_name}/{filename})"

def generate_gallery_table(image_prefix: str, image_folder_name: str, filenames: list[str]) -> str:
    if len(filenames) == 0:
        return ""

    image_row = f"|{'|'.join([get_image_html(image_folder_name, filename) for filename in filenames])}|\n"
    center_justification_row = f"|{'|'.join([CENTER_JUSTIFICATION_ELEMENT for _ in range(len(filenames))])}|\n"
    caption_row = f"|{'|'.join([get_caption_markdown(image_prefix, image_folder_name, filename) for filename in filenames])}|\n"

    return image_row + center_justification_row + caption_row

def update_cat_gallery_in_readme(markdown_filepath: Path, sitting_cat_gallery_markdown_str: str, standing_cat_gallery_markdown_str: str) -> None:
    """
    Updates the contents in the 'Cat Gallery' section in provided markdown file
    """
    text = markdown_filepath.read_text(encoding="utf-8")
    gallery_heading = R"### Cat gallery."
    idx = text.find(gallery_heading)
    updated_text = text[: idx + len(gallery_heading)] + "\n" + "___\n" + "#### Sitting Cat gallery.\n" + sitting_cat_gallery_markdown_str.strip() + '\n'
    updated_text +=  "___" + "\n#### Standing Cat gallery.\n\n" + standing_cat_gallery_markdown_str.strip() + '\n'
    markdown_filepath.write_text(updated_text)


def main() -> None:
    sitting_cat_image_filenames = [
        file_path.name
        for file_path in sorted(SITTING_CATS_IMAGE_FOLDER_PATH.iterdir())
        if (file_path.is_file() and (file_path.suffix == PNG_EXTENSION))
    ]

    standing_cat_image_filenames = [
        file_path.name
        for file_path in sorted(STANDING_CATS_IMAGE_FOLDER_PATH.iterdir())
        if (file_path.is_file() and (file_path.suffix == PNG_EXTENSION))
    ]

    print(f"Detected {len(sitting_cat_image_filenames)} sitting cats.")
    print(f"Detected {len(standing_cat_image_filenames)} standing cats.")

    sitting_cat_image_filenames.sort()
    standing_cat_image_filenames.sort()

    grouped_sitting_cat_filenames = group_list(ungrouped_list=sitting_cat_image_filenames, elements_per_group=CATS_PER_ROW)
    grouped_standing_cat_filenames = group_list(ungrouped_list=standing_cat_image_filenames, elements_per_group=CATS_PER_ROW)

    sitting_cats_table_markdown = "\n".join([generate_gallery_table(SITTING_CATS_IMAGE_PREFIX, SITTING_CATS_IMAGE_FOLDER_NAME, image_filenames) for image_filenames in grouped_sitting_cat_filenames])
    standing_cats_table_markdown = "\n".join([generate_gallery_table(STANDING_CATS_IMAGE_PREFIX, STANDING_CATS_IMAGE_FOLDER_NAME, image_filenames) for image_filenames in grouped_standing_cat_filenames])

    print("Updating README.md...")

    update_cat_gallery_in_readme(README_FILE_PATH, sitting_cats_table_markdown, standing_cats_table_markdown)

    print("Updated README.md.")

if __name__ == "__main__":
    main()
