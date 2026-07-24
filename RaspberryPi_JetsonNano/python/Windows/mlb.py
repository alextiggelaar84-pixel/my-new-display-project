import os
from pydoc import text
import sys
import logging
from tkinter import font
import statsapi
from PIL import Image, ImageDraw, ImageFont

# Define the target folder
save_dir = r"C:\git\real_eink\RaspberryPi_JetsonNano\python\Windows\standings"

# Ensure the target folder exists
os.makedirs(save_dir, exist_ok=True)

leagues = [103, 104]  # 103 for AL, 104 for NL

# Set up local library path
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

##from waveshare_epd import epd7in5_V2

logging.basicConfig(level=logging.INFO)

class epd:
    width = 800
    height = 480


def make_image_files():
    try:
        logging.info("Initializing 7.5in V2 Display...")
        ##epd = epd7in5_V2.EPD()
        ##epd.init()           
        ##epd.Clear()

        # Calculate middle coordinates for header
        center_x = epd.width // 2
        center_y = epd.height // 2

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
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
                
                # Draw Division Header
                draw.text((center_x, 15), div_name, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
                draw.text((250,45), "W-L", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
                draw.text((450,45), "PCT", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
                draw.text((650,45), "GB", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
                            
                # Loop through division teams
                for i, team in enumerate(division.get('teams', [])):
                    team_name = team.get('name')
                    
                    # Fetch team ID dynamically from team name
                    team_info = statsapi.lookup_team(team_name)
                    if team_info:
                        team_id = team_info[0]['id']
                        logo_path = f"C:\\git\\real_eink\\MLB Logos\\{team_id}.png"
                        
                        if os.path.exists(logo_path):
                            teamlogo = Image.open(logo_path).resize((75, 75))
                            height_offset = i * 80 + 60
                            background.paste(teamlogo, (40, height_offset))
                    
                    wins = team.get('w', 0)
                    losses = team.get('l', 0)
                    gb = team.get('gb', '-')
                    pct = wins / (wins + losses) if (wins + losses) > 0 else 0

                    height_offset = i * 80 + 100
                    draw.text((250, height_offset), f"{wins}-{losses}", font=font, fill=0, anchor="mm")
                    draw.text((450, height_offset), f"{pct:.3f}", font=font, fill=0, anchor="mm")
                    draw.text((650, height_offset), f"{gb}", font=font, fill=0, anchor="mm")

                # Clean division name and create full file path
                safe_div_name = div_name.replace(" ", "_").lower()
                file_path = os.path.join(save_dir, f"{safe_div_name}_standings.png")

                # Save the completed division image
                background.save(file_path)
                logging.info(f"Saved: {file_path}")

                # Automatically open image viewer on Windows
                os.startfile(file_path)

                input("Press Enter to continue to next division...")

    except IOError as e:
        logging.error(f"Hardware/SPI error: {e}")

    except KeyboardInterrupt:    
        logging.info("Script stopped by user.")
        sys.exit()

# CALL THE FUNCTION SO IT ACTUALLY RUNS
if __name__ == "__main__":
    make_image_files()