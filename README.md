# **ANAV Autonomous Drone System**

## **Overview**
The ANAV Autonomous Drone System is designed to perform fully autonomous flights using a Raspberry Pi 4B connected to a SpeedyBee F405 V3 flight controller. The system operates without the need for an RC transmitter and includes a suite of Python scripts for different functionalities such as motor testing, telemetry, battery status check, and more.

This repository contains all the necessary code and scripts to achieve autonomous takeoff, hovering, and landing, while utilizing sensors like the HC-SR04 ultrasonic sensor for altitude measurement and optional MS5611 barometer for more accurate altitude estimation.

### **Key Features:**
- **Autonomous Flight**: Includes autonomous takeoff, hover, and landing.
- **Sensor Integration**: Utilizes the HC-SR04 ultrasonic sensor for altitude control and optional MS5611 barometer.
- **MSP Communication**: Communication with Betaflight firmware through the MSP protocol.
- **Telemetry**: Real-time telemetry logging from Betaflight.
- **Emergency Handling**: Low battery detection and UART disconnect handling.
- **PID Control**: PID control loop for maintaining altitude and stability.

---

## **File Descriptions**

### 1. **full_autonomous_flight.py**
   - This is the main script for the autonomous flight system. It handles takeoff, hover, and landing procedures by interacting with the flight controller over the MSP protocol.

### 2. **arm.py**
   - This script is used to arm the drone and prepare it for flight. It interfaces with the flight controller and ensures that the system is ready for autonomous operation.

### 3. **disarm.py**
   - This script disarms the drone and halts any active flight commands, ensuring the motors are stopped safely.

### 4. **battery_status_check.py**
   - A script for checking the battery status of the drone. It can trigger a fail-safe response when the battery is critically low.

### 5. **motor_test.py**
   - A basic test script to ensure that the motors are functioning correctly before the flight.

### 6. **reciever_connection_test.py**
   - A script to test the communication between the drone receiver and flight controller. Ensures that the receiver is properly connected and transmitting data.

### 7. **test-fc-telemetry.py**
   - A telemetry script that reads flight data (altitude, position, etc.) from the flight controller and logs it for analysis.

### 8. **Wiring_Representation**
   - An image that illustrates the wiring setup for connecting the Raspberry Pi to the SpeedyBee F405 V3 flight controller, sensors, and other components.

### 9. **Test.mp4**
   - A video showing a test flight or system demonstration.

---

## **System Requirements**

- **Hardware**:
  - Raspberry Pi 4B
  - SpeedyBee F405 V3 Flight Controller
  - HC-SR04 Ultrasonic Sensor (for altitude measurement)
  - MS5611 Barometer (optional)
  - Raspberry Pi Camera (optional, for optical flow)

- **Software**:
  - Betaflight firmware running on the flight controller
  - Python 3.x installed on Raspberry Pi
  - Required Python libraries:
    - `pyserial`
    - `struct`
    - `time`
    - `threading`

---

## **Installation Instructions**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ANAV-Autonomous-Drone.git
   cd ANAV-Autonomous-Drone
   ```

2. **Install Dependencies**:
   Make sure Python 3.x is installed, then install required libraries:
   ```bash
   pip install pyserial
   ```

3. **Connect the Hardware**:
   - Connect the Raspberry Pi 4B to the SpeedyBee F405 V3 via UART (using `/dev/ttyACM0`).
   - Attach the HC-SR04 ultrasonic sensor and any other sensors you plan to use.
   - Ensure that the necessary wiring is done according to the **Wiring_Representation** diagram.

4. **Run the Scripts**:
   - **Arm the Drone**: Run `arm.py` to arm the drone for flight.
   - **Execute Autonomous Flight**: Run `full_autonomous_flight.py` to perform the autonomous flight sequence (takeoff, hover, landing).
   - **Monitor Telemetry**: Use `test-fc-telemetry.py` to log telemetry data from Betaflight.

---

## **Usage Example**

1. **Start Autonomous Flight**:
   ```bash
   python full_autonomous_flight.py
   ```

2. **Check Battery Status**:
   ```bash
   python battery_status_check.py
   ```

3. **Test Motors**:
   ```bash
   python motor_test.py
   ```

4. **Telemetry Logging**:
   ```bash
   python test-fc-telemetry.py
   ```

---

## **Contributing**

If you’d like to contribute to the development of the ANAV Autonomous Drone System, feel free to fork the repository, make improvements, and create a pull request with your changes.

---

## **License**

This project is open source and available under the [MIT License](LICENSE).

---

**Author**: Pranay1004  
**Project Repository**: https://github.com/Pranay1004/IRoCU-2025/

---
