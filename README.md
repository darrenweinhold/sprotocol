# sprotocol

For interfacing with Brooks Instrument Mass Flow Controllers, Meters, and Pressure Controllers with S-Protocol over RS-485.

## Installation

```bash
$ pip install sprotocol
```

## Usage

This package is written for interfacing with Brooks Instrument devices using S-Protocol. S-Protocol is a proprietary protocol based on HART communications utilizing RS-485. 

'''
from sprotocol import mfc, mfm, pc

device = mfc('COM10')
device.get_address()

device.read_flow_rate()

device.write_setpoint(10)

'''

### Disclaimer and Overview
This module is intended to ease setting up and utilizing S protocol communications over RS-485 with Brooks Instrument devices. This module is provided for free and is currently in beta. Feedback is welcome and requested features as well as bug fixes will be added over time. It is recommended to review the S-protocol manual for the appropriate device.

### S-Protocol Manuals
The following device-specific S-protocol manuals can be found on the Brooks Instrument website. 
- GF40/80 Mass Flow Controllers: https://cdn.brooksinstrument.com/-/media/brooks/documentation/products/mass-flow-controllers/elastomer-sealed/gf40/mass-flow-controller-rs485-s-protocol-manual-gf40-gf80.pdf?rev=1c25ff086a6447cab610679dbdc5845d&sc_lang=en&hash=4321acf7275f5ec39ac5534d8369bc20
- SLA Mass Flow Controllers, Mass Flow Meters, and Pressure Controllers: https://cdn.brooksinstrument.com/-/media/brooks/documentation/products/mass-flow-controllers/elastomer-sealed/sla5800/mass-flow-pressure-controller-rs485-manual-sla5800-slamf-series-revb.pdf?rev=a50429ef455a4608ac50e581bbffd17b&sc_lang=en&hash=31c84901f51466f646ec959c79d71dfb


### Getting Started - Single Unit Connection
1. Connect your S protocol device and note the com port it is connected to. 
2. Import the module s_protocol.py
3. Initialize the appropriate class—Mass Flow Controller (mfc), Mass Flow Meter (mfm), or Pressure Controller (pc). 
4. Pass in the com port that is connected to the device along with the baudrate. Note that the default baudrate is 19200. Alternately, a serial connection can be passed for the initialization instead.
5. To begin communicating, the address of the unit is necessary. This can be set in two different ways. 
-   Call the get_address method. This is recommended.
```
From sprotocol import device

gf40 = device.mfc('COM10') 
gf40.get_address()

gf40.read_flow_rate()
```
- 	Set the long_frame_address property to the device address. This will be a bytearray consisting of five elements. See the S-Protocol device manual for more information.  
```
From sprotocol import device

gf40 = device.mfc('COM10') 
gf40.long_frame_address = bytearray(b'\x8aZ\xe7wI')

gf40.read_flow_rate()
```
6.	Once the address is known by the unit, commands can be sent. 
7.	The following commands are supported by each device type. The command number is noted below. The command number can be used to reference the S protocol device manual for the relevant unit. Note that if the baudrate is changed, communications will be lost and the class will need to be reinitialized.
#### Commands supported by device.
The commands supported are based on the device type. The command numbers are listed. Please see the S-Protocol manual for more information on the commands.
####	MFC Supported Commands
1.	Read Setpoint—Command 235
2.	Write Setpoint—Command 236
3.	Read Totalizer Status—Command 240
4.	Write Totalizer Status—Command 241
5.	Read Totalizer Value—Command 242
6.	Read Setpoint Source—Command 215
7.	Write Setpoint Source—Command 216
8.	Read Flow Rate—Command 1
9.	Read Full Scale Flow Rate—Command 152
10.	Read Standard Temperature and Pressure—Command 190
11.	Write Standard Temperature and Pressure—Command 191 
12.	Write Flow Units—Command 196
13.	Write Temperature Units—Command 197 
14.	Write Baudrate—Command 123

####	MFM Supported Commands
1.	Read Flow Rate—Command 1
2.	Read Full Scale Flow Rate—Command 152
3.	Read Standard Temperature and Pressure—Command 190
4.	Write Standard Temperature and Pressure—Command 191 
5.	Write Flow Units—Command 196
6.	Write Temperature Units—Command 197 
7.	Write Baudrate—Command 123

#### Pressure Controller Supported Commands
1.	Read Pressure—Command 1
2.	Read Full Scale Pressure—Command 152
3.	Write Pressure Units—Command 198
4.	Read Setpoint—Command 235
5.	Write Setpoint—Command 236
6.	Read Setpoint Source—Command 215
7.	Write Setpoint Source—Command 216

####	Commands with selections
Some commands require a selection to be specified. This will be an integer based on tables found in the manual. The tables can also be reviewed in the module. 

#### Sending Additional Commands
Not all commands from the manual are supported with methods. Generic commands may be sent to the unit. 
The follow methods are supported and can be used to send other commands that are not directly supported. 
1.	Write_command(self, command_number, data=None)
This is used to send a generic command, specified as an integer, with the data payload. The data payload should be a bytearray consisting of the necessary data for the command. The checksum should not be included in the data bytearray. 
2.	Read_command(self)
This is used to read the response from the unit and parse it. This should be called approximately 100 ms (or more) after sending a write command. This will return an array with the address, command_byte (should match the integer command sent), the two status bytes, and any returned data bytes. The checksum is not included in the data bytes. 

## License

`sprotocol` was created by Darren Weinhold. It is licensed under the terms of the MIT license.

## Credits

`sprotocol` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).
