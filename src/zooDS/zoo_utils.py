import time
import isotp

"""
Utility module to handle common tasks
   """
# Dictionary mapping standard UDS negative response codes (NRC) to their text descriptions.
NEGATIVE_RESPONSE_CODES = {
    0x10: "General Reject",
    0x11: "Service Not Supported",
    0x12: "Sub-Function Not Supported",
    0x13: "Incorrect Message Length or Invalid Format",
    0x14: "Response Too Long",
    0x21: "Busy Repeat Request",
    0x22: "Conditions Not Correct",
    0x24: "Request Sequence Error",
    0x31: "Request Out Of Range",
    0x33: "Security Access Denied",
    0x35: "Invalid Key",
    0x36: "Exceeded Number of Attempts",
    0x37: "Required Time Delay Not Expired",
    0x70: "Upload/Download Not Accepted",
    0x71: "Transfer Data Suspended",
    0x72: "General Programming Failure",
    0x73: "Wrong Block Sequence Counter",
    0x78: "Response Pending",
    0x7E: "Sub-function Not Supported In Active Session",
    0x7F: "Service Not Supported In Active Session"
}


def is_negative_response(response):
    """Determines if the provided UDS response is a negative response.
        The first byte of a UDS negative response is 0x7F."""
    # return True if it is a negative response, otherwise False
    return len(response) > 0 and response[0] == 0x7F


def process_ecu_response(response: bytes) -> str:
    """Processes a UDS response and compares it against standard negative response codes.

    The UDS negative response format is:
        [0x7F, <original service id>, <negative response code>]

    return: A text description of the negative response if one is detected.
             If the response is not negative, returns an empty string.
             If the response is malformed, returns a suitable error message."""
    if not response:
        return "No response received."

    # Check if it is a negative response (first byte should be 0x7F).
    if response[0] != 0x7F:
        return "Positive Response"

    # Ensure response has enough bytes to extract the negative response code.
    if len(response) < 3:
        return "Malformed negative response."

    # The negative response code starts at the third byte.
    nrc = response[2]
    description = NEGATIVE_RESPONSE_CODES.get(nrc, f"Unknown negative response code: {nrc:02X}")
    return description

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
            # print(f"Received response: {response.hex()}")
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

def print_response(response, service_bytes):
    """
    Prints ECU response frame's message data, and decoded ASCII data.

    Args:
        response: ECU response frame (bytes).
    """
    processed = process_ecu_response(response)
    raw = response.hex(' ')
    # first two bytes in response are header  first two bytes.
    if len(service_bytes) > 2:
        data = response.hex()[8:]
    else:
        data = response.hex()[4:]
    try:
        decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
    except ValueError:
        decoded = ""
    print(f"{raw}: {processed}")
    print(f"data: {data}")
    print(f"ascii: {decoded}")
