import machine
import onewire
import ds18x20
import time

# Setup
dat = machine.Pin(15)
ow = onewire.OneWire(dat)
ds = ds18x20.DS18X20(ow)
roms = ds.scan()

# LED Setup
led = machine.Pin("LED", machine.Pin.OUT)

# ============================================================
# SETTINGS — Adjust these as needed
INTERVAL_MINUTES = 5         # How often to take a reading
SAMPLES_PER_READING = 10     # Number of samples to average each time
TEMP_LIMIT = 85            # Maximum safe temperature in °C
# ============================================================

INTERVAL_SECONDS = INTERVAL_MINUTES * 60

def blink_led(times=3, on_ms=200, off_ms=200):
    """Blink the LED a number of times"""
    for _ in range(times):
        led.on()
        time.sleep_ms(on_ms)
        led.off()
        time.sleep_ms(off_ms)

def alarm_blink():
    """Rapidly blink LED to indicate temperature alarm"""
    alarm_start = time.time()
    while time.time() - alarm_start < 10:
        led.on()
        time.sleep_ms(100)
        led.off()
        time.sleep_ms(100)

def check_temp_alarm(temp, sensor_number):
    """Check if temperature exceeds limit and trigger alarm if needed"""
    if temp > TEMP_LIMIT:
        print('!' * 50)
        print('WARNING: TEMPERATURE LIMIT EXCEEDED!')
        print('  Sensor {}:      {:.2f}°C'.format(sensor_number, temp))
        print('  Limit:          {:.2f}°C'.format(TEMP_LIMIT))
        print('  Exceeded by:    {:.2f}°C'.format(temp - TEMP_LIMIT))
        print('!' * 50)
        alarm_blink()
        return True
    return False

def get_rom_str(rom):
    """Convert ROM bytearray to readable string"""
    return ''.join('{:02X}'.format(b) for b in rom)

def take_reading(reading_number, elapsed_minutes, all_readings):
    """Take a reading from all sensors and print results"""
    print('=' * 60)
    print('READING {} | Time elapsed: {} minutes'.format(
        reading_number, int(elapsed_minutes)))
    print('-' * 60)

    # Trigger conversion for ALL sensors simultaneously
    ds.convert_temp()
    time.sleep_ms(1500)

    # Collect samples for each sensor
    sensor_samples = {i: [] for i in range(len(roms))}

    for _ in range(SAMPLES_PER_READING):
        ds.convert_temp()
        time.sleep_ms(1500)
        for i, rom in enumerate(roms):
            temp = ds.read_temp(rom)
            sensor_samples[i].append(temp)

            # Check every sample against limit
            check_temp_alarm(temp, i + 1)

    # Calculate and print averages for each sensor
    for i, rom in enumerate(roms):
        samples = sensor_samples[i]
        avg_temp = sum(samples) / len(samples)
        min_temp = min(samples)
        max_temp = max(samples)

        # Store reading for final report
        all_readings[i].append(avg_temp)

        # Calculate change from first reading
        if len(all_readings[i]) > 1:
            change = avg_temp - all_readings[i][0]
            change_str = '{:+.2f}°C'.format(change)
        else:
            change_str = 'N/A (first reading)'

        # Print sensor report
        limit_warning = '  ⚠ ABOVE LIMIT!' if avg_temp > TEMP_LIMIT else ''
        print('  Sensor {} (ROM: {})'.format(i + 1, get_rom_str(rom)))
        print('    Average:  {:.2f}°C{}'.format(avg_temp, limit_warning))
        print('    Minimum:  {:.2f}°C'.format(min_temp))
        print('    Maximum:  {:.2f}°C'.format(max_temp))
        print('    Change:   {}'.format(change_str))
        print()

    # Blink LED 3 times to confirm reading was taken
    blink_led(times=3)

def print_final_report(all_readings, total_readings, test_start):
    """Print final summary report for all sensors"""
    total_time = (time.time() - test_start) // 60
    print('=' * 60)
    print('FINAL REPORT')
    print('=' * 60)
    print('Total readings taken:  {}'.format(total_readings))
    print('Total time elapsed:    {} minutes'.format(int(total_time)))
    print('-' * 60)

    for i, rom in enumerate(roms):
        readings = all_readings[i]
        if len(readings) > 0:
            print('Sensor {} (ROM: {}):'.format(i + 1, get_rom_str(rom)))
            print('  Starting temp:  {:.2f}°C'.format(readings[0]))
            print('  Ending temp:    {:.2f}°C'.format(readings[-1]))
            print('  Total change:   {:.2f}°C'.format(
                readings[-1] - readings[0]))
            print('  Maximum temp:   {:.2f}°C'.format(max(readings)))
            print('  Minimum temp:   {:.2f}°C'.format(min(readings)))
            print('  All averages:')
            for j, avg in enumerate(readings):
                marker = ' ⚠ ABOVE LIMIT' if avg > TEMP_LIMIT else ''
                print('    Reading {} ({} min): {:.2f}°C{}'.format(
                    j + 1,
                    j * INTERVAL_MINUTES,
                    avg,
                    marker
                ))
            print()

    print('=' * 60)
    print('Test complete!')
    blink_led(times=5, on_ms=100, off_ms=100)

def led_heartbeat(minutes_remaining):
    """Blink LED every minute during wait period"""
    for minute in range(minutes_remaining):
        time.sleep(60)
        blink_led(times=1, on_ms=500, off_ms=200)
        print('  [Heartbeat] Still running... {} minutes until next reading'.format(
            minutes_remaining - minute - 1
        ))

# ============================================================
# MAIN PROGRAM
# ============================================================

if not roms:
    print('ERROR: No sensors found! Check your wiring.')
else:
    num_sensors = len(roms)
    print('=' * 60)
    print('CONTINUOUS MULTI-PROBE TEMPERATURE MONITOR')
    print('=' * 60)
    print('Sensors found:     {}'.format(num_sensors))
    for i, rom in enumerate(roms):
        print('  Sensor {}: ROM = {}'.format(i + 1, get_rom_str(rom)))
    print('Interval:          Every {} minutes'.format(INTERVAL_MINUTES))
    print('Temperature limit: {:.1f}°C'.format(TEMP_LIMIT))
    print('To stop the test:  Press Ctrl+C')
    print('=' * 60)

    # Initialise storage for all sensor readings
    all_readings = {i: [] for i in range(num_sensors)}
    reading_number = 1
    test_start = time.time()

    # Blink 3 times at startup
    blink_led(times=3)

    # Run until user presses Ctrl+C
    try:
        while True:
            elapsed_minutes = (time.time() - test_start) // 60

            # Take reading from all sensors
            take_reading(reading_number, elapsed_minutes, all_readings)
            reading_number += 1

            # Wait for next interval with heartbeat
            print('  Next reading in {} minutes. Press Ctrl+C to stop.'.format(
                INTERVAL_MINUTES))
            led_heartbeat(INTERVAL_MINUTES - (SAMPLES_PER_READING // 60))

    except KeyboardInterrupt:
        # User pressed Ctrl+C — print final report
        print()
        print('Test stopped by user!')
        print_final_report(all_readings, reading_number - 1, test_start)