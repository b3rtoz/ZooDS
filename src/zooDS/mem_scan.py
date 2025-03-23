from .utils import wait_for_responses, process_ecu_response

def build_read_memory_request(address, size, mem_addr_len=4, mem_size_len=1):
    """
    Builds a UDS ReadMemoryByAddress (0x23) request message.

    Message structure:
        [0x23] [addressAndLengthFormatIdentifier] [MemoryAddress] [MemorySize]

    The addressAndLengthFormatIdentifier is constructed as:
        (mem_size_len << 4) | mem_addr_len

    For example, with mem_addr_len=4 and mem_size_len=1:
        format_identifier = (1 << 4) | 4 = 0x14

    Args:
        address (int): Memory address to read.
        size (int): Number of bytes to read.
        mem_addr_len (int): Number of bytes for MemoryAddress.
        mem_size_len (int): Number of bytes for MemorySize.

    Returns:
        bytes: The complete UDS request message.
    """
    service = 0x23
    format_identifier = ((mem_size_len & 0x0F) << 4) | (mem_addr_len & 0x0F)
    address_bytes = address.to_bytes(mem_addr_len, byteorder='big')
    size_bytes = size.to_bytes(mem_size_len, byteorder='big')
    request = bytes([service, format_identifier]) + address_bytes + size_bytes
    return request


def scan_memory_by_address(stack, start_address, end_address, mem_size,
                           mem_addr_len=4, mem_size_len=1, timeout=1.0):
    """
    Scans memory using the UDS ReadMemoryByAddress service at every byte from
    start_address to end_address. Each request reads 'mem_size' bytes.

    For each address, a request is built and sent. If any ECU response is received,
    the responses are printed. If a positive response (i.e. response[0] != 0x7F) is received,
    the scan pauses and asks the user whether to continue scanning.

    Args:
        stack: The iso-tp communication interface.
        start_address (int): Starting memory address.
        end_address (int): Ending memory address.
        mem_size (int): Number of bytes to read from each address.
        mem_addr_len (int): Number of bytes for MemoryAddress.
        mem_size_len (int): Number of bytes for MemorySize.
        timeout (float): Timeout in seconds for ECU responses.

    Returns:
        list of tuples: Each tuple is (address, request, responses)
    """
    results = []
    try:
        for address in range(start_address, end_address + 1):
            request = build_read_memory_request(address, mem_size, mem_addr_len, mem_size_len)
            print(f"\nScanning memory at address 0x{address:0{mem_addr_len * 2}X} with size {mem_size} bytes.")
            stack.send(request)
            responses = wait_for_responses(stack, timeout)
            if responses:
                #print(f"Response for address 0x{address:0{mem_addr_len * 2}X}:")
                positive = False
                for r in responses:
                    processed = process_ecu_response(r)
                    # data = r.hex(' ')[4:]
                    # decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
                    print(f"  {processed} - {r.hex(' ')}")
                    #if r[0] != 0x7F:  # positive response
                        #positive = True
                results.append((address, request, responses))
                #if positive:
                    #cont = input(
                        #f"Positive response received for address 0x{address:0{mem_addr_len * 2}X}. Continue scanning? (y/n): ").strip().lower()
                    #if not cont.startswith('y'):
                        #print("Memory scan aborted.")
                        #break
            else:
                print(f"No response for address 0x{address:0{mem_addr_len * 2}X}.")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Aborting memory scan.")
    return results


def try_memory_scan(stack):
    """
    Prompts the user for a memory address range and memory size, then scans memory using
    the UDS ReadMemoryByAddress service. If the user leaves the memory size input empty,
    a default value of 0xFF is used.

    The scan tries every byte starting from the entered address until the end address,
    pausing when a positive response is received.

    Args:
        stack: The iso-tp communication interface.

    Returns:
        List of scan results as returned by scan_memory_by_address.
    """
    try:
        start_str = input("Enter start memory address (in hex, e.g., 10000000): ").strip()
        end_str = input("Enter end memory address (in hex, e.g., 100000FF): ").strip()
        mem_size_str = input("Enter memory size in bytes (press Enter to use default 0xFF): ").strip()
        start_address = int(start_str, 16)
        end_address = int(end_str, 16)
        mem_size = int(mem_size_str, 16) if mem_size_str != "" else 0xFF
    except ValueError:
        print("Invalid input. Please enter valid hexadecimal addresses and memory size.")
        return []

    results = scan_memory_by_address(stack, start_address, end_address, mem_size)
    if results:
        print("\nMemory scan results:")
        for addr, req, responses in results:
            print(f"Address 0x{addr:0{4}X}:")
            for r in responses:
                processed = process_ecu_response(r)
                # data = r.hex(' ')[4:]
                # decoded = bytearray.fromhex(data).decode('ascii', errors='replace')
                print(f"  {processed} - {r.hex(' ')}")
                # print(f"    Decoded data: {decoded}\n")
    else:
        print("No responses found during memory scan.")
    return results
