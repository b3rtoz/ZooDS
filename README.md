# ZooDS

ZooDS is a Python-based command-line interface (CLI) tool designed for automotive diagnostic applications. It leverages the Unified Diagnostic Services (UDS) protocol to provide a suite of diagnostic functionalities for vehicle systems.

## Features

- **Service Execution:** Send UDS diagnostic commands for various services.
- **DID Scanning:** Discovery valid UDS Data Identifiers.
- **RID Scanning:** Discovery supported UDS Routine Identifiers.
- **Memory Scanning:** Scan memory for a given address range and return data.
- **0x27 Handler:** Retrieves seed and generates key for UDS Security Access.
- **(planned)** UDS Session Management: Initiate and maintain diagnostic sessions.

## Requirements

- Python 3.9 or later
- Dependencies:
  - click (≥ 8.0.0): Command line interface creation toolkit
  - python-can (≥ 4.5.0): CAN bus interface module
  - can-isotp (≥ 2.0.6): ISO-TP (ISO 15765-2) implementation for CAN communication
  - rich (≥ 13.9.4): Rich text and formatting in the terminal
  - typer (≥ 0.15.2): Building CLI applications

## Installation

Clone the repository, install the dependencies:

```bash
git clone https://github.com/b3rtoz/zooDS.git
cd zooDS
pip install -r requirements.txt
```
Install from src:

```bash
pip install the/path/to/ZooDS

```
Or build the package and install from local archive:

```bash
python3 -m build
pip install ZooDS/dist/zoods-x.x.x.x.tar.gz
```

## Usage

After installation, you can run ZooDS from the command line:

```bash
zooDS
```
zooDS will guide user through interface setup:

```bash
Enter CAN interface (e.g., can0, vcan0): 
```
user has the option to discover valid tester IDs or enter manually:

```bash
Attempt to discover valid tester ID? (y/n): n
Enter tester (source) id in hex: 7E0
```

### Common Use Cases

ToDO: add example feature use here

## Hardware Requirements

- CAN interface compatible with python-can (e.g., Vector, PCAN, Kvaser, SocketCAN)

## Contributing

Contributions are welcome! If you have suggestions, bug reports, or would like to contribute code:

- Create your feature branch (`git checkout -b feature/your-feature`).
- Commit your changes (`git commit -m 'Add new feature'`).
- Push to the branch (`git push origin feature/your-feature`).
- Open a Pull Request with a detailed description of your feature or bug fix.

## License

ZooDS is distributed under the MIT license. See the [LICENSE](LICENSE) file for more information.

## Contact

For feature requests, questions, or bug reports, please open an issue or post in the discussions.

## Acknowledgements

ZooDS leverages several open-source libraries for CAN communication and UDS protocol implementation. Special thanks to the maintainers of python-can and can-isotp.

---
