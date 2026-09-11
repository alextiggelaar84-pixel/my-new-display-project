import os
import sys
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
    OUTPUT_DIR = os.path.expanduser("~/testrepo/e-Paper/standings")
else:
    OUTPUT_DIR = r"C:\Users\sherr\Documents\git\real_eink\standings"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_logo_dir():
    pi_logo_path = os.path.expanduser("~/testrepo/e-Paper/MLB Logos")
    if os.path.exists(pi_logo_path):
        return pi_logo_path

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

    return pi_logo_path

LOGO_DIR = get_logo_dir()


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


def paste_logo(image, team_id, position, size=(120, 120)):
    if not team_id:
        return
    logo_path = os.path.join(LOGO_DIR, f"{int(team_id)}.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert('RGBA')
            logo = logo.resize(size, Image.Resampling.LANCZOS)
            
            bg = Image.new('RGBA', size, (255, 255, 255, 255))
            bg.paste(logo, (0, 0), logo)
            
            gray = bg.convert('L')
            bw = gray.point(lambda p: 0 if p < 200 else 255, mode='1')
            
            image.paste(bw, position)
        except Exception as e:
            logging.error(f"Error processing logo {logo_path}: {e}")


# ==========================================
# RENDERERS (PREGAME & POSTGAME ONLY)
# ==========================================

def render_pregame(game, team_id):
    """Renders upcoming game details, game time, and probable pitchers."""
    image = create_blank_canvas()
    draw = ImageDraw.Draw(image)

    home_id = game.get('home_id')
    away_id = game.get('away_id')
    is_home = (team_id == home_id)
    
    opp_id = away_id if is_home else home_id
    opp_name = game.get('away_name') if is_home else game.get('home_name')

    raw_datetime = game.get('game_datetime', '')
    if raw_datetime:
        try:
            game_date_utc = datetime.fromisoformat(raw_datetime.replace('Z', '+00:00'))
            if game_date_utc.tzinfo is None:
                game_date_utc = game_date_utc.replace(tzinfo=timezone.utc)
            local_game_time = game_date_utc.astimezone(LOCAL_TZ)
            time_str = local_game_time.strftime("%I:%M %p")
        except Exception:
            time_str = "TBD"
    else:
        time_str = "TBD"

    draw.text((400, 30), "UPCOMING GAME", font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((400, 70), f"Game Time: {time_str}", font=FONT_LARGE, fill=0, anchor="mm")
    draw.line([(50, 95), (750, 95)], fill=0, width=2)

    paste_logo(image, team_id, (150, 120))
    paste_logo(image, opp_id, (530, 120))
    
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


def render_postgame(game):
    """Renders final game card with team logos and final scores."""
    image = create_blank_canvas()
    draw = ImageDraw.Draw(image)

    home_id = game.get('home_id')
    away_id = game.get('away_id')
    home_score = game.get('home_score', 0)
    away_score = game.get('away_score', 0)

    draw.text((400, 30), "FINAL SCORE", font=FONT_TITLE, fill=0, anchor="mm")
    draw.line([(50, 70), (750, 70)], fill=0, width=2)

    paste_logo(image, away_id, (150, 100))
    paste_logo(image, home_id, (530, 100))

    draw.text((210, 240), game.get('away_name', ''), font=FONT_MEDIUM, fill=0, anchor="mm")
    draw.text((590, 240), game.get('home_name', ''), font=FONT_MEDIUM, fill=0, anchor="mm")

    # Display Final Scores
    draw.text((210, 310), str(away_score), font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((400, 310), "-", font=FONT_TITLE, fill=0, anchor="mm")
    draw.text((590, 310), str(home_score), font=FONT_TITLE, fill=0, anchor="mm")

    return image


# ==========================================
# MAIN EXECUTION
# ==========================================

def generate_game_image():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        team_id = get_team_id(TARGET_TEAM_NAME)
        today = datetime.now().strftime('%Y-%m-%d')
        schedule = statsapi.schedule(team=team_id, start_date=today, end_date=today)

        if not schedule:
            logging.info(f"No game scheduled today for {TARGET_TEAM_NAME}.")
            return None

        game = schedule[0]
        status = game.get('status', '').lower()
        logging.info(f"Game status found: '{status}'")

        if 'final' in status or 'completed' in status:
            img = render_postgame(game)
        else:
            # Handles 'scheduled', 'pre-game', or any non-final state as pregame
            img = render_pregame(game, team_id)

        output_path = os.path.join(OUTPUT_DIR, "00_dodgers_game_info.png")
        img.save(output_path)
        logging.info(f"Saved game image to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Error generating game image: {e}")
        return None


if __name__ == "__main__":
    saved_file = generate_game_image()
    
    # Fallback mock pregame render when no game exists today
    if not saved_file:
        logging.info("No game card created. Rendering mock pregame card...")
        mock_game = {
            'home_id': 119,  # Dodgers
            'away_id': 147,  # Yankees
            'home_name': 'Los Angeles Dodgers',
            'away_name': 'New York Yankees',
            'game_datetime': '2026-07-30T23:00:00Z',
            'home_probable_pitcher': 'Yamamoto',
            'away_probable_pitcher': 'Cole'
        }
        test_img = render_pregame(mock_game, 119)
        test_path = os.path.join(OUTPUT_DIR, "00_dodgers_game_info.png")
        test_img.save(test_path)
        logging.info(f"Mock image saved to {test_path}")