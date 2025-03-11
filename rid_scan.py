import read_response
from zoo_utils import wait_for_responses

def scan_rid(rid, stack, timeout=1.0):
    """
    Sends a RoutineControl (0x31) request for the given RID.

    Parameters:
        rid (int): A 2-byte identifier (0x0000 - 0xFFFF).
        stack: The iso-tp communication interface.
        timeout (float): Time in seconds to wait for ECU responses.

    Returns:
        List of response frames.
    """
    # Build UDS request: 0x31 followed by 2 bytes representing the RID.
    request = bytes([0x31, (rid >> 8) & 0xFF, rid & 0xFF])
    print(f"Sending RoutineControl (0x31) for RID: 0x{rid:04X}")
    stack.send(request)

    # Use the centralized wait_for_responses function.
    responses = wait_for_responses(stack, timeout)
    for response in responses:
        print(f"Received response for RID 0x{rid:04X}: {response.hex()}")
    return responses


def try_all_rids(stack, timeout=1.0):
    """
    Iterates through all possible 2-byte RIDs, sending a RoutineControl request for each.
    Processes and prints responses, distinguishing positive from negative responses.
    Supports KeyboardInterrupt (Ctrl+C) to abort the scan.

    Parameters:
        stack: The iso-tp communication interface.
        timeout (float): Timeout in seconds for each RID request.
    """
    try:
        for rid in range(0x0000, 0x10000):
            responses = scan_rid(rid, stack, timeout)
            if responses:
                # A positive response is assumed if the first byte is not 0x7F.
                if responses[0][0] != 0x7F:
                    for resp in responses:
                        processed = read_response.process_ecu_response(resp)
                        print(f"    {processed}")
                        print(f"    {resp.hex(' ')}")
                        data = resp.hex(' ')[2:]
                        decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
                        print(f"    Data: {data}")
                        print(f"    Decoded data: {decoded}\n")
                else:
                    error_msg = read_response.process_ecu_response(responses[0])
                    print(f"Negative response for RID 0x{rid:04X}: {error_msg}\n")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting RID scan.")
