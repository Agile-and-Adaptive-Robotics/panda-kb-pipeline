/*
Uses the Timer library to generate a sine wave with a given amplitude, frequency, phase shift, and duration.
The sine wave is generated using the formula: f(t) = A * sin(ωt + φ), where:
- f(t) is the value of the sine wave at time t,
- A is the amplitude of the sine wave,
- ω is the angular frequency (2π times the frequency),
- φ is the phase shift of the sine wave,
- t is the time variable.
The sine wave is generated at a fixed interval (1ms) using an IntervalTimer object. The Interval timer library can
be found here: https://www.pjrc.com/teensy/td_timing_IntervalTimer.html
*/

#include "Oscillator.h"

Oscillator* Oscillator::instance = nullptr;

Oscillator::Oscillator(float amplitude, float frequency, float phase_shift, float duration)
    : amplitude(amplitude), frequency(frequency), phase_shift(phase_shift), duration(duration), running(false), spikeCallback(nullptr) {
    omega = 2 * PI * frequency;
    maxDT = 5e-3; // 5 milliseconds
    tLastSpike = 0;
}

void Oscillator::begin() {
    if (running) return;

    running = true;
    startTime = millis() / 1000.0; // Convert to seconds
    instance = this;
    timer.begin(onTimer, 1000); // Set timer to call onTimer every 1ms
}

void Oscillator::stop() {
    running = false;
    timer.end();
}

void Oscillator::setSpikeCallback(void (*callback)(int)) {
    spikeCallback = callback;
}

void Oscillator::onTimer() {
    if (!instance || !instance->running) return;

    float currentTime = millis() / 1000.0 - instance->startTime;
    if (instance->duration > 0 && currentTime > instance->duration) {
        instance->stop();
        return;
    }

    float fNow = instance->amplitude * sin(instance->omega * currentTime + instance->phase_shift);
    float currentDt = currentTime - instance->tLastSpike;

    if (currentDt > instance->maxDT) {
        float dtNow = abs(1 / fNow);

        if (currentDt > dtNow) {
            instance->tLastSpike = currentTime;
            if (instance->spikeCallback) {
                uint8_t neuronId = fNow > 0 ? 0 : 1;
                instance->spikeCallback(neuronId);
            }
        }
    }
}
