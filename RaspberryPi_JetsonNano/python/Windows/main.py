import os
import time
import glob
import logging
import threading
from PIL import Image

# Import your script file (assumes mlb.py is in the same directory)
import mlb  

# Target directory where mlb.py saves standings images
STANDINGS_DIR = r"C:\git\real_eink\RaspberryPi_JetsonNano\python\Windows\standings"
TWELVE_HOURS_IN_SECONDS = 12 * 60 * 60
ONE_MINUTE_IN_SECONDS = 60

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_standings_images():
    """Returns a sorted list of all generated PNG standings files."""
    pattern = os.path.join(STANDINGS_DIR, "*_standings.png")
    return sorted(glob.glob(pattern))


def check_and_generate_images():
    """Runs mlb.make_image_files() if images are missing or older than 12 hours."""
    images = get_standings_images()
    
    should_run = False
    
    if not images:
        logging.info("No standings images found. Triggering mlb.py generation...")
        should_run = True
    else:
        # Check the age of the oldest image file
        oldest_file_time = min(os.path.getmtime(img) for img in images)
        file_age = time.time() - oldest_file_time
        
        if file_age >= TWELVE_HOURS_IN_SECONDS:
            logging.info(f"Images are {file_age / 3600:.1f} hours old. Triggering regeneration...")
            should_run = True

    if should_run:
        try:
            mlb.make_image_files()
            logging.info("Image generation complete.")
        except Exception as e:
            logging.error(f"Error executing mlb.make_image_files(): {e}")


def start_12hr_generator_loop():
    """Background loop that ensures images are regenerated every 12 hours."""
    while True:
        check_and_generate_images()
        # Sleep for 12 hours before checking again
        time.sleep(TWELVE_HOURS_IN_SECONDS)


def run_display_cycle():
    """Main loop: checks files on launch, starts generator thread, cycles images every minute."""
    
    # 1. Initial check & generation if files don't exist
    check_and_generate_images()

    # 2. Start the 12-hour background updater thread
    generator_thread = threading.Thread(target=start_12hr_generator_loop, daemon=True)
    generator_thread.start()

    logging.info("Starting 1-minute image rotation loop...")
    
    # 3. Continuous 1-minute display rotation loop
    while True:
        images = get_standings_images()
        
        if not images:
            logging.warning("No images available to display. Waiting 1 minute...")
            time.sleep(ONE_MINUTE_IN_SECONDS)
            continue
            
        for img_path in images:
            logging.info(f"Displaying: {os.path.basename(img_path)}")
            
            try:
                # Open image
                with Image.open(img_path) as img:
                    # Windows preview fallback (Replace with epd hardware logic on Pi)
                    os.startfile(img_path) 
            except Exception as e:
                logging.error(f"Failed to display image {img_path}: {e}")
            
            # Wait 60 seconds before showing the next image
            time.sleep(ONE_MINUTE_IN_SECONDS)


if __name__ == "__main__":
    run_display_cycle()