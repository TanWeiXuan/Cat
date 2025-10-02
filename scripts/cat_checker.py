import argparse
from fnmatch import fnmatchcase
from pathlib import Path
from PIL import Image, ImageChops

TEMPLATE_BACKGROUND_COLOUR = "#99D9EA"

TEMPLATE_IMAGE_PATH = Path(__file__).parent.parent.resolve() / "cat_sitting_template.png"

REPORT_OUTPUT_FOLDER_PATH = Path(__file__).parent.parent.resolve() / "reports"

CHECKS = {
    "valid_png": False,
    "valid_name": False,
    "valid_dimensions": False,
    "within_template_outline": False
}

def validate_path(filepath: str) -> Path:
    path = Path(filepath)
    if not path.exists() and not path.is_file():
        raise argparse.ArgumentTypeError(f"The path '{filepath}' is not a path to a file.")
    return path

def check_if_valid_png(image_path: Path) -> bool:
    try:
        with Image.open(image_path) as img:
            img.verify()
            return img.format == "PNG"
    except Exception:
        return False

def check_if_filename_valid(cat_image_path: Path) -> bool:
    return fnmatchcase(cat_image_path.name, "cat_sitting_*.png")

def extract_cat_name(cat_image_path: Path) -> str:
    return cat_image_path.stem.removeprefix("cat_sitting_")

def check_if_same_dimension(image1: Image.Image, image2: Image.Image) -> bool:
    return image1.size == image2.size

def check_if_within_template_outline_highlight_changes(template_image: Image.Image, cat_image: Image.Image) -> tuple[bool, Image.Image | None]:
    template_bg_color = tuple(int(TEMPLATE_BACKGROUND_COLOUR[i:i+2], 16) for i in (1, 3, 5)) + (255,)
    w, h = template_image.size
    outline_violation_found = False
    diff_mask = Image.new("RGBA", template_image.size, (0, 0, 0, 0))

    template_image_rgba:Image.Image = template_image.convert("RGBA")
    cat_image_rgba:Image.Image = cat_image.convert("RGBA")
    
    for x in range(w):
        for y in range(h):
            px1 = template_image_rgba.getpixel((x, y))
            px2 = cat_image_rgba.getpixel((x, y))
            if px1 != px2:
                if px1 == template_bg_color:
                    diff_mask.putpixel((x, y), (255, 0, 0, 128)) # Annotate viloations with transparent red overlay
                    outline_violation_found = True
                if px1 == (255, 255, 255, 255):
                    diff_mask.putpixel((x, y), (0, 0, 255, 128)) # Annotate differences with transparent blue overlay

    annotated_image = Image.alpha_composite(cat_image_rgba, diff_mask) 
    return (not outline_violation_found), annotated_image


def generate_markdown_report_string(checks: dict[str, bool], cat_name: str, report_path: Path) -> str:
    markdown_report_string = f"### Preliminary Checks Report - `{cat_name}`: \n"
    markdown_report_string += "|Check    |Status |\n"
    markdown_report_string += "|:--------|:-----:|\n"

    markdown_report_string += "|Image file is a valid .png"
    if CHECKS["valid_png"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "|Image file has valid name"
    if CHECKS["valid_name"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "|Image file dimensions matches template"
    if CHECKS["valid_dimensions"]:
        markdown_report_string += "|:white_check_mark:|\n"
    else:
        markdown_report_string += "|:x:|\n"

    markdown_report_string += "|Drawing is within outline of template"
    if CHECKS["within_template_outline"]:
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
        help="The path to cat_sitting image filepath."
    )

    args = parser.parse_args()
    image_path = args.input_filepath

    print(f"Checking {image_path}.")

    checks_pass = True

    REPORT_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

    if checks_pass:
        checks_pass = CHECKS["valid_png"] = check_if_valid_png(image_path)
    if checks_pass:
        checks_pass = CHECKS["valid_name"] = check_if_filename_valid(image_path)
        cat_name = extract_cat_name(image_path)
    if checks_pass:
        template_image = Image.open(TEMPLATE_IMAGE_PATH)
        cat_image = Image.open(image_path)
        checks_pass = CHECKS["valid_dimensions"] = check_if_same_dimension(template_image, cat_image)
    if checks_pass:
        checks_pass, annotated_changes_image = check_if_within_template_outline_highlight_changes(template_image, cat_image)
        CHECKS["within_template_outline"] = checks_pass
        annotated_changes_image.save(REPORT_OUTPUT_FOLDER_PATH / f"{cat_name}_changes.png")

    markdown_report_string = generate_markdown_report_string(CHECKS, cat_name, REPORT_OUTPUT_FOLDER_PATH)

    with open(REPORT_OUTPUT_FOLDER_PATH / f"{cat_name}_preliminary_check_report.md", "w", encoding="utf-8") as f:
        f.write(markdown_report_string)

    print(f"Done checking {image_path}.\nResults written to {REPORT_OUTPUT_FOLDER_PATH}.")

if __name__ == "__main__":
    main()
