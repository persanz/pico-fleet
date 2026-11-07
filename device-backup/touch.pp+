from machine import I2C, Pin, Timer
import time

# Pin definition
SDA = 6
SCL = 7
INT = 15
RST = 16

class Touch_CST816T(object):
    def __init__(self, address=0x15, mode=0, i2c_num=1, i2c_sda=SDA, i2c_scl=SCL, int_pin=INT, rst_pin=RST, lcd=None):
        self._bus = I2C(id=i2c_num, scl=Pin(i2c_scl), sda=Pin(i2c_sda), freq=400_000)
        self._address = address
        self.int = Pin(int_pin, Pin.IN, Pin.PULL_UP)     
        self.tim = Timer()     
        self.rst = Pin(rst_pin, Pin.OUT)
        self.reset()
        
        bRet = self.who_am_i()
        if bRet:
            print("Success: Detected CST816T.")
            rev = self.read_revision()
            print("CST816T Revision = {}".format(rev))
            self.stop_sleep()
        else:
            print("Error: Not Detected CST816T.")
            return None
            
        self.mode = mode
        self.gestures = "None"
        self.flag = self.flgh = self.l = 0
        self.x_point = self.y_point = 0
        self.int.irq(handler=self.int_callback, trigger=Pin.IRQ_FALLING)
      
    def _read_byte(self, cmd):
        rec = self._bus.readfrom_mem(int(self._address), int(cmd), 1)
        return rec[0]
    
    def _read_block(self, reg, length=1):
        rec = self._bus.readfrom_mem(int(self._address), int(reg), length)
        return rec
    
    def _write_byte(self, cmd, val):
        self._bus.writeto_mem(int(self._address), int(cmd), bytes([int(val)]))

    def who_am_i(self):
        if 0xB6 != self._read_byte(0xA7):
            return False
        return True
    
    def read_revision(self):
        return self._read_byte(0xA9)
      
    def stop_sleep(self):
        self._write_byte(0xFE, 0x01)
    
    def reset(self):
        self.rst(0)
        time.sleep_ms(100)
        self.rst(1)
        time.sleep_ms(100)
    
    def set_mode(self, mode, callback_time=10, rest_time=5):
        if mode == 1:      # CST816S_Point_Mode
            self._write_byte(0xFA, 0X41)

        elif mode == 2:    # ALL Mode
            self._write_byte(0xFA, 0X71)
            
        else:              # CST816S_Gesture_Mode
            self._write_byte(0xFA, 0X11)
            self._write_byte(0xEE, 0X01)
            self._write_byte(0xED, 0X01)
            self._write_byte(0xEC, 0X01)
     
    def get_point(self):
        xy_point = self._read_block(0x03, 4)
        x_point = ((xy_point[0] & 0x0f) << 8) + xy_point[1]
        y_point = ((xy_point[2] & 0x0f) << 8) + xy_point[3]
        self.x_point = x_point
        self.y_point = y_point
        
    def int_callback(self, pin):
        if self.mode == 0:
            self.gestures = self._read_byte(0x01)
            if self.gestures == 0x0C:
                self.flag = 1
        elif self.mode == 1:           
            self.flag = 1
            self.get_point()
        else:
            self.gestures = self._read_byte(0x01)
            self.get_point()

    def timer_callback(self, t):
        self.l += 1
        if self.l > 100:
            self.l = 50
