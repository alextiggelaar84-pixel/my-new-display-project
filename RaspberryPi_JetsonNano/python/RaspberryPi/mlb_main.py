#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
import time
import glob
import logging
import threading
from PIL import Image, ImageDraw, ImageFont
import statsapi

# ----------------------------------------------------------------------
# PATH & ENVIRONMENT SETUP
# ----------------------------------------------------------------------
script_dir = os.path.dirname(os.path.realpath(__file__))

# Setup path to Waveshare's 'lib' directory
libdir = os.path.join(os.path.dirname(script_dir), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2

# Output folder for generated PNGs
save_dir = os.path.join(script_dir, 'standings')
os.makedirs(save_dir, exist_ok=True)

# MLB Leagues (103 = AL, 104 = NL)
leagues = [103, 104]

# Display Specs
EPD_WIDTH = 800
EPD_HEIGHT = 480
TWELVE_HOURS = 12 * 60 * 60
ONE_MINUTE = 60

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ----------------------------------------------------------------------
# 1. IMAGE GENERATOR FUNCTION
# ----------------------------------------------------------------------
def make_image_files():
    """Fetches MLB standings data and generates 1-bit B&W PNG images."""
    try:
        logging.info("Fetching MLB standings data...")
        center_x = EPD_WIDTH // 2

        # Load Linux font fallback
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        except IOError:
            logging.warning("DejaVu font not found, falling back to default.")
            font = ImageFont.load_default()

        for league_id in leagues:
            standings = statsapi.standings_data(leagueId=league_id)
            
            for division_id, division in standings.items():
                div_name = division.get('div_name', 'Division')
                background = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)  # 255 = White
                draw = ImageDraw.Draw(background)
                
                # Draw Header
                draw.text((center_x, 20), div_name, font=font, fill=0, anchor="mm")
                
                # Draw Teams
                for i, team in enumerate(division.get('teams', [])):
                    team_name = team.get('name')
                    height_offset = i * 75 + 60
                    
                    # Fetch and convert logo
                    team_info = statsapi.lookup_team(team_name)
                    if team_info:
                        team_id = team_info[0]['id']
                        logo_path = os.path.join(script_dir, "MLB Logos", f"{team_id}.png")
                        
                        if os.path.exists(logo_path):
                            teamlogo = Image.open(logo_path).resize((65, 65))
                            
                            # Clean 1-bit conversion
                            mask = teamlogo.split()[3] if 'A' in teamlogo.mode else None
                            logo_bw = teamlogo.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
                            
                            if mask:
                                logo_bg = Image.new('1', (65, 65), 255)
                                logo_bg.paste(logo_bw, (0, 0), mask=mask)
                                background.paste(logo_bg, (40, height_offset))
                            else:
                                background.paste(logo_bw, (40, height_offset))

                    wins = team.get('w', 0)
                    losses = team.get('l', 0)
                    gb = team.get('gb', '-')
                    pct = wins / (wins + losses) if (wins + losses) > 0 else 0

                    # Draw Team Stats
                    draw.text((250, height_offset + 20), f"{wins}-{losses}", font=font, fill=0, anchor="mm")
                    draw.text((450, height_offset + 20), f"{pct:.3f}", font=font, fill=0, anchor="mm")
                    draw.text((650, height_offset + 20), f"{gb}", font=font, fill=0, anchor="mm")

                # Save 1-bit image to standings directory
                safe_div_name = div_name.replace(" ", "_").lower()
                file_path = os.path.join(save_dir, f"{safe_div_name}_standings.png")
                background.save(file_path)
                logging.info(f"Saved: {file_path}")

    except Exception as e:
        logging.error(f"Error generating standings images: {e}")


# ----------------------------------------------------------------------
# 2. HELPER & BACKGROUND THREAD LOGIC
# ----------------------------------------------------------------------
def get_standings_images():
    """Returns all generated PNG files from the standings directory."""
    pattern = os.path.join(save_dir, "*_standings.png")
    return sorted(glob.glob(pattern))


def check_and_generate_images():
    """Checks if images exist or are older than 12 hours before generating."""
    images = get_standings_images()
    should_run = False
    
    if not images:
        logging.info("No standings images found. Generating now...")
        should_run = True
    else:
        oldest_file_time = min(os.path.getmtime(img) for img in images)
        file_age = time.time() - oldest_file_time
        if file_age >= TWELVE_HOURS:
            logging.info(f"Images are {file_age / 3600:.1f} hours old. Regenerating...")
            should_run = True

    if should_run:
        make_image_files()


def start_12hr_generator_loop():
    """Background loop that sleeps for 12 hours between API refreshes."""
    while True:
        check_and_generate_images()
        time.sleep(TWELVE_HOURS)


# ----------------------------------------------------------------------
# 3. MAIN HARDWARE DISPLAY CYCLE
# ----------------------------------------------------------------------
def main():
    # 1. Run immediate check/generation on launch
    check_and_generate_images()

    # 2. Start background thread to update API data every 12 hours
    generator_thread = threading.Thread(target=start_12hr_generator_loop, daemon=True)
    generator_thread.start()

    # 3. Hardware Display Driver Loop
    try:
        epd = epd7in5_V2.EPD()
        logging.info("Initializing 7.5in V2 Display...")
        epd.init()
        epd.Clear()

        logging.info("Starting 1-minute image rotation loop...")
        
        while True:
            images = get_standings_images()
            
            if not images:
                logging.warning("No images available to display. Retrying in 1 minute...")
                time.sleep(ONE_MINUTE)
                continue
                
            for img_path in images:
                logging.info(f"Pushing to e-Paper: {os.path.basename(img_path)}")
                
                with Image.open(img_path) as Himage:
                    # Quick init and update hardware
                    epd.init_fast() 
                    epd.display(epd.getbuffer(Himage))
                    
                    # Put hardware to sleep between updates
                    epd.sleep()
                
                time.sleep(ONE_MINUTE)

    except IOError as e:
        logging.error(f"Hardware Error: {e}")

    except KeyboardInterrupt:
        logging.info("Stopping script and putting display to sleep...")
        epd7in5_V2.epdconfig.module_exit(cleanup=True)
        sys.exit()


if __name__ == "__main__":
    main()