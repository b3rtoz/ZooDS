from .utils import wait_for_responses, process_ecu_response

def key_request(key_req, stack, timeout=0.3):
    """
    Sends a UDS key request and waits for the ECU's response.

    Args:
        key_req (bytes): The full UDS key request message.
        stack: Communication interface with send, recv, process, and available methods.
        timeout (float): Time (in seconds) to wait for responses.

    Returns:
        tuple: (found, candidate, responses)
            found (bool): True if a positive response is received.
            candidate (bytes): Candidate key extracted from key_req (key_req[2:]).
            responses (list): All response frames received.
    """
    print(f"Sending UDS key request: {key_req.hex()}")
    stack.send(key_req)
    candidate = key_req[2:]
    responses = wait_for_responses(stack, timeout)

    if responses:
        if responses[0][0] != 0x7F:
            flag = responses[0].hex(' ')[6:]
            print(f"\nKey found!\n Security Access gained with key {candidate.hex()}\nResponse: {flag}")
            print(f"Decoded data: {bytearray.fromhex(flag).decode('ascii', errors='replace')}")
            return True, candidate, responses
        else:
            print(process_ecu_response(responses[0]))
    return False, candidate, responses


def xor_key(seed, stack, key_send_bytes):
    """
    Generates candidate keys by XORing each byte of the seed with every possible byte (0x00-0xFF)
    and sends them via the key_request helper function.

    Args:
        seed (bytes): The seed value.
        stack: Communication interface with required methods.
        key_send_bytes (bytes): UDS request header for sending a key.
    """
    try:
        for candidate in range(256):
            xor_value = bytes([b ^ candidate for b in seed])
            print(f"Candidate {candidate:02X}: {xor_value.hex()}")
            key_req = key_send_bytes + xor_value
            found, candidate_key, responses = key_request(key_req, stack)
            if found:
                break
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting key scan.")


def invert_bits(seed, stack, service_bytes):
    """
    Inverts the bits of a hex string seed, builds the key request, and sends it.

    Args:
        seed (str): The seed as a hex string.
        stack: Communication interface with required methods.
        service_bytes (bytes): UDS request header for sending a key.
    """
    num = int(seed, 16)
    num_bits = len(seed) * 4  # Each hex digit represents 4 bits.
    inverted_num = ~num & ((1 << num_bits) - 1)
    inverted_seed = f'{inverted_num:0{len(seed)}X}'
    key_str = ' '.join([inverted_seed[i:i + 2] for i in range(0, len(inverted_seed), 2)])
    print(f"Original hex: {seed}")
    print(f"Bitwise inverted hex: {inverted_seed}")
    print(f"Key: {key_str}")

    inverted_bytes = bytes.fromhex(inverted_seed)
    key_req = service_bytes + inverted_bytes
    key_request(key_req, stack)


def handle_security_access(service_bytes, responses, stack):
    """
    Handles Security Access responses (service 0x27). If a positive response is received,
    extracts the seed and optionally attempts to crack the key.

    Args:
        service_bytes (bytes): The original service request bytes.
        responses (list): List of ECU response frames.
        stack: Communication interface with required methods.
    """
    complete_response = responses[0]
    result = process_ecu_response(complete_response)
    if result.startswith("P"):
        # Assuming a positive response code "67 01" where the seed follows.
        seed = complete_response[2:]
        print(f"Security Access positive response. Seed: {seed.hex(' ')}")
        if input("Attempt to crack Security Access key? (y/n): ").strip().lower().startswith('y'):
            # Modify key request header: increment second byte.
            ser_byte_array = bytearray(service_bytes)
            ser_byte_array[1] = (ser_byte_array[1] + 1) % 256
            key_send_bytes = bytes(ser_byte_array)
            cipher = input(
                "Which cipher tool?\n"
                "1. Single Byte XOR\n"
                "2. Bitwise Inversion\n"
                # "3. ..." list to be expanded with additional "bit twiddling"
            ).strip()
            if cipher == "1":
                xor_key(seed, stack, key_send_bytes)
            elif cipher == "2":
                # For bitwise inversion, convert seed to hex string.
                invert_bits(seed.hex(), stack, key_send_bytes)
    else:
        print("Security Access did not return a positive response.")
