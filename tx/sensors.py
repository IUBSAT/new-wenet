# Written by Annabel Brinker and Lucas Snyder

import time
from datetime import datetime, timezone
import csv, os
import smbus2
import bme680
import math

# LSM303AGR registers
LSM303AGR_ADDR = 0x19  # I2C address for LSM303AGR
LSM303AGR_REG_ACCEL_X_LSB = 0x28
LSM303AGR_REG_ACCEL_X_MSB = 0x29
LSM303AGR_REG_ACCEL_Y_LSB = 0x2A
LSM303AGR_REG_ACCEL_Y_MSB = 0x2B
LSM303AGR_REG_ACCEL_Z_LSB = 0x2C
LSM303AGR_REG_ACCEL_Z_MSB = 0x2D

# BME680 setup
bme = bme680.BME680(0x77)

# LSM303AGR setup
bus = smbus2.SMBus(1)  # Use bus 1 for Raspberry Pi
bus.write_byte_data(LSM303AGR_ADDR, 0x20, 0x27)  # Enable accelerometer, set to normal mode

def bme_is_alive():
    return bme.get_sensor_data()


def read_bme680():
    bme.set_humidity_oversample(bme680.OS_2X)

    bme.set_pressure_oversample(bme680.OS_4X)
    bme.set_temperature_oversample(bme680.OS_8X) 
    bme.set_filter(bme680.FILTER_SIZE_3)
    bme.set_gas_status(bme680.ENABLE_GAS_MEAS) 
    bme.set_gas_heater_temperature(320) 
    bme.set_gas_heater_duration(150)  

    if bme.get_sensor_data():
        temperature = bme.data.temperature
        pressure = bme.data.pressure
        humidity = bme.data.humidity
        gas = bme.data.gas_resistance
    else:
        temperature = 0
        pressure = 0
        humidity = 0
        gas = 0
    return temperature, pressure, gas, humidity

def altitude():
    temperature, pressure, gas, humidity = read_bme680()
    SeaPress = pressure / ((1 - (243/44330))**5.255)
    altitude = int( 44330*(1 - ((pressure / SeaPress)**(1/5.255))) )
    #print("this is altitude: ") 
    #print(altitude)
    #print("\n") 
    return altitude, temperature, pressure, gas, humidity

def read_lsm303agr():
    def read_signed_data(register):
        low_byte = bus.read_byte_data(LSM303AGR_ADDR, register)
        high_byte = bus.read_byte_data(LSM303AGR_ADDR, register + 1)
        value = (high_byte << 8) | low_byte
        return value if value < 32768 else value - 65536

    accel_x = read_signed_data(LSM303AGR_REG_ACCEL_X_LSB)
    accel_y = read_signed_data(LSM303AGR_REG_ACCEL_Y_LSB)
    accel_z = read_signed_data(LSM303AGR_REG_ACCEL_Z_LSB)
    return accel_x, accel_y, accel_z

def SensCall():
    SenFile = open("SensorData.txt", "a")
    seconds = time.time() 
    alt, temperature, pressure, gas, humidity = altitude()
    accel_x, accel_y, accel_z = read_lsm303agr()
    #alt = altitude()
    print("epoch time: ", seconds)
    message = [f"\nNEW TRANSMIT, {seconds}\n"] 
    SenFile.writelines(message)

    lines = [f"Time: {seconds}, Alt: {int(alt)}, Temp: {temperature:.2f} C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%, Gas: {gas:0} Ohms \nAccelX: {accel_x}, AccelY: {accel_y}, AccelZ: {accel_z}\n"]
    SenFile.writelines(lines)   

    print(f"Temperature: {temperature:.2f}°C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%, Gas: {gas:0} Ohms")
    print(f"Acceleration - X: {accel_x}, Y: {accel_y}, Z: {accel_z}")

    SenFile.close()

def SensCall2(filename):
    try:
        with open(filename, "a", newline='') as SenFile:
            #seconds = time.time()
            is_file_empty = os.stat(filename).st_size == 0
            csv_writer = csv.writer(SenFile, lineterminator=os.linesep)

            #Write headers if the file is empty
            if is_file_empty:
                csv_writer.writerow(["Timestamp", "Altitude", "Temperature", "Pressure", "Humidity", "Gas", "AccelX", "AccelY", "AccelZ"])

            timestamp = datetime.now(timezone.utc)
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            alt, temperature, pressure, gas, humidity = altitude()
            accel_x, accel_y, accel_z = read_lsm303agr()
            
            print("Time: ", timestamp_str)
            print(f"Alt: {alt}, Temperature: {temperature:.2f}°C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%, Gas: {gas:0} Ohms")
            print(f"Acceleration - X: {accel_x}, Y: {accel_y}, Z: {accel_z}")
            # message = [f"\nNEW TRANSMIT, {timestamp_str}\n"] 
            # SenFile.writelines(message)

            # lines = [f"Time: {timestamp_str}, Alt: {alt}, Temp: {temperature:.2f} C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%, Gas: {gas:0} Ohms \nAccelX: {accel_x}, AccelY: {accel_y}, AccelZ: {accel_z}\n"]
            # SenFile.writelines(lines)   
            csv_writer.writerow([timestamp_str, alt, temperature, pressure, humidity, gas, accel_x, accel_y, accel_z])

            SenFile.flush()  # Ensure data is written to the file immediately
    except KeyboardInterrupt:
        return 1


def main():
    SensCall()

 
if __name__ == "__main__":
    main()