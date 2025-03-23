from .utils import wait_for_responses, process_ecu_response


def read_did(did, stack, timeout = 0.3):
    """
    Sends a ReadDataByIdentifier (0x22) request for the specified DID and collects responses.

    Args:
        did (int): A 2-byte identifier (0x0000 - 0xFFFF).
        stack: The iso-tp communication interface.
        timeout (float): Time in seconds to wait for responses.

    Returns:
        List of response frames.
    """
    request = bytes([0x22, (did >> 8) & 0xFF, did & 0xFF])
    print(f"Sending ReadDataByIdentifier (0x22) for DID: 0x{did:04X}")
    stack.send(request)

    responses = wait_for_responses(stack, timeout)
    for response in responses:
        print(f"Received response for DID 0x{did:04X}: {response.hex()}")
    return responses


def try_all_dids(stack, timeout=0.3):
    """
    Iterates over all possible 2-byte DIDs, sending a ReadDataByIdentifier request for each.
    Processes and prints responses, distinguishing between positive and negative responses.
    Allows a KeyboardInterrupt (Ctrl+C) to abort the scan.
    """
    try:
        for did in range(0x0000, 0x10000):
            responses = read_did(did, stack, timeout)
            if responses:
                if responses[0][0] != 0x7F:  # Positive response check
                    for r in responses:
                        processed = process_ecu_response(r)
                        print(f"    {processed}")
                        print(f"    {r.hex(' ')}")
                        data = r.hex()[4:]
                        decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
                        print(f"    Data: {data}")
                        print(f"    Decoded data: {decoded}\n")
                        cont = input("Positive response received for DID 0x{0:04X}. Continue scanning DIDs? (y/n): ".format(did)).strip().lower()
                        if cont.startswith('n'):
                            print("exiting DID scan")
                            break
                        else:
                            continue
                else:
                    error_msg = process_ecu_response(responses[0])
                    print(f"Negative response for DID 0x{did:04X}: {error_msg}\n")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting DID scan.")
