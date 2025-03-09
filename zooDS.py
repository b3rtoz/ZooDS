import can
import isotp
import time
import threading

import tester_present
import key_crack
import read_response


def main():
    # 1. Ask for the socket-CAN interface (e.g., can0, vcan0)
    interface = input("Enter CAN interface (e.g., can0, vcan0): ")
    try:
        bus = can.interface.Bus(channel=interface, interface='socketcan')
    except Exception as e:
        print(f"Error opening interface {interface}: {e}")
        return

    # 2. Attempt functional broadcast for Tester Present using both 11-bit and 29-bit IDs.
    tester_present.try_functional_broadcast(bus)

    # 3. Ask for tester (local) and ECU (destination) arbitration IDs.
    tester_id_input = input("Enter Tester (source) id: ")
    ecu_id_input = input("Enter ECU (destination) id: ")
    try:
        tester_arbitration_id = int(tester_id_input, 16)
        ecu_arbitration_id = int(ecu_id_input, 16)
    except ValueError:
        print("Invalid arbitration id input.")
        return

    # 4. Create an ISO-TP stack with the provided addressing for multi-frame support.
    address = isotp.Address(isotp.AddressingMode.Normal_11bits,
                            txid=tester_arbitration_id,
                            rxid=ecu_arbitration_id)
    stack = isotp.CanStack(bus=bus, address=address, params={'stmin': 0, 'blocksize': 8})
    print(f"ISO-TP stack created with Tester ID {hex(tester_arbitration_id)} and ECU ID {hex(ecu_arbitration_id)}.")

    # 5. Loop to send UDS service requests and receive responses.
    while True:
        service_hex = input("Enter UDS service in hex (or type 'exit' to quit): ")
        if service_hex.lower() == "exit":
            bus.shutdown()
            stop_event.set()
            bg_tp.join()
            print("CAN bus shut down.")
            print("Exiting.")
            break
        try:
            service_bytes = bytes.fromhex(service_hex)
        except ValueError:
            print("Invalid hex input. Please try again.")
            continue

        print(f"Sending UDS service {service_hex}...")
        stack.send(service_bytes)

        # wait for responses with a timeout that resets after each received frame.
        timeout_gap = 1.0  # seconds to wait after the last received frame
        last_frame_time = time.time()
        responses = []
        while True:
            stack.process()
            if stack.available():
                response_data = stack.recv()
                responses.append(response_data)
                print(f"Response:", ecu_arbitration_id, ' ', response_data.hex(' '))
                last_frame_time = time.time()  # reset timeout on each new frame
            if time.time() - last_frame_time > timeout_gap:
                break
            time.sleep(0.01)
        if responses:
            print("Complete UDS response(s):")
            for resp in responses:
                print(ecu_arbitration_id, " ", resp.hex(' '))
        else:
            print("No UDS response received within timeout.")

        # if the service request was "27 01", process the response to save the seed.
        # UDS positive response for 27 01 should be "67 01 <seed...>"
        if service_hex.replace(" ", "").lower() == "2701" and responses:
            complete_response = responses[0]
            if len(complete_response) > 2:
                # the seed is all bytes after the positive response "xx 67 01".
                seed = complete_response[2:]
                key_crack.xor_key(seed, stack)

        # if the service request was non-default session (10 02, or 10 03)
        if service_hex.replace(" ", "").lower() == "1003" or "1002" and responses:
            complete_response = responses[0]
            if read_response.is_negative_response(complete_response):
                continue
            else:
                # the seed is all bytes after the positive response "xx 67 01".
                # Start the background tester present thread.
                stop_event = threading.Event()
                bg_tp = threading.Thread(target=tester_present.background_tester_present(bus, stop_event), daemon=True)
                bg_tp.start()


if __name__ == '__main__':
    main()
