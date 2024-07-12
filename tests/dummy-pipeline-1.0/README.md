# Dummy Pipeline 1.0:
This project is dedicated to setting up the basic framework on how our hardware devices will talk to each other 
- Eventually the quadruped will be setup with this data pipeline: **Potentiometer** --->**Teensy** ---[SPI]---> **Panda** ---[USB]---> **Loihi (KB)** 
- In future iterations we will be using biofeedback sensors in place of the potentiometer. We have a student working on a strain gauge sensor from Liquid Wire that is supposed to provide us real-time length sensing. This iteraiton omits any "real" sensory feedback and uses a potentiometer reading to emulate this piece of the pipeline.

## Design Steps: 
1. Setup Teensy Board to read potentiometer readings
2. Create UART connection between Teensy & Panda Board
3. Define Loihi Network
4. Create Host SNIPs on Loihi for Data Exchange between Panda and KB

# 1. Setting up Teensy Board: 
The following Pin will be used for UART Communication
- **Pin 0** = RX (Receive)
- **Pin 1** = TX (Transmit)
- The Teensy website has a few more control pins for flow control, [See Here](https://www.pjrc.com/teensy/td_uart.html)

# 2. Create UART Connection between Teensy & Panda Board
### Encoding Ideas
- We will need a rate encoding scheme (i.e. frequency)
- A latency encoding scheme (i.e. spike timing)
- Delta modulation uses the temporal change of input feature to generate spikes??? Not sure what this means

See this article for spike encoding [SNNTorch](https://snntorch.readthedocs.io/en/latest/tutorials/tutorial_1.html)

### UART Communication Considerations:
- At this time, I'm using a one to one point communication via UART. Of course, this poses issues since we have four Teensy boards that need to communicate with the LattePanda. Future iterations will need to consider using the Arduino Library `SoftwareSerial.h`. The software implementation introduces more latency, and we might need to consider I2C. 

### Comparison of I2C and UART
- Below are the considerations of both the LattePanda and Teensy and how they would work together

**Trade offs**  
For Real-Time Applications:
   -  UART is generally better for real-time applications that require low latency, simplicity, and point-to-point communication. It is more deterministic and has less overhead, making it suitable for applications where quick and reliable data transfer between two devices is critical.
   -  I2C can be used in real-time applications where multiple devices need to communicate on the same bus, but it requires careful management of bus contention and potential latency issues. It is less suited for high-speed real-time communication due to its inherent complexities and potential for higher latency.

**I2C**  
- Teensy 4.1 supports up to 1000 kbits/sec
- The LattePanda's ATmega32u4 MCU only supports speeds up to 400 kbits/sec
- Half Duplex which greatly reduces throughput

**UART**
- Full Duplex and generally better for lower latency point to point communication
- Both device say they support high speed  baud rates, but don't specify a maximum. 
 - Generally, high speed rates are considered to be 230400, 460800, and 921600 bps. 
- UART is generally for point-to-point communication but it could be designed in software to support a sort of daisy chain configuration so that we can connect all four teensys on a single bus. The issue is that the LattePanda only has one UART port. 


### Programming Arduino on Latte Panda
- See /dummy-pipeline-1.0/panda-uart/panda-uart.ino for more details
- If you code a program that continuously run the device/ resource will be busy and you cannot upload a new sketch. Run the following command to get the PID associated with this process, then kill it: 
```bash
sudo fuser /dev/ttyACM0 
#output should be something like this
/dev/ttyaCM0:           12439

#kill process
sudo kill -9 12439
```
- To see the current baud rate of the panda -> leondardo connection:
```bash
sudo stty -F /dev/ttyACM0
# to update or change baud rate
stty -F /dev/ttyACM0
```
# 3. Define Loihi Network
`TODO`: Need to create an Oscillator Network

# 4. Programming SNIPs
- In the test program `/tests/oscillator` I quickly realized the limitations of using SpikeGenerator and Receivers- they aren't appropriate for real time performance. The reason I used them was to keep things simple and get myself working with the KB API as much as possible. In this section I will discuss steps I took and general findings on programming the SNIPs. 
- Within this dummy pipeline, I implement encoder and decoder in seperate threads using pythons threading library. This allows the two to execute in parallel. It's important that the two are in seperate and asynchronous threads as the communication channels and the SNIPs they interface with are asynchronous. Additionally, calls to read and write from from channels are blocking so it's important to handle each seperately to avoid deadlock and slowing down either process. 

### Below are some notes on [Combra Lab's] Implementation using Loihi as a controller
