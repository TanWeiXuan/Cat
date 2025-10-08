import argparse
from fnmatch import fnmatchcase
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

def validate_path(filepath: str) -> Path:
    path = Path(filepath)
    if not path.exists() and not path.is_file():
        raise argparse.ArgumentTypeError(f"The path '{filepath}' is not a path to a file.")
    return path


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
