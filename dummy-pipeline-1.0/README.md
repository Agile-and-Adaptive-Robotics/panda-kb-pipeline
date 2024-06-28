# Dummy Pipeline 1.0:
This project is dedicated to setting up the basic framework on how our hardware devices will talk to each other 
- Eventually the quadruped will be setup with this data pipeline: **Potentiometer** --->**Teensy** ---[SPI]---> **Panda** ---[USB]---> **Loihi (KB)** 
- In future iterations we will be using biofeedback sensors in place of the potentiometer. We have a student working on a strain gauge sensor from Liquid Wire that is supposed to provide us real-time length sensing. This iteraiton omits any "real" sensory feedback and uses a potentiometer reading to emulate this piece of the pipeline.

## Design Steps: 
1. Setup Teensy Board to read potentiometer readings
2. Create SPI connection between Teensy & Panda Board
3. Define Loihi Network
4. Create Host SNIPs on Loihi for Data Exchange between Panda and KB

# 1. Setting up Teensy Board: 
The following Pin will be used for SPI Communication
- **Pin 10** = CS (Chip Select)
- **Pin 11** = MOSI (Main Out, Sub In): Serial Data from master, most significant bit first
- **Pin 12** = MISO (Main In, Sub Out): Serial Data from subscriber, most significant bit first
- **Pin 13** = SCLK (Serial Clock)


# 2. Create SPI Connection between Teensy & Panda Board
### Encoding Ideas
- We will need a rate encoding scheme (i.e. frequency)
- A latency encoding scheme (i.e. spike timing)
- Delta modulation uses the temporal change of input feature to generate spikes??? Not sure what this means

See this article for spike encoding [SNNTorch](https://snntorch.readthedocs.io/en/latest/tutorials/tutorial_1.html)

### Notes on SPI Communications: 
- **SPI Library Does NOT support Peripheral configuration for the Teensy's or any Arduino for that matter**
    - The work around would be to write our own driver for the on board SPI controller. The SoC datasheet can be found here if you decide to go that route -> [NXP i.MX RT 1060 MCU](https://www.nxp.com/products/processors-and-microcontrollers/arm-microcontrollers/i-mx-rt-crossover-mcus/i-mx-rt1060-crossover-mcu-with-arm-cortex-m7:i.MX-RT1060)

- The other option would be to decide on a different serial protocol that is easier to program given the current Arduino Libraries, see a comparison of I2C and UART below. 

### Comparison of I2C and UART
- Below are the considerations of both the LattePanda and Teensy and how they would work together

**Summary of the two's trade offs**  
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