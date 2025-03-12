import time
import can
import isotp
import read_response

def wait_for_responses(stack, timeout, sleep_interval=0.01):
    """
    Waits for responses from the ECU via the provided stack.

    Args:
        stack: Communication interface with methods process(), available(), and recv().
        timeout (float): Time in seconds to wait after the last received frame before stopping.
        sleep_interval (float): Interval in seconds between stack checks.

    Returns:
        List of received response frames.
    """
    responses = []
    last_frame_time = time.time()
    while True:
        stack.process()
        if stack.available():
            response = stack.recv()
            print(f"Received response: {response.hex()}")
            responses.append(response)
            last_frame_time = time.time()  # Reset timeout on each response.
        if time.time() - last_frame_time > timeout:
            break
        time.sleep(sleep_interval)
    return responses

def get_hex_input(prompt):
    """
    Prompts the user for a hexadecimal input and returns its integer value.

    Args:
        prompt (str): The prompt string.

    Returns:
        int or None: The integer value of the hex input, or None if invalid.
    """
    user_input = input(prompt)
    try:
        return int(user_input, 16)
    except ValueError:
        print("Invalid hex format.")
        return None

def create_iso_tp_stack(bus, tester_id, ecu_id, id_mode="11", stmin=0, blocksize=8):
    """
    Creates and returns an ISO-TP stack for the provided tester and ECU IDs.

    Args:
        bus: The CAN bus instance.
        tester_id (int): The tester (source) ID.
        ecu_id (int): The target ECU (destination) ID.
        id_mode (str): "11" for 11-bit or "29" for 29-bit identifiers.
        stmin (int): Separation time minimum (default 0).
        blocksize (int): Block size (default 8).

    Returns:
        isotp.CanStack: The configured ISO-TP stack.
    """
    if id_mode == "11":
        addressing_mode = isotp.AddressingMode.Normal_11bits
    elif id_mode == "29":
        addressing_mode = isotp.AddressingMode.Normal_29bits
    else:
        print("Invalid identifier mode, defaulting to 11-bit.")
        addressing_mode = isotp.AddressingMode.Normal_11bits

    address = isotp.Address(addressing_mode, txid=tester_id, rxid=ecu_id)
    return isotp.CanStack(bus=bus, address=address, params={'stmin': stmin, 'blocksize': blocksize})

def print_response(response):
    """
    Prints a response frame's processed message, raw hex, and decoded ASCII data.

    Args:
        response: A response frame (bytes).
    """
    processed = read_response.process_ecu_response(response)
    raw = response.hex(' ')
    # Skip header bytes if needed; here we assume the first two bytes are header.
    data = response.hex(' ')[2:]
    try:
        decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
    except ValueError:
        decoded = ""
    print(f"Response: {processed}")
    print(f"Raw: {raw}")
    print(f"Data: {data}")
    print(f"Decoded data: {decoded}")
