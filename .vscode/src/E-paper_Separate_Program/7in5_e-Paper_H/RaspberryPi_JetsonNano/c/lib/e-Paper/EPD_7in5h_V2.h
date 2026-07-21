/*****************************************************************************
* | File      	:   EPD_7in5h.h
* | Author      :   Waveshare team
* | Function    :   7.5inch e-paper (G)
* | Info        :
*----------------
* |	This version:   V1.0
* | Date        :   2024-08-07
* | Info        :
* -----------------------------------------------------------------------------
******************************************************************************/
#ifndef __EPD_7IN5H_V2_H
#define __EPD_7IN5H_V2_H

#include "DEV_Config.h"

// Display resolution
#define EPD_7IN5H_V2_WIDTH       800
#define EPD_7IN5H_V2_HEIGHT      480

// Color
#define  EPD_7IN5H_V2_BLACK   0x0
#define  EPD_7IN5H_V2_WHITE   0x1
#define  EPD_7IN5H_V2_YELLOW  0x2
#define  EPD_7IN5H_V2_RED     0x3

void EPD_7IN5H_V2_Init(void);
void EPD_7IN5H_V2_Init_Fast(void);
void EPD_7IN5H_V2_Clear(UBYTE color);
void EPD_7IN5H_V2_Display(const UBYTE *Image);
void EPD_7IN5H_V2_Sleep(void);

#endif
