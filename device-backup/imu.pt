from machine import I2C, Pin

# I2C pin definition
I2C_SDA = 6
I2C_SDL = 7

class QMI8658(object):
    def __init__(self, address=0X6B):
        self._address = address
        self._bus = I2C(id=1, scl=Pin(I2C_SDL), sda=Pin(I2C_SDA), freq=100_000)
        bRet = self.who_am_i()
        if bRet:
            self.read_revision()
        else:
            return None
        self.config_apply()

    def _read_byte(self, cmd):
        rec = self._bus.readfrom_mem(int(self._address), int(cmd), 1)
        return rec[0]
        
    def _read_block(self, reg, length=1):
        rec = self._bus.readfrom_mem(int(self._address), int(reg), length)
        return rec
        
    def _read_u16(self, cmd):
        lsb = self._bus.readfrom_mem(int(self._address), int(cmd), 1)
        msb = self._bus.readfrom_mem(int(self._address), int(cmd)+1, 1)
        return (msb[0] << 8) + lsb[0]
        
    def _write_byte(self, cmd, val):
        self._bus.writeto_mem(int(self._address), int(cmd), bytes([int(val)]))

    def who_am_i(self):
        if 0x05 == self._read_byte(0x00):
            return True
        return False
        
    def read_revision(self):
        return self._read_byte(0x01)
        
    def config_apply(self):
        self._write_byte(0x02, 0x60)
        self._write_byte(0x03, 0x23)
        self._write_byte(0x04, 0x53)
        self._write_byte(0x05, 0x00)
        self._write_byte(0x06, 0x11)
        self._write_byte(0x07, 0x00)
        self._write_byte(0x08, 0x03)

    def read_raw_xyz(self):
        xyz = [0, 0, 0, 0, 0, 0]
        raw_timestamp = self._read_block(0x30, 3)
        raw_xyz = self._read_block(0x35, 12)
        for i in range(6):
            xyz[i] = (raw_xyz[(i*2)+1] << 8) | raw_xyz[i*2]
            if xyz[i] >= 32767:
                xyz[i] = xyz[i] - 65535
        return xyz
        
    def read_xyz(self):
        xyz = [0, 0, 0, 0, 0, 0]
        raw_xyz = self.read_raw_xyz()
        acc_lsb_div = (1 << 12)
        gyro_lsb_div = 64
        for i in range(3):
            xyz[i] = raw_xyz[i] / acc_lsb_div
            xyz[i+3] = raw_xyz[i+3] * 1.0 / gyro_lsb_div
        return xyz