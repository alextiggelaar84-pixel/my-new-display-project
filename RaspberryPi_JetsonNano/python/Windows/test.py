import os
import sys
import logging

# Set up local library path just like the original script
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

##from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

class epd:
    width = 800
    height = 480

try:
    logging.info("Initializing 7.5in V2 Display...")
    ##epd = epd7in5_V2.EPD()
    ##epd.init()
    ##epd.Clear()

    # Create a blank white canvas matching the display's dimensions
    # 255 represents white in a 1-bit pixel mode ('1')
    image = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(image)

    # Load a standard default system font
    # Note: load_default() doesn't allow changing size, but works out-of-the-box
    # Load a pre-installed system font and set it to a large, readable size (e.g., 40)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        print("Using DejaVuSans-Bold font at size 40")
    except IOError:
        logging.warning("DejaVu font not found, falling back to default.")
        font = ImageFont.load_default()
        print("Using Default font")
    text = "Hello World"

    # Calculate exact middle coordinates for the text bounding box
    # 'anchor="mm"' tells PIL to center the text exactly on these coordinates
    center_x = epd.width // 2
    center_y = epd.height // 2

    logging.info("Drawing text...")
    draw.text((center_x, center_y), text, font=font, fill=0, anchor="mm")

    # Send the canvas buffer to the screen hardware
    logging.info("Updating display...")
    ##epd.display(epd.getbuffer(image))

    # Crucial step: put the display hardware to sleep to save power and prevent burn-in
    logging.info("Putting display to deep sleep...")
    ##epd.sleep()
    image.show()

except IOError as e:
    logging.error(f"Hardware/SPI error: {e}")

except KeyboardInterrupt:    
    logging.info("Script stopped by user.")
    ##epd7in5_V2.epdconfig.module_exit()
    exit()
