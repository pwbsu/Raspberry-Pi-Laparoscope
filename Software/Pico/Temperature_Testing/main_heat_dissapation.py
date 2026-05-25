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
INTERVAL_MINUTES = 10        # How often to take a reading
SAMPLES_PER_READING = 10     # Number of samples to average each time
TOTAL_HOURS = 2              # How long to run the test in hours
TEMP_LIMIT = 50.0            # Maximum safe temperature in °C
# ============================================================

INTERVAL_SECONDS = INTERVAL_MINUTES * 60
TOTAL_READINGS = (TOTAL_HOURS * 60) // INTERVAL_MINUTES

def blink_led(times=3, on_ms=200, off_ms=200):
    """Blink the LED a number of times"""
    for _ in range(times):
        led.on()
        time.sleep_ms(on_ms)
        led.off()
        time.sleep_ms(off_ms)

def alarm_blink():
    """
    Rapidly blink LED continuously to indicate
    temperature alarm — runs for 10 seconds
    """
    alarm_start = time.time()
    while time.time() - alarm_start < 10:
        led.on()
        time.sleep_ms(100)
        led.off()
        time.sleep_ms(100)

def check_temp_alarm(temp, sensor_number):
    """
    Check if temperature exceeds limit.
    Prints error and triggers alarm if it does.
    Returns True if alarm triggered, False if safe.
    """
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

def led_heartbeat():
    """
    Blink LED every minute during the waiting period
    to show the Pico is still running
    """
    wait_minutes = INTERVAL_MINUTES - (SAMPLES_PER_READING // 60)
    for minute in range(wait_minutes):
        time.sleep(60)
        blink_led(times=1, on_ms=500, off_ms=200)
        print('  [Heartbeat] Still running... {} minutes until next reading'.format(
            wait_minutes - minute - 1
        ))

if not roms:
    print('ERROR: No sensors found! Check your wiring.')
else:
    print('=' * 50)
    print('HEAT DISSIPATION MONITOR')
    print('=' * 50)
    print('Interval:        Every {} minutes'.format(INTERVAL_MINUTES))
    print('Total duration:  {} hours'.format(TOTAL_HOURS))
    print('Total readings:  {}'.format(TOTAL_READINGS))
    print('Temperature limit: {:.1f}°C'.format(TEMP_LIMIT))
    print('=' * 50)
    print('Time(min) | Avg Temp | Min Temp | Max Temp | Change')
    print('-' * 50)

    all_averages = []
    alarm_count = 0
    reading_number = 1
    test_start = time.time()

    # Blink 3 times at startup to confirm everything is working
    blink_led(times=3)

    while reading_number <= TOTAL_READINGS:
        # Take multiple samples and average them
        samples = []
        for _ in range(SAMPLES_PER_READING):
            ds.convert_temp()
            time.sleep_ms(1000)
            temp = ds.read_temp(roms[0])
            samples.append(temp)

            # Check EVERY individual sample against limit
            # This catches spikes between averaged readings
            if temp > TEMP_LIMIT:
                check_temp_alarm(temp, 1)
                alarm_count += 1

        avg_temp = sum(samples) / len(samples)
        min_temp = min(samples)
        max_temp = max(samples)
        elapsed_minutes = (time.time() - test_start) // 60

        # Calculate temperature change from first reading
        if len(all_averages) == 0:
            change = 0.0
        else:
            change = avg_temp - all_averages[0]

        all_averages.append(avg_temp)

        # Blink LED 3 times when a reading is taken
        blink_led(times=3)

        # Only print the reading if temperature is within safe range
        if avg_temp <= TEMP_LIMIT:
            print('{:>9} | {:>8.2f} | {:>8.2f} | {:>8.2f} | {:>+.2f}°C'.format(
                int(elapsed_minutes),
                avg_temp,
                min_temp,
                max_temp,
                change
            ))
        else:
            # Temperature exceeded limit — print warning line instead
            print('{:>9} | {:>8.2f} | {:>8.2f} | {:>8.2f} | {:>+.2f}°C  ⚠ ABOVE LIMIT!'.format(
                int(elapsed_minutes),
                avg_temp,
                min_temp,
                max_temp,
                change
            ))

        reading_number += 1

        # Wait for next interval with heartbeat blinks every minute
        if reading_number <= TOTAL_READINGS:
            led_heartbeat()

    # Final summary report
    print('=' * 50)
    print('FINAL HEAT DISSIPATION REPORT')
    print('=' * 50)
    print('Starting temperature:  {:.2f}°C'.format(all_averages[0]))
    print('Ending temperature:    {:.2f}°C'.format(all_averages[-1]))
    print('Total change:          {:.2f}°C'.format(all_averages[-1] - all_averages[0]))
    print('Maximum temperature:   {:.2f}°C'.format(max(all_averages)))
    print('Minimum temperature:   {:.2f}°C'.format(min(all_averages)))
    print('Total alarms triggered: {}'.format(alarm_count))
    if alarm_count > 0:
        print('WARNING: Temperature limit was exceeded {} time(s)!'.format(alarm_count))
    print('=' * 50)
    print('All averages:')
    for i, avg in enumerate(all_averages):
        # Add warning marker next to readings that exceeded limit
        marker = ' ⚠ ABOVE LIMIT' if avg > TEMP_LIMIT else ''
        print('  Reading {} ({} min): {:.2f}°C{}'.format(
            i + 1,
            i * INTERVAL_MINUTES,
            avg,
            marker
        ))

    # Blink rapidly 5 times to signal test is complete
    blink_led(times=5, on_ms=100, off_ms=100)
    print('Test complete!')