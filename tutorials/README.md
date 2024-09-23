# Tutorials
When working with new or unfamiliar technology it is always best to get a sense of the hardware and how it will work. In doing these tutorial projects my hope was to better understand the limitations and nuances of the Kapoho Bay Board. In a similar vein, my tutorial projects brought to light potential ways to set up the full pipeline and how the Loihi can communicate with the LattePanda in real-time, and how the LattePanda can communicate with peripheral Teensy's. **Any future contributors of the project should familiarize themselves with the NxSDK API and the Tutorials provided from Intel before work through these tutorials**. I found that the jupyter notebook tutorials in the NxSDK documentation were the best place to start. 

### Key Findings From These Tutorials
- [Very Important] Host snips will be the best way to communicate with the Loihi in real-time, see `oscillator/` project for more detail
- UART communication between the LattePanda and Teensy seems to be the best option for three reasons: 1) Full duplex communication will offer the best throughput, and prevents the LattePanda from having to continuously poll for data or events from a Peripheral Teensy, 2) UART can run at high speeds of up to 1 Mbps, and 3) the Asynchronous nature allows for real-time responses. 
    - The difficult thing with UART is that it's a one to one connection so connecting four Teensy's will be a challenging task and will take some creative wiring and software implementation. To that note, SPI communication might be a good thing to revisit. **At the time of writing this, the reason SPI was not used is because the Arduino Libraries do not allow for the Teensy's to be configured in Child Mode; this makes the SPI ports virtually useless for us because SPI requires there to be a single parent node, with possibly multiple children.**


### Tutorial Directory
Click on folder/file to be brought to the respective documentation on that project

| Folder/File | |
|-------------|-------------------|
| [led-blink](#led-blink) |  |
| [dummy-pipeline-1.0](#dummy-1) | Contains various notes and code bases for simple applications of the KB and LattePanda |
| [dummy-pipeline-2.0](#dummy-2) | Simple code exploring the functionality of the c++ library LibSerial |
| [oscillator](#oscillator) | |
| [cpp-serial-to-ino](#cpp-serial) | |
| [bursting_neuron](#bursting-neuron) | Based on the Loihi implementation found in this paper: [link](https://dl.acm.org/doi/10.1145/3407197.3407205) |

# Tutorial Project Descriptions and Documentation

## LED Blink<a name="led-blink"></a>
The infamous LED blink program is a great place to start when getting a handle of new hardware. In this tutorial, I connected an LED to the lattePanda's `D13` arduino pin and blinked it whenever a spike was received from the Loihi. Spikes were read by using embedded snips. Lastly the arduino (i.e. ATMega Coprocessor-> [Documentation](http://docs.lattepanda.com/content/3rd_delta_edition/specification/)) is accessed using the PinPong Library. I found this library to be lacking in functionality and tutorials so I ditched it to other methods found in `dummy-pipeline-1.0/2.0`. 

### Dummy Pipeline 1.0<a name="dummy-1"></a>
Simple UART datapipeline with a simulated oscillator to respresent a form of sensory feedback. In a practical setup, this would emulate a biofeedback sensor but this was beyond my expertise at the time of writing this program. 
- See `README.md` found in `dummy-pipeline-1.0/` directory for a summary of finding from this setup

### Dummy Pipeline 2.0<a name="dummy-2"></a>
This project is a new iteration of 1.0, but instead the major change is the implementation of host snips to bypass superhost (i.e. NxSDK python script) due to python's inability to handle real time tasks. Host snips are implemented in cpp and have much lower latency and better real time capabilities. This pipeline also implements an LED blinking to signal activations of Neuron 1 or Neuron 2. 

### Oscillator<a name="oscillator"></a>
Oscillator program utilizes a sine wave generator program to stimulate Loihi compartments.

### CPP Serial to INO<a name="cpp-serial"></a>
This is a small project that was created to perform some simple performance testing of the c++ lib serial library and the speed of the internal serial bus that connect the core process with the sub-processor (arduino).
- See `README.md` foud in `cpp-serial-to-ino` directory for more details

### Bursting Neuron<a name="bursting-neuron"></a>
[Your content for Bursting Neuron project goes here] TODO: 
