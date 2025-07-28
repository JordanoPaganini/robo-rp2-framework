from machine import Pin, reset
from time import sleep_ms

BUTTON_PIN = 15

def handle_button_irq(pin):
    print("#CODE:100") # Código 100 - Representa o reset via botão
    reset()

button = Pin(BUTTON_PIN, Pin.IN)
Pin('LED', Pin.OUT).on()

while button.value() == 0:
    sleep_ms(50)
while button.value() == 1:
    sleep_ms(50)

sleep_ms(200)  # Debounce antes de iniciar

button.irq(trigger=Pin.IRQ_FALLING, handler=handle_button_irq)

# Roda o código principal (code.mpy)
import code