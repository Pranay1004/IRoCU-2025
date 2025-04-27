import serial
import struct
import time

class MSP:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for connection to establish
        
    def send_cmd(self, cmd, data=None):
        if data is None:
            data = []
        size = len(data)
        checksum = 0
        
        # Calculate checksum
        checksum ^= size
        checksum ^= cmd
        for i in data:
            checksum ^= i
        
        # Construct message
        msg = b'$M<' + struct.pack('<BB', size, cmd)
        msg += bytes(data)
        msg += struct.pack('<B', checksum)
        
        # Send message
        self.ser.write(msg)
        
    def read_response(self, cmd):
        header = self.ser.read(3)  # $M>
        if len(header) != 3:
            print("Error: No proper header received")
            return None
            
        size = ord(self.ser.read(1))
        command = ord(self.ser.read(1))
        
        if command != cmd:
            print(f"Error: Expected command {cmd}, got {command}")
            return None
            
        data = self.ser.read(size)
        checksum = ord(self.ser.read(1))
        
        return data
    
    def disarm(self):
        # Method 1: Direct disarming via MSP_SET_ARMED
        print("Disarming using MSP_SET_ARMED...")
        self.send_cmd(216, [0])  # MSP_SET_ARMED = 216
        return self.read_response(216)
    
    def disarm_via_channels(self):
        # Method 2: Disarming via RC channels
        print("Disarming via RC channels...")
        
        # [Roll, Pitch, Throttle, Yaw, AUX1, AUX2, AUX3, AUX4]
        channels = [1500, 1500, 1000, 1500, 1000, 1500, 1500, 1500]
        
        # Set AUX1 (channel 5) to disarm position
        channels[4] = 1000  # AUX1 to disarm position
        self.set_raw_rc(channels)
        
        return True
    
    def set_raw_rc(self, channels):
        # MSP_SET_RAW_RC = 200
        data = []
        for ch in channels:
            data.extend([ch & 0xFF, (ch >> 8) & 0xFF])
        self.send_cmd(200, data)
        return self.read_response(200)
    
    def get_status(self):
        # MSP_STATUS_EX = 150
        self.send_cmd(150)
        data = self.read_response(150)
        
        if data and len(data) >= 14:
            arming_flags = data[2] + (data[3] << 8)
            return {
                "armed": bool(arming_flags & 1)
            }
        return None

# Main script
if __name__ == "__main__":
    # Change this to your actual serial port
    serial_port = "/dev/ttyACM0"
    
    try:
        print(f"Connecting to flight controller on {serial_port}...")
        msp = MSP(serial_port)
        
        print("\n--- EMERGENCY DISARM ---")
        
        # Check current arming status
        status = msp.get_status()
        if status:
            print(f"Current state: {'ARMED' if status['armed'] else 'DISARMED'}")
            
            if not status['armed']:
                print("Drone is already disarmed.")
                exit()
        
        # Try both disarm methods for reliability
        print("\nAttempting to disarm...")
        
        # Method 1: Direct MSP disarm
        msp.disarm()
        time.sleep(0.5)
        
        # Method 2: RC channel disarm
        msp.disarm_via_channels()
        time.sleep(0.5)
        
        # Verify disarmed status
        status = msp.get_status()
        if status:
            if status['armed']:
                print("❌ DISARM FAILED! Drone is still armed!")
                print("Try disconnecting the battery if safe to do so.")
            else:
                print("✅ DISARM SUCCESSFUL! Drone is now disarmed.")
        
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Tips to fix:")
        print("- Check if the serial port is correct")
        print("- Make sure you have permissions (run: sudo usermod -a -G dialout $USER)")
        
    except Exception as e:
        print(f"Error: {e}")
