import time
import board
import adafruit_dht
import Adafruit_BMP.BMP085 as BMP085
import spidev                               #linux driver to access the SPI bus
import datetime
from w1thermsensor import W1ThermSensor

bmp180Sensor = BMP085.BMP085()
altReal = 1000

#open and configure the SPI bus
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1000000

""" This function calls on all the sensor functions and returns weather data.
Note: DHT22 data intentionally left out since sensor connection frequently dropping out. """

def getAllSensorData():
    
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    
#    dht_temp, dht_hum = run_dht22()
#    if dht_temp is None and dht_hum is None:
#        dht_temp = 0
#        dht_hum = 0         

    bmp_temp, bmp_pres, bmp_altLab, bmp_presSL = bmp180GetData()
    ds18b20_ext_temp = ds18b20GetData()
    
    uv_mV = readSensorUV()
    uv_index = indexCalculate(uv_mV)
    #dht_temp, dht_hum,
    
    return timeString,  bmp_temp, bmp_pres, bmp_altLab, bmp_presSL, ds18b20_ext_temp, uv_mV,uv_index                                                        


""" This function obtains the temperature and humidity data from DHT22 sensor. """
def run_dht22():
    dhtDevice = adafruit_dht.DHT22(board.D16)
    #while True:
        
        # Print the values to the serial port
    temperature_c = dhtDevice.temperature
    temperature_f = temperature_c * (9 / 5) + 32
    humidity = dhtDevice.humidity
    
    return temperature_c, humidity 

""" This function obtains external temperature from the DS19B20 temperature sensor.
    Note: make sure to enable the 1-Wire interface on the Raspberry Pi in order to communicate with
    this sensor.  """           
def ds18b20GetData():
    ds18b20Sensor = W1ThermSensor()
    
    tempExt = round(ds18b20Sensor.get_temperature(), 1)
    
    return tempExt

""" This function returns the temperature, altitude and barometric pressure from the BMP180 sensor
    Note: make sure to enable the I2C interface on the Raspberry Pi in order to communicate with
    this sensor. """
def bmp180GetData():
    temp = bmp180Sensor.read_temperature()
    pres = bmp180Sensor.read_pressure()
    alt =  bmp180Sensor.read_altitude()
    
    presSeaLevel = pres / pow(1.0 - alt/44330.0, 5.255)
    temp = round (temp, 1)
    pres = round (pres/100, 2)
    alt = round (alt)
    presSeaLevel = round (presSeaLevel/100, 2)
 
    return temp, pres, alt, presSeaLevel

""" This function outputs raw data being transmitted from the analog UV sensor to the Analog-to-Digital
    Converter (ADC) when the UV sensor is connected to the one of the ADC channels. An ADC is necessary
    since the Raspberry Pi cannot read any analog signals. """
def ReadChannel(channel):
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

""" This function runs the ReadChannel function three times in order to generate an average of the raw
    data sent by the UV sensor. The analog value is then converted to mV. """
def readSensorUV():
    numOfReadings = 3
    dataSensorUV = 0.0
    for i in range(numOfReadings):
        dataSensorUV += ReadChannel(0)
        time.sleep(0.2)
    dataSensorUV /= numOfReadings
    dataSensorUV = (dataSensorUV * (3.3 / 1023.0))*1000;
    return round(dataSensorUV)
           
""" This function checks the raw analog data average sent by the UV sensor, and compares it with the
    Vout (in mV) and UV index chart to output the corresponding UV index based on the Vout. """           
def indexCalculate(dataSensorUV):
    if dataSensorUV < 227: indexUV = 0
    elif (227 <= dataSensorUV) & (dataSensorUV < 318): indexUV = 1
    elif (318 <= dataSensorUV) & (dataSensorUV < 408): indexUV = 2
    elif (408 <= dataSensorUV) & (dataSensorUV < 503): indexUV = 3
    elif (503 <= dataSensorUV) & (dataSensorUV < 606): indexUV = 4
    elif (606 <= dataSensorUV) & (dataSensorUV < 696): indexUV = 5
    elif (696 <= dataSensorUV) & (dataSensorUV < 795): indexUV = 6
    elif (795 <= dataSensorUV) & (dataSensorUV < 881): indexUV = 7
    elif (881 <= dataSensorUV) & (dataSensorUV < 976): indexUV = 8
    elif (976 <= dataSensorUV) & (dataSensorUV < 1079): indexUV = 9
    elif (1079 <= dataSensorUV) & (dataSensorUV < 1170): indexUV =10
    else: indexUV = 11
    return indexUV

""" This piece of code is responsible for writing all the acquired data into a .csv file every 15 seconds. """
with open("/home/pi/rpi_weather_station.csv", "a") as f:
    while True:
        timing,  bmptemp, bmppres, bmpaltLab, bmppresSL, ds18b20ext_temp, uvmV, uvindex = getAllSensorData()
      
        f.write("{},{},{},{},{},{},{},{}\n".format(timing, bmptemp, bmppres, bmpaltLab, bmppresSL, ds18b20ext_temp, uvmV, uvindex))

        time.sleep(15)
        
