from machine import Pin, ADC, PWM


class DigitalIn:
    def __init__(self, pin: int, Pull_type: bool|str = 0):
        Pull_type = str(Pull_type).upper()
        if Pull_type in ["TRUE", "HIGH", "PULL_UP"]:
            self.Pull_type = True 
            self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        elif Pull_type in ["FALSE", "LOW", "PULL_DOWN"]:
            self.pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
            self.Pull_type = False 
        else:
            raise ValueError("Erro ao criar Botão: Pull_type não identificado")

    @property
    def value(self):
        return self.pin.value()
    
    def is_pressed(self):
        if self.Pull_type:
            return not self.value
        else:
            return self.value
        
    def set_irq(self, trigger: str, func):
        trigger = trigger.upper()
        
        if trigger == "HIGH":
            self.pin.irq(trigger=Pin.IRQ_HIGH_LEVEL, handler=func)
        elif trigger == "LOW":
            self.pin.irq(trigger=Pin.IRQ_LOW_LEVEL, handler=func)
        elif trigger == "FALLING":
            self.pin.irq(trigger=Pin.IRQ_FALLING, handler=func)
        elif trigger == "RISING":
            self.pin.irq(trigger=Pin.IRQ_RISING, handler=func)
        else:
            raise TypeError("trigger especificado não encontrado")
    


class AnalogIn:
    def __init__(self, pin: int):
        self.pin = ADC(Pin(pin))
        
    @property
    def value(self):
        return self.pin.read_u16()
    
    @property
    def percentage(self):
        return (self.value/65535) * 100
    
    @property
    def voltage(self):
        return(self.value/65535) * 3.3

class DigitalOut:
    def __init__(self, pin: int):
        self.pin = Pin(pin, Pin.OUT)
        
    def on(self):
        self.pin.on()
        
    def off(self):
        self.pin.off()

    
class AnalogOut:
    def __init__(self, pin: int, frequency: int = 50, duty: int = 0):
        self.pin = PWM(Pin(pin), freq=frequency, duty_u16=duty)
    
    def set_duty_percentage(self, value: int):
        self.pin.duty_u16(int((value/100)*65535))
        
    def set_voltage(self, value: int):
        self.pin.duty_u16(int((value/3.3)*65535))
    
    def set_duty(self, value: int):
        self.pin.duty_u16(value)

class RgbLed:
    def __init__(self, pinR: int, pinG: int, pinB: int, freq: int = 1000):
        self.pinR = AnalogOut(pinR, frequency=freq)
        self.pinG = AnalogOut(pinG, frequency=freq)
        self.pinB = AnalogOut(pinB, frequency=freq)
    
    def set_duty_percentage(self, value: int):
        self.pinR.set_duty(int((value/100)*65535))
        self.pinG.set_duty(int((value/100)*65535))
        self.pinB.set_duty(int((value/100)*65535))
        
    def set_voltage(self, value: int):
        self.pinR.set_duty(int((value/3.3)*65535))
        self.pinG.set_duty(int((value/3.3)*65535))
        self.pinB.set_duty(int((value/3.3)*65535))
    
    def set_duty(self, value: int):
        self.pinR.set_duty(value)
        self.pinG.set_duty(value)
        self.pinB.set_duty(value)
    
    def set_RGB(self, value: int):
        
        r = (value >> 16) & 0xFF
        g = (value >> 8) & 0xFF
        b = value & 0xFF
        
        self.pinR.set_duty(int((r / 255) * 65535))
        self.pinG.set_duty(int((g / 255) * 65535))
        self.pinB.set_duty(int((b / 255) * 65535))
    
        
class AnalogSensor(AnalogIn):
    pass
class DigitalSensor(DigitalIn):
    pass
class button(DigitalIn):
    pass
class variableResistor(AnalogIn):
    pass
class digitalLed(DigitalOut):
    pass
class analogLed(AnalogOut):
    pass