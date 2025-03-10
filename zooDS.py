import can
import isotp
import time
import fnmatch
import threading

import tester_present
import key_crack
import read_response


def print_ascii_art(filename):
    try:
        with open(filename, 'r') as file:
            for line in file:
                print(line, end='')  # Print each line without adding extra newlines
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    print_ascii_art("monkey-art.txt")

    # 1. Ask for the socket-CAN interface (e.g., can0, vcan0)
    interface = input("\nEnter CAN interface (e.g., can0, vcan0): ")
    try:
        bus = can.interface.Bus(channel=interface, interface='socketcan')
    except Exception as e:
        print(f"Error opening interface {interface}: {e}")
        return

    # Ask user for tester ID discovery choice
    discover_id = input("attempt to discover valid tester ID? (y/n):")
    if discover_id.lower().startswith('y'):
        # Attempt functional broadcast for Tester Present using both 11-bit and 29-bit IDs.
        tester_present.try_functional_broadcast(bus)
    # Ask user for tester (source) and ECU (destination) arbitration IDs.
    tester_id_input = input("Enter Tester (source) id: ")
    ecu_id_input = input("Enter target ECU (destination) id: ")

    try:
        tester_arbitration_id = int(tester_id_input, 16)
        ecu_arbitration_id = int(ecu_id_input, 16)
    except ValueError:
        print("\ninvalid id format.")
        return

    # Create an ISO-TP stack with the provided addressing.
    address = isotp.Address(isotp.AddressingMode.Normal_11bits,
                            txid=tester_arbitration_id,
                            rxid=ecu_arbitration_id)
    stack = isotp.CanStack(bus=bus, address=address, params={'stmin': 0, 'blocksize': 8})
    print(f"    ISO-TP stack created with Tester ID {hex(tester_arbitration_id)} and ECU ID {hex(ecu_arbitration_id)}.")

    # Loop to send UDS service requests and receive responses.
    while True:
        service_hex = input("\nEnter UDS service in hex (or type 'exit' to quit): ")
        if service_hex.lower() == "exit":
            bus.shutdown()
            # stop_event.set()
            # bg_tp.join()
            break
        try:
            service_bytes = bytes.fromhex(service_hex)
        except ValueError:
            print("Invalid hex input. Please try again.")
            continue

        print(f"Sending UDS service {service_hex}...\n")
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
                last_frame_time = time.time()  # reset timeout on each new frame
            if time.time() - last_frame_time > timeout_gap:
                break
            time.sleep(0.01)
        if responses:
            for resp in responses:
                print(f"    {read_response.process_ecu_response(resp)}")
                print(f"    ECU ID:{hex(ecu_arbitration_id)}  Response data:{resp.hex(' ')}\n")
        else:
            print("     No UDS response received within timeout.")

        # if the service request was "27 01", process the response to save the seed.
        # UDS positive response for 27 01 should be "67 01 <seed...>"
        if service_hex.replace(" ", "").lower() == "27??" and responses:
            complete_response = responses[0]
            result = read_response.process_ecu_response(complete_response)
            print(f"    {read_response.process_ecu_response(complete_response)}")
            if len(complete_response) > 2:
                # the seed is all bytes after the positive response "67 01".
                seed = complete_response[2:]
                print(f"      {seed.hex(' ')}")
                try_crack = input("Attempt to crack Security Access key? (y/n):")
                if try_crack.lower().startswith('y'):
                    # single byte xor crack for BH User Space Diagnostics Terminal
                    key_crack.xor_key(seed, stack)
        """
        # This section is in development...
         
        # if the service request was non-default session (10 02, or 10 03)
        non_default = ["1002", "1003"]
        # and the ECU replies with a positive response, start sending cyclic tester present to keep session active
        if service_hex.replace(" ", "").lower() in non_default and responses:
            complete_response = responses[0]
            if read_response.is_negative_response(complete_response):
                continue
            else:
                # Start the background tester present thread.
                stop_event = threading.Event()
                bg_tp = threading.Thread(target=tester_present.background_tester_present(bus, tester_arbitration_id,
                                                                                         stop_event), daemon=True)
                bg_tp.start()
        """


if __name__ == '__main__':
    main()
