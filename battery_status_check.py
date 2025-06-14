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
    
    def get_battery_status(self):
        # MSP_BATTERY_STATE = 130
        self.send_cmd(130)
        data = self.read_response(130)
        
        if data is None or len(data) < 8:
            print("Failed to get battery data")
            return None
            
        # Parse battery data
        battery = {}
        # First byte is cell count, may be 0 if not detected
        battery['cell_count'] = data[0]
        
        # Next 2 bytes are capacity in mAh
        battery['capacity'] = data[1] + (data[2] << 8)
        
        # Next 2 bytes are voltage in 10mV steps
        voltage_raw = data[3] + (data[4] << 8)
        battery['voltage'] = voltage_raw / 100.0  # Convert to volts
        
        # Next 2 bytes are drawn current in 10mA steps
        current_raw = data[5] + (data[6] << 8)
        battery['current'] = current_raw / 100.0  # Convert to amps
        
        # Next 2 bytes are mAh drawn
        battery['mah_drawn'] = data[7] + (data[8] << 8)
        
        # Calculate remaining battery percentage (estimation)
        if battery['capacity'] > 0:
            battery['remaining'] = max(0, min(100, 100 - (battery['mah_drawn'] * 100 / battery['capacity'])))
        else:
            # If capacity not configured, estimate from voltage
            # Assuming LiPo with 3.3V min and 4.2V max per cell
            if battery['cell_count'] > 0:
                voltage_per_cell = battery['voltage'] / battery['cell_count']
                battery['remaining'] = max(0, min(100, (voltage_per_cell - 3.3) * 100 / 0.9))
            else:
                battery['remaining'] = "Unknown"
        
        return battery

    def get_analog(self):
        # MSP_ANALOG = 110
        self.send_cmd(110)
        data = self.read_response(110)
        
        if data is None or len(data) < 7:
            print("Failed to get analog data")
            return None
            
        analog = {}
        # First byte is battery voltage in 0.1V steps
        analog['voltage'] = data[0] / 10.0  # Convert to volts
        
        # Next 2 bytes are mAh drawn
        analog['mah_drawn'] = data[1] + (data[2] << 8)
        
        # Next byte is RSSI (0-255)
        analog['rssi'] = data[3]
        
        # Next 2 bytes are amperage in 0.01A steps
        amperage_raw = data[4] + (data[5] << 8)
        analog['current'] = amperage_raw / 100.0  # Convert to amps
        
        return analog

# Test script
if __name__ == "__main__":
    # Change this to your actual serial port
    serial_port = "/dev/ttyACM0"
    
    try:
        print(f"Connecting to flight controller on {serial_port}...")
        msp = MSP(serial_port)
        
        print("\n--- CHECKING BATTERY STATUS ---")
        
        # First try the detailed battery state (newer Betaflight)
        battery = msp.get_battery_status()
        
        if battery:
            print("\nDetailed Battery Information:")
            print(f"Cell Count: {battery['cell_count']} cells")
            print(f"Capacity: {battery['capacity']} mAh")
            print(f"Voltage: {battery['voltage']:.2f}V")
            print(f"Current: {battery['current']:.2f}A")
            print(f"mAh Drawn: {battery['mah_drawn']} mAh")
            print(f"Battery Remaining: {battery['remaining']}" + 
                  ("%" if isinstance(battery['remaining'], (int, float)) else ""))
                  
            # Calculate estimated cell voltages
            if battery['cell_count'] > 0:
                voltage_per_cell = battery['voltage'] / battery['cell_count']
                print(f"Voltage per cell: {voltage_per_cell:.2f}V")
                
                # Battery health indicator
                if voltage_per_cell > 4.1:
                    print("Battery Status: FULL")
                elif voltage_per_cell > 3.7:
                    print("Battery Status: GOOD")
                elif voltage_per_cell > 3.5:
                    print("Battery Status: LOW")
                else:
                    print("Battery Status: CRITICAL - LAND IMMEDIATELY!")
            
        # Try also the basic analog info (works on all versions)
        analog = msp.get_analog()
        
        if analog:
            if not battery:  # Only show if detailed info not available
                print("\nBasic Battery Information:")
                print(f"Voltage: {analog['voltage']:.1f}V")
                print(f"Current: {analog['current']:.2f}A")
                print(f"mAh Drawn: {analog['mah_drawn']} mAh")
            
            # RSSI information
            rssi_percent = analog['rssi'] * 100 // 255
            print(f"\nReceiver Signal Strength (RSSI): {rssi_percent}%")
            
            if rssi_percent < 30:
                print("⚠️ WARNING: Signal strength is very low!")
            elif rssi_percent < 50:
                print("⚠️ Signal strength is moderate.")
            else:
                print("✅ Signal strength is good.")
        
        if not battery and not analog:
            print("❌ Could not retrieve battery information.")
            print("Make sure your battery is connected and voltage monitoring is configured in Betaflight.")
            
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Tips to fix:")
        print("- Check if the serial port is correct")
        print("- Make sure you have permissions (run: sudo usermod -a -G dialout $USER)")
        
    except Exception as e:
        print(f"Error: {e}")
