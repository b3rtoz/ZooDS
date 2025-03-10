import time
import read_response  # Module assumed to process ECU responses


def create_stack():
    """
    Placeholder function.
    Replace this with your actual stack initialization which must provide:
      - send(message: bytes)
      - process()
      - available()
      - recv()
    """
    raise NotImplementedError("Implement the stack interface initialization.")


def read_did(did, stack, timeout=1.0):
    """
    Send a ReadDataByIdentifier (0x22) request for the given DID.

    Parameters:
        did (int): A 2-byte identifier (0x0000 - 0xFFFF).
        stack: Communication interface object.
        timeout (float): Time in seconds to wait for ECU responses.

    Returns:
        list: A list of response bytes received.
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


def try_all_dids(stack, timeout=1.0):
    """
    Iterates through all possible 2-byte DIDs and sends a ReadDataByIdentifier request.
    Prints whether a positive response is received (non-negative response) or prints the error.

    Parameters:
        stack: Communication interface object.
        timeout (float): Timeout in seconds for each DID request.
    """
    for did in range(0x0000, 0x10000):
        responses = read_did(did, stack, timeout)
        if responses:
            # Check the first response: a positive response does not start with 0x7F.
            if responses[0][0] != 0x7F:
                print(f"Positive response for DID 0x{did:04X}.")
            else:
                error_msg = read_response.process_ecu_response(responses[0])
                print(f"Negative response for DID 0x{did:04X}: {error_msg}")


def main():
    """
    Main entry point for scanning all DIDs.
    """
    # Initialize the communication stack.
    try:
        stack = create_stack()
    except NotImplementedError as nie:
        print(nie)
        return

    # Start scanning DIDs.
    try_all_dids(stack)


if __name__ == "__main__":
    main()
