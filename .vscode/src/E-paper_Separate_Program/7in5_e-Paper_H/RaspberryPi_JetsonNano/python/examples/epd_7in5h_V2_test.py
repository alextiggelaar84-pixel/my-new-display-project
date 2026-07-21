#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pic")
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib")
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
import time
import traceback
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5h_V2


logging.basicConfig(level=logging.DEBUG)

try:
    logging.info("epd7in5h V2 Demo")

    epd = epd7in5h_V2.EPD()

    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    epd.sleep()
    time.sleep(2)

    # read bmp file
    logging.info("show BMP")
    epd.init_fast()
    Himage = Image.open(os.path.join(picdir, "7in5h.bmp"))
    epd.display(epd.getbuffer(Himage))
    epd.sleep()
    time.sleep(2)

    # Drawing on the image
    logging.info("Drawing on the image")
    epd.init()
    font12 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 12)
    font16 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 16)
    font24 = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), 24)

    Himage = Image.new("RGB", (epd.width, epd.height), epd.WHITE)# 255: clear the frame
    draw = ImageDraw.Draw(Himage)

    draw.point((10, 80), fill=epd.RED)
    draw.point((10, 90), fill=epd.YELLOW)
    draw.point((10, 100), fill=epd.BLACK)
    draw.line((20, 70, 70, 120), fill=epd.RED)
    draw.line((70, 70, 20, 120), fill=epd.RED)
    draw.rectangle((20, 70, 70, 120), outline=epd.YELLOW)
    draw.rectangle((80, 70, 130, 120), fill=epd.YELLOW)
    draw.ellipse((25, 75, 65, 115), outline=epd.BLACK)
    draw.ellipse((85, 75, 125, 115), fill=epd.BLACK)
    draw.line((85, 95, 125, 95), fill=epd.RED)
    draw.line((105, 75, 105, 115), fill=epd.YELLOW)
    draw.text((10, 0), "Red, yellow, white and black", font=font16, fill=epd.RED)
    draw.text((10, 20), "Four color e-Paper", font=font12, fill=epd.YELLOW)
    draw.text((150, 20), "Waveshare", font=font24, fill=epd.RED)
    draw.text((10, 35), "123456", font=font12, fill=epd.RED)

    logging.info("EPD_Display")
    epd.display(epd.getbuffer(Himage))
    epd.sleep()
    time.sleep(3)

    logging.info("Clear")
    epd.init()
    epd.Clear()

    logging.info("Goto Sleep")
    epd.sleep()

    logging.info("close 5V, Module enters 0 power consumption")
    epd.EPD_END()

except IOError as e:
    logging.info(e)
    logging.info(traceback.format_exc())

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5h_V2.epdconfig.module_exit(cleanup=True)
    exit()
