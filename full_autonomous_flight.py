import serial
import time
import struct
import threading
import sys

# Constants and Configuration
MSP_PORT = '/dev/ttyACM0'
BAUD_RATE = 921600
TAKEOFF_ALTITUDE = 3.75  # meters
HOVER_ALTITUDE = 3.75  # meters (constant altitude hold)
LANDING_ALTITUDE = 0.2  # meters (safe landing threshold)

# MSP commands
MSP_STATUS = 0x10
MSP_SET_RAW_RC = 0x13
MSP_RAW_IMU = 0x12
MSP_ALTITUDE = 0x15  # Altitude data

# Initialize Serial Communication with Betaflight
def init_msp_connection():
    try:
        ser = serial.Serial(MSP_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for Betaflight to initialize
        return ser
    except Exception as e:
        print(f"Error initializing MSP connection: {e}")
        sys.exit(1)

# Send MSP Command
def send_msp_command(ser, command, payload=b''):
    length = len(payload)
    checksum = 0
    packet = bytearray([0x24, 0x4D, 0x53, 0x50, length, command])
    
    # Append payload and calculate checksum
    packet.extend(payload)
    for byte in packet:
        checksum ^= byte
    packet.append(checksum)
    
    # Send to the flight controller
    ser.write(packet)
    ser.flush()

# Read MSP Response
def read_msp_response(ser):
    # Read until the start byte is detected
    while True:
        byte = ser.read(1)
        if byte == b'\x24':  # start byte
            header = ser.read(4)  # header length 4 bytes
            if header == b'MSP':
                length = ord(ser.read(1))
                command = ord(ser.read(1))
                payload = ser.read(length)
                checksum = ord(ser.read(1))
                # Validate checksum here
                return command, payload
        time.sleep(0.01)

# Altitude Measurement from HC-SR04 Sensor (simple version)
def read_altitude():
    # This is a placeholder. In real code, use GPIO to trigger and read from the HC-SR04
    return 1.0  # Simulate 1m altitude for testing

# Takeoff Procedure
def takeoff(ser):
    print("Starting takeoff...")
    while True:
        current_altitude = read_altitude()
        if current_altitude >= TAKEOFF_ALTITUDE:
            print(f"Reached takeoff altitude: {current_altitude}m")
            break
        else:
            # Send a command to the flight controller to ascend
            payload = struct.pack('<H', 1000)  # Example: throttle
            send_msp_command(ser, MSP_SET_RAW_RC, payload)
            time.sleep(0.1)

# Hover and Maintain Altitude
def hover(ser):
    print("Hovering...")
    while True:
        current_altitude = read_altitude()
        if abs(current_altitude - HOVER_ALTITUDE) > 0.1:
            payload = struct.pack('<H', 1000)  # Adjust throttle for hovering
            send_msp_command(ser, MSP_SET_RAW_RC, payload)
        else:
            print(f"Maintaining hover at: {current_altitude}m")
        time.sleep(1)

# Landing Procedure
def land(ser):
    print("Initiating landing...")
    while True:
        current_altitude = read_altitude()
        if current_altitude <= LANDING_ALTITUDE:
            print(f"Landing complete. Altitude: {current_altitude}m")
            break
        else:
            payload = struct.pack('<H', 1000)  # Example: gradual throttle reduction
            send_msp_command(ser, MSP_SET_RAW_RC, payload)
            time.sleep(0.1)

# Emergency Handler (Low Battery, UART Disconnect)
def emergency_handler(ser):
    print("Emergency landing triggered...")
    # Send command to initiate immediate landing
    payload = struct.pack('<H', 1000)  # Example: throttle to zero
    send_msp_command(ser, MSP_SET_RAW_RC, payload)

# Telemetry logging
def log_telemetry(ser):
    while True:
        command, payload = read_msp_response(ser)
        if command == MSP_ALTITUDE:
            altitude_data = struct.unpack('<H', payload)
            print(f"Altitude: {altitude_data[0]} meters")
        time.sleep(0.5)

# Main Autonomous Flight Logic
def autonomous_flight():
    ser = init_msp_connection()

    # Start telemetry logging in background
    telemetry_thread = threading.Thread(target=log_telemetry, args=(ser,))
    telemetry_thread.start()

    # Run the flight sequence: Takeoff -> Hover -> Landing
    takeoff(ser)
    hover(ser)
    land(ser)

if __name__ == "__main__":
    autonomous_flight()
