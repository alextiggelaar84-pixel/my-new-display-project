import logging
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Append local library path if present
libdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"
)
if os.path.exists(libdir):
    sys.path.append(libdir)

logging.basicConfig(level=logging.INFO)


def get_logo_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.expanduser("~/my-new-display-project/MLB Logos"),
        os.path.expanduser("~/testrepo/e-Paper/MLB Logos"),
        os.path.abspath(os.path.join(script_dir, "..", "MLB Logos")),
        os.path.abspath(os.path.join(script_dir, "MLB Logos")),
        r"C:\git\real_eink\MLB Logos",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


LOGO_DIR = get_logo_dir()


class epd:
    width = 800
    height = 480


def load_font(size):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
        )
    except IOError:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()


def make_image_files():
    try:
        logging.info("Initializing 7.5in V2 Display Canvas...")
        background = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(background)
        text = "American League East"

        center_x = epd.width // 2
        font = load_font(30)

        # Dynamic Logo Loading
        logo_path = os.path.join(LOGO_DIR, "143.png")

        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo = logo.resize((75, 75), Image.Resampling.LANCZOS)

                bg = Image.new("RGBA", (75, 75), (255, 255, 255, 255))
                bg.paste(logo, (0, 0), logo)
                bw_logo = bg.convert("L").point(
                    lambda p: 0 if p < 200 else 255, mode="1"
                )

                for i in range(5):
                    height_offset = i * 85 + 60
                    background.paste(bw_logo, (40, height_offset))
            except Exception as logo_err:
                logging.error(f"Error processing test logo {logo_path}: {logo_err}")

        draw.text((center_x, 15), text, font=font, fill=0, anchor="mm")
        draw.text((250, 45), "W-L", font=font, fill=0, anchor="mm")
        draw.text((450, 45), "PCT", font=font, fill=0, anchor="mm")
        draw.text((650, 45), "GB", font=font, fill=0, anchor="mm")

        # Save to common output directory
        if sys.platform.startswith("linux"):
            output_dir = os.path.expanduser("~/testrepo/e-Paper/standings")
        else:
            output_dir = r"C:\Users\sherr\Documents\git\real_eink\standings"

        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(
            output_dir, "american_league_east_standings.png"
        )
        background.save(save_path)
        logging.info(f"Saved standings image to {save_path}")

    except Exception as e:
        logging.error(f"Error in make_image_files: {e}")


if __name__ == "__main__":
    make_image_files()