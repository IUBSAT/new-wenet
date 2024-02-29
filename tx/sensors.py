# Written by Annabel Brinker

import time
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

def read_bme680():
    bme.set_humidity_oversample(bme680.OS_2X)

    bme.set_pressure_oversample(bme680.OS_4X)
    bme.set_temperature_oversample(bme680.OS_8X) 
    bme.set_filter(bme680.FILTER_SIZE_3)
    bme.set_gas_status(bme680.ENABLE_GAS_MEAS) 
    bme.set_gas_heater_temperature(320) 
    bme.set_gas_heater_duration(150)  

     
    temperature = bme.data.temperature
    pressure = bme.data.pressure
    humidity = bme.data.humidity
    gas = bme.data.gas_resistance 
    return temperature, pressure, gas, humidity

def altitude():
    temperature, pressure, gas, humidity = read_bme680()
    SeaPress = pressure / ((1 - (804/44330))**5.255)
    altitude = 44330*(1 - (pressure / SeaPress))**(1/5.255)
    print("this is altitude: ") 
    print(altitude)
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
    altitude() 
    SenFile = open("SensorData.txt", "a")
    seconds = time.time() 
    temperature, pressure, gas, humidity = read_bme680()
    accel_x, accel_y, accel_z = read_lsm303agr()
    print("epoch time: ", seconds)
    message = [f"\nNEW TRANSMIT, {seconds}\n"] 
    SenFile.writelines(message)

    lines = [f"Temp: {temperature:.2f} C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%, Gas: {gas:0} Ohms \nAccelX: {accel_x}, AccelY: {accel_y}, AccelZ: {accel_z}\n"]
    SenFile.writelines(lines)   

    print(f"Temperature: {temperature:.2f}°C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%, Gas: {gas:0} Ohms")
    print(f"Acceleration - X: {accel_x}, Y: {accel_y}, Z: {accel_z}")

    SenFile.close()




def main():
    SensCall()

 
if __name__ == "__main__":
    main()