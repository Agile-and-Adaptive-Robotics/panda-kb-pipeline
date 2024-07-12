def encoder_thread(encoderChannel, num_steps):
    curr_neuron = 0
    for step in range(num_steps):
        encoderChannel.write(1, [curr_neuron])
        curr_neuron = 1 - curr_neuron  # toggle between neuron 0 and neuron 1

def decoder_thread(decoderChannel, stop_event):
    while not stop_event.is_set():
         if(decoderChannel.probe()):
            data = decoderChannel.read(2)
            #print(f"Received from decoder, [synapse Id, time of spike]: {data}")

