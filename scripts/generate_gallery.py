from pathlib import Path
from PIL import Image

IMAGE_SIZE = 200
CATS_PER_ROW = 3

SITTING_CATS_IMAGE_FOLDER_NAME = "cats"
STANDING_CATS_IMAGE_FOLDER_NAME = "cats_2"

SITTING_CATS_IMAGE_FOLDER_PATH = Path(__file__).parent.parent.resolve() / SITTING_CATS_IMAGE_FOLDER_NAME
STANDING_CATS_IMAGE_FOLDER_PATH = Path(__file__).parent.parent.resolve() / STANDING_CATS_IMAGE_FOLDER_NAME
README_FILE_PATH = Path(__file__).parent.parent.resolve() / "README.md"

JPEG_CATS_FOLDER_NAME = "scripts/misc/jpeg_cats"
JPEG_CATS_2_FOLDER_NAME = "scripts/misc/jpeg_cats_2"
JPEG_CATS_FOLDER_PATH = Path(__file__).parent.parent.resolve() / JPEG_CATS_FOLDER_NAME
JPEG_CATS_2_FOLDER_PATH = Path(__file__).parent.parent.resolve() / JPEG_CATS_2_FOLDER_NAME

SITTING_CATS_IMAGE_PREFIX = "cat_sitting_"
STANDING_CATS_IMAGE_PREFIX = "cat_standing_"
PNG_EXTENSION = ".png"
JPEG_EXTENSION = ".jpg"
CENTER_JUSTIFICATION_ELEMENT = ":--:"

def group_list(ungrouped_list: list[str], elements_per_group: int) -> list[list[str]]:
    return [
        ungrouped_list[i : i + elements_per_group]
        for i in range(0, len(ungrouped_list), elements_per_group)
    ]

def convert_png_to_jpeg(png_path: Path, jpeg_path: Path) -> None:
    """
    Convert PNG to half-resolution progressive JPEG with low compression.
    """
    with Image.open(png_path) as img:
        # Calculate half resolution
        new_width = img.width // 2
        new_height = img.height // 2
        
        # Resize to half resolution
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert RGBA to RGB if necessary
        if img_resized.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', img_resized.size, (255, 255, 255))
            background.paste(img_resized, mask=img_resized.split()[3])  # Use alpha channel as mask
            img_resized = background
        elif img_resized.mode != 'RGB':
            img_resized = img_resized.convert('RGB')
        
        # Save as progressive JPEG with quality 85 (low compression)
        img_resized.save(jpeg_path, 'JPEG', quality=85, optimize=True, progressive=True)

def process_images(png_folder: Path, jpeg_folder: Path, image_prefix: str) -> list[str]:
    """
    Process PNG images: convert to JPEGs if needed, delete orphaned JPEGs.
    Returns list of JPEG filenames.
    """
    # Get all PNG files
    png_files = {
        file_path.name: file_path
        for file_path in png_folder.iterdir()
        if file_path.is_file() and file_path.suffix == PNG_EXTENSION
    }
    
    # Get all existing JPEG files
    existing_jpegs = {
        file_path.name: file_path
        for file_path in jpeg_folder.iterdir()
        if file_path.is_file() and file_path.suffix == JPEG_EXTENSION
    }
    
    # Convert PNGs to JPEGs if they don't exist
    jpeg_filenames = []
    for png_filename, png_path in png_files.items():
        jpeg_filename = png_path.stem + JPEG_EXTENSION
        jpeg_path = jpeg_folder / jpeg_filename
        
        if jpeg_filename not in existing_jpegs:
            print(f"Converting {png_filename} to {jpeg_filename}...")
            convert_png_to_jpeg(png_path, jpeg_path)
        
        jpeg_filenames.append(jpeg_filename)
    
    # Delete orphaned JPEGs (exist in jpeg folder but not in main folder)
    png_stems = {Path(png_name).stem for png_name in png_files.keys()}
    for jpeg_filename, jpeg_path in existing_jpegs.items():
        jpeg_stem = Path(jpeg_filename).stem
        if jpeg_stem not in png_stems:
            print(f"Deleting orphaned JPEG: {jpeg_filename}")
            jpeg_path.unlink()
    
    return sorted(jpeg_filenames)

def get_image_html(image_folder_name: str, filename: str) -> str:
    return f'<img loading="lazy" src="{image_folder_name}/{filename}" width="{IMAGE_SIZE}" />'

def get_cat_name(image_prefix: str, filename: str) -> str:
    # This assumes that filename contains image_prefix, no check done for this
    return Path(filename).stem[len(image_prefix):]

def get_caption_markdown(image_prefix: str, image_folder_name: str, filename: str) -> str:
    # filename is the JPEG filename, but we need to link to the PNG
    png_filename = Path(filename).stem + PNG_EXTENSION
    return f"[{get_cat_name(image_prefix, filename)}]({image_folder_name}/{png_filename})"

def generate_gallery_table(image_prefix: str, jpeg_folder_name: str, png_folder_name: str, filenames: list[str]) -> str:
    if len(filenames) == 0:
        return ""

    image_row = f"|{'|'.join([get_image_html(jpeg_folder_name, filename) for filename in filenames])}|\n"
    center_justification_row = f"|{'|'.join([CENTER_JUSTIFICATION_ELEMENT for _ in range(len(filenames))])}|\n"
    caption_row = f"|{'|'.join([get_caption_markdown(image_prefix, png_folder_name, filename) for filename in filenames])}|\n"

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
    # Ensure JPEG folders exist
    JPEG_CATS_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
    JPEG_CATS_2_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

    # Process images: convert PNGs to JPEGs and clean up orphaned JPEGs
    print("Processing sitting cats...")
    sitting_cat_jpeg_filenames = process_images(
        SITTING_CATS_IMAGE_FOLDER_PATH,
        JPEG_CATS_FOLDER_PATH,
        SITTING_CATS_IMAGE_PREFIX
    )

    print("Processing standing cats...")
    standing_cat_jpeg_filenames = process_images(
        STANDING_CATS_IMAGE_FOLDER_PATH,
        JPEG_CATS_2_FOLDER_PATH,
        STANDING_CATS_IMAGE_PREFIX
    )

    print(f"Detected {len(sitting_cat_jpeg_filenames)} sitting cats.")
    print(f"Detected {len(standing_cat_jpeg_filenames)} standing cats.")

    grouped_sitting_cat_filenames = group_list(ungrouped_list=sitting_cat_jpeg_filenames, elements_per_group=CATS_PER_ROW)
    grouped_standing_cat_filenames = group_list(ungrouped_list=standing_cat_jpeg_filenames, elements_per_group=CATS_PER_ROW)

    sitting_cats_table_markdown = "\n".join([generate_gallery_table(SITTING_CATS_IMAGE_PREFIX, JPEG_CATS_FOLDER_NAME, SITTING_CATS_IMAGE_FOLDER_NAME, image_filenames) for image_filenames in grouped_sitting_cat_filenames])
    standing_cats_table_markdown = "\n".join([generate_gallery_table(STANDING_CATS_IMAGE_PREFIX, JPEG_CATS_2_FOLDER_NAME, STANDING_CATS_IMAGE_FOLDER_NAME, image_filenames) for image_filenames in grouped_standing_cat_filenames])

    print("Updating README.md...")

    update_cat_gallery_in_readme(README_FILE_PATH, sitting_cats_table_markdown, standing_cats_table_markdown)

    print("Updated README.md.")

if __name__ == "__main__":
    main()
