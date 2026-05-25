import machine
import onewire
import ds18x20
import time

dat = machine.Pin(15)
ow = onewire.OneWire(dat)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
print('Found sensors:', roms)

def get_average_temp(rom, samples=10):
    readings = []
    for _ in range(samples):
        ds.convert_temp()
        time.sleep_ms(1000)
        readings.append(ds.read_temp(rom))
    return sum(readings) / len(readings)

while True:
    for rom in roms:
        avg_temp = get_average_temp(rom)
        print('Average Temperature: {:.1f}°C'.format(avg_temp))
    time.sleep(2)