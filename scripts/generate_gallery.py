from pathlib import Path
from PIL import Image

IMAGE_SIZE = 200
CATS_PER_ROW = 3

BASE_DIR = Path(__file__).parent.parent.resolve()
README_FILE_PATH = BASE_DIR / "README.md"

CAT_TYPES = {
    "sitting": {
        "display_name": "Sitting Cat",
        "png_folder_name": "cats",
        "jpeg_folder_name": "scripts/misc/jpeg_cats",
        "image_prefix": "cat_sitting_",
    },
    "standing": {
        "display_name": "Standing Cat",
        "png_folder_name": "cats_2",
        "jpeg_folder_name": "scripts/misc/jpeg_cats_2",
        "image_prefix": "cat_standing_",
    },
}

for config in CAT_TYPES.values():
    config["png_folder_path"] = BASE_DIR / config["png_folder_name"]
    config["jpeg_folder_path"] = BASE_DIR / config["jpeg_folder_name"]

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

def update_cat_gallery_in_readme(markdown_filepath: Path, gallery_markdown_by_cat_type: dict[str, str]) -> None:
    """
    Updates the contents in the 'Cat Gallery' section in provided markdown file
    """
    text = markdown_filepath.read_text(encoding="utf-8")
    gallery_heading = R"### Cat gallery."
    idx = text.find(gallery_heading)
    updated_text = text[: idx + len(gallery_heading)] + "\n"
    for cat_type, config in CAT_TYPES.items():
        gallery_markdown = gallery_markdown_by_cat_type.get(cat_type, "")
        updated_text += (
            "___\n"
            f"#### {config['display_name']} gallery.\n\n"
            f"{gallery_markdown.strip()}\n"
        )
    markdown_filepath.write_text(updated_text)


def main() -> None:
    gallery_markdown_by_cat_type: dict[str, str] = {}

    for cat_type, config in CAT_TYPES.items():
        # Ensure JPEG folders exist
        config["jpeg_folder_path"].mkdir(parents=True, exist_ok=True)

        # Process images: convert PNGs to JPEGs and clean up orphaned JPEGs
        print(f"Processing {cat_type} cats...")
        jpeg_filenames = process_images(
            config["png_folder_path"],
            config["jpeg_folder_path"],
            config["image_prefix"],
        )
        print(f"Detected {len(jpeg_filenames)} {cat_type} cats.")

        grouped_cat_filenames = group_list(ungrouped_list=jpeg_filenames, elements_per_group=CATS_PER_ROW)
        gallery_markdown_by_cat_type[cat_type] = "\n".join(
            [
                generate_gallery_table(
                    config["image_prefix"],
                    config["jpeg_folder_name"],
                    config["png_folder_name"],
                    image_filenames,
                )
                for image_filenames in grouped_cat_filenames
            ]
        )

    print("Updating README.md...")

    update_cat_gallery_in_readme(README_FILE_PATH, gallery_markdown_by_cat_type)

    print("Updated README.md.")

if __name__ == "__main__":
    main()
