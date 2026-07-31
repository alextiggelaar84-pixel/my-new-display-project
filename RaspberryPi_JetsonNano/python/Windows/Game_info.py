import os
import sys
import time
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import statsapi
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
TARGET_TEAM_NAME = "Los Angeles Dodgers"
LOCAL_TIMEZONE_NAME = "America/Chicago"  # Adjust timezone if needed
LOCAL_TZ = ZoneInfo(LOCAL_TIMEZONE_NAME)

EPD_WIDTH = 800
EPD_HEIGHT = 480

if sys.platform.startswith("linux"):
    # Path when running on Raspberry Pi
    OUTPUT_DIR = os.path.expanduser("~/testrepo/e-Paper/standings")
else:
    # Path when running on Windows
    OUTPUT_DIR = r"C:\git\real_eink\RaspberryPi_JetsonNano\python\Windows\standings"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_logo_dir():
    """Dynamically locates the MLB Logos directory on both Raspberry Pi and Windows."""
    
    # 1. Primary path for your Raspberry Pi setup (~/testrepo/e-Paper/MLB Logos)
    pi_logo_path = os.path.expanduser("~/testrepo/e-Paper/MLB Logos")
    if os.path.exists(pi_logo_path):
        return pi_logo_path

    # 2. Fallback check relative to the git project structure
    current_path = os.path.abspath(__file__)
    parts = current_path.split(os.sep)
    
    git_idx = -1
    for i, part in enumerate(parts):
        if part.lower() == 'git':
            git_idx = i
            break
            
    if git_idx != -1:
        base_git = os.sep.join(parts[:git_idx + 1])
        for folder_name in ["real_eink", "real eink"]:
            candidate = os.path.join(base_git, folder_name, "MLB Logos")
            if os.path.exists(candidate):
                return candidate
                
    # 3. Local directory fallback
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for relative_path in [
        os.path.join(script_dir, "..", "..", "MLB Logos"),
        os.path.join(script_dir, "..", "MLB Logos"),
        os.path.join(script_dir, "MLB Logos"),
        r"C:\git\real_eink\MLB Logos"
    ]:
        resolved = os.path.abspath(relative_path)
        if os.path.exists(resolved):
            return resolved

    return pi_logo_path  # Default to expanded Pi path if all else fails

def load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except IOError:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()

FONT_TITLE = load_font(32)
FONT_LARGE = load_font(28)
FONT_MEDIUM = load_font(20)
FONT_SMALL = load_font(16)

def get_team_id(team_name_str):
    teams = statsapi.lookup_team(team_name_str)
    if not teams:
        raise ValueError(f"Could not find MLB team: '{team_name_str}'")
    return teams[0]['id']

def create_blank_canvas():
    return Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 255)

def paste_logo(image, team_id, position, size=(100, 100)):
    if not team_id:
        return
    logo_path = os.path.join(LOGO_DIR, f"{team_id}.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            if logo.mode in ('RGBA', 'LA') or (logo.mode == 'P' and 'transparency' in logo.info):
                alpha = logo.convert('RGBA').split()[-1]
                background = Image.new('RGBA', logo.size, (255, 255, 255, 255))
                background.paste(logo, mask=alpha)
                logo = background.convert('RGB')
            else:
                logo = logo.convert('RGB')

            logo = logo.resize(size, Image.Resampling.LANCZOS)
            logo_1bit = logo.convert('1')
            image.paste(logo_1bit, position)
        except Exception as e:
            logging.error(f"Error processing logo {logo_path}: {e}")

def render_pregame(game, team_id):
    image = create_blank_canvas()
    draw = ImageDraw.Draw(image)

    home_id = game.get('home_id')
    away_id = game.get('away_id')
    is_home = (team_id == home_id)
    
    opp_id = away_id if is_home else home_id
    opp_name = game.get('away_name') if is_home else game.get('home_name')

    raw_datetime = game.get('game_datetime', '')
    if raw_datetime:
        game_date_utc = datetime.fromisoformat(raw_datetime.replace('Z', '+00:00'))
        if game_date_utc.tzinfo is None:
            game_date_utc = game_date_utc.replace(tzinfo=timezone.utc)
        local_game_time = game_date_utc.astimezone(LOCAL_TZ)
        time_str = local_game_time.strftime("%I:%M %p")
    else:
        time_str = "TBD"

    draw.text((400, 30), "UPCOMING GAME", font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((400, 70), f"Game Time: {time_str}", font=FONT_LARGE, fill=0, anchor="mm")
    draw.line([(50, 95), (750, 95)], fill=0, width=2)

    paste_logo(image, team_id, (150, 120), size=(120, 120))
    paste_logo(image, opp_id, (530, 120), size=(120, 120))
    
    draw.text((400, 180), "VS", font=FONT_TITLE, fill=0, anchor="mm")
    
    home_pitcher = game.get('home_probable_pitcher', 'TBD')
    away_pitcher = game.get('away_probable_pitcher', 'TBD')
    
    target_pitcher = home_pitcher if is_home else away_pitcher
    opp_pitcher = away_pitcher if is_home else home_pitcher

    draw.text((210, 260), TARGET_TEAM_NAME, font=FONT_MEDIUM, fill=0, anchor="mm")
    draw.text((210, 290), f"P: {target_pitcher}", font=FONT_SMALL, fill=0, anchor="mm")

    draw.text((590, 260), opp_name, font=FONT_MEDIUM, fill=0, anchor="mm")
    draw.text((590, 290), f"P: {opp_pitcher}", font=FONT_SMALL, fill=0, anchor="mm")

    return image

def render_live(game_id, team_id):
    image = create_blank_canvas()
    draw = ImageDraw.Draw(image)

    linescore = statsapi.linescore(game_id)
    live_data = statsapi.game_data(game_id)
    
    current_inning = linescore.split('\n')[0] if linescore else "LIVE"
    plays = live_data.get('liveData', {}).get('plays', {}).get('currentPlay', {})
    count = plays.get('count', {})
    
    balls = count.get('balls', 0)
    strikes = count.get('strikes', 0)
    outs = count.get('outs', 0)
    
    batter = plays.get('matchup', {}).get('batter', {}).get('fullName', 'N/A')
    pitcher = plays.get('matchup', {}).get('pitcher', {}).get('fullName', 'N/A')

    boxscore = statsapi.boxscore_data(game_id)
    home_team = boxscore.get('home', {}).get('team', {}).get('name', 'Home')
    away_team = boxscore.get('away', {}).get('team', {}).get('name', 'Away')
    
    draw.text((400, 30), f"LIVE - {current_inning}", font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((150, 100), away_team, font=FONT_MEDIUM, fill=0, anchor="mm")
    draw.text((650, 100), home_team, font=FONT_MEDIUM, fill=0, anchor="mm")

    draw.rectangle([(250, 150), (550, 310)], outline=0, width=2)
    draw.text((400, 180), f"Count: {balls} - {strikes}", font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((400, 225), f"Outs: {outs}", font=FONT_LARGE, fill=0, anchor="mm")

    draw.text((400, 350), f"At Bat: {batter}", font=FONT_MEDIUM, fill=0, anchor="mm")
    draw.text((400, 390), f"Pitching: {pitcher}", font=FONT_MEDIUM, fill=0, anchor="mm")

    return image

def render_postgame(game, game_id, team_id):
    image = create_blank_canvas()
    draw = ImageDraw.Draw(image)

    home_name = game.get('home_name')
    away_name = game.get('away_name')
    home_score = game.get('home_score')
    away_score = game.get('away_score')

    winning_pitcher = game.get('winning_pitcher', 'N/A')
    losing_pitcher = game.get('losing_pitcher', 'N/A')
    save_pitcher = game.get('save_pitcher', None)

    draw.text((400, 40), "FINAL SCORE", font=FONT_TITLE, fill=0, anchor="mm")
    draw.line([(50, 75), (750, 75)], fill=0, width=2)

    paste_logo(image, game.get('away_id'), (100, 100), size=(100, 100))
    paste_logo(image, game.get('home_id'), (600, 100), size=(100, 100))

    draw.text((230, 150), f"{away_name}", font=FONT_MEDIUM, fill=0, anchor="mm")
    draw.text((340, 150), f"{away_score}", font=FONT_TITLE, fill=0, anchor="mm")

    draw.text((460, 150), f"{home_score}", font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((570, 150), f"{home_name}", font=FONT_MEDIUM, fill=0, anchor="mm")

    draw.rectangle([(100, 250), (700, 420)], outline=0, width=2)
    draw.text((400, 280), "PITCHING SUMMARY", font=FONT_MEDIUM, fill=0, anchor="mm")
    
    draw.text((400, 320), f"Win:  {winning_pitcher}", font=FONT_SMALL, fill=0, anchor="mm")
    draw.text((400, 355), f"Loss: {losing_pitcher}", font=FONT_SMALL, fill=0, anchor="mm")
    
    if save_pitcher:
        draw.text((400, 390), f"Save: {save_pitcher}", font=FONT_SMALL, fill=0, anchor="mm")

    return image

def generate_game_image():
    """Generates the appropriate game image (pregame/live/postgame) and saves to disk."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        team_id = get_team_id(TARGET_TEAM_NAME)
        today = datetime.now().strftime('%Y-%m-%d')
        schedule = statsapi.schedule(team=team_id, start_date=today, end_date=today)

        if not schedule:
            logging.info(f"No game today for {TARGET_TEAM_NAME}.")
            return None

        game = schedule[0]
        game_id = game['game_id']
        status = game.get('status', '')

        if status in ['In Progress', 'Manager Challenge']:
            img = render_live(game_id, team_id)
        elif status in ['Final', 'Completed Early', 'Game Over']:
            img = render_postgame(game, game_id, team_id)
        else:
            img = render_pregame(game, team_id)

        output_path = os.path.join(OUTPUT_DIR, "00_dodgers_game_info.png")
        img.save(output_path)
        logging.info(f"Saved game info image to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Error generating game info image: {e}")
        return None