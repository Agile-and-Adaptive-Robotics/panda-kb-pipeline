#ifndef OSCILLATOR_H
#define OSCILLATOR_H

#include <Arduino.h>
#include <math.h>

class Oscillator {
public:
    Oscillator(float amplitude, float frequency, float phase_shift, float duration = -1);
    void begin();
    void stop();
    void setSpikeCallback(void (*callback)(int));

private:
    static void onTimer();
    static Oscillator* instance;

    float amplitude;
    float frequency;
    float phase_shift;
    float duration;
    float omega;
    float maxDT;
    float startTime;
    float tLastSpike;
    bool running;
    void (*spikeCallback)(int);

    IntervalTimer timer;
};

#endif // OSCILLATOR_H
