"""
Import Libraries
"""
import time
import struct
import serial
from serial.tools import list_ports

arduino_serial = None

# Search for Arduino and establish a serial connection
def search_for_arduino():
    """
    Search for arduino when making serial connection
    """
    available_ports = [port.device for port in list_ports.comports()]
    # print("Available COM ports:")
    for port in reversed(available_ports):
        try:
            # print(port)
            ser = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)
            ser.write(b"?")
            response = ser.readline().strip()

            if response == b"BJI_Hello There!":
                return ser

        except serial.SerialException as e:
            arduino_serial.close()
            raise serial.SerialException("")

    return None

def disconnect_arduino():
    """
    Disconnect Arduino
    """
    global arduino_serial
    if arduino_serial:
        arduino_serial.close()
        arduino_serial = None
        print("Arduino disconnected successfully")

def get_device_status():
    """
    Fetch Arduino"s status while connecting
    """
    global arduino_serial
    arduino_serial = search_for_arduino()
    if arduino_serial is not None:
        try:
            arduino_serial.write(b"!")
            response = arduino_serial.readline().strip()
            print("Received data: ", response)
            return response
        except Exception as e:
            print(f"Error getting status: {e}")
            raise serial.SerialException()
    else:
        raise ConnectionError("Arduino device not found.")

def initialize_arduino(epoch_time):
    """
    Initialize Arduino based on the specified time

    epoch_time: specified time (Datetime)
    """
    global arduino_serial

    # Send initialization command to Arduino
    if epoch_time and arduino_serial:
        try:
            arduino_serial.write(b"i")
            print(arduino_serial.readline())
            packed_data = struct.pack("<Q", epoch_time)
            arduino_serial.write(packed_data)
        except serial.SerialException as e:
            arduino_serial.close()
            print(e)
            raise serial.SerialException()
    else:
        raise ValueError("Time was not specified or Arduino is not connected.")

    arduino_serial.close()

def download_file(file_path, get_readable=False):
    """
    Download the stored data from Arduino

    file_path: location to store the data file
    get_readable: download .RAW or .CSV format (boolean)
    """
    global arduino_serial
    
    try:
        with open(file_path, "wb") as file:
            # Send "r" to the Arduino to initiate readable file transfer, or "t" for binary.
            if get_readable == True:
                arduino_serial.write(b"r")
            else:
                arduino_serial.write(b"t")
            end_data_marker = b"BJI_END_DATA"
            marker_position = 0  # Tracks the position within the end data marker

            # Wait for data to become available
            while arduino_serial.in_waiting == 0:
                pass

            data_buffer = bytearray()  # Buffer to store data
            data_in_buffer = False

            # Continuously read the data until the end marker is found
            while True:
                if arduino_serial.in_waiting > 0:
                    data = arduino_serial.read(1024)
                    print(f"Received data: {data}")
                    for byte in data:
                        # Check for the end of marker sequence
                        if byte == end_data_marker[marker_position]:
                            data_buffer.append(byte)
                            data_in_buffer = True
                            marker_position += 1
                            if marker_position == len(end_data_marker):
                                break
                        else:
                            marker_position = 0
                            if data_in_buffer:
                                file.write(data_buffer)
                                data_in_buffer = False
                                data_buffer.clear()
                            file.write(bytes([byte]))

                    if marker_position == len(end_data_marker):
                        break

        file.close()
        print("File downloaded successfully!")

    except Exception as e:
        print(f"Error downloading file: {e}")
        raise ConnectionError()
