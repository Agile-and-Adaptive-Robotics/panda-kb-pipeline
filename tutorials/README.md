# Tutorials
When working with new or unfamiliar technology it is always best get a sense of the hardware and how it will work. In doing this my hope was to better understand the limitations and nuances of the Kapoho Bay Board. In a similar vein, my tutorial projects brought to light potential ways to setup the full pipeline and how the Loihi can communicate with the LattePanda in real-time, and how the LattePanda can communicate with peripheral Teensy's. **Any future contributors of the project should familiarize themselves with the NxSDK API and the Tutorials provided from Intel before work through these tutorials**. I found that the jupyter notebook tutorials in the NxSDK documentation were the best place to start. 

### Key Findings From These Tutorials
- [Very Important] Host snips will be the best way to communicate with the Loihi in real-time, see oscillator project for more detail
- UART communication between the LattePanda and Teensy seems to be the best option for three reasons: 1) Full duplex communication will offer the best throughput, and prevents the LattePanda from having to continuously poll for data or events from a Peripheral Teensy, 2) UART can run at high speeds of up to 1 Mbps, and 3) the Asynchronous nature allows for real-time responses. 
    - The difficult thing with UART is that it's a one to one connection so connecting four Teensy's will be a challenging task and will take some creativity wiring and software implementation. To that note, SPI communication might be a good thing to revisit. **At the time of writing this, the reason SPI was not used is because the Arduino Libraries do not allow for the Teensy's to be configured in Child Mode; this makes the SPI ports virtually useless for us because SPI requires there to be a single parent node, with possibly multiple children**


### Tutorial Directory
Click on folder/file to brought to the respective documentation on that project

| Folder/File    | Short Description  |  
|---------------|---------------|  
| led-blink | Contains setup instructions of the LattePanda and KB  |  
| `dummy-pipeline-1.0`  | Contains various notes and code bases for simple applications of the KB and LattePanda |
| `dummy-pipeline-2.0`   | Simple code exploring the functionality of the c++ library LibSerial  |
| `oscillator` |   |
| `cpp-serial-to-ino`| |
| `bursting_neuron` | Based on the Loihi implementation found in this paper: [link](https://dl.acm.org/doi/10.1145/3407197.3407205) |


## LED Blink <a name="led-blink"></a>