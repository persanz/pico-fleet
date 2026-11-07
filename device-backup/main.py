from machine import Pin, ADC
import time
import gc  # <-- Added for memory management
from lcd import LCD_1inch54
from touch import Touch_CST816T
from imu import QMI8658

Vbat_Pin = 29

def touch_hand_writing(lcd, touch):
    # Force complete garbage collection before starting drawing canvas
    gc.collect()
    
    x = y = data = 0
    color = 0
    touch.flgh = 0
    touch.flag = 0
    touch.mode = 1
    touch.set_mode(touch.mode)
    
    lcd.fill(lcd.white)
    lcd.rect(0, 0, 35, 208, lcd.red, True)
    lcd.rect(0, 0, 208, 35, lcd.green, True)
    lcd.rect(205, 0, 240, 240, lcd.blue, True)
    lcd.rect(0, 205, 240, 240, lcd.brown, True)
    lcd.show()
    
    touch.tim.init(period=1, callback=touch.timer_callback)
    
    try:
        while True:
            if touch.flgh == 0 and touch.x_point != 0:
                touch.flgh = 1
                x = touch.x_point
                y = touch.y_point
                
            if touch.flag == 1:
                if (touch.x_point > 34 and touch.x_point < 205) and (touch.y_point > 34 and touch.y_point < 205):
                    touch.flgh = 3
                else:
                    if (touch.x_point > 0 and touch.x_point < 33) and (touch.y_point > 0 and touch.y_point < 208):
                        color = lcd.red
                    if (touch.x_point > 0 and touch.x_point < 208) and (touch.y_point > 0 and touch.y_point < 33):
                        color = lcd.green
                    if (touch.x_point > 208 and touch.x_point < 240) and (touch.y_point > 0 and touch.y_point < 240):
                        color = lcd.blue
                    if (touch.x_point > 0 and touch.x_point < 240) and (touch.y_point > 208 and touch.y_point < 240):
                        lcd.fill(lcd.white)
                        lcd.rect(0, 0, 35, 208, lcd.red, True)
                        lcd.rect(0, 0, 208, 35, lcd.green, True)
                        lcd.rect(205, 0, 240, 240, lcd.blue, True)
                        lcd.rect(0, 205, 240, 240, lcd.brown, True)
                        lcd.show()
                    touch.flgh = 4
                    
                if touch.flgh == 3:
                    time.sleep(0.001)
                    if touch.l < 25:           
                        touch.flag = 0
                        lcd.line(x, y, touch.x_point, touch.y_point, color)
                        lcd.windows_show(x,y,touch.x_point,touch.y_point)
                        touch.l=0
                    else:
                        touch.flag = 0
                        lcd.pixel(touch.x_point, touch.y_point, color)
                        lcd.windows_show(x, y, touch.x_point, touch.y_point)
                        touch.l = 0
                        
                    x = touch.x_point
                    y = touch.y_point
    except KeyboardInterrupt:
        pass

def touch_gesture(lcd, touch):
    gc.collect()
    touch.mode = 0
    touch.set_mode(touch.mode)
    lcd.fill(lcd.white)
    lcd.write_text('Gesture test', 70, 90, 1, lcd.black)
    lcd.write_text('Complete as prompted', 35, 120, 1, lcd.black)
    lcd.show()
    time.sleep(1)
    lcd.fill(lcd.white)
    
    while touch.gestures != 0x01:
        gc.collect()  # Clean font arrays
        lcd.fill(lcd.white)
        lcd.write_text('UP', 100, 110, 3, lcd.black)
        lcd.show()
        time.sleep(0.1)
    
    while touch.gestures != 0x02:
        gc.collect()
        lcd.fill(lcd.white)
        lcd.write_text('DOWN', 70, 110, 3, lcd.black)
        lcd.show()
        time.sleep(0.1)
    
    while touch.gestures != 0x03:
        gc.collect()
        lcd.fill(lcd.white)
        lcd.write_text('LEFT', 70, 110, 3, lcd.black)
        lcd.show()
        time.sleep(0.1)
    
    while touch.gestures != 0x04:
        gc.collect()
        lcd.fill(lcd.white)
        lcd.write_text('RIGHT', 60, 110, 3, lcd.black)
        lcd.show()
        time.sleep(0.1)
    
    while touch.gestures != 0x0C:
        gc.collect()
        lcd.fill(lcd.white)
        lcd.write_text('Long Press', 40, 110, 2, lcd.black)
        lcd.show()
        time.sleep(0.1)
    
    while touch.gestures != 0x0B:
        gc.collect()
        lcd.fill(lcd.white)
        lcd.write_text('Double Click', 25, 110, 2, lcd.black)
        lcd.show()
        time.sleep(0.1)

def dof_read(lcd, touch):
    qmi8658 = QMI8658()
    vbat = ADC(Pin(Vbat_Pin))   
    touch.mode = 0
    touch.set_mode(touch.mode)

    while True:
        # CRITICAL: Force clear old string objects out of RAM on every frame
        gc.collect() 
        
        xyz = qmi8658.read_xyz()
        
        lcd.fill(lcd.white)
        lcd.fill_rect(0, 0, 240, 40, lcd.red)
        lcd.text("Waveshare", 80, 25, lcd.white)
        
        lcd.fill_rect(0, 40, 240, 40, lcd.blue)
        # Using native, lower-level lcd.text instead of heavy write_text when possible cuts down RAM allocations
        lcd.text("Long Press to Quit", 45, 55, lcd.white)
        
        lcd.fill_rect(0, 80, 120, 120, 0x1805)
        lcd.text("ACC_X={:+.2f}".format(xyz[0]), 20, 97, lcd.white)
        lcd.text("ACC_Y={:+.2f}".format(xyz[1]), 20, 137, lcd.white)
        lcd.text("ACC_Z={:+.2f}".format(xyz[2]), 20, 177, lcd.white)

        lcd.fill_rect(120, 80, 120, 120, 0xF073)
        lcd.text("GYR_X={:+3.2f}".format(xyz[3]), 135, 105, lcd.white)
        lcd.text("GYR_Y={:+3.2f}".format(xyz[4]), 130, 145, lcd.white)
        lcd.text("GYR_Z={:+3.2f}".format(xyz[5]), 127, 185, lcd.white)
        
        lcd.fill_rect(0, 200, 240, 40, 0x180f)
        reading = vbat.read_u16() * 3.3 / 65535 * 3
        lcd.text("Vbat={:.2f}".format(reading), 80, 215, lcd.white)
        
        lcd.show()
        time.sleep(0.1)
        if touch.flag == 1:
            break

if __name__ == '__main__':
    # Flush RAM completely before allocating the huge LCD buffer
    gc.collect()
    
    lcd = LCD_1inch54()
    lcd.fill(lcd.white)
    lcd.show()
    
    touch = Touch_CST816T(mode=2, lcd=lcd)

    dof_read(lcd, touch)
    touch_gesture(lcd, touch)
    touch_hand_writing(lcd, touch)