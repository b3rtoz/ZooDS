import time
import read_response
from zoo_utils import wait_for_responses

def build_read_memory_request(address, size, mem_addr_len=4, mem_size_len=2):
    """
    Builds a UDS ReadMemoryByAddress (0x23) request message.

    Args:
        address (int): Memory address to read.
        size (int): Number of bytes to read.
        mem_addr_len (int): Number of bytes used to represent the address.
        mem_size_len (int): Number of bytes used to represent the size.

    Returns:
        bytes: The complete UDS request message.
    """
    service = 0x23
    # Construct the AddressAndLengthFormatIdentifier: high nibble = mem_addr_len, low nibble = mem_size_len.
    format_identifier = ((mem_addr_len & 0x0F) << 4) | (mem_size_len & 0x0F)
    # Convert address and size to big-endian byte sequences.
    address_bytes = address.to_bytes(mem_addr_len, byteorder='big')
    size_bytes = size.to_bytes(mem_size_len, byteorder='big')
    request = bytes([service, format_identifier]) + address_bytes + size_bytes
    return request


def scan_memory_by_address(stack, start_address, end_address, block_size,
                           mem_addr_len=4, mem_size_len=2, timeout=1.0):
    """
    Scans memory using the UDS ReadMemoryByAddress service for addresses in the specified range.

    For each address in the range (stepping by block_size), a request is sent and any ECU responses are collected.

    Args:
        stack: The iso-tp communication interface.
        start_address (int): Starting memory address.
        end_address (int): Ending memory address.
        block_size (int): Number of bytes to read from each address.
        mem_addr_len (int): Number of bytes for the memory address (default: 4).
        mem_size_len (int): Number of bytes for the memory size (default: 2).
        timeout (float): Timeout in seconds for ECU responses.

    Returns:
        list of tuples: Each tuple is (address, request, responses),
        where responses is a list of received response frames.
    """
    results = []
    for address in range(start_address, end_address + 1, block_size):
        request = build_read_memory_request(address, block_size, mem_addr_len, mem_size_len)
        print(f"Scanning memory at address 0x{address:0{mem_addr_len * 2}X} "
              f"with block size {block_size} bytes.")
        stack.send(request)
        responses = wait_for_responses(stack, timeout)
        if responses:
            print(f"Response for address 0x{address:0{mem_addr_len * 2}X}:")
            for r in responses:
                processed = read_response.process_ecu_response(r)
                print(f"  {processed} - {r.hex(' ')}")
            results.append((address, request, responses))
        else:
            print(f"No response for address 0x{address:0{mem_addr_len * 2}X}.")
    return results


def try_memory_scan(stack):
    """
    Prompts the user for a memory address range and block size, then scans the ECU
    using the UDS ReadMemoryByAddress service. All responses are printed.

    Args:
        stack: The iso-tp communication interface.

    Returns:
        List of scan results as returned by scan_memory_by_address.
    """
    try:
        start_str = input("Enter start memory address (in hex, e.g., 1000): ").strip()
        end_str = input("Enter end memory address (in hex, e.g., 1FFF): ").strip()
        block_size_str = input("Enter block size in bytes (e.g., 16): ").strip()
        start_address = int(start_str, 16)
        end_address = int(end_str, 16)
        block_size = int(block_size_str)
    except ValueError:
        print("Invalid input. Please enter valid hexadecimal addresses and an integer block size.")
        return []

    results = scan_memory_by_address(stack, start_address, end_address, block_size)
    if results:
        print("Memory scan results:")
        for addr, req, responses in results:
            print(f"Address 0x{addr:0{4}X}:")
            for r in responses:
                processed = read_response.process_ecu_response(r)
                print(f"  {processed} - {r.hex(' ')}")
    else:
        print("No responses found during memory scan.")
    return results
