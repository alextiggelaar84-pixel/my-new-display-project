import os
import sys
import logging
import statsapi
from PIL import Image, ImageDraw, ImageFont

# Define Windows paths
save_dir = r"~/testrepo/e-Paper/MLB Standings"
logo_dir = r"~/testrepo/e-Paper/MLB Logos"

os.makedirs(save_dir, exist_ok=True)

leagues = [103, 104]  # 103 for AL, 104 for NL

logging.basicConfig(level=logging.INFO)

# Dummy EPD dimensions for local testing
class MockEPD:
    width = 800
    height = 480

epd = MockEPD()

def make_image_files():
    center_x = epd.width // 2

    # Load Windows default font or PIL default
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    for league_id in leagues:
        try:
            standings = statsapi.standings_data(leagueId=league_id)
        except Exception as e:
            logging.error(f"Failed to fetch standings: {e}")
            continue
        
        for division_id, division in standings.items():
            div_name = division.get('div_name', 'Division')
            background = Image.new('1', (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(background)
            
            # Draw Headers
            draw.text((center_x, 15), div_name, font=font, fill=0, anchor="mm")
            draw.text((250, 45), "W-L", font=font, fill=0, anchor="mm")
            draw.text((450, 45), "PCT", font=font, fill=0, anchor="mm")
            draw.text((650, 45), "GB", font=font, fill=0, anchor="mm")
                        
            # Draw Teams
            for i, team in enumerate(division.get('teams', [])):
                # Get ID directly — no statsapi.lookup_team network call!
                team_id = team.get('team_id') or team.get('id')
                
                if team_id:
                    logo_path = os.path.expanduser(f"~/testrepo/e-Paper/MLB Logos/{team_id}.png")
                    if os.path.exists(logo_path):
                        try:
                            with Image.open(logo_path) as logo:
                                teamlogo = logo.resize((75, 75))
                                height_offset = i * 80 + 60
                                background.paste(teamlogo, (40, height_offset))
                        except Exception as err:
                            logging.error(f"Error loading logo {logo_path}: {err}")

                # Calculate stats safely
                wins = team.get('w', team.get('wins', 0))
                losses = team.get('l', team.get('losses', 0))
                gb = team.get('gb', team.get('gamesBack', '-'))
                
                if 'pct' in team:
                    try:
                        pct = float(team['pct'])
                    except ValueError:
                        pct = 0.0
                else:
                    pct = wins / (wins + losses) if (wins + losses) > 0 else 0.0

                height_offset = i * 80 + 100
                draw.text((250, height_offset), f"{wins}-{losses}", font=font, fill=0, anchor="mm")
                draw.text((450, height_offset), f"{pct:.3f}", font=font, fill=0, anchor="mm")
                draw.text((650, height_offset), f"{gb}", font=font, fill=0, anchor="mm")

            # Save & view
            safe_div_name = div_name.replace(" ", "_").lower()
            file_path = os.path.join(save_dir, f"{safe_div_name}_standings.png")
            epd.display(epd.getbuffer(background))
            logging.info("Putting display to deep sleep...")
            epd.sleep()
            background.save(file_path)
            logging.info(f"Saved: {file_path}")


            if sys.platform == "win32":
                os.startfile(file_path)

            input("Press Enter to continue to next division...")

if __name__ == "__main__":
    make_image_files()