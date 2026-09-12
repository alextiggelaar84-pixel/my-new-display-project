import glob
import logging
import os
import sys
import threading
import time
from PIL import Image

# Import script modules
import Game_info as game_info
import mlb

# Dynamic directory resolution for standings/game PNGs across Linux & Windows
if sys.platform.startswith("linux"):
    MLB_STANDINGS_DIR = os.path.expanduser("~/testrepo/e-Paper/standings")
else:
    MLB_STANDINGS_DIR = (
        r"C:\Users\sherr\Documents\git\real_eink\standings"
    )

os.makedirs(MLB_STANDINGS_DIR, exist_ok=True)

# Dynamic path resolution to locate your Waveshare driver folder
script_dir = os.path.dirname(os.path.abspath(__file__))
possible_lib_paths = [
    os.path.join(script_dir, "lib"),
    os.path.expanduser(
        "~/testrepo/e-Paper/RaspberryPi_JetsonNano/python/lib"
    ),
]

for lib_path in possible_lib_paths:
    if os.path.exists(lib_path):
        sys.path.append(lib_path)

# Try importing the hardware driver
try:
    from waveshare_epd import epd7in5_V2

    HARDWARE_CONNECTED = True
    logging.info("Waveshare e-Paper library successfully loaded!")
except ImportError as e:
    HARDWARE_CONNECTED = False
    logging.warning(
        f"Waveshare library not found ({e}). Running in simulation mode."
    )
TWELVE_HOURS_IN_SECONDS = 12 * 60 * 60
TEN_MINUTES_IN_SECONDS = 10 * 60
THREE_MINUTES_IN_SECONDS = 180

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_all_display_images():
    """Returns a sorted list of all generated PNG files."""
    pattern = os.path.join(MLB_STANDINGS_DIR, "*.png")
    return sorted(glob.glob(pattern))


def check_and_generate_standings():
    """Runs mlb.make_image_files() if standings are missing or > 12 hours old."""
    pattern = os.path.join(MLB_STANDINGS_DIR, "*standings.png")
    images = glob.glob(pattern)

    should_run = False
    if not images:
        logging.info(
            "No standings images found. Triggering mlb.py generation..."
        )
        should_run = True
    else:
        oldest_file_time = min(os.path.getmtime(img) for img in images)
        file_age = time.time() - oldest_file_time
        if file_age >= TWELVE_HOURS_IN_SECONDS:
            logging.info(
                f"Standings are {file_age / 3600:.1f} hours old. Triggering regeneration..."
            )
            should_run = True

    if should_run:
        try:
            mlb.make_image_files()
            logging.info("Standings generation complete.")
        except Exception as e:
            logging.error(f"Error executing mlb.make_image_files(): {e}")


def start_standings_generator_loop():
    """Background loop that ensures standings are regenerated every 12 hours."""
    while True:
        check_and_generate_standings()
        time.sleep(TWELVE_HOURS_IN_SECONDS)


def start_game_info_generator_loop():
    """Background loop that updates game status every 10 minutes."""
    while True:
        try:
            game_info.generate_game_image()
        except Exception as e:
            logging.error(f"Error in game info loop: {e}")
        time.sleep(TEN_MINUTES_IN_SECONDS)


def run_display_cycle():
    """Main loop: launches image generators and cycles generated images on e-Paper."""
    epd = None
    if HARDWARE_CONNECTED:
        epd = epd7in5_V2.EPD()
        epd.init()

    # Initial generation checks on startup
    game_info.generate_game_image()
    check_and_generate_standings()

    # Start background generator threads
    threading.Thread(
        target=start_standings_generator_loop, daemon=True
    ).start()
    threading.Thread(
        target=start_game_info_generator_loop, daemon=True
    ).start()

    logging.info("Starting image rotation loop...")

    while True:
        images = get_all_display_images()

        if not images:
            logging.warning(
                "No images available to display. Waiting 3 minutes..."
            )
            time.sleep(THREE_MINUTES_IN_SECONDS)
            continue

        for img_path in images:
            logging.info(
                f"Displaying on E-Paper: {os.path.basename(img_path)}"
            )

            try:
                with Image.open(img_path) as img:
                    if HARDWARE_CONNECTED:
                        epd.init()
                        epd.display(epd.getbuffer(img.convert("1")))
                        epd.sleep()
                    else:
                        img.show()

            except Exception as e:
                logging.error(f"Failed to display image {img_path}: {e}")

            time.sleep(THREE_MINUTES_IN_SECONDS)


if __name__ == "__main__":
    run_display_cycle()