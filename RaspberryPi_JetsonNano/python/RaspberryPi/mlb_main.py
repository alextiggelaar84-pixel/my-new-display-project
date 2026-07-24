import os
import sys
import time
import logging
import statsapi
from PIL import Image, ImageDraw, ImageFont

# Set up local library path for Waveshare e-Paper driver
libdir = "/home/pi/testrepo/e-Paper/RaspberryPi_JetsonNano/python/lib"
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2

# Hardcoded Pi directories
save_dir = "/home/pi/testrepo/e-Paper/standings"
logo_dir = "/home/pi/testrepo/e-Paper/MLB Logos"

# Ensure target folder exists
os.makedirs(save_dir, exist_ok=True)

leagues = [103, 104]  # 103 for AL, 104 for NL
CACHE_EXPIRATION_SECONDS = 12 * 3600  # 12 hours

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def is_cache_valid(file_path):
    """Check if the PNG image exists and is younger than 12 hours."""
    if not os.path.exists(file_path):
        return False
    file_age = time.time() - os.path.getmtime(file_path)
    return file_age < CACHE_EXPIRATION_SECONDS


def generate_division_image(div_name, division, font):
    """Draws and saves the division standings image."""
    # Screen dimensions for 7.5in V2 display
    width = 800
    height = 480
    center_x = width // 2

    background = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(background)

    # Draw Headers
    draw.text((center_x, 15), div_name, font=font, fill=0, anchor="mm")
    draw.text((250, 45), "W-L", font=font, fill=0, anchor="mm")
    draw.text((450, 45), "PCT", font=font, fill=0, anchor="mm")
    draw.text((650, 45), "GB", font=font, fill=0, anchor="mm")

    # Loop through division teams
    for i, team in enumerate(division.get('teams', [])):
        team_id = team.get('team_id') or team.get('id')

        if team_id:
            logo_path = os.path.join(logo_dir, f"{team_id}.png")
            if os.path.exists(logo_path):
                try:
                    teamlogo = Image.open(logo_path).resize((75, 75))
                    height_offset = i * 80 + 60
                    background.paste(teamlogo, (40, height_offset))
                except Exception as logo_err:
                    logging.error(f"Error loading logo {logo_path}: {logo_err}")

        # Extract stats safely
        wins = team.get('w', team.get('wins', 0))
        losses = team.get('l', team.get('losses', 0))
        gb = team.get('gb', team.get('gamesBack', '-'))
        pct = wins / (wins + losses) if (wins + losses) > 0 else 0

        height_offset = i * 80 + 100
        draw.text((250, height_offset), f"{wins}-{losses}", font=font, fill=0, anchor="mm")
        draw.text((450, height_offset), f"{pct:.3f}", font=font, fill=0, anchor="mm")
        draw.text((650, height_offset), f"{gb}", font=font, fill=0, anchor="mm")

    safe_div_name = div_name.replace(" ", "_").lower()
    file_path = os.path.join(save_dir, f"{safe_div_name}_standings.png")
    background.save(file_path)
    logging.info(f"Generated & saved new standings image: {file_path}")
    return background


def update_display(epd, image_path):
    """Loads an existing image file and renders it on the e-Paper display."""
    try:
        logging.info(f"Rendering on display: {image_path}")
        image = Image.open(image_path)
        epd.init()
        epd.display(epd.getbuffer(image))
        epd.sleep()
    except Exception as e:
        logging.error(f"Failed to update display: {e}")


def main_loop():
    logging.info("Starting MLB E-Paper Loop...")
    epd = epd7in5_V2.EPD()

    # Load font
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 30)
    except IOError:
        logging.warning("DejaVu font not found, falling back to default font.")
        font = ImageFont.load_default()

    # Define division order
    division_files = [
        "american_league_east_standings.png",
        "american_league_central_standings.png",
        "american_league_west_standings.png",
        "national_league_east_standings.png",
        "national_league_central_standings.png",
        "national_league_west_standings.png"
    ]

    while True:
        try:
            # Check if any cached file is older than 12 hours (or missing)
            needs_refresh = any(
                not is_cache_valid(os.path.join(save_dir, f_name)) 
                for f_name in division_files
            )

            if needs_refresh:
                logging.info("Cache expired or missing. Fetching fresh standings data from API...")
                for league_id in leagues:
                    try:
                        standings = statsapi.standings_data(leagueId=league_id)
                        for division_id, division in standings.items():
                            div_name = division.get('div_name', 'Division')
                            generate_division_image(div_name, division, font)
                    except Exception as api_err:
                        logging.error(f"Error fetching API data for league {league_id}: {api_err}")

            # Cycle through each division image on display
            for f_name in division_files:
                file_path = os.path.join(save_dir, f_name)
                
                if os.path.exists(file_path):
                    update_display(epd, file_path)
                    logging.info("Waiting 60 seconds before next division...")
                    time.sleep(60)  # Pause 1 minute between divisions
                else:
                    logging.warning(f"File {file_path} not ready yet, skipping step.")

        except KeyboardInterrupt:
            logging.info("Script stopped by user.")
            epd7in5_V2.epdconfig.module_exit()
            sys.exit()
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main_loop()