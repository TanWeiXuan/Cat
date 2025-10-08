import argparse
from pathlib import Path
from PIL import Image, ImageChops

BACKGROUND_COLOUR = "#99D9EA"

PARAMS = {
    "cat_sitting": {
        "folder_str": "cats",
        "roi": [0, 0, 0, 0], # left, upper, right, lower
        "stickerset_prefix": "Sitting Cats "
    }
}

def extract_cat_name(cat_image_path: Path, cat_image_prefix: str) -> str:
    pattern = re.compile(fr"^{cat_image_prefix}_(.+)\.png$")
    match = pattern.match(cat_image_path.name)
    if not match:
        raise ValueError(f"Invalid filename format: {cat_image_path.name}")
    name = match.group(1)
    return name

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bot_token",
        type=str,
        help="Telegram bot token"
    )

    parser.add_argument(
        "user_id",
        type=str,
        help="Telegram user ID"
    )

    args = parser.parse_args()

    print(f"Converting cats to Telegram stickers.")

    # Process images and use telegram bot API to convert cat images to telegram stickers

    print(f"Completed converting cats to Telegram stickers.")

if __name__ == "__main__":
    main()
