import time
import read_response


def scan_rid(rid, stack, timeout=1.0):
    """
    Send a ReadDataByIdentifier (0x31) request for the given RID.

    Parameters:
        did (int): 2-byte identifier (0x0000 - 0xFFFF).
        stack: iso-tp communication interface object
        timeout (float): time in seconds to wait for ECU responses.

    Returns:
        responses: list of response bytes received.
    """
    # Build UDS request: 0x31 followed by 2 bytes of RID.
    request = bytes([0x31, (rid >> 8) & 0xFF, rid & 0xFF])
    print(f"Sending ReadDataByIdentifier (0x31) for RID: 0x{rid:04X}")
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


def try_all_rids(stack, timeout=1.0):
    """
    Iterates through all possible 2-byte RIDs and sends a RoutineControl request.
    Prints whether a positive response is received (non-negative response) or prints the error.
    Allows a keyboard interrupt (Ctrl+C) to break the loop.

    Parameters:
        stack: iso-tp communication interface object
        timeout (float): timeout in seconds for each RID request
    """
    try:
        for rid in range(0x0000, 0x10000):
            responses = scan_rid(rid, stack, timeout)
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
                    print(f"Negative response for DID 0x{rid:04X}: {error_msg}\n")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting DID scan.")

