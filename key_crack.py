import time
import read_response

def xor_key(seed, stack):
    # Iterate over candidate bytes 0-255 to generate a key via single byte XOR.
    for candidate in range(256):
        xor_value = bytes([b ^ candidate for b in seed])
        print(f"Candidate {candidate:02X}: {xor_value.hex()}")
        # Build UDS "send key" request for service 27 02.
        key_request = b'\x27\x02' + xor_value
        print(f"Sending UDS key request: {key_request.hex()}")
        stack.send(key_request)
        # Wait for ECU response with a timeout resetting on each frame.
        candidate_timeout_gap = 1.0
        candidate_last_frame = time.time()
        candidate_responses = []
        while True:
            stack.process()
            if stack.available():
                resp_data = stack.recv()
                candidate_responses.append(resp_data)
                print(f"Received response for candidate {candidate:02X}: {resp_data.hex()}")
                candidate_last_frame = time.time()
            if time.time() - candidate_last_frame > candidate_timeout_gap:
                break
            time.sleep(0.01)
        # If a response was received, check for positive response.
        if candidate_responses:
            if candidate_responses[0][0] != 0x7F:
                flag = resp_data.hex(' ')
                print(f"\n  Key found! Key:{candidate} \nResponse:  {flag}")
                print(f"Decoded data: {bytearray.fromhex(flag).decode('ascii', errors='replace')}")
                break
            else:
                print(print(f"{read_response.process_ecu_response(candidate_responses[0])}"))
