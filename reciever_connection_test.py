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
    
    def get_rx_status(self):
        # MSP_RX = 105
        self.send_cmd(105)
        data = self.read_response(105)
        
        if data is None:
            print("Failed to get receiver data")
            return None
            
        channels = []
        for i in range(0, len(data), 2):
            # Convert 2 bytes to an RC value
            if i+1 < len(data):
                ch_value = data[i] + (data[i+1] << 8)
                channels.append(ch_value)
        
        return channels
    
    def get_arming_status(self):
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

# Test script
if __name__ == "__main__":
    # Change this to your actual serial port
    serial_port = "/dev/ttyACM0"  # Use ACM0 as mentioned in your setup
    
    try:
        print(f"Connecting to flight controller on {serial_port}...")
        msp = MSP(serial_port)
        
        print("\n--- TESTING RECEIVER CONNECTION ---")
        print("Reading receiver channel values...")
        print("Move sticks on your transmitter to see values change.")
        
        for i in range(10):  # Read 10 times with delay
            channels = msp.get_rx_status()
            
            if channels:
                print("\nReceiver channel values:")
                for idx, value in enumerate(channels[:8]):  # Show first 8 channels
                    channel_name = "AUX" + str(idx-3) if idx > 3 else ["Roll", "Pitch", "Throttle", "Yaw"][idx]
                    print(f"CH{idx+1} ({channel_name}): {value}")
                
                # Check if AUX1 (arm switch) is present
                if len(channels) >= 5:
                    aux1 = channels[4]
                    if aux1 < 1300:
                        print("AUX1 position: LOW (disarmed)")
                    elif aux1 > 1700:
                        print("AUX1 position: HIGH (armed)")
                    else:
                        print("AUX1 position: MIDDLE")
                
                # Check if values look valid
                valid_values = all(900 <= ch <= 2100 for ch in channels[:4])
                if valid_values:
                    print("✅ Channel values look good!")
                else:
                    print("⚠️ Some values are outside expected range")
            else:
                print("❌ Failed to read receiver values")
            
            # Get arming status
            arming_status = msp.get_arming_status()
            if arming_status:
                print(f"Armed: {'YES' if arming_status['armed'] else 'NO'}")
                print(f"Arming flags: {arming_status['arming_flags']}")
                print(f"Arming disable flags: {arming_status['arming_disable_flags']}")
                if arming_status['arming_disable_flags'] & 1:
                    print("⚠️ RXLOSS flag set - No receiver signal detected!")
                if arming_status['arming_disable_flags'] & 32:
                    print("⚠️ MSP flag set - Arming via MSP disabled!")
            
            time.sleep(1)
            
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Tips to fix:")
        print("- Check if the serial port is correct")
        print("- Make sure you have permissions (run: sudo usermod -a -G dialout $USER)")
        print("- Verify port is enabled for MSP in Betaflight")
        
    except Exception as e:
        print(f"Error: {e}")
