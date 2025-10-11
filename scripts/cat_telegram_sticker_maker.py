import argparse
import asyncio
import io
import re
from pathlib import Path
from PIL import Image, ImageChops

from telegram import Bot, InputFile, InputSticker
from telegram.error import TelegramError

BACKGROUND_COLOUR = "#99D9EA"
MAX_CONCURRENT_REQUESTS = 5

PARAMS = {
    "cat_sitting": {
        "folder_str": "cats",
        "roi": [445, 115, 1750, 1420], # left, upper, right, lower
        "stickerset_prefix": "Sitting Cats"
    },
    "cat_standing": {
        "folder_str": "cats_2",
        "roi": [540, 115, 1705, 1280], # left, upper, right, lower
        "stickerset_prefix": "Standing Cats"
    }
}

def extract_cat_name(cat_image_path: Path, cat_image_prefix: str) -> str:
    pattern = re.compile(fr"^{cat_image_prefix}_(.+)\.png$")
    match = pattern.match(cat_image_path.name)
    if not match:
        raise ValueError(f"Invalid filename format: {cat_image_path.name}")
    name = match.group(1)
    return name

def prepare_sticker_sync(cat_image_path: Path, roi: list[int], cat_image_prefix: str) -> InputSticker:
    cat_image = Image.open(cat_image_path).convert("RGBA")
    if roi != [0, 0, 0, 0]:
        cat_image = cat_image.crop(roi)

    # replace background with transparent
    bg_color = tuple(int(BACKGROUND_COLOUR[i:i+2], 16) for i in (1, 3, 5)) + (255,)
    datas = cat_image.getdata()
    new_data = [(255, 255, 255, 0) if item[:3] == bg_color[:3] else item for item in datas]
    cat_image.putdata(new_data)

    # Resize to fit within 512x512 while maintaining aspect ratio
    cat_image.thumbnail((512, 512), Image.Resampling.LANCZOS)

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

async def prepare_sticker(cat_image_path: Path, roi: list[int], cat_image_prefix: str) -> InputSticker:
    """Run prepare_sticker() in a thread pool."""
    return await asyncio.to_thread(prepare_sticker_sync, cat_image_path, roi, cat_image_prefix)


async def delete_sticker(bot: Bot, sticker_file_id: str, semaphore: asyncio.Semaphore, index: int, total: int):
    async with semaphore:
        print(f"Deleting [{index}/{total}] stickers...")
        await bot.delete_sticker_from_set(sticker_file_id)
        await asyncio.sleep(0.5)  # To avoid hitting rate limits


async def add_sticker(bot: Bot, user_id: int, sticker_set_name: str, cat_image_path: Path, roi: list[int], cat_image_prefix: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        try:
            cat_sticker = await prepare_sticker(cat_image_path, roi, cat_image_prefix)
            await bot.add_sticker_to_set(
                user_id=user_id,
                name=sticker_set_name,
                sticker=cat_sticker
            )
            print(f"Added sticker '{extract_cat_name(cat_image_path, cat_image_prefix)}'.")
            await asyncio.sleep(0.5)  # To avoid hitting rate limits
        except TelegramError as e:
            print(f"Error adding '{cat_image_path.name}': {e}")


async def process_sticker_set(bot: Bot, user_id: int, cat_image_prefix: str, param: dict):
    cat_folder_path = Path(__file__).parent.parent.resolve() / param["folder_str"]
    roi = param["roi"]
    stickerset_prefix = param["stickerset_prefix"]

    cat_image_paths = sorted(cat_folder_path.glob(f"{cat_image_prefix}_*.png"))
    bot_me = await bot.get_me()
    sticker_set_name = f"{stickerset_prefix.replace(' ', '_')}_by_{bot_me.username}"
    sticker_set_title = stickerset_prefix

    print(f"Checking if sticker set '{sticker_set_name}' exists...")
    try:
        sticker_set = await bot.get_sticker_set(sticker_set_name)
        print(f"Sticker set '{sticker_set_name}' already exists.")
    except TelegramError as e:
        if "Stickerset_invalid" in str(e):
            print(f"Creating new sticker set '{sticker_set_name}'...")
            first_sticker = await prepare_sticker(cat_image_paths[0], roi, cat_image_prefix)
            await bot.create_new_sticker_set(
                user_id=user_id,
                name=sticker_set_name,
                title=sticker_set_title,
                stickers=[first_sticker]
            )
            sticker_set = await bot.get_sticker_set(sticker_set_name)
        else:
            print(f"Error checking/creating sticker set: {e}")
            return

    print(f"Clearing existing stickers in '{sticker_set_name}'...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    delete_tasks = [
        delete_sticker(bot, sticker.file_id, semaphore, i + 1, len(sticker_set.stickers))
        for i, sticker in enumerate(sticker_set.stickers)
    ]
    await asyncio.gather(*delete_tasks)
    print(f"Cleared existing stickers in '{sticker_set_name}'.")

    print(f"Adding stickers to '{sticker_set_name}'...")
    add_tasks = [
        add_sticker(bot, user_id, sticker_set_name, path, roi, cat_image_prefix, semaphore)
        for path in cat_image_paths
    ]
    await asyncio.gather(*add_tasks)
    print(f"Finished adding stickers to '{sticker_set_name}'.")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bot_token", type=str)
    parser.add_argument("user_id", type=int)
    args = parser.parse_args()

    print(f"Converting cats to Telegram stickers...")

    bot = Bot(token=args.bot_token)
    for cat_image_prefix, param in PARAMS.items():
        await process_sticker_set(bot, args.user_id, cat_image_prefix, param)


if __name__ == "__main__":
    asyncio.run(main())
