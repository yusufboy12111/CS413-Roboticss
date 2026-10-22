import os
import time


WHEELS = [
    {"wheel_id": 1, "motor_port": "M3", "encoder_port": "E3"},
    {"wheel_id": 2, "motor_port": "M4", "encoder_port": "E4"},
]
RUN_TIME = 2.0
SAMPLE_PERIOD = 0.005
RESET_SETTLE_TIME = 0.5
REST_TIME = 1.0
DATA_DIR = "Yusufboy_motor_data"
LEVELS = list(range(-100, 0, 5)) + list(range(5, 101, 5))


def record_step(motor_port, encoder_port, power):
    encoder = brick.encoder(encoder_port)
    motor = brick.motor(motor_port)

    encoder.reset()
    time.sleep(RESET_SETTLE_TIME)

    samples = []
    start_time = time.time()
    motor.setPower(power)
    while True:
        elapsed = time.time() - start_time
        if elapsed > RUN_TIME:
            break
        samples.append((encoder.read(), int(elapsed * 1000)))
        time.sleep(SAMPLE_PERIOD)

    motor.powerOff()
    return samples


def save_step(wheel_id, power, battery_voltage, samples):
    path = os.path.join(
        DATA_DIR, "wheel_%d_v_%d.txt" % (wheel_id, power)
    )
    with open(path, "w") as output:
        output.write("# wheel_id: %d\n" % wheel_id)
        output.write("# voltage_percent: %d\n" % power)
        output.write("# battery_voltage_v: %s\n" % battery_voltage)
        output.write("# format: position_deg time_ms\n")
        for position, time_ms in samples:
            output.write("%s %d\n" % (position, time_ms))


def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    battery_voltage = brick.battery().readVoltage()
    for wheel in WHEELS:
        wheel_id = wheel["wheel_id"]
        battery_path = os.path.join(
            DATA_DIR, "wheel_%d_battery.txt" % wheel_id
        )
        with open(battery_path, "w") as output:
            output.write("battery_voltage_v: %s\n" % battery_voltage)

        print("Wheel %d, battery %.3f V" % (wheel_id, battery_voltage))
        for power in LEVELS:
            print("Wheel %d: testing PWM %d%%" % (wheel_id, power))
            samples = record_step(
                wheel["motor_port"], wheel["encoder_port"], power
            )
            save_step(wheel_id, power, battery_voltage, samples)
            time.sleep(REST_TIME)

    brick.stop()


if __name__ == "__main__":
    main()
