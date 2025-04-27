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
    
    def arm(self):
        # Method 1: Using MSP_SET_ARMED (direct arming)
        print("Attempting to arm using MSP_SET_ARMED...")
        self.send_cmd(216, [1])  # MSP_SET_ARMED = 216
        return self.read_response(216)
    
    def disarm(self):
        # Direct disarming
        print("Disarming...")
        self.send_cmd(216, [0])  # MSP_SET_ARMED = 216
        return self.read_response(216)
    
    def arm_via_channels(self):
        # Method 2: Arming by setting channel values (simulating stick positions)
        print("Attempting to arm via RC channels...")
        
        # Default channel values
        # [Roll, Pitch, Throttle, Yaw, AUX1, AUX2, AUX3, AUX4]
        channels = [1500, 1500, 1000, 1500, 1000, 1500, 1500, 1500]
        
        # Set minimum throttle
        channels[2] = 1000  # Throttle low
        
        # Send neutral channels first
        self.set_raw_rc(channels)
        time.sleep(0.5)
        
        # Set AUX1 (channel 5) to arm position (typically 1800-2000)
        channels[4] = 1800  # AUX1 to arm position
        self.set_raw_rc(channels)
        
        return True
    
    def disarm_via_channels(self):
        # Disarming via channels
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
            arming_disable_flags = data[6] + (data[7] << 8) + (data[8] << 16) + (data[9] << 24)
            return {
                "armed": bool(arming_flags & 1),
                "arming_flags": arming_flags,
                "arming_disable_flags": arming_disable_flags
            }
        return None

# Main script
if __name__ == "__main__":
    # Change this to your actual serial port
    serial_port = "/dev/ttyACM0"
    
    try:
        print(f"Connecting to flight controller on {serial_port}...")
        msp = MSP(serial_port)
        
        print("\n--- ARMING COMMAND ---")
        print("WARNING: This will arm the motors! Props should be removed for safety!")
        confirm = input("Props removed or area clear and safe? Type 'ARM' to continue: ")
        
        if confirm != "ARM":
            print("Arming cancelled for safety reasons.")
            exit()
        
        # Check current arming status
        status = msp.get_status()
        if status:
            print(f"Current armed state: {'ARMED' if status['armed'] else 'DISARMED'}")
            if status['arming_disable_flags'] > 0:
                print(f"Warning: Arming disable flags present: {status['arming_disable_flags']}")
                print("Some flags might prevent arming. Common flags:")
                if status['arming_disable_flags'] & 1:
                    print("- RXLOSS: No valid receiver signal")
                if status['arming_disable_flags'] & 32:
                    print("- MSP: Arming via MSP is disabled")
        
        # Try method 1: Direct MSP arming
        print("\nMethod 1: Direct MSP arming...")
        msp.arm()
        time.sleep(1)
        
        # Check if armed
        status = msp.get_status()
        if status and status['armed']:
            print("✅ Successfully armed via direct MSP command!")
        else:
            print("❌ Direct MSP arming failed.")
            
            # Try method 2: RC channel arming
            print("\nMethod 2: RC channel arming...")
            msp.arm_via_channels()
            time.sleep(1)
            
            # Check if armed
            status = msp.get_status()
            if status and status['armed']:
                print("✅ Successfully armed via RC channels!")
            else:
                print("❌ RC channel arming failed.")
                print("\nPossible issues:")
                print("1. MSP arming is disabled in Betaflight")
                print("2. Safety arming conditions not met (e.g., accelerometer not calibrated)")
                print("3. Receiver signal required but not detected")
                print("\nTry the following in Betaflight CLI:")
                print("- 'set arm_allowed_always = ON'")
                print("- 'set arming_check = -ALL'")
                print("- 'set small_angle = 180'")
                print("- 'save'")
        
        # Keep armed for 10 seconds
        if status and status['armed']:
            print("\nDrone is armed! Staying armed for 10 seconds...")
            for i in range(10, 0, -1):
                print(f"{i} seconds remaining...")
                time.sleep(1)
        
        # Always disarm at the end
        print("\nDisarming...")
        msp.disarm()  # Try direct disarm
        time.sleep(0.5)
        msp.disarm_via_channels()  # Try channel disarm
        
        # Verify disarmed
        status = msp.get_status()
        if status:
            print(f"Final armed state: {'ARMED' if status['armed'] else 'DISARMED'}")
            
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Tips to fix:")
        print("- Check if the serial port is correct")
        print("- Make sure you have permissions (run: sudo usermod -a -G dialout $USER)")
        
    except Exception as e:
        print(f"Error: {e}")
