import os
import time
import glob
import logging
import threading
from PIL import Image

# Import both script modules
import mlb
import Game_info as game_info


try:
    from waveshare_epd import epd7in5_V2
    HARDWARE_CONNECTED = True
except ImportError:
    HARDWARE_CONNECTED = False
    logging.warning("Waveshare library not found. Running in simulation mode.")


# Target directory where generated images live
MLB_STANDINGS_DIR = r"C:\Users\sherr\Documents\git\real_eink\standings"
TWELVE_HOURS_IN_SECONDS = 12 * 60 * 60
TEN_MINUTES_IN_SECONDS = 10 * 60
THREE_MINUTE_IN_SECONDS = 180

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_all_display_images():
    """Returns a sorted list of all generated PNG files (Game Info + Division Standings)."""
    pattern = os.path.join(MLB_STANDINGS_DIR, "*.png")
    return sorted(glob.glob(pattern))


def check_and_generate_standings():
    """Runs mlb.make_image_files() if standings are missing or older than 12 hours."""
    pattern = os.path.join(MLB_STANDINGS_DIR, "*_standings.png")
    images = glob.glob(pattern)
    
    should_run = False
    if not images:
        logging.info("No standings images found. Triggering mlb.py generation...")
        should_run = True
    else:
        oldest_file_time = min(os.path.getmtime(img) for img in images)
        file_age = time.time() - oldest_file_time
        if file_age >= TWELVE_HOURS_IN_SECONDS:
            logging.info(f"Standings are {file_age / 3600:.1f} hours old. Triggering regeneration...")
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
    """Background loop that updates game status (Pregame/Live/Postgame) every 10 minutes."""
    while True:
        try:
            game_info.generate_game_image()
        except Exception as e:
            logging.error(f"Error in game info loop: {e}")
        time.sleep(TEN_MINUTES_IN_SECONDS)


def run_display_cycle():
    """Main loop: launches image generators and cycles all generated images on the e-Paper display."""
    
    # Initialize hardware once if available
    epd = None
    if HARDWARE_CONNECTED:
        epd = epd7in5_V2.EPD()
        epd.init()

    # Initial generation checks
    game_info.generate_game_image()
    check_and_generate_standings()

    # Start background generator threads
    threading.Thread(target=start_standings_generator_loop, daemon=True).start()
    threading.Thread(target=start_game_info_generator_loop, daemon=True).start()

    logging.info("Starting 1-minute image rotation loop...")
    
    while True:
        images = get_all_display_images()
        
        if not images:
            logging.warning("No images available to display. Waiting 1 minute...")
            time.sleep(THREE_MINUTE_IN_SECONDS)
            continue
            
        for img_path in images:
            logging.info(f"Displaying on E-Paper: {os.path.basename(img_path)}")
            
            try:
                with Image.open(img_path) as img:
                    if HARDWARE_CONNECTED:
                        # Re-init hardware if it went into sleep mode
                        epd.init()
                        # Push 1-bit monochrome image buffer to the screen
                        epd.display(epd.getbuffer(img.convert('1')))
                        # Put panel into low-power sleep mode while waiting for the next update
                        epd.sleep()
                    else:
                        # Fallback for Windows desktop testing
                        img.show()
                        
            except Exception as e:
                logging.error(f"Failed to display image {img_path}: {e}")
            
            # Wait 60 seconds before showing the next image
            time.sleep(THREE_MINUTE_IN_SECONDS)


if __name__ == "__main__":
    run_display_cycle()