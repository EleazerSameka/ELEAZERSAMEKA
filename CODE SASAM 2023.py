import time
import requests
import math
import random
import RPi.GPIO as GPIO

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq7_dpin = 26
mq7_apin = 0
RELAY_PIN = 27

#port init
def init():
         GPIO.setwarnings(False)
         GPIO.cleanup()			#clean up at the end of your script
         GPIO.setmode(GPIO.BCM)		#to specify whilch pin numbering system
         # set up the SPI interface pins
         GPIO.setup(SPIMOSI, GPIO.OUT)
         GPIO.setup(SPIMISO, GPIO.IN)
         GPIO.setup(SPICLK, GPIO.OUT)
         GPIO.setup(SPICS, GPIO.OUT)
         GPIO.setup(mq7_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
         GPIO.setup(RELAY_PIN, GPIO.OUT)

#read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)	

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout
    
#main ioop
def utama():
        init()
        print("please wait...")
        time.sleep(3)
        COlevel=readadc(mq7_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
        kualitas_udara = ((COlevel/1024.)*5)
        kerapatan_udara = ((COlevel/2047)*100)
         
        if GPIO.input(mq7_dpin):
                           print("Udara Bersih")
                           print(GPIO.input(26))
                           GPIO.output(RELAY_PIN, GPIO.HIGH)
                           time.sleep(0.5)
        else:
                        print("Udara Kotor")
                        print(COlevel)
                        print("Nilai Kualitas Udara sekarang = " +str("%.2f"%((COlevel/1024.)*5))+" V")
                        print("Kerapatan Udara sekarang:" +str("%.2f"%((COlevel/2047)*100))+" %")
                        GPIO.output(RELAY_PIN, GPIO.LOW)
                        time.sleep(0.5)
        return kualitas_udara, kerapatan_udara
    
TOKEN = "BBFF-Lm4PqVq3vB0t3quol9D9ULglvubmhd"  # Put your TOKEN here
DEVICE_LABEL = "SASAM"  # Put your device label here 
VARIABLE_LABEL_1 = "KADAR ASAP"  # Put your first variable label here
VARIABLE_LABEL_2 = "KADAR GAS"  # Put your second variable label here


def build_payload(variable_1, variable_2):
    # Creates two random values for sending data
    kualitas_udara, kerapatan_udara = utama()
    value_1 = kerapatan_udara
    value_2 = kualitas_udara

    payload = {variable_1: value_1,
               variable_2: value_2,}
               

    return payload


def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

    # Makes the HTTP requests
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.post(url=url, headers=headers, json=payload)
        status = req.status_code
        attempts += 1
        time.sleep(1)

    # Processes results
    print(req.status_code, req.json())
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False

    print("[INFO] request made properly, your device is updated")
    return True


def main():
    payload = build_payload(
        VARIABLE_LABEL_1, VARIABLE_LABEL_2)

    print("[INFO] Attemping to send data")
    post_request(payload)
#     print("[INFO] finished")


if __name__ == '__main__':
    while (True):
        main()
        time.sleep(1)
        
GPIO.cleanup()