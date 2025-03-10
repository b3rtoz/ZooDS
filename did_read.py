import time
import read_response


def read_did(did, stack, timeout=0.5):
    """
    Send a ReadDataByIdentifier (0x22) request for the given DID.

    Parameters:
        did (int): 2-byte identifier (0x0000 - 0xFFFF).
        stack: iso-tp communication interface object
        timeout (float): time in seconds to wait for ECU responses.

    Returns:
        responses: list of response bytes received.
    """
    # Build UDS request: 0x22 followed by 2 bytes of DID.
    request = bytes([0x22, (did >> 8) & 0xFF, did & 0xFF])
    print(f"Sending ReadDataByIdentifier (0x22) for DID: 0x{did:04X}")
    stack.send(request)

    responses = []
    last_response_time = time.time()

    # Wait until no new frames are received for 'timeout' seconds.
    while True:
        stack.process()
        if stack.available():
            response = stack.recv()
            responses.append(response)
            print(f"Received response for DID 0x{did:04X}: {response.hex()}")
            last_response_time = time.time()
        if time.time() - last_response_time > timeout:
            break
        time.sleep(0.01)

    return responses


def try_all_dids(stack, timeout=0.5):
    """
    Iterates through all possible 2-byte DIDs and sends a ReadDataByIdentifier request.
    Prints whether a positive response is received (non-negative response) or prints the error.
    Allows a keyboard interrupt (Ctrl+C) to break the loop.

    Parameters:
        stack: iso-tp communication interface object
        timeout (float): timeout in seconds for each DID request
    """
    try:
        for did in range(0x0000, 0x10000):
            responses = read_did(did, stack, timeout)
            if responses:
                # Check the first response: a positive response does not start with 0x7F.
                if responses[0][0] != 0x7F:
                    for resp in responses:
                        print(f"    {read_response.process_ecu_response(resp)}")
                        print(f"    {resp.hex(' ')}")
                        data = resp.hex(' ')[2:]
                        print(f"    Data: {data}")
                        print(f"    Decoded data: {bytearray.fromhex(data).decode('ascii', errors='replace')}\n")
                else:
                    error_msg = read_response.process_ecu_response(responses[0])
                    print(f"Negative response for DID 0x{did:04X}: {error_msg}\n")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting DID scan.")

