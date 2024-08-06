# Dummy-pipeline 2.0
This project is a new iteration of 1.0, but instead the major change is the implementation of host snips to bypass superhost (i.e. NxSDK python script) due to python's inability to handle real time tasks. Host snips are implemented in cpp and have much lower latency and better real time capabilities. 

### Dependencies
`lib-serial`