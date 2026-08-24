from machine import Pin, PWM, time_pulse_us, ADC
import time


# 
# -------------------------------------------------------------------------------------------------------------------------------------
# Motor Controls for DC 6V Motors:


# Keep track of current motor action, set speed of motors

max_speed = int(65535)              # duty cycle: fresh 2s 18650 batteries give 7v at motor driver outputs, used give 6v, do 85% of max voltage (65535 duty cycle aka 7v) to supply safe ~6v with fresh batteries

current_action = ""                 # keep track of what the current motor movement is so you don't stop motor over and over if repeated same movement in super fast main while loop (ie fwd over and over every 0.005s + 0.005s)

# Initialize the motor pins (define them and set PWM freq) so u can use them in the motor action functions with global command (global only needed if modifying variable, we don't really need it since just setting duty cycle but I still have it there) 
motors_left1 = PWM(Pin(25))       #IN4 on driver (left fwd)
motors_left2 = PWM(Pin(24))       #IN3 on driver (left bwd)
motors_right1 = PWM(Pin(23))      #IN2 on driver (right fwd)
motors_right2 = PWM(Pin(22))      #IN1 on driver (right bwd)

motors_left1.freq(1000)          # freq: set between 500Hz-2000Hz for best balance between motor torque, motor whine, and mx 1508 (mini l298n) driver thermal stress
motors_left2.freq(1000)          # higher freq = less low end torque, less motor whine (though audible up to 20,000 Hz), more motor driver heat
motors_right1.freq(1000)         # lower freq = opposite
motors_right2.freq(1000)


# Define the motor actions like stop, bwd, fwd, turn and initialize motor pins (both globally and inside motor_startup() function)

def motor_stop():
    global motors_left1
    global motors_left2
    global motors_right1
    global motors_right2
    
    motors_left1.duty_u16(0)           # left 1 and right 1 = fwd pins
    motors_left2.duty_u16(0)           # left 2 and right 2  = bwd pins 
    motors_right1.duty_u16(0)          # set all duty cycle to 0 to brake
    motors_right2.duty_u16(0)


def motor_shutdown():                # for easier programming and to prevent buck resets with both logical/physical off and on, full shutdown of the motors by deinitializing the pwm setup for that pin (deinit) and making them inputs (no signal coming from them)
    
    global motors_left1
    global motors_left2
    global motors_right1
    global motors_right2
    
    motor_stop()                      
    
    motors_left1.deinit()            # full shutdown is needed because otherwise when programming pico with USB plugged in (rest powered from buck, only pico from USB) stopping the code doesn't stop the last PWM signals to motor, so they will keep running
                                     # turning the switch off to stop motors + rest hardware still keeps pico running (if plugged in for programming), so the PWM signals remain when you turn the buck back on to power the motors
    motors_left2.deinit()            # this triggers buck safety features and causes it to reset constantly (flashing light), makes programming slower since need to unplug USB for every code test (to fully disconnect the PWM signals)
    motors_right1.deinit()           # use motor_shutdown() with try/except to run code and shut those signals off for good when you stop the code, so no need to switch off to stop hardware and you can switch off and on without resets as long as you stop code first
    motors_right2.deinit()           
    
    Pin(25, Pin.IN)
    Pin(24, Pin.IN)
    Pin(23, Pin.IN)
    Pin(22, Pin.IN)
    

# Initialize the motor pins (define them, set PWM frequency, to start the motors in a stopped state
# Note that there are 4 motors in parallel driven by a single mx1508 motor driver so each side both motors controlled together (left together or right together)
def motor_startup():
    motors_left1 = PWM(Pin(25))       #IN4 on driver (left fwd)
    motors_left2 = PWM(Pin(24))       #IN3 on driver (left bwd)
    motors_right1 = PWM(Pin(23))      #IN2 on driver (right fwd)
    motors_right2 = PWM(Pin(22))      #IN1 on driver (right bwd)

    motors_left1.freq(1000)          # freq: set between 500Hz-2000Hz for best balance between motor torque, motor whine, and mx 1508 (mini l298n) driver thermal stress
    motors_left2.freq(1000)          # higher freq = less low end torque, less motor whine (though audible up to 20,000 Hz), more motor driver heat
    motors_right1.freq(1000)         # lower freq = opposite
    motors_right2.freq(1000)

    # ensure motors start in a stopped state
    motors_left1.duty_u16(0)           # left 1 and right 1 = fwd pins
    motors_left2.duty_u16(0)           # left 2 and right 2  = bwd pins 
    motors_right1.duty_u16(0)          # set all duty cycle to 0 to brake
    motors_right2.duty_u16(0)
    
    

def fwd():
    
    global motors_left1
    global motors_left2
    global motors_right1
    global motors_right2
    
    global current_action              # only stop motor if the next motor action is different from previous (ie. going from fwd to turn), without motor_stop() overshooting happens and old signal (ie. fwd) interferes with new signal (ie. turn)
    if current_action != "fwd":        # without motor_stop() overshooting happens and old commands (ie. fwd) interfere with new commands (ie. turn) since motors/hardware aren't as fast as the pico commands (which are sent fast in a loop)
        motor_stop()                   # without the current_action condition the motors will stop briefly if the looping commands are the same (ie. fwd over and over but every new fwd will do motor_stop())
        current_action = "fwd"         # motor_stop() matters alot, current_action not as big a deal since fwd command sent after the motor_stop() (meaning fwd command lasts longer when looped) so it won't stutter but still less efficient
        
    motors_left1.duty_u16(max_speed)   # left1 and right1 set with duty cycle max_speed to move fwd
    motors_left2.duty_u16(0)
    motors_right1.duty_u16(max_speed)
    motors_right2.duty_u16(0)
    
def bwd():
    
    global motors_left1
    global motors_left2
    global motors_right1
    global motors_right2
    
    global current_action
    if current_action != "bwd":
        motor_stop()
        current_action = "bwd"
    motors_left1.duty_u16(0)           # left2 and right2 set with duty cycle max_speed to move bwd
    motors_left2.duty_u16(max_speed)
    motors_right1.duty_u16(0)
    motors_right2.duty_u16(max_speed)

# consider adding softer turns by just lowering one side PWM by 0.5 or more (this will prevent voltage sag issue I think)
# can use softer turns for regular turns from 101 and hard turns (other side reversed not slowed) from 111
# then the code will behave like the AI code basically but IMO only hard turns is better (and faster) but more jittery

def slight_right():
    
    global motors_left1
    global motors_left2
    global motors_right1
    global motors_right2
    
    global current_action
    
    if current_action != "right":         # if it's going from left/fwd to a right turn, don't just switch the motors to opposite immediately, stop left side first, move left fwd, then reverse right side bwd (prevents excess current draw)
                                          # buck converter has max 5A current draw, switching motors opposite instantly exceeeds that and causes buck/pico both to reset 
        motors_left1.duty_u16(0)          # stop left side first (right side still going fwd) 
        motors_left2.duty_u16(0)
        
        time.sleep(0.03)
        
        motors_left1.duty_u16(max_speed)  # now move the left side fwd()
        motors_left2.duty_u16(0)
        
        time.sleep(0.03)
        
        motors_right1.duty_u16(0)         # finally reverse the right side motors to turn right at full power
        motors_right2.duty_u16(max_speed)
        
 
    
    current_action = "right"
    
def slight_left():
    
    global motors_left1
    global motors_left2
    global motors_right1
    global motors_right2
    
    global current_action
    
    if current_action != "left":          # if it's going from right/fwd to a left turn, don't just switch the motors to opposite immediately, stop right side first, move right fwd, then reverse left side bwd (prevents excess current draw)
                                          # buck converter has max 5A current draw, switching motors opposite instantly exceeeds that and causes buck/pico both to reset 
        motors_right1.duty_u16(0)         # stop right side first (left side still going fwd)
        motors_right2.duty_u16(0)
        
        time.sleep(0.03)
        
        motors_right1.duty_u16(max_speed) # now move the right side fwd
        motors_right2.duty_u16(0)
        
        time.sleep(0.03)
        
        motors_left1.duty_u16(0)          # finally reverse the left side motors to turn left at full power
        motors_left2.duty_u16(max_speed)
        
    
    current_action = "left"
# -------------------------------------------------------------------------------------------------------------------------------------
#


#
# -------------------------------------------------------------------------------------------------------------------------------------
# Line Follower Code Only:

# Define the 3 infrared (IR) sensor pins
# Input 1 = IR light reflected by surface back to sensor (white/non-black surface)
# Input 0 = IR light absorbed by the surface (black surface)

ir_left = Pin(15, Pin.IN)      # left IR sensor
ir_center = Pin(14, Pin.IN)    # center IR sensor
ir_right = Pin(13, Pin.IN)     # right IR sensor

last_seen = ""                 # keep track of what the most recent position over the line is (ie left = last position is to the left of the line)

# line_following() is the main line following function which automatically moves fwd() and automatically adjusts position left/right depending on where the line is

def line_following():
    global obstacle_avoidance_mode   # use global variables from main mode-switching code below to allow mode switching while in a particular mode (so you don't get stuck in the loop of that mode)
    global last_press_time
    
    global last_seen # give the function permission to use the global variable last_seen
    
    while True:
        current_time = time.ticks_ms()
        
        # if button is pressed (pressed = 0 value) with 200ms debounce, alternate modes and switch to correct LED 
        if button.value() == 0 and time.ticks_diff(current_time, last_press_time) > 200:
            obstacle_avoidance_mode = True                # if button pressed, switch modes to obstacle avoidance by making obstacle_avoidance_mode = True from it's False state (which happened with previous button press)
            last_press_time = current_time                # reset the debounce timer
             
            led_red.value(1)                              # turn red LED on to indicate obstacle avoidance mode
            led_yellow.value(0)
            
            return   # return statement to break out of the while loop upon button press so that the mode can switch and you don't get stuck in the while loop (stuck in that mode basically)
        
        first_read = (ir_left.value(), ir_center.value(), ir_right.value())     # debounce IR readings to keep them stable by taking a first read of all 3 IR sensors, waiting 0.005s, then taking second read
        time.sleep(0.005)                                                       # then compare and if both readings match that means IR reading is stable and proceed with correct motor action
        second_read = (ir_left.value(), ir_center.value(), ir_right.value())
        
        if first_read == second_read:
            
            l_c_r = first_read                                   # once the IR reading is confirmed stable, store it in l_c_r (left, center, right) as a tuple containing the 3 IR sensor values
                
            if l_c_r == (1, 0, 1):                               # if the 3 IR sensors read 101 it's over the black line so move fwd(), update last seen position
                fwd()
                last_seen = "fwd"
                
            elif l_c_r == (1, 1, 0) or l_c_r == (1, 0, 0):       # if the 3 IR sensors read 110 or 100 it's to the left so slight_right(), update last seen position

                slight_right()
                last_seen = "left"

            elif l_c_r == (0, 1, 1) or l_c_r == (0, 0, 1):       # if the 3 IR sensors read 011 or 001 it's to the right so slight_left(), update last seen position

                slight_left()
                last_seen = "right"

            
            elif l_c_r == (1, 1, 1) or l_c_r == (0, 0, 0):       # if the 3 IR sensors read 111 or 000 that means it's completely off the line (111) or all sensors above line (000)

                                                                 # in that case invoke the last_seen variable from when it was on the line before going 111/000 to adjust back to the line

                if last_seen == "left":                          # if it goes from 110/100 (left) to 111/000 then go right to correct
                    slight_right()

                elif last_seen == "right":                       # if it goes from 011/001 (right) to 111/000 then go left to correct 
                    slight_left()

                elif last_seen == "fwd":                         # sometimes it will go from 101 (fwd/straight) to 111/000 (usually 111) even if some sensor is over black line (sensor glitches and reads 1 when it should read 0 for lots of different reasons)
                                                                 # since last seen is "straight" in this case we need to set an action for this condition or motors stop (since no command is given for the condition)
                    fwd()                                        # in those cases move forward so that eventually one of the left or right sensors goes low (stops glitching) and turn left or right, usually it just needs to move fwd a little to get the sensors working 
                
        time.sleep(0.005)                                        # main loop has a 0.005s delay and debounce has 0.005s delay meaning it's reading sensor data and giving motor commands every 0.01 seconds (can adjust but this works)

#
# -------------------------------------------------------------------------------------------------------------------------------------
#


# Ultrasonic Readings (Reads at single servo angle while servo is panning)


trig = Pin(11, Pin.OUT)                        # define trig (emits sounds) and echo (listens sounds) pins for ultrasonic sensor
echo = Pin(12, Pin.IN)

def ultrasonic_reading():
    
    for attempt in range(3):                       # use 3 attempts to filter values, can use median filtering (better) but it's slower and for this design it is meant to be fast


        trig.value(0)                              # initialize to 0 state for 10 us to prevent false readings
        time.sleep_us(10)

        trig.value(1)                              # pico raises trig high for 10 us and then low, after low the sensor fires 8 40khz ultrasonic sound bursts (takes 200 us)
        time.sleep_us(10)                          # after it sends these bursts, the sensor raises echo to 1 (high) and only sets it to 0 (low) when the sound bounces back to it (how long it takes = calculate distance)
        trig.value(0)
    

        # for below we can try time.ticks_us() followed by a while loop with time.ticks_diff() but you lose accuracy measuring the time of sound wave to hit and bounce back
        # because of background python interpreter processes, whereas time_pulse_us is optimized to be less slow (more accurate)

        duration = time_pulse_us(echo, 1, 30000) # time_pulse_us function starts a microsecond timer when the specified pin (echo pin 12) goes high (because we specified 1 in second argument)
                                             # ultrasonic (not pico) makes echo go high (1) after receiving complete trig pulse of 10 us (trig high --> low)   
                                             # time_pulse_us then stops the timer when that pin goes low (ultrasonic makes echo 0 when sound bounces back to it)
                                             # with a 30,000 microsecond delay so it isn't stuck on timer waiting for echo pin to go low (30,000 us will let sound travel outside sensor range anyway)
                                                                
        if duration >= 0:                       # if the attempt gives an actual result (not timeout which = -1 duration from time_pulse_us), then get the distance from that duration
         
            distance = (0.0343 * duration)/2    # 0.0343 cm per microsecond = speed of sound, multiply by duration of full bounce and divide by 2 to get distance for half bounce (actual distance)
            return round(distance, 1)


    
    
                                             # so basically the pico is doing the timing and setting state 1/0 of the trig (output) pin
                                             # and ultrasonic sets state 1/0 of echo (input) pin which pico listens for because we set Pin.IN for echo and used time_pulse_us
                                             # if echo was set to output, then the pico drives the pin (usually low by default since nobody set the pin high), then it and ultrasonic are competing to control the pin ie. ultrasonic wants to set it high pico wants to set it low
        
    return None                              # after 3 attempts return None 
    

#
# -------------------------------------------------------------------------------------------------------------------------------------
# Servo Control for SG90 Micro Servo

big_right = 500
small_right = 937
center = 1425
small_left = 1863
big_left = 2350

servo = PWM(Pin(10))

servo.freq(50)

def move_servo(position):
        servo.duty_u16(int((position / 20000) * 65535))
        time.sleep(0.15)


# pin configuration for button and 2 LED's to indicate either obstacle avoidance (red) or line following (yellow)
button = Pin(21, Pin.IN, Pin.PULL_UP) # note that button is pulled up to 1, pressing it closes circuit to ground and makes it 0 
led_red = Pin(26, Pin.OUT)
led_yellow = Pin(29, Pin.OUT)

# initial state is obstacle_avoidance = True, last_press_time is for keeping track of current time to debounce the button press
obstacle_avoidance_mode = True
last_press_time = 0




# stop_scan() runs only when picobot stops (encounters obstacle), it takes 5 ultrasonic readings and makes a decision on where to go based on those readings

def stop_scan():
    
    ultrasonic_readings = []       # reset ultrasonic_readings list after every full scan otherwise list grows infinitely and pico slows down 
    
    # collect 5 ultrasonic readings at 5 different servo angles and store it in the list ultrasonic_readings
    
    move_servo(big_left)
    
    stop_reading = ultrasonic_reading()      # take ultrasonic reading after servo movement and store it in stop_reading
    while stop_reading is None:              # if the reading is None (failed reading), keep trying to take the reading until it's not None            
        
        time.sleep(0.005)                       
        stop_reading = ultrasonic_reading()

        
    ultrasonic_readings.append(stop_reading) # store the good reading in list ultrasonic_readings
    print(ultrasonic_readings)
    
    move_servo(small_left)
    
    stop_reading = ultrasonic_reading()      # take ultrasonic reading after servo movement and store it in stop_reading
    while stop_reading is None:              # if the reading is None (failed reading), keep trying to take the reading until it's not None
        
        time.sleep(0.005)                     
        stop_reading = ultrasonic_reading()

        
    ultrasonic_readings.append(stop_reading) # store the good reading in list ultrasonic_readings
    print(ultrasonic_readings)
    
    move_servo(center)
    
    stop_reading = ultrasonic_reading()      # take ultrasonic reading after servo movement and store it in stop_reading
    while stop_reading is None:              # if the reading is None (failed reading), keep trying to take the reading until it's not None
    
        time.sleep(0.005)
        stop_reading = ultrasonic_reading()

    ultrasonic_readings.append(stop_reading) # store the good reading in list ultrasonic_readings
    
    print(ultrasonic_readings)
    
    move_servo(small_right)
    
    stop_reading = ultrasonic_reading()      # take ultrasonic reading after servo movement and store it in stop_reading
    while stop_reading is None:              # if the reading is None (failed reading), keep trying to take the reading until it's not None
        
        time.sleep(0.005)                     
        stop_reading = ultrasonic_reading()

        
    ultrasonic_readings.append(stop_reading) # store the good reading in list ultrasonic_readings
    print(ultrasonic_readings)
    
    move_servo(big_right)
    
    stop_reading = ultrasonic_reading()      # take ultrasonic reading after servo movement and store it in stop_reading
    while stop_reading is None:              # if the reading is None (failed reading), keep trying to take the reading until it's not None
        
        time.sleep(0.005)                   
        stop_reading = ultrasonic_reading()

    ultrasonic_readings.append(stop_reading) # store the good reading in list ultrasonic_readings
    print(ultrasonic_readings)
    
    
    # group the data into Left, Center, and Right scores
    # use averages for left and right readings so 2 readings don't artificially double the distance value
    
    avg_left = (ultrasonic_readings[0] + ultrasonic_readings[1]) / 2
    center_fwd = ultrasonic_readings[2]
    avg_right = (ultrasonic_readings[3] + ultrasonic_readings[4]) / 2
    
    
    # 3-way conditional to find the path with the most open space, and move picobot there
    
    if center_fwd >= avg_left and center_fwd >= avg_right:
        fwd()           # Center has the highest distance, so go fwd
        
    elif avg_left > avg_right:
        slight_left()   # Left has more open space than Right, so turn left for 1 seconds then go fwd
        time.sleep(1)
        fwd()
        
    else:
        slight_right()  # Right has more open space than Left, so turn right for 2 seconds then go fwd
        time.sleep(1)
        fwd()
        
# fwd_scan() runs in a while loop to move the robot forward and center servo until it encounters an obstacle, after which it stops and runs stop_scan() to make a decision on where to go next

def fwd_scan():
    # when there is no obstacle <20cm away, do the following by default:
    fwd()                               # move fwd by default 
    move_servo(center)                  # center the servo by default
    fwd_reading = ultrasonic_reading()  # take ultrasonic readings as picobot moves fwd and servo is centered, store it in fwd_reading
    
    print(fwd_reading) # print the center fwd ultrasonic reading as it goes fwd                

    if fwd_reading != None and 0 < fwd_reading <= 25:    # if fwd_reading is not none and between 0 and 25 cm, it means obstacle encountered
        motor_stop()                                     # stop pico_bot
        time.sleep(0.5)                                  # wait 0.5 seconds
        stop_scan()                                      # run motor_scan to decide where to move next, either left/fwd, fwd, or right/fwd
        




# main obstacle avoidance code that runs fwd_scan() in a loop to move the robot fwd and center servo by default until it encounters an obstacle <20cm away
# after which fwd_scan() runs stop_scan() to decide where to go next, and then back to fwd_scan() default fwd and servo center when there isn't any obstacle <20cm away

def obstacle_avoidance():
    global obstacle_avoidance_mode # use global variables from initialization above to allow mode switching while in a particular mode (so you don't get stuck in the loop of that mode)
    global last_press_time
    
    while True:
        current_time = time.ticks_ms()
        
        # if button is pressed (pressed = 0 value) with 200ms debounce, alternate modes and switch to correct LED 
        if button.value() == 0 and time.ticks_diff(current_time, last_press_time) > 200:
            obstacle_avoidance_mode = False               # if button pressed, switch modes to line_following() by making obstacle_avoidance_mode = False from it's True state (which happened with the previous button press)
            last_press_time = current_time                # reset the debounce timer
             
            led_red.value(0)                              # turn yellow LED on to indicate line following mode 
            led_yellow.value(1)
            
            return   # return statement to break out of the while loop upon button press so that the mode can switch and you don't get stuck in the while loop (stuck in that mode basically)
        
        # note that if that button is pressed while fwd_scan() running (usually the case) then fwd_scan() will finish first and then it will switch to line following mode
        # meaning the servo should auto center itself for line following (just aesthetic, doesn't alter function)
        # sometimes button pressed in the small moment that fwd_scan() isn't running (due to 0.005s pause) then servo will not center
        fwd_scan()
        time.sleep(0.005) # small pause to keep pico stable




# -------------------------------------------------------------------------------------------------------------
# MAIN CODE WHICH ALLOWS USER TO SWITCH MODES BETWEEN OBSTACLE AVOIDING AND LINE FOLLOWING, WITH LED INDICATORS
# -------------------------------------------------------------------------------------------------------------

# note that button press only works when in fwd_scan() not while in stop_scan() in obstacle avoidance mode
# so you can't change mode while servo is panning around to scan and make decision (stop_scan)
# button works all the time in line following mode though

try:
    
    # note: the 2 capacitors (470uF 16V) placed between 5V power/grnd rails were also causing buck to reset even with the code below, removing both of them and putting just 1 of them on buck output fixed resets mostly + the code below also helps (unsure which helps more)
        
    motor_shutdown()           # CRUCIAL: Shutdown motors for 0.5 seconds on electrical boot-up (power supply on) to fix buck resets on power supply on/off
    time.sleep(0.5)            # "finally" at bottom of code only helps buck reset due to software on/off, while this helps with physical power supply on/off causing buck resets
                               # still resets sometimes but if u wait a bit after putting batteries in for the first time or after powering off it works usually

    motor_startup()            # then boot up the motors again by reinitializing the pins and setting the frequency again for all motors, but don't move the motors yet (motor_stop() prevents motors from moving) for 0.5 seconds
    time.sleep(0.5)            # THIS ALSO PREVENTS GENERAL CRASHES DUE TO SERVO/MOTOR CONFLICT (basically prevents commands from interfering with each other)
    
    # give a tiny visual confirmation that boot-up was successful by flashing the LED's
    for i in range(5):
        led_red.value(1)
        led_yellow.value(1)
        time.sleep(0.1)
        led_red.value(0)
        led_yellow.value(0)
        time.sleep(0.1)
    
    # note that initial default state is obstacle_avoidance_mode = True, so after flashing LED's turn the red LED on to indicate obstacle avoidance mode is on
    led_red.value(1)
    led_yellow.value(0)
    time.sleep(0.1)
    
    while True:
        
        # based on the mode that was decided with button press, call either the main "obstacle_avoidance()" function or main "line_following" function
        # obstacle_avoidance() makes the robot move fwd and avoid obstacles, while line_following() follows a black line (ie. electrical tape).
        
        if obstacle_avoidance_mode == True:
            obstacle_avoidance()
            time.sleep(0.05)   # small pause to keep button switching stable
        elif obstacle_avoidance_mode == False:
            line_following()  # small pause to keep button switching stable
            time.sleep(0.05)
                
        time.sleep(0.05) # small pause in the main loop to keep the Pico stable
        
# CRUCIAL: run the obstacle avoidance code, but if there is anything to stop the program (software shutdown only) then shut down the motors fully to prevent the pico from continuing to send PWM signals from whatever last command was sent to motors
# without this the buck will reset every startup of the robot or any attempt to run code due to extra current from the stalling motors which have to deal with sudden new commands after continuing old commands
# "finally" is better than "except" in this case because finally will run motor_shutdown() for any code-related reason the code is stopped, while except needs a specific reason like KeyboardInterrupt
finally:    
    motor_shutdown()









