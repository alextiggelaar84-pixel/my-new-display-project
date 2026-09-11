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
    pi_logo_path = os.path.expanduser("~/testrepo/e-Paper/MLB Logos")
    if os.path.exists(pi_logo_path):
        return pi_logo_path

    script_dir = os.path.dirname(os.path.abspath(__file__))
    for relative_path in [
        os.path.join(script_dir, "..", "..", "MLB Logos"),
        os.path.join(script_dir, "..", "MLB Logos"),
        r"C:\git\real_eink\MLB Logos",
    ]:
        resolved = os.path.abspath(relative_path)
        if os.path.exists(resolved):
            return resolved
    return pi_logo_path


LOGO_DIR = get_logo_dir()


class epd:
    width = 800
    height = 480


def make_image_files():
    try:
        logging.info("Initializing 7.5in V2 Display Canvas...")
        background = Image.new("1", (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(background)
        text = "American League East"

        center_x = epd.width // 2

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30
            )
        except IOError:
            logging.warning("DejaVu font not found, falling back to default.")
            font = ImageFont.load_default()

        # Dynamic Logo Loading
        logo_path = os.path.join(LOGO_DIR, "143.png")

        for i in range(5):
            if os.path.exists(logo_path):
                teamlogo = Image.open(logo_path)
                teamlogo = teamlogo.resize((75, 75))
                height_offset = i * 85 + 60
                background.paste(teamlogo, (40, height_offset))

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