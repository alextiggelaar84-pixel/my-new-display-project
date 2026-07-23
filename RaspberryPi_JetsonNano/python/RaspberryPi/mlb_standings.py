import os
import sys
import logging
from tkinter import font

# Set up local library path just like the original script
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

class epd:
    width = 800
    height = 480

try:
    logging.info("Initializing 7.5in V2 Display...")
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()

    # Create a blank white canvas matching the display's dimensions
    # 255 represents white in a 1-bit pixel mode ('1')
    background = Image.new('1', (epd.width, epd.height), 255)
    teamlogo = Image.open( "C:\\git\\real_eink\\MLB Logos\\143.png")
    teamlogo = teamlogo.resize((240, 240))
    draw = draw = ImageDraw.Draw(background)
    text = "American League East"


    # Calculate exact middle coordinates for the text bounding box
    # 'anchor="mm"' tells PIL to center the text exactly on these coordinates
    center_x = epd.width // 2
    center_y = epd.height // 2

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        print("Using DejaVuSans-Bold font at size 30")
    except IOError:
        logging.warning("DejaVu font not found, falling back to default.")
        font = ImageFont.load_default()
        print("Using Default font")

    for i in range(5):
        teamlogo = Image.open( "C:\\git\\real_eink\\MLB Logos\\143.png")
        teamlogo = teamlogo.resize((75, 75))
        logging.info(f"Pasting team logo iteration...")
        height_offset = i*85 +60
        background.paste(teamlogo, (40,height_offset))

    draw.text((center_x, 15), text, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
    draw.text((250,40), "W-L", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
    draw.text((450,40), "PCT", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
    draw.text((650,40), "GB", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30), fill=0, anchor="mm")
    # Send the canvas buffer to the screen hardware
    logging.info("Updating display...")
    epd.display(epd.getbuffer(background))

    # Crucial step: put the display hardware to sleep to save power and prevent burn-in
    logging.info("Putting display to deep sleep...")
    epd.sleep()
    background.show()


except IOError as e:
    logging.error(f"Hardware/SPI error: {e}")

except KeyboardInterrupt:    
    logging.info("Script stopped by user.")
    epd7in5_V2.epdconfig.module_exit()
    exit()
