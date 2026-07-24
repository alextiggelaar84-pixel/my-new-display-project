import sys
import os
import time
import glob
import logging
import threading
import statsapi
from PIL import Image, ImageDraw, ImageFont

# Set up local library path
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

try:
    from waveshare_epd import epd7in5_V2
except ImportError:
    from waveshare_epd import epd7in5_V2

# Constants & Paths on Raspberry Pi
STANDINGS_DIR = "/home/pi/testrepo/e-Paper/MLB Logos"
LEAGUES = [103, 104]  # 103: American League, 104: National League

TWELVE_HOURS_IN_SECONDS = 12 * 60 * 60
ONE_MINUTE_IN_SECONDS = 60

EPD_WIDTH = 800
EPD_HEIGHT = 480

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def make_image_files():
    """Fetches MLB standings via statsapi and generates standings images for each division."""
    logging.info("Starting MLB standings image generation...")
    os.makedirs(STANDINGS_DIR, exist_ok=True)

    # Calculate middle coordinates for header
    center_x = EPD_WIDTH // 2

    # Load Font
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 30)
    except IOError:
        logging.warning("DejaVu font not found, falling back to default.")
        font = ImageFont.load_default()

    # Process each league and division
    for league_id in LEAGUES:
        try:
            standings = statsapi.standings_data(leagueId=league_id)
        except Exception as e:
            logging.error(f"Failed to fetch standings data for league {league_id}: {e}")
            continue

        for division_id, division in standings.items():
            div_name = division.get('div_name', 'Division')
            background = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)
            draw = ImageDraw.Draw(background)
            
            # Draw Division Header
            draw.text((center_x, 15), div_name, font=font, fill=0, anchor="mm")
            draw.text((250, 45), "W-L", font=font, fill=0, anchor="mm")
            draw.text((450, 45), "PCT", font=font, fill=0, anchor="mm")
            draw.text((650, 45), "GB", font=font, fill=0, anchor="mm")
                        
            # Loop through division teams
            for i, team in enumerate(division.get('teams', [])):
                # Get team ID directly from statsapi data
                team_id = team.get('team_id') or team.get('id')
                
                if team_id:
                    logo_path = os.path.join(STANDINGS_DIR, f"{team_id}.png")
                    
                    if os.path.exists(logo_path):
                        try:
                            with Image.open(logo_path) as logo:
                                teamlogo = logo.resize((75, 75))
                                height_offset = i * 80 + 60
                                background.paste(teamlogo, (40, height_offset))
                        except Exception as logo_err:
                            logging.error(f"Failed pasting logo for team ID {team_id}: {logo_err}")
                    else:
                        logging.warning(f"Logo file not found: {logo_path}")

                # Extract stats safely
                wins = team.get('w', team.get('wins', 0))
                losses = team.get('l', team.get('losses', 0))
                gb = team.get('gb', team.get('gamesBack', '-'))
                
                # Calculate win percentage
                if 'pct' in team:
                    try:
                        pct = float(team['pct'])
                    except ValueError:
                        pct = 0.0
                else:
                    pct = wins / (wins + losses) if (wins + losses) > 0 else 0.0

                # Draw Team Stats text
                height_offset = i * 80 + 100
                draw.text((250, height_offset), f"{wins}-{losses}", font=font, fill=0, anchor="mm")
                draw.text((450, height_offset), f"{pct:.3f}", font=font, fill=0, anchor="mm")
                draw.text((650, height_offset), f"{gb}", font=font, fill=0, anchor="mm")

            # Clean division name and save file
            safe_div_name = div_name.replace(" ", "_").lower()
            file_path = os.path.join(STANDINGS_DIR, f"{safe_div_name}_standings.png")

            background.save(file_path)
            logging.info(f"Generated and saved: {file_path}")


def get_standings_images():
    """Returns a sorted list of generated PNG standings files."""
    pattern = os.path.join(STANDINGS_DIR, "*_standings.png")
    return sorted(glob.glob(pattern))


def check_and_generate_images():
    """Checks if standing images exist or are stale (>12 hours old) and triggers generation."""
    images = get_standings_images()
    should_run = False

    if not images:
        logging.info("No standings images found. Triggering generation...")
        should_run = True
    else:
        oldest_file_time = min(os.path.getmtime(img) for img in images)
        file_age = time.time() - oldest_file_time

        if file_age >= TWELVE_HOURS_IN_SECONDS:
            logging.info(f"Images are {file_age / 3600:.1f} hours old. Triggering regeneration...")
            should_run = True

    if should_run:
        try:
            make_image_files()
        except Exception as e:
            logging.error(f"Error during make_image_files(): {e}")


def start_12hr_generator_loop():
    """Background thread loop to keep data refreshed every 12 hours."""
    while True:
        check_and_generate_images()
        time.sleep(TWELVE_HOURS_IN_SECONDS)


def run_display_cycle():
    """Initializes screen, checks/generates data, and cycles through images continuously."""
    epd = epd7in5_V2.EPD()
    logging.info("Initializing Waveshare 7.5in V2 Display...")
    epd.init()
    epd.Clear()

    # Initial check & generate on startup
    check_and_generate_images()

    # Start 12-hour background updates
    generator_thread = threading.Thread(target=start_12hr_generator_loop, daemon=True)
    generator_thread.start()

    logging.info("Starting 1-minute display rotation loop...")

    try:
        while True:
            images = get_standings_images()

            if not images:
                logging.warning("No standings images found to display. Waiting 1 minute...")
                time.sleep(ONE_MINUTE_IN_SECONDS)
                continue

            for img_path in images:
                logging.info(f"Displaying on screen: {os.path.basename(img_path)}")

                try:
                    epd.init()
                    with Image.open(img_path) as img:
                        img_resized = img.resize((EPD_WIDTH, EPD_HEIGHT))
                        img_bw = img_resized.convert("1")
                        epd.display(epd.getbuffer(img_bw))
                except Exception as e:
                    logging.error(f"Failed to write image to display: {e}")

                # Put hardware into low-power sleep mode while waiting
                epd.sleep()
                time.sleep(ONE_MINUTE_IN_SECONDS)

    except KeyboardInterrupt:
        logging.info("Stopping script via user interrupt...")
    finally:
        logging.info("Clearing and powering down e-Paper panel...")
        epd.init()
        epd.Clear()
        epd.sleep()


if __name__ == "__main__":
    run_display_cycle()