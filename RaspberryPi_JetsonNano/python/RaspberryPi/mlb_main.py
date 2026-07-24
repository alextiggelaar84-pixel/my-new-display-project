import sys
import os
import time
import glob
import logging
import threading
from PIL import Image, ImageDraw, ImageFont

# Add Waveshare library path if necessary
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

try:
    from waveshare_epd import epd7in5_V2
except ImportError:
    from waveshare_epd import epd7in5_V2

# Constants & Paths
STANDINGS_DIR = "/home/pi/testrepo/e-Paper/MLB Logos"
LOGO_PATH = os.path.join(STANDINGS_DIR, "143.png")
OUTPUT_IMAGE_PATH = os.path.join(STANDINGS_DIR, "al_east_standings.png")

TWELVE_HOURS_IN_SECONDS = 12 * 60 * 60
ONE_MINUTE_IN_SECONDS = 60

EPD_WIDTH = 800
EPD_HEIGHT = 480

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def generate_standings_image():
    """Generates the standings layout image using PIL and saves it locally."""
    logging.info("Generating standings image...")

    # Create a blank white canvas (255 = white in 1-bit '1' mode)
    background = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)
    draw = ImageDraw.Draw(background)

    # Load custom font or fallback to default
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font_large = ImageFont.truetype(font_path, 30)
    except IOError:
        logging.warning("DejaVu font not found, falling back to default.")
        font_large = ImageFont.load_default()

    # Draw Title & Table Headers
    center_x = EPD_WIDTH // 2
    draw.text((center_x, 15), "American League East", font=font_large, fill=0, anchor="mm")
    draw.text((250, 45), "W-L", font=font_large, fill=0, anchor="mm")
    draw.text((450, 45), "PCT", font=font_large, fill=0, anchor="mm")
    draw.text((650, 45), "GB", font=font_large, fill=0, anchor="mm")

    # Draw Team Logos
    if os.path.exists(LOGO_PATH):
        with Image.open(LOGO_PATH) as logo:
            teamlogo = logo.resize((75, 75))
            for i in range(5):
                height_offset = i * 85 + 60
                background.paste(teamlogo, (40, height_offset))
    else:
        logging.error(f"Logo not found at {LOGO_PATH}. Skipping logo paste.")

    # Ensure directory exists and save the output file
    os.makedirs(STANDINGS_DIR, exist_ok=True)
    background.save(OUTPUT_IMAGE_PATH)
    logging.info(f"Successfully saved standings image to {OUTPUT_IMAGE_PATH}")


def get_standings_images():
    """Returns a sorted list of generated PNG standings files."""
    pattern = os.path.join(STANDINGS_DIR, "*_standings.png")
    return sorted(glob.glob(pattern))


def check_and_generate_images():
    """Generates the image if missing or older than 12 hours."""
    images = get_standings_images()
    should_run = False

    if not images:
        logging.info("No standings images found. Generating now...")
        should_run = True
    else:
        oldest_file_time = min(os.path.getmtime(img) for img in images)
        file_age = time.time() - oldest_file_time

        if file_age >= TWELVE_HOURS_IN_SECONDS:
            logging.info(f"Images are {file_age / 3600:.1f} hours old. Regenerating...")
            should_run = True

    if should_run:
        try:
            generate_standings_image()
        except Exception as e:
            logging.error(f"Error executing generate_standings_image(): {e}")


def start_12hr_generator_loop():
    """Background loop that ensures images are regenerated every 12 hours."""
    while True:
        check_and_generate_images()
        time.sleep(TWELVE_HOURS_IN_SECONDS)


def run_display_cycle():
    """Main loop: initializes display, starts generator thread, and updates screen."""
    epd = epd7in5_V2.EPD()
    logging.info("Initializing Waveshare 7.5-inch e-Paper display...")
    epd.init()
    epd.Clear()

    # Initial image generation check
    check_and_generate_images()

    # Start 12-hour background updater
    generator_thread = threading.Thread(target=start_12hr_generator_loop, daemon=True)
    generator_thread.start()

    logging.info("Starting image rotation loop...")

    try:
        while True:
            images = get_standings_images()

            if not images:
                logging.warning("No images available to display. Retrying in 1 minute...")
                time.sleep(ONE_MINUTE_IN_SECONDS)
                continue

            for img_path in images:
                logging.info(f"Displaying on EPD: {os.path.basename(img_path)}")

                try:
                    epd.init()
                    with Image.open(img_path) as img:
                        img_resized = img.resize((EPD_WIDTH, EPD_HEIGHT))
                        img_bw = img_resized.convert("1")
                        epd.display(epd.getbuffer(img_bw))

                except Exception as e:
                    logging.error(f"Failed to display image {img_path}: {e}")

                # Put hardware to sleep to protect the panel
                epd.sleep()
                time.sleep(ONE_MINUTE_IN_SECONDS)

    except KeyboardInterrupt:
        logging.info("Exiting script...")
    finally:
        logging.info("Putting display into deep sleep...")
        epd.init()
        epd.Clear()
        epd.sleep()


if __name__ == "__main__":
    run_display_cycle()