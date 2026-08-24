# PicoBot
A raspberry pi pico based robot that can follow black lines (ie. electrical tape) or avoid obstacles while moving around, with button and LED indicators to switch between either mode. It uses 3 IR sensors, an ultrasonic sensor paired with a servo, 4 motors driven by a motor driver and pico microcontroller as the brain. 

Note to self: Future changes to the repo will include circuit diagrams and other relevant documentation. 

## Some Pictures:
<p>
  <img width="49%" height="100%" alt="front_view_picobot" src="https://github.com/user-attachments/assets/0245a0bf-01c6-475e-a9b6-8638cbcc87e1" />
  <img width="49%" height="50%" alt="top_view_picobot" src="https://github.com/user-attachments/assets/d92e2cc7-0845-4f54-96c8-0132615390cd" />
</p>

## Video Showing Full Functionality:
https://github.com/user-attachments/assets/12376918-3ae8-46aa-82f1-461c3f1d1bef

## Features:
### Obstacle Avoiding: 
- Will move forward until an obstacle within 25cm is encountered by ultrasonic sensor, then pans ultrasonic sensor left --> right with servo to take 5 readings, compare which (left, forward, right) gives highest distance reading and either turn left/right or go forward, repeat.
- Note: Since cheap ultrasonic sensor used is not always reliable, distance readings are not always consistent (and therefore movement is not always consistent) so further optimization might be needed in code.
### Black Line Following: 
- Uses 3 IR sensors to determine if robot is on the line (go forward), to the left of the line (go right), or to the right of the line (go left), combining all 3 movements results in fairly smooth line following (without PID)
- Note: Because infrared light sensors are used, the only black line the robot will follow is one that will reliably absorb IR light on a reflecting surface (ie. black electrical tape on white floor), though the IR sensors themselves are very reliable once their position relative to line is calibrated
- Note: The maximum angle PicoBot will turn on a black line is 90 degrees, more than 3 IR sensors would allow sharper turns but this might also be improved with further code optimization.
### Alternate Between Modes: 
- Using a standard push button, a single press alternates between obstacle avoiding or line following mode with LED indicators for visual confirmation. On startup the default mode is obstacle avoiding.
- Note: PicoBot will not switch modes with button press if it has detected an obstacle and is panning the servo/ultrasonic to take readings, but it will switch modes in all other states

## Hardware:
- Raspberry Pi Pico (RP2040)
- 4 Yellow TT Motors 6V (1:48 gear ratio)
- Mini L298N Motor Driver
- SG90 Micro Servo
- HC-SR04 Ultrasonic Sensor 5V (for obstacle avoidance)
- 3 TCRT500 IR Sensors 3.3V/5V (for black line following)
- 1 470uF 16V Electrolytic Capacitor (placed at buck output, helps with buck reset due to overcurrent)
- Standard Breadboard Push Button
- 2 LEDs (different colors) with 220ohm resistors each
- 1kohm and 2kohm resistors for HC-SR04 ECHO Line Voltage Divider
- 3S (series) 18650 Lithium Battery Holder With Switch (I used single 18650 holders and joined them together)
- 24V/12V to 5V DC-DC Buck Converter with 5A Output (need high current output to handle motor stall current)
- Chassis, wheels, and ultrasonic/servo mounts were 3D printed in PLA
- Super glue + hot glue to hold everything together
- Super glue for wheel "tires" (traction)
- 3 18650 Lithium Batteries
- IMPORTANT: BATTERY MANAGEMENT SYSTEM (BMS) IS NOT USED IN THIS BUILD SO DO NOT LET BATTERIES OVERDISCHARGE OR LEAVE THEM IN BATTERY HOLDERS WHILE NOT USING PicoBot

## Software:
- See main_code.py file within repository for full python source code which implements all PicoBot features mentioned above.
- Code file also has much more general detail about the robot in the comments


