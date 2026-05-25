from machine import Pin
from time import sleep

led = Pin("LED", Pin.OUT)
n = 0

while True:
    led.toggle()
    sleep(1)
    led.toggle()
    sleep(1)
    print("{}".format(n))
    n = n+1
