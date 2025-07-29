from machine import Pin, PWM, Timer
import rp2
import time

class PID():
    def __init__(self,
                 kp = 1.0,
                 ki = 0.0,
                 kd = 0.0,
                 min_output = 0.0,
                 max_output = 1.0,
                 max_derivative = None,
                 max_integral = None,
                 tolerance = 0.1,
                 tolerance_count = 1
                 ):

        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_output = min_output
        self.max_output = max_output
        self.max_derivative = max_derivative
        self.max_integral = max_integral
        self.tolerance = tolerance
        self.tolerance_count = tolerance_count

        self.prev_error = 0
        self.prev_integral = 0
        self.prev_output = 0

        self.start_time = None
        self.prev_time = None

        # number of actual times in tolerance
        self.times = 0

    def _handle_exit_condition(self, error: float):
        if abs(error) < self.tolerance:
            # if error is within tolerance, increment times in tolerance
            self.times += 1
        else:
            # otherwise, reset times in tolerance, because we need to be in tolerance for numTimesInTolerance consecutive times
            self.times = 0

    def update(self, error: float, debug: bool = False) -> float:
        
        current_time = time.ticks_ms()
        if self.prev_time is None:
            # First update after instantiation
            self.start_time = current_time
            timestep = 0.01
        else:
            # get time delta in seconds
            timestep = time.ticks_diff(current_time, self.prev_time) / 1000
        self.prev_time = current_time # cache time for next update

        self._handle_exit_condition(error)

        integral = self.prev_integral + error * timestep
        
        if self.max_integral is not None:
            integral = max(-self.max_integral, min(self.max_integral, integral))

        derivative = (error - self.prev_error) / timestep

        # derive output
        output = self.kp * error + self.ki * integral + self.kd * derivative
        self.prev_error = error
        self.prev_integral = integral

        # Bound output by minimum
        if output > 0:
            output = max(self.min_output, output)
        else:
            output = min(-self.min_output, output)
        
        # Bound output by maximum
        output = max(-self.max_output, min(self.max_output, output))

        # Bound output by maximum acceleration
        if self.max_derivative is not None:
            lower_bound = self.prev_output - self.max_derivative * timestep
            upper_bound = self.prev_output + self.max_derivative * timestep
            output = max(lower_bound, min(upper_bound, output))

        # cache output for next update
        self.prev_output = output

        if debug:
            print(f"{output}: ({self.kp * error}, {self.ki * integral}, {self.kd * derivative})")

        return output
    
    def is_done(self) -> bool:
        return self.times >= self.tolerance_count

    def clear_history(self):
        self.prev_error = 0
        self.prev_integral = 0
        self.prev_output = 0
        self.prev_time = None
        self.times = 0

class _Encoder:
    _gear_ratio = 45 # (30/14) * (28/16) * (36/9) * (26/8) # 48.75
    _counts_per_motor_shaft_revolution = 53 #12
    resolution = _counts_per_motor_shaft_revolution * _gear_ratio
    
    def __init__(self, index, encAPin: int|str, encBPin: int|str):
        
        basePin = Pin(min(encAPin, encBPin), Pin.IN)
        nextPin = Pin(max(encAPin, encBPin), Pin.IN)
        self.sm = rp2.StateMachine(index, self._encoder, in_base=basePin)
        self.reset_encoder_position()
        self.sm.active(1)
    
    def reset_encoder_position(self):
        self.sm.exec("set(x, 0)")
    
    def get_position_counts(self):
        # Read 5 times for it to get past the buffer
        counts = self.sm.get()
        counts = self.sm.get()
        counts = self.sm.get()
        counts = self.sm.get()
        counts = self.sm.get()
        if(counts > 2**31):
            counts -= 2**32
        return counts
    
    def get_position(self):
        return self.get_position_counts() / self.resolution

    @rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
    def _encoder():
        # Register descriptions:
        # X - Encoder count, as a 32-bit number
        # OSR - Previous pin values, only last 2 bits are used
        # ISR - Push encoder count, and combine pin states together
        
        # Jump table
        # The program counter is moved to memory address 0000 - 1111, based
        # on the previous (left 2 bits) and current (right  bits) pin states
        jmp("read") # 00 -> 00 No change, continue
        jmp("decr") # 00 -> 01 Reverse, decrement count
        jmp("incr") # 00 -> 10 Forward, increment count
        jmp("read") # 00 -> 11 Impossible, continue
        
        jmp("incr") # 01 -> 00 Forward, increment count
        jmp("read") # 01 -> 01 No change, continue
        jmp("read") # 01 -> 10 Impossible, continue
        jmp("decr") # 01 -> 11 Reverse, decrement count
        
        jmp("decr") # 10 -> 00 Reverse, decrement count
        jmp("read") # 10 -> 01 Impossible, continue
        jmp("read") # 10 -> 10 No change, continue
        jmp("incr") # 10 -> 11 Forward, increment count
        
        jmp("read") # 11 -> 00 Impossible, continue
        jmp("incr") # 11 -> 01 Forward, increment count
        jmp("decr") # 11 -> 10 Reverse, decrement count
        jmp("read") # 11 -> 11 No change, continue
        
        label("read")
        mov(osr, isr)   # Store previous pin states in OSR
        mov(isr, x)     # Copy encoder count to ISR
        push(noblock)   # Push count to RX buffer, and reset ISR to 0
        out(isr, 2)     # Shift previous pin states into ISR
        in_(pins, 2)    # Shift current pin states into ISR
        mov(pc, isr)    # Move PC to jump table to determine what to do next
        
        label("decr")           # There is no explicite increment intruction, but X can be
        jmp(x_dec, "decr_nop")  # decremented in the jump instruction. So we use that and jump
        label("decr_nop")       # to the next instruction, which is equivalent to just decrementing
        jmp("read")
        
        label("incr")           # There is no explicite increment intruction, but X can be
        mov(x, invert(x))       # decremented in the jump instruction. So we invert X, decrement, 
        jmp(x_dec, "incr_nop")  # then invert again - this is equivalent to incrementing.
        label("incr_nop")
        mov(x, invert(x))
        jmp("read")
        
        # Fill remaining instruction memory with jumps to ensure nothing bad happens
        # For some reason, weird behavior happens if the instruction memory isn't full
        jmp("read")
        jmp("read")
        jmp("read")
        jmp("read")
        

class Motor:
    def __init__(self, in1_pwm_forward: int|str, in2_pwm_backward: int|str, flip_dir:bool=False, PWM_frequency: int = 50):
        self.flip_dir = flip_dir
        self._MAX_PWM = 65535
        self._pwm_fwd = PWM(Pin(in1_pwm_forward, Pin.OUT))
        self._pwm_rev = PWM(Pin(in2_pwm_backward, Pin.OUT))
        self._pwm_fwd.freq(PWM_frequency)
        self._pwm_rev.freq(PWM_frequency)

    def set_effort(self, effort: float): #sentido da direção da roda
        
        effort = max(min(effort, 1.0), -1.0)  # Limita de -1 a 1

        # Inverte direção, se necessário
        if self.flip_dir:
            effort = -effort

        pwm_value = int(abs(effort) * self._MAX_PWM)

        if effort > 0:
            self._pwm_fwd.duty_u16(pwm_value)
            self._pwm_rev.duty_u16(0)
        elif effort < 0:
            self._pwm_fwd.duty_u16(0)
            self._pwm_rev.duty_u16(pwm_value)
        else:
            self.coast()

    def brake(self): #aplica tensão por completo no motor
        self._pwm_fwd.duty_u16(int(self._MAX_PWM))
        self._pwm_rev.duty_u16(int(self._MAX_PWM))

    def coast(self): #desativa por completo a tensão no motor
        self._pwm_fwd.duty_u16(int(0))
        self._pwm_rev.duty_u16(int(0))

class EncodedMotor:
    def __init__(self, motor: Motor, index, encAPin: int|str, encBPin: int|str):
        self._motor = motor
        self._encoder = _Encoder(index, encAPin, encBPin)
        self.brake_at_zero = True

        self.speedController = PID(
            kp=0.035,
            ki=0.03,
            kd=0,
            max_integral=50
        )

        self.target_speed = None
        self.prev_position = 0
        self.speed = 0


        self.updateTimer = Timer(-1)
        self.updateTimer.init(period=20, callback=lambda t: self._update())

        print("EncodedMotor inicializado com controle PID.")

    def set_effort(self, effort: float):
        if self.brake_at_zero and effort == 0:
            self.brake()
        else:
            self._motor.set_effort(effort)

    def set_zero_effort_behavior(self, brake_at_zero_effort: bool):
        self.brake_at_zero = brake_at_zero_effort

    def brake(self):
        self._motor.brake()
        self.updateTimer.deinit()

    def coast(self):
        self._motor.coast()
        self.updateTimer.deinit()

    def get_position(self) -> float:
        invert = -1 if self._motor.flip_dir else 1
        return self._encoder.get_position() * invert
    
    def get_position_counts(self) -> int:
        invert = -1 if self._motor.flip_dir else 1
        return self._encoder.get_position_counts() * invert

    def reset_encoder_position(self):
        self._encoder.reset_encoder_position()
    
    @property
    def get_speed(self) -> float:
        # Convert from counts per 20ms to RPM (60 sec/min, 50 Hz update rate)
        return self.speed * (60 * 50) / self._encoder.resolution

    def set_speed(self, speed_rpm: float = None):
        if speed_rpm is None or speed_rpm == 0:
            self.target_speed = None
            self.set_effort(0)
        else:
            # Convert from RPM to counts por 20ms (50Hz loop)
            self.target_speed = speed_rpm * self._encoder.resolution / (60 * 50)

    def set_speed_controller(self, kp=0.035,
                 ki=0.03,
                 kd=0,
                 min_output = 0.0,
                 max_output = 1.0,
                 max_derivative = None,
                 max_integral = 50,
                 tolerance = 0.1,
                 tolerance_count = 1):
        
        self.speedController = PID(kp,ki,kd,min_output,max_output,max_derivative,max_integral,tolerance,tolerance_count)
        
        self.speedController.clear_history()

    def _update(self):
        try:
            current_position = self.get_position_counts()
            self.speed = current_position - self.prev_position
            self.prev_position = current_position

            if self.target_speed is not None:
                error = self.target_speed - self.speed
                effort = self.speedController.update(error)
                self._motor.set_effort(effort)

        except Exception as e:
            print("Erro no _update():", e)
    
    def stop(self):
        self.set_speed(0)
        self.brake()

