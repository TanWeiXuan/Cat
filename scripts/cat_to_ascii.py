import argparse
import re
import sys
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

import cat_telegram_sticker_maker as ctsm

""""
Convert cat images to ASCII art. References implementation from gouwsxander/ascii-view.
"""

ASCII_BRIGHTNESS_CHARS = np.array(list(r" .-':_,^=;><+!rc*/z?sLTv)J7(|Fi{C}fI31tlu[neoZ5Yxjya]2ESwqkP6h9d4VpOGbUAKXHm8RD#$Bg0MNWQ%&@"))
ASCII_BRIGHTNESS_VALS = np.array([0, 0.0829, 0.0848, 0.1227, 0.1403, 0.1559, 0.185, 0.2183, 0.2417, 0.2571, 0.2852, 0.2902, 0.2919, 0.3099, 0.3192, 0.3232, 
                         0.3294, 0.3384, 0.3609, 0.3619, 0.3667, 0.3737, 0.3747, 0.3838, 0.3921, 0.396, 0.3984, 0.3993, 0.4075, 0.4091, 0.4101, 0.42, 0.423, 0.4247, 
                         0.4274, 0.4293, 0.4328, 0.4382, 0.4385, 0.442, 0.4473, 0.4477, 0.4503, 0.4562, 0.458, 0.461, 0.4638, 0.4667, 0.4686, 0.4693, 0.4703, 0.4833, 
                         0.4881, 0.4944, 0.4953, 0.4992, 0.5509, 0.5567, 0.5569, 0.5591, 0.5602, 0.5602, 0.565, 0.5776, 0.5777, 0.5818, 0.587, 0.5972, 0.5999, 0.6043, 
                         0.6049, 0.6093, 0.6099, 0.6465, 0.6561, 0.6595, 0.6631, 0.6714, 0.6759, 0.6809, 0.6816, 0.6925, 0.7039, 0.7086, 0.7235, 0.7302, 0.7332, 0.7602, 
                         0.7834, 0.8037, 0.9999])

def make_ascii_brightness_lookup_table() -> np.ndarray:
    vals = np.linspace(0, 1, 256)
    idx = np.searchsorted(ASCII_BRIGHTNESS_VALS, vals, side="left")
    return ASCII_BRIGHTNESS_CHARS[np.clip(idx, 0, len(ASCII_BRIGHTNESS_CHARS) - 1)]

ASCII_BRIGHTNESS_LUT = make_ascii_brightness_lookup_table()

def prepare_cat_image(cat_image_path: Path, roi: list[int]) -> Image.Image:
    cat_image = Image.open(cat_image_path).convert("RGBA")
    if roi != [0, 0, 0, 0]:
        cat_image = cat_image.crop(roi)

    # replace background with black
    bg_color = tuple(int(ctsm.BACKGROUND_COLOUR[i:i+2], 16) for i in (1, 3, 5)) + (255,)
    datas = cat_image.getdata()
    new_data = [(0, 0, 0, 255) if item[:3] == bg_color[:3] else item for item in datas]
    cat_image.putdata(new_data)

    return cat_image

def resize_image_for_ascii(image: Image.Image, max_dims: list[int] = [250, 250], char_h_to_w_ratio: float = 2.0) -> Image.Image:
    max_width, max_height = max_dims
    og_width, og_height = image.size

    proposed_height = (og_height * max_width) / (char_h_to_w_ratio * og_width)
    if proposed_height <= max_height:
        new_width = max_width
        new_height = int(proposed_height)
    else:
        new_width = int((og_width * max_height * char_h_to_w_ratio) / og_height)
        new_height = max_height

    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized_image

def image_to_ascii(image: Image.Image) -> str:
    gray = np.array(image.convert("L"))
    ascii_pixels = ASCII_BRIGHTNESS_LUT[gray]
    return "\n".join("".join(row) for row in ascii_pixels)

def get_cat_filepath(cat_filename:str, params: dict) -> Path:
    path = Path(__file__).parent.parent.resolve() / params["folder_str"] / cat_filename
    if not path.exists() or not path.is_file():
        print(f"File: {cat_filename} does not exist.")
        return None
    return path

def extract_cat_type_and_name(cat_image_filename: str) -> list[str]:
    pattern = re.compile(r"^cat_(sitting|standing)_(.+)\.png$")
    match = pattern.match(cat_image_filename)
    if not match:
        print(f"Invalid filename format: {cat_image_filename}")
        return [None, None]
    cat_type, name = match.groups()
    return [cat_type, name]

def video_to_frames(video_path: Path) -> list[int, list[Image.Image]]:
    frames = []
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Converting video {video_path} to frames...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        frames.append(pil_image)
    cap.release()
    return int(fps), frames

def ascii_to_image(ascii_art: str) -> Image.Image:
    font_path = Path(__file__).parent.resolve() / "misc" / "consolas" / "consolas.ttf"
    font_size = 12
    font = ImageFont.truetype(str(font_path), font_size)

    # Compute image dimensions based on longest line and line count
    lines = ascii_art.splitlines()
    line_count = len(lines)
    _, _, img_width, _ = font.getbbox(lines[0], anchor="lt")  # assume monospaced font
    img_height = font_size * line_count
    img = Image.new("RGB", (img_width, img_height), color="black")

    draw = ImageDraw.Draw(img)
    y = 0
    for line in lines:
        draw.text((0, y), line, fill="white", font=font)
        y += font_size

    return img

def frames_to_video(frames: list[Image.Image], output_path: Path, fps: int) -> None:
    if len(frames) == 0:
        print("No frames to convert to video.")
        return

    frame_width, frame_height = frames[0].size
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(str(output_path), fourcc, fps, (frame_width, frame_height))

    for frame in frames:
        frame_bgr = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        video_writer.write(frame_bgr)

    video_writer.release()
    print(f"Video saved to {output_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert cat images to ASCII art.")
    parser.add_argument(
        "input_cat_filename",
        type=str,
        help="The filename of the cat image to convert to ASCII art."
    )

    parser.add_argument(
        "--mh",
        type=int,
        default=250,
        help="The maximum height of the ASCII art."
    )
    parser.add_argument(
        "--mw",
        type=int,
        default=250,
        help="The maximum width of the ASCII art."
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    cat_type, _ = extract_cat_type_and_name(args.input_cat_filename)

    params = ctsm.PARAMS.get(f"cat_{cat_type}")
    if params is None:
        return
    
    cat_filepath = get_cat_filepath(args.input_cat_filename, params)
    if cat_filepath is None:
        return

    cat_image = prepare_cat_image(cat_filepath, params["roi"])
    resized_cat_image = resize_image_for_ascii(cat_image, max_dims=[args.mw, args.mh])
    ascii_art = image_to_ascii(resized_cat_image)

    print(ascii_art)

    return

if __name__ == "__main__":
    main()
