import argparse
import sys
from fnmatch import fnmatchcase
from pathlib import Path
from PIL import Image

TEMPLATE_BACKGROUND_COLOUR = "#99D9EA"

BASE_DIR = Path(__file__).parent.parent.resolve()
REPORT_OUTPUT_FOLDER_PATH = BASE_DIR / "reports"

CAT_TYPES = {
    "sitting": {
        "folder": "cats",
        "filename_pattern": "cat_sitting_*.png",
        "filename_prefix": "cat_sitting_",
        "template_path": BASE_DIR / "cat_templates" / "cat_sitting_template.png",
    },
    "standing": {
        "folder": "cats_2",
        "filename_pattern": "cat_standing_*.png",
        "filename_prefix": "cat_standing_",
        "template_path": BASE_DIR / "cat_templates" / "cat_standing_template.png",
    },
}

CHECKS = {
    "valid_png": False,
    "valid_name": False,
    "valid_dimensions": False,
    "within_template_outline": False,
}


def validate_path(filepath: str) -> Path:
    path = Path(filepath)
    if not path.exists() and not path.is_file():
        raise argparse.ArgumentTypeError(f"The path '{filepath}' is not a path to a file.")
    return path


def detect_cat_type(cat_image_path: Path) -> str:
    for cat_type, config in CAT_TYPES.items():
        if config["folder"] in cat_image_path.parts:
            return cat_type
    raise ValueError(
        "Could not detect cat type from path. Expected file to be under 'cats/' or 'cats_2/'."
    )


def check_if_valid_png(image_path: Path) -> bool:
    try:
        with Image.open(image_path) as img:
            img.verify()
            return img.format == "PNG"
    except Exception:
        return False


def check_if_filename_valid(cat_image_path: Path, cat_type: str) -> bool:
    return fnmatchcase(cat_image_path.name, CAT_TYPES[cat_type]["filename_pattern"])


def extract_cat_name(cat_image_path: Path, cat_type: str) -> str:
    return cat_image_path.stem.removeprefix(CAT_TYPES[cat_type]["filename_prefix"])


def check_if_same_dimension(image1: Image.Image, image2: Image.Image) -> bool:
    return image1.size == image2.size


def check_if_within_template_outline_highlight_changes(
    template_image: Image.Image, cat_image: Image.Image
) -> tuple[bool, Image.Image | None]:
    template_bg_color = tuple(int(TEMPLATE_BACKGROUND_COLOUR[i : i + 2], 16) for i in (1, 3, 5)) + (255,)
    w, h = template_image.size
    outline_violation_found = False
    diff_mask = Image.new("RGBA", template_image.size, (0, 0, 0, 0))

    template_image_rgba: Image.Image = template_image.convert("RGBA")
    cat_image_rgba: Image.Image = cat_image.convert("RGBA")

    for x in range(w):
        for y in range(h):
            px1 = template_image_rgba.getpixel((x, y))
            px2 = cat_image_rgba.getpixel((x, y))
            if px1 != px2:
                if px1 == template_bg_color:
                    diff_mask.putpixel((x, y), (255, 0, 0, 128))  # Annotate violations with transparent red overlay
                    outline_violation_found = True
                if px1 == (255, 255, 255, 255):
                    diff_mask.putpixel((x, y), (0, 0, 255, 128))  # Annotate differences with transparent blue overlay

    annotated_image = Image.alpha_composite(cat_image_rgba, diff_mask)
    return (not outline_violation_found), annotated_image


def generate_markdown_report_string(checks: dict[str, bool], cat_name: str) -> str:
    markdown_report_string = f"### Preliminary Checks Report - `{cat_name}`: \n"
    markdown_report_string += "|Check    |Status |\n"
    markdown_report_string += "|:--------|:-----:|\n"

    markdown_report_string += "|Image file is a valid .png"
    if checks["valid_png"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "|Image file has valid name"
    if checks["valid_name"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "|Image file dimensions matches template"
    if checks["valid_dimensions"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "|Drawing is within outline of template"
    if checks["within_template_outline"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "\n"

    return markdown_report_string


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_filepath",
        type=validate_path,
        help="The path to a cat image filepath.",
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    image_path = args.input_filepath

    print(f"Checking {image_path}.")

    checks_pass = True
    checks = CHECKS.copy()
    cat_name = image_path.stem

    REPORT_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

    try:
        cat_type = detect_cat_type(image_path)
    except ValueError as err:
        print(str(err))
        sys.exit(1)

    if checks_pass:
        checks_pass = checks["valid_png"] = check_if_valid_png(image_path)
    if checks_pass:
        checks_pass = checks["valid_name"] = check_if_filename_valid(image_path, cat_type)
        cat_name = extract_cat_name(image_path, cat_type)
    if checks_pass:
        template_image = Image.open(CAT_TYPES[cat_type]["template_path"])
        cat_image = Image.open(image_path)
        checks_pass = checks["valid_dimensions"] = check_if_same_dimension(template_image, cat_image)
    if checks_pass:
        checks_pass, annotated_changes_image = check_if_within_template_outline_highlight_changes(
            template_image, cat_image
        )
        checks["within_template_outline"] = checks_pass
        annotated_changes_image.save(REPORT_OUTPUT_FOLDER_PATH / f"{cat_name}_changes.png")

    markdown_report_string = generate_markdown_report_string(checks, cat_name)

    with open(REPORT_OUTPUT_FOLDER_PATH / f"{cat_name}_preliminary_check_report.md", "w", encoding="utf-8") as f:
        f.write(markdown_report_string)

    print(f"Done checking {image_path}.\nResults written to {REPORT_OUTPUT_FOLDER_PATH}.")


if __name__ == "__main__":
    main()
