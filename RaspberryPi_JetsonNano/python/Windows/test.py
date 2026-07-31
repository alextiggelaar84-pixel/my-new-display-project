import os
import sys
import logging
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_git_base_path():
    """Dynamically finds the 'git' directory in the current working/script path."""
    current_path = os.path.abspath(__file__)
    parts = current_path.split(os.sep)
    
    # Look for 'git' in the path (case-insensitive)
    for i, part in enumerate(parts):
        if part.lower() == 'git':
            # Reconstruct path up to and including 'git'
            return os.sep.join(parts[:i+1])
            
    # Fallback to current working directory if 'git' is not in the folder path
    logging.warning("'git' folder not found in script path. Falling back to relative path from execution directory.")
    return os.getcwd()

# Dynamically set LOGO_DIR starting from the 'git' folder
BASE_GIT_DIR = get_git_base_path()
LOGO_DIR = os.path.join(BASE_GIT_DIR, "real_eink", "MLB Logos")

def test_display_logos():
    logging.info(f"Resolved Logo Directory: {LOGO_DIR}")

    if not os.path.exists(LOGO_DIR):
        logging.error(f"Directory not found: {LOGO_DIR}")
        return

    # Find all PNG files in the logo folder
    logo_files = [f for f in os.listdir(LOGO_DIR) if f.lower().endswith('.png')]
    
    if not logo_files:
        logging.warning(f"No PNG files found in {LOGO_DIR}")
        return

    logging.info(f"Found {len(logo_files)} logos. Processing into 1-bit black & white...")

    for filename in logo_files:
        logo_path = os.path.join(LOGO_DIR, filename)
        
        try:
            # 1. Open original image
            logo = Image.open(logo_path)

            # 2. Handle transparent PNG backgrounds (fill transparency with solid white)
            if logo.mode in ('RGBA', 'LA') or (logo.mode == 'P' and 'transparency' in logo.info):
                alpha = logo.convert('RGBA').split()[-1]
                bg = Image.new('RGBA', logo.size, (255, 255, 255, 255))
                bg.paste(logo, mask=alpha)
                logo = bg.convert('RGB')
            else:
                logo = logo.convert('RGB')

            # 3. Convert directly to 1-bit monochrome (Strict Black and White for e-Paper)
            bw_logo = logo.convert('1')

            logging.info(f"Displaying: {filename} (Mode: {bw_logo.mode}, Size: {bw_logo.size})")

            # 4. Show the image in native system viewer
            bw_logo.show()

            # Interactive step-through
            input(f"Showing '{filename}'. Press Enter in console for next image...")

        except Exception as e:
            logging.error(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    test_display_logos()