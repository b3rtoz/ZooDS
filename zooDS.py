import can
import isotp
import time

import did_scan
import mem_scan
import rid_scan
import tester_present
import key_crack
import read_response


def print_logo_art(filename):
    """Prints ASCII logo art"""
    try:
        with open(filename, 'r') as file:
            print(file.read(), end='')
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_hex_input(prompt):
    """Prompts user for a hex input and returns integer value."""
    user_input = input(prompt)
    try:
        return int(user_input, 16)
    except ValueError:
        print("Invalid hex format.")
        return None


def create_iso_tp_stack(bus, tester_id, ecu_id, id_mode="11", stmin=0, blocksize=8):
    """
    Creates and returns ISO-TP stack for the provided tester and ECU IDs.

    Args:
        bus: The CAN bus instance.
        tester_id: The tester (source) ID as an integer.
        ecu_id: The target ECU (destination) ID as an integer.
        id_mode: "11" for 11-bit identifiers or "29" for 29-bit identifiers.
        stmin: Separation time minimum (default 0).
        blocksize: Block size for ISO-TP (default 8).

    Returns:
        An isotp.CanStack instance.
    """
    if id_mode == "11":
        addressing_mode = isotp.AddressingMode.Normal_11bits
    elif id_mode == "29":
        addressing_mode = isotp.AddressingMode.Normal_29bits
    else:
        print("Invalid identifier mode, defaulting to 11-bit")
        addressing_mode = isotp.AddressingMode.Normal_11bits

    address = isotp.Address(addressing_mode,
                            txid=tester_id,
                            rxid=ecu_id)
    return isotp.CanStack(bus=bus, address=address, params={'stmin': stmin, 'blocksize': blocksize})


def send_and_receive(stack, service_bytes, timeout_gap=1.0):
    """
    Sends UDS service bytes via the ISO-TP stack and collects responses until timeout.

    Args:
        stack: The isotp.CanStack instance.
        service_bytes: The bytes to send.
        timeout_gap: Time in seconds to wait after the last received frame.

    Returns:
        List of response byte sequences.
    """
    stack.send(service_bytes)
    responses = []
    last_frame_time = time.time()
    while True:
        stack.process()
        if stack.available():
            responses.append(stack.recv())
            last_frame_time = time.time()  # Reset timeout after each received frame
        if time.time() - last_frame_time > timeout_gap:
            break
        time.sleep(0.01)
    return responses


def handle_security_access(service_bytes, responses, stack):
    """
    Handles Security Access responses (service 0x27). If the ECU returns a positive response,
    extracts the seed and optionally attempts to crack the key.
    """
    complete_response = responses[0]
    result = read_response.process_ecu_response(complete_response)
    if result.startswith("P"):
        # Assuming the positive response code "67 01", the seed follows after the first two bytes.
        seed = complete_response[2:]
        print(f"    Seed: {seed.hex(' ')}")
        if input("Attempt to crack Security Access key? (y/n): ").strip().lower().startswith('y'):
            # Prepare key request by incrementing the second byte modulo 256
            # (if 2701 seed request, then 2702 key request per iso-14229).
            ser_byte_array = bytearray(service_bytes)
            ser_byte_array[1] = (ser_byte_array[1] + 1) % 256
            key_send_bytes = bytes(ser_byte_array)
            cipher = input("Which cipher tool? (enter 1-n):\n1. single byte XOR\n2. bit inversion\n3. ...\n").strip()
            if cipher == "1":
                key_crack.xor_key(seed, stack, key_send_bytes)
            if cipher == "2":
                key_crack.invert_bits(seed, stack, key_send_bytes)
            # Additional cipher methods to be added here...
    else:
        print("Security Access did not return a positive response.")


def main():
    # Set up the CAN bus interface.
    interface = input("Enter CAN interface (e.g., can0, vcan0): ").strip()
    try:
        bus = can.interface.Bus(channel=interface, interface='socketcan')
    except Exception as e:
        print(f"Error opening interface {interface}: {e}")
        return

    # Optionally perform functional broadcast to discover tester IDs.
    if input("Attempt to discover valid tester ID? (y/n): ").strip().lower().startswith('y'):
        discovered_ids = tester_present.try_functional_broadcast(bus)
        # Assume discovered_ids is a list of integers. If not, treat as empty.
        if discovered_ids and isinstance(discovered_ids, list) and len(discovered_ids) > 0:
            print("Discovered tester IDs:")
            for i, tid in enumerate(discovered_ids):
                print(f"{i + 1}. {hex(tid)}")
            choice = input("Select a tester ID by number, or press Enter to enter your own: ").strip()
            if choice:
                try:
                    selected_index = int(choice) - 1
                    tester_id = discovered_ids[selected_index]
                except (ValueError, IndexError):
                    print("Invalid selection. Please enter a tester ID manually.")
                    tester_id = get_hex_input("Enter Tester (source) id in hex: ")
            else:
                tester_id = get_hex_input("Enter Tester (source) id in hex: ")
        else:
            print("No tester IDs discovered.")
            tester_id = get_hex_input("Enter Tester (source) id in hex: ")
    else:
        tester_id = get_hex_input("Enter Tester (source) id in hex: ")

    ecu_id = get_hex_input("Enter target ECU (destination) id in hex: ")
    if tester_id is None or ecu_id is None:
        return

    # Ask the user for the identifier mode.
    id_mode_choice = input("Select identifier mode:\n1. 11-bit\n2. 29-bit\nYour choice (default 1): ").strip()
    id_mode = "29" if id_mode_choice == "2" else "11"

    # Create the ISO-TP stack using the helper function.
    stack = create_iso_tp_stack(bus, tester_id, ecu_id, id_mode=id_mode)
    print(
        f"ISO-TP stack created with Tester ID {hex(tester_id)} and ECU ID {hex(ecu_id)} using {id_mode}-bit identifiers.")

    # Main loop to process UDS commands.
    while True:
        user_choice = input(
            "\nEnter UDS service in hex (e.g., '10 01') or choose an option:\n"
            "1. Scan DIDs\n"
            "2. Scan RIDs\n"
            "3. Scan ECU Memory\n"
            "4. Exit\n"
            "Entry: "
        ).strip()

        if user_choice == "1":
            did_scan.try_all_dids(stack)
            continue
        elif user_choice == "2":
            rid_scan.try_all_rids(stack)
            continue
        elif user_choice == "3":
            mem_scan.try_memory_scan(stack)
            continue
        elif user_choice == "4":
            bus.shutdown()
            print("Shutting down interface")
            break

        try:
            service_bytes = bytes.fromhex(user_choice)
        except ValueError:
            print("Invalid hex input. Please try again.")
            continue

        print(f"Sending UDS service: {user_choice}...")
        responses = send_and_receive(stack, service_bytes)

        if responses:
            for resp in responses:
                processed = read_response.process_ecu_response(resp)
                print(f"Response: {processed} from {hex(ecu_id)}")
                print(f"Raw response: {resp.hex(' ')}")
                data = resp.hex(' ')[3:]
                print(f"Data: {data}")
                decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
                print(f"Decoded data: {decoded}\n")
        else:
            print("No UDS response received within timeout.")

        # Handles Security Access (service 0x27)
        if service_bytes[0] == 0x27 and responses:
            handle_security_access(service_bytes, responses, stack)


if __name__ == '__main__':
    main()
