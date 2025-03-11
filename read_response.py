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
    0x78: "Response Pending"
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

    # The negative response code is typically in the third byte.
    nrc = response[2]
    description = NEGATIVE_RESPONSE_CODES.get(nrc, f"Unknown negative response code: {nrc:02X}")
    return description


if __name__ == "__main__":
    # Test:
    test_response = bytes.fromhex('7f 67 35')
    print("Test response:", test_response.hex())
    print(f"{process_ecu_response(test_response)}")
