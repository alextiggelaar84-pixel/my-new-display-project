import logging
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import statsapi

if sys.platform.startswith("linux"):
    save_dir = os.path.expanduser("~/testrepo/e-Paper/standings")
else:
    save_dir = r"C:\Users\sherr\Documents\git\real_eink\standings"

os.makedirs(save_dir, exist_ok=True)

leagues = [103, 104]  # 103 for AL, 104 for NL

logging.basicConfig(level=logging.INFO)


class epd:
    width = 800
    height = 480


def get_logo_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.expanduser("~/my-new-display-project/MLB Logos"),
        os.path.expanduser("~/testrepo/e-Paper/MLB Logos"),
        os.path.abspath(os.path.join(script_dir, "..", "MLB Logos")),
        os.path.abspath(os.path.join(script_dir, "MLB Logos")),
        r"C:\git\real_eink\MLB Logos",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


LOGO_DIR = get_logo_dir()


def load_font(size):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
        )
    except IOError:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()


def make_image_files():
    try:
        logging.info("Generating division standings images...")

        center_x = epd.width // 2
        font_header = load_font(30)
        font_data = load_font(24)

        for league_id in leagues:
            standings = statsapi.standings_data(leagueId=league_id)

            for division_id, division in standings.items():
                div_name = division.get("div_name", "Division")
                background = Image.new("1", (epd.width, epd.height), 255)
                draw = ImageDraw.Draw(background)

                # Draw Division Headers
                draw.text(
                    (center_x, 15),
                    div_name,
                    font=font_header,
                    fill=0,
                    anchor="mm",
                )
                draw.text(
                    (250, 45), "W-L", font=font_header, fill=0, anchor="mm"
                )
                draw.text(
                    (450, 45), "PCT", font=font_header, fill=0, anchor="mm"
                )
                draw.text(
                    (650, 45), "GB", font=font_header, fill=0, anchor="mm"
                )

                # Loop through division teams
                for i, team in enumerate(division.get("teams", [])):
                    team_id = team.get("team_id") or team.get("id")

                    if team_id:
                        logo_path = os.path.join(LOGO_DIR, f"{team_id}.png")

                        if os.path.exists(logo_path):
                            try:
                                logo = Image.open(logo_path).convert("RGBA")
                                logo = logo.resize(
                                    (75, 75), Image.Resampling.LANCZOS
                                )

                                bg = Image.new(
                                    "RGBA", (75, 75), (255, 255, 255, 255)
                                )
                                bg.paste(logo, (0, 0), logo)
                                bw_logo = bg.convert("L").point(
                                    lambda p: 0 if p < 200 else 255, mode="1"
                                )

                                height_offset = i * 80 + 60
                                background.paste(bw_logo, (40, height_offset))
                            except Exception as e:
                                logging.error(
                                    f"Error processing logo {logo_path}: {e}"
                                )

                    wins = team.get("w", 0)
                    losses = team.get("l", 0)
                    gb = team.get("gb", "-")
                    pct = (
                        wins / (wins + losses) if (wins + losses) > 0 else 0
                    )

                    height_offset = i * 80 + 100
                    draw.text(
                        (250, height_offset),
                        f"{wins}-{losses}",
                        font=font_data,
                        fill=0,
                        anchor="mm",
                    )
                    draw.text(
                        (450, height_offset),
                        f"{pct:.3f}",
                        font=font_data,
                        fill=0,
                        anchor="mm",
                    )
                    draw.text(
                        (650, height_offset),
                        f"{gb}",
                        font=font_data,
                        fill=0,
                        anchor="mm",
                    )

                safe_div_name = div_name.replace(" ", "_").lower()
                file_path = os.path.join(
                    save_dir, f"{safe_div_name}_standings.png"
                )

                background.save(file_path)
                logging.info(f"Saved standings image to {file_path}")

                if sys.platform.startswith("win32"):
                    os.startfile(file_path)

    except Exception as e:
        logging.error(f"Error generating standings: {e}")


if __name__ == "__main__":
    make_image_files()