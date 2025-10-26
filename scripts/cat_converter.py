import argparse
import re
import sys
from pathlib import Path
from PIL import Image

""" Cat Conversion Script
Converts a cat image specified by inpu_cat_filepath to the cat type specified by input_template_filepath.
NOTE: Works for most cats, but may not work for cats where the drawing exceeds the head region in the template.
"""

CAT_FOLDER_DICT = {
    "sitting": Path(__file__).parent.parent.resolve() / "cats",
    "standing": Path(__file__).parent.parent.resolve() / "cats_2"
}

# left, upper, right, lower
CAT_REGIONS = [
    [1075, 115, 1520, 465], 
    [1150, 115, 1480, 550]
]

def validate_path(filepath: str) -> Path:
    path = Path(filepath)
    if not path.exists() and not path.is_file():
        raise argparse.ArgumentTypeError(f"The path '{filepath}' is not a path to a file.")
    return path


def extract_cat_type_and_name(cat_image_path: Path) -> list[str]:
    pattern = re.compile(r"^cat_(sitting|standing)_(.+)\.png$")
    match = pattern.match(cat_image_path.name)
    if not match:
        raise ValueError(f"Invalid filename format: {cat_image_path.name}")
    cat_type, name = match.groups()
    return [cat_type, name]

def convert_cat(cat_image_path: Path, template_image_path: Path) -> None:
    _, cat_name = extract_cat_type_and_name(cat_image_path)
    cat_type, _ = extract_cat_type_and_name(template_image_path)

    cat_image = Image.open(cat_image_path).convert("RGBA")
    converted_image = Image.open(template_image_path).convert("RGBA")

    for cat_region in CAT_REGIONS:
        converted_image.paste(cat_image.crop(cat_region), cat_region[:2], cat_image.crop(cat_region))

    converted_image.save(CAT_FOLDER_DICT[cat_type] / f"cat_{cat_type}_{cat_name}.png")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_cat_filepath",
        type=validate_path,
        help="The path to the cat to be converted."
    )

    parser.add_argument(
        "input_template_filepath",
        type=validate_path,
        help="The path to the template to convert the cat to."
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    input_cat_filepath = args.input_cat_filepath
    input_template_filepath = args.input_template_filepath

    print(f"Converting {input_cat_filepath.name}...")
    convert_cat(input_cat_filepath, input_template_filepath)
    print(f"Converted {input_cat_filepath.name}.")

if __name__ == "__main__":
    main()
