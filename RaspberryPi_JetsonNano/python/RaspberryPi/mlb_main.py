import os
import sys
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

# Ensure the target folder exists
os.makedirs(save_dir, exist_ok=True)

leagues = [103, 104]  # 103 for AL, 104 for NL

logging.basicConfig(level=logging.INFO)


def make_image_files():
    try:
        logging.info("Initializing 7.5in V2 Display...")
        epd = epd7in5_V2.EPD()
        epd.init()
        epd.Clear()

        # Calculate middle coordinates for header
        center_x = epd.width // 2

        # Load font
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        try:
            font = ImageFont.truetype(font_path, 30)
            print("Using DejaVuSans-Bold font at size 30")
        except IOError:
            logging.warning("DejaVu font not found, falling back to default.")
            font = ImageFont.load_default()
            print("Using Default font")

        # Process each league and division
        for league_id in leagues:
            standings = statsapi.standings_data(leagueId=league_id)

            for division_id, division in standings.items():
                div_name = division.get('div_name', 'Division')
                background = Image.new('1', (epd.width, epd.height), 255)
                draw = ImageDraw.Draw(background)

                # Draw Division Header & Column Labels
                draw.text((center_x, 15), div_name, font=font, fill=0, anchor="mm")
                draw.text((250, 45), "W-L", font=font, fill=0, anchor="mm")
                draw.text((450, 45), "PCT", font=font, fill=0, anchor="mm")
                draw.text((650, 45), "GB", font=font, fill=0, anchor="mm")

                # Loop through division teams
                for i, team in enumerate(division.get('teams', [])):
                    # Get Team ID directly from response (avoids slow API lookup calls)
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

                    # Extract stats
                    wins = team.get('w', team.get('wins', 0))
                    losses = team.get('l', team.get('losses', 0))
                    gb = team.get('gb', team.get('gamesBack', '-'))
                    pct = wins / (wins + losses) if (wins + losses) > 0 else 0

                    height_offset = i * 80 + 100
                    draw.text((250, height_offset), f"{wins}-{losses}", font=font, fill=0, anchor="mm")
                    draw.text((450, height_offset), f"{pct:.3f}", font=font, fill=0, anchor="mm")
                    draw.text((650, height_offset), f"{gb}", font=font, fill=0, anchor="mm")

                # Clean division name and save PNG image to disk
                safe_div_name = div_name.replace(" ", "_").lower()
                file_path = os.path.join(save_dir, f"{safe_div_name}_standings.png")
                background.save(file_path)
                logging.info(f"Saved: {file_path}")

                # Send buffer directly to e-Paper display
                logging.info(f"Rendering {div_name} on display...")
                epd.init()
                epd.display(epd.getbuffer(background))
                epd.sleep()

                # Pause execution until user presses Enter
                input("Press Enter to continue to next division...")

    except IOError as e:
        logging.error(f"Hardware/SPI error: {e}")

    except KeyboardInterrupt:
        logging.info("Script stopped by user.")
        epd7in5_V2.epdconfig.module_exit()
        sys.exit()


if __name__ == "__main__":
    make_image_files()