import argparse
import asyncio
import io
import re
from pathlib import Path
from PIL import Image, ImageChops

from telegram import Bot, InputFile, InputSticker
from telegram.error import TelegramError

BACKGROUND_COLOUR = "#99D9EA"

PARAMS = {
    "cat_sitting": {
        "folder_str": "cats",
        "roi": [445, 115, 1750, 1420], # left, upper, right, lower
        "stickerset_prefix": "Sitting Cats"
    }
}

def extract_cat_name(cat_image_path: Path, cat_image_prefix: str) -> str:
    pattern = re.compile(fr"^{cat_image_prefix}_(.+)\.png$")
    match = pattern.match(cat_image_path.name)
    if not match:
        raise ValueError(f"Invalid filename format: {cat_image_path.name}")
    name = match.group(1)
    return name

def prepare_sticker(cat_image_path: Path, roi: list[int], cat_image_prefix: str) -> InputSticker:
    cat_image = Image.open(cat_image_path).convert("RGBA")
    if roi != [0, 0, 0, 0]:
        cat_image = cat_image.crop(roi)

    # replace background with transparent
    bg_color = tuple(int(BACKGROUND_COLOUR[i:i+2], 16) for i in (1, 3, 5)) + (255,)
    datas = cat_image.getdata()
    new_data = []
    for item in datas:
        if item[0:3] == bg_color[0:3]:
            new_data.append((255, 255, 255, 0)) # Transparent
        else:
            new_data.append(item)
    cat_image.putdata(new_data)

    # Resize to fit within 512x512 while maintaining aspect ratio
    max_size = 512
    cat_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    cat_image_buffer = io.BytesIO()
    cat_image.save(cat_image_buffer, format="PNG")
    cat_image_buffer.seek(0)

    cat_sticker = InputSticker(
        sticker=cat_image_buffer.getvalue(),
        emoji_list=["😺"],
        keywords=[extract_cat_name(cat_image_path, cat_image_prefix)],
        format="static"
    )

    return cat_sticker

async def main() -> None:
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

    for cat_image_prefix, param in PARAMS.items():
        cat_folder_path = Path(__file__).parent.parent.resolve() / param["folder_str"]
        roi = param["roi"]
        stickerset_prefix = param["stickerset_prefix"]

        cat_image_paths = list(cat_folder_path.glob(f"{cat_image_prefix}_*.png"))
        cat_image_paths.sort()

        bot = Bot(token=args.bot_token)
        bot_me = await bot.get_me()
        sticker_set_name = f"{stickerset_prefix.replace(' ', '_')}_by_{bot_me.username}"
        sticker_set_title = f"{stickerset_prefix}"

        # Check if sticker set exists, if not create it
        print(f"Checking if sticker set '{sticker_set_name}' exists...")
        try:
            sticker_set = await bot.get_sticker_set(sticker_set_name)
            print(f"Sticker set '{sticker_set_name}' already exists.")

        except TelegramError as e:
            if "Stickerset_invalid" in str(e):
                print(f"Sticker set does not exist, creating sticker set '{sticker_set_name}'...")

                # Placeholder to create the sticker set
                cat_sticker = prepare_sticker(cat_image_paths[0], roi, cat_image_prefix)

                await bot.create_new_sticker_set(
                    user_id=int(args.user_id),
                    name=sticker_set_name,
                    title=sticker_set_title,
                    stickers=[cat_sticker]
                )
                print(f"Sticker set '{sticker_set_name}' created.")
            else:
                print(f"Error checking/creating sticker set: {e}")
                continue
        
        # Not sure what's a good way to check existing stickers in the set
        # So just delete all stickers and re-add them
        print(f"Clearing existing stickers in sticker set '{sticker_set_name}'...")
        sticker_set = await bot.get_sticker_set(sticker_set_name)
        for cnt, sticker in enumerate(sticker_set.stickers, start=1):
            print(f"Deleting [{cnt}/{len(sticker_set.stickers)}] stickers.")
            await bot.delete_sticker_from_set(sticker.file_id)
        print(f"Cleared existing stickers in sticker set '{sticker_set_name}'.")

        print(f"Adding stickers to sticker set '{sticker_set_name}'...")
        for cat_image_path in cat_image_paths:
            try:
                cat_sticker = prepare_sticker(cat_image_path, roi, cat_image_prefix)
                await bot.add_sticker_to_set(
                    user_id=int(args.user_id),
                    name=sticker_set_name,
                    sticker=cat_sticker
                )
                print(f"Added sticker '{extract_cat_name(cat_image_path, cat_image_prefix)}'.")
            except TelegramError as e:
                print(f"Error adding sticker '{extract_cat_name(cat_image_path, cat_image_prefix)}': {e}")
                continue
        print(f"Finish adding stickers to sticker set '{sticker_set_name}'.")

if __name__ == "__main__":
    asyncio.run(main())
