import time
import read_response
from zoo_utils import wait_for_responses

def scan_rid(rid, stack, timeout=0.1):
    """
    Sends a RoutineControl (0x31) request for the given RID using the "StartRoutine" sub-function.
    """
    # Build UDS request: 0x31 (RoutineControl), 0x01 (StartRoutine), followed by the 2-byte RID.
    request = bytes([0x31, 0x01, (rid >> 8) & 0xFF, rid & 0xFF])
    print(f"\nSending RoutineControl (0x31, StartRoutine) for RID: 0x{rid:04X}")
    stack.send(request)

    responses = wait_for_responses(stack, timeout)
    for response in responses:
        print(f"Received response for RID 0x{rid:04X}: {response.hex()}")
    return responses

def try_all_rids(stack, timeout=1.0):
    """
    Iterates through all possible 2-byte RIDs, sending a RoutineControl (StartRoutine) request for each.
    Processes and prints responses, and if a positive response is received, pauses to ask the user
    whether to continue scanning.
    """
    try:
        for rid in range(0x0000, 0x10000):
            responses = scan_rid(rid, stack, timeout)
            if responses:
                # Positive response assumed if first byte is not 0x7F.
                if responses[0][0] != 0x7F:
                    for r in responses:
                        processed = read_response.process_ecu_response(resp)
                        print(f"    {processed}")
                        print(f"    {r.hex(' ')}")
                        data = r.hex(' ')[4:]
                        decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
                        print(f"    Data: {data}")
                        print(f"    Decoded data: {decoded}\n")
                    cont = input("Positive response received for RID 0x{0:04X}. Continue scanning RIDs? (y/n): ".format(rid)).strip().lower()
                    if not cont.startswith('y'):
                        print("exiting RID scan")
                        break
                else:
                    error_msg = read_response.process_ecu_response(responses[0])
                    print(f"Negative response for RID 0x{rid:04X}: {error_msg}\n")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting RID scan.")
