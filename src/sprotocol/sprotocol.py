'''
Version 0.0.1

Command 1 returns in units--need to implement units
Command 11: done
Command 123: select baudrate 
Command 152: Read Full Scale Flow Rate (MFC/MFM only)
Command 159: Pressure Controllers FS (PC only) 
Command 190: Read Standard Temperature and Pressure (MFC/MFM only)
Command 191: Set Stanard Temperature and Pressure (MFC/MFM only)
Command 196: Select Flow unit (MFC/MFM only)
Command 197: Select Temperature unit(MFC/MFM only) 
Command 198: Select Pressure units(PC only) 
Command 215: Read setpoint settings
Command 216: Select Setpoint Source (MFC/PC only) 
Command 235: Read Setpoint in % and units (MFC/PC only)
Command 236: Write setpoint in % and units (MFC/PC only)
Command 240: Read Totalizer Status (MFC/MFM only) 
Command 241: Start/Stop/Run totalizer (MFC/MFM only) 
Command 242: Read totalizer value and unit (MFC/MFM only)
'''

import serial
from time import sleep
import binascii
from struct import pack, unpack


class s_protocol_device:
    def __init__(self, com_port, baudrate, timeout):
        self._tag_name = None
        self._long_frame_address = None
        self._units = None
        if type(com_port) is str:
            self._com_port = com_port
            self._baudrate = baudrate
            try:
                self._ser = serial.Serial(
                port = com_port,
                parity=serial.PARITY_ODD,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                baudrate = baudrate,
                timeout = timeout
                )
                self._ser.is_open
            except serial.serialutil.SerialException:
                raise RuntimeError('Port already in use. Pass serial object instead.')
        else:
            self._ser = com_port
            if self._ser.is_open is False:
                try:
                    self._ser.open()
                except Exception:
                    raise RuntimeError('Failed to open com port. Ensure correct passing of a serial object.')
    
    @property
    def ser(self):
        return self._ser
    @ser.setter
    def ser(self,value):
        self._ser = value
    
    @property
    def tag_name(self):
        return self._tag_name
    @tag_name.setter
    def tag_name(self,value):
        self._tag_name = value
    
    @property
    def long_frame_address(self):
        return self._long_frame_address
    @long_frame_address.setter
    def long_frame_address(self,value):
        self._long_frame_address = value

    @property
    def units(self):
        return self._units
    def units(self,value):
        self._units = value

    def get_tag_name(self):
        '''
        Uses a broadcast command to get the tag name of a device. 
        Note that all connected devices will respond so this should only be used with a single device. 
        If the long_frame_address is already known, this command is not necessary.
        '''
        if self.tag_name == None:
            self.command13()
        return self.tag_name
    
    def get_address(self):
        '''
        Uses a broadcast command to get the long_frame_address of a device whose tag name is known. 
        If the long_frame_address is already known, this command is not necessary.
        '''
        if self.tag_name == None:
            self.get_tag_name()
            sleep(.1)
        if self.long_frame_address == None:
            self.command11()
        return self.long_frame_address

    def command11(self):
        command11 = b'\xff\xff\xff\xff\xff\x82\x80\x00\x00\x00\x00\x0b\x06'+self.tag_name
        command11 += checksum_calculation(command11)
        self.ser.write(command11)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = parse_response(self.ser.read_all())
        self.long_frame_address = bytearray([
            data_bytes[1]|0x80,
            data_bytes[2],
            data_bytes[9],
            data_bytes[10],
            data_bytes[11]
            ])
        # print('\n\n Data bytes from Command 11')
        # for el in data_bytes:
        #     print('hex is ',hex(el),'  int is  ', el)
        
        # print('\n\n Long frame address')
        # for el in self.long_frame_address:
        #     print('hex is ',hex(el),'  int is  ', el)
        
    
    def command13(self):
        command13 = b'\xff\xff\xff\xff\xff\x82\x80\x00\x00\x00\x00\x0d\x00\x0f\n'
        self.ser.write(command13)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        self.tag_name = data_bytes[0:6]


    def write_baudrate(self, value):
        '''
        Command 123
        Writes a new baudrate to the unit.
        The function does not return anything given the change in baudrate.
        '''
        supported_baudrates = [9600,19200,38400]
        if value not in supported_baudrates:
            raise Exception('Unsupport baudrate')
        
        self.write_command(123,bytearray([supported_baudrates.index(value)]))
        sleep(.1)
    
    

    def write_command(self,command_number, data=None):
        '''
        Used to send any generic command with the optional data payload.
        Use for commands that have not been implemeneted in this module.
        '''
        if data is None:
            data = bytearray(1)
        else:
            data = bytearray([len(data)]) + data

        command_to_send = b'\xff\xff\xff\xff\xff\x82' + self.long_frame_address + bytearray([command_number]) +  data
        command_to_send += checksum_calculation(command_to_send)

        # print('\n\n Command to send')
        # for el in command_to_send:
        #     print('hex is ',hex(el),'  int is  ', el)
        self.ser.write(command_to_send)
    def read_command(self):
        '''
        Used to read any generic command. 
        Returns the parsed response which includes the address, command_byte, status_bytes, data_bytes.
        '''
        received = self.ser.read_all()
        if received == b'':
            raise Exception('No response received')
        # print(received)
        # for el in received:
        #     print('hex is ',hex(el),'  int is  ', el)
        return parse_response(received)


class mfm(s_protocol_device):
    def __init__(self, com_port, baudrate = 19200, timeout = .1):
        super().__init__(com_port, baudrate, timeout)


    def read_flow_rate(self):
        '''
        Command 1
        Returns the primary variable (flow) along with the units. 
        '''
        self.write_command(1)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        unit_code = data_bytes[0]
        units = units_from_int_flow(unit_code)
        self._units = units
        value = unpack('!f',data_bytes[1:5])[0]
        #value = float(data_bytes[1:5])
        return value, units
    
    def read_full_scale_flow_rate(self,page=1):
        '''
        Command 152
        Returns the value and the units of the specified gas page. 
        Page 1 is the default
        '''
        self.write_command(152,bytearray([page]))
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        unit_code = data_bytes[0]
        units = units_from_int_flow(unit_code)
        self._units = units
        value = unpack('!f',data_bytes[1:5])[0]
        return value, units
    def read_standard_temperature_and_pressure(self):
        '''
        Command 190
        '''
        self.write_command(190)
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        temp_units = units_from_int_temperature(data_bytes[0])
        temperature_value = unpack('!f',data_bytes[1:5])[0]
        pressure_units = units_from_int_pressure(data_bytes[5])
        print(data_bytes[5])
        pressure_value = unpack('!f',data_bytes[6:10])[0]
        return temperature_value, temp_units, pressure_value, pressure_units
    def write_standard_temperature_and_pressure(self,temperature_unit_code,temperature_value,pressure_unit_code,pressure_value):
        '''
        Command 191
        '''
        data = bytearray([temperature_unit_code]) + pack('!f',temperature_value) + bytearray([pressure_unit_code]) + pack('!f',pressure_value)
        self.write_command(191,data)
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        temp_units = units_from_int_temperature(data_bytes[0])
        temperature_value = unpack('!f',data_bytes[1:5])[0]
        pressure_units = units_from_int_pressure(data_bytes[5])
        pressure_value = unpack('!f',data_bytes[6:10])[0]
        return temperature_value, temp_units, pressure_value, pressure_units
    def write_flow_unit(self,flow_ref,flow_unit):
        '''
        Commmand 196
        '''
        data = bytearray([flow_ref, flow_unit])
        self.write_command(196,data)
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return units_from_flow_ref(data[0]), units_from_int_flow(data[1])

    def write_temperature_units(self,temperature_unit):
        '''
        Command 197
        '''
        data = bytearray([temperature_unit])
        self.write_command(197,data)
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return units_from_int_temperature(data[0])
        
class mfc(mfm):
    def __init__(self, com_port, baudrate = 19200, timeout = .1):
        super().__init__(com_port, baudrate, timeout)

    def read_setpoint(self):
        '''
        Command 235
        Returns the setpoint as a percent of full scale as well as the setpoint as a float with units
        '''
        self.write_command(235)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        percent_sp = unpack('!f',data_bytes[1:5])[0]
        setpoint_units = units_from_int_flow(data_bytes[5])
        setpoint_float = unpack('!f',data_bytes[6:10])[0]
        return percent_sp, setpoint_float, setpoint_units

    def write_setpoint(self, setpoint_value, units=57):
        '''
        Command 236
        Writes the setpoint (expreseed as a float) in the given units.
        Select '57' for percent, which is the default
        '''
        data = bytearray([units]) + pack('!f',setpoint_value)
        self.write_command(236, data)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        percent_sp = unpack('!f',data_bytes[1:5])[0]
        setpoint_units = units_from_int_flow(data_bytes[5])
        setpoint_float = unpack('!f',data_bytes[6:10])[0]
        return percent_sp, setpoint_float, setpoint_units
    
    def read_totalizer_status(self):
        '''
        Command 240
        Returns the totalizer status and the totalizer units
        '''
        self.write_command(240)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return totalizer_status_from_int(data_bytes[0]), totalizer_units_from_int(data_bytes[1])
    
    def write_totalizer_control(self, command):
        '''
        Command 241
        Sets the totalizer status and the totalizer units
        '''
        self.write_command(241,bytearray([command]))
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return totalizer_status_from_int(data_bytes[0])
    def read_totalizer_value(self):
        '''
        Command 242
        Reads the totalizer value and the totalizer units
        '''
        self.write_command(242)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return totalizer_units_from_int(data_bytes[0]), unpack('!f',data_bytes[1:5])[0]
    def read_setpoint_source(self):
        '''
        Command 215
        Returns the setpoint source from the table, the setpoint as a float, and the setpoint offset.
        Currently the softstart settings are not supported.
        '''
        self.write_command(215)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        source = setpoint_source_from_int(data_bytes[0])
        setpoint = unpack('!f',data_bytes[1:5])[0]
        setpoint_offset = unpack('!f',data_bytes[5:9])[0]
        return source, setpoint, setpoint_offset

    def write_setpoint_source(self,setpoint_source_code):
        '''
        Command 216
        Takes an integer which specifies the setpoint source.
        See the setpoint source table for the supported sources. 
        '''
        data = bytearray([setpoint_source_from_int(setpoint_source_code)])
        self.write_command(216,data)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return setpoint_source_from_int(data_bytes[0])

class pc(s_protocol_device):
    def __init__(self, com_port, baudrate = 19200, timeout = .1):
        super().__init__(com_port, baudrate, timeout)
    
    def read_pressure(self):
        '''
        Command 1
        Returns the primary variable (flow or pressure) along with the units. 
        '''
        self.write_command(1)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        unit_code = data_bytes[0]
        units = units_from_int_pressure(unit_code)
        self._units = units
        value = unpack('!f',data_bytes[1:5])[0]
        #value = float(data_bytes[1:5])
        return value, units
    
    def read_full_scale_pressure(self,page=1):
        '''
        Command 152
        Returns the value and the units
        Not functional
        '''
        self.write_command(159,bytearray([page]))
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        unit_code = data_bytes[0]
        units = units_from_int_pressure(unit_code)
        self._units = units
        value = unpack('!f',data_bytes[1:5])[0]
        return value, units

    def write_pressure_units(self,pressure_unit):
        '''
        Command 198
        '''
        data = bytearray([pressure_unit])
        self.write_command(198,data)
        sleep(.2)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return units_from_int_pressure(data[0])

    def read_setpoint(self):
        '''
        Command 235
        Returns the setpoint as a percent of full scale as well as the setpoint as a float with units
        '''
        self.write_command(235)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        percent_sp = unpack('!f',data_bytes[1:5])[0]
        setpoint_units = units_from_int_pressure(data_bytes[5])
        setpoint_float = unpack('!f',data_bytes[6:10])[0]
        return percent_sp, setpoint_float, setpoint_units
    
    def write_setpoint(self, setpoint_value, units=57):
        '''
        Command 236
        Writes the setpoint (expreseed as a float) in the given units.
        Select '57' for percent, which is the default
        '''
        data = bytearray([units]) + pack('!f',setpoint_value)
        self.write_command(236, data)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        percent_sp = unpack('!f',data_bytes[1:5])[0]
        setpoint_units = units_from_int_pressure(data_bytes[5])
        setpoint_float = unpack('!f',data_bytes[6:10])[0]
        return percent_sp, setpoint_float, setpoint_units

    #def write_command(self,command_number, data=bytearray(1)):
    def read_setpoint_source(self):
        '''
        Command 215
        Returns the setpoint source from the table, the setpoint as a float, and the setpoint offset.
        Currently the softstart settings are not supported.
        '''
        self.write_command(215)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        source = setpoint_source_from_int(data_bytes[0])
        setpoint = unpack('!f',data_bytes[1:5])[0]
        setpoint_offset = unpack('!f',data_bytes[5:9])[0]
        return source, setpoint, setpoint_offset

    def write_setpoint_source(self,setpoint_source_code):
        '''
        Command 216
        Takes an integer which specifies the setpoint source.
        See the setpoint source table for the supported sources. 
        '''
        data = bytearray([setpoint_source_from_int(setpoint_source_code)])
        self.write_command(216,data)
        sleep(.1)
        [address, command_byte,status_bytes,data_bytes] = self.read_command()
        return setpoint_source_from_int(data_bytes[0])

def checksum_calculation(to_send):
    checksum = 0
    start = False
    for el in to_send:
        if start is False:
            if el==0x86 or el==0x82:
                start = True
            checksum = el
        else:
            checksum = checksum ^ el
    return bytearray([checksum])

def parse_response(response):
    START = 0
    PREAMBLE= 1
    #PREAMBLE2 = 2
    START_CHAR=3
    ADDRESS1 = 4
    ADDRESS2 = 5
    ADDRESS3 = 6
    ADDRESS4 = 7
    ADDRESS5 = 8
    COMMAND = 9
    BYTECOUNT = 10
    STATUS1 = 11
    STATUS2 = 12
    DATA = 13
    CHECKSUM = 14

    status_bytes = bytearray(2)
    command_byte = None
    num_data_bytes = None
    data_bytes_read = 0
    data_bytes = None
    address = bytearray(5)
    
    state = START
    for el in response:
        if state == START:
            if el == 255:
                state = PREAMBLE
        elif state == PREAMBLE:
            if el == 255:
                state = PREAMBLE
            elif el == 134: # hex is 86 for long frame. Consider raising error if it is 06. This is short frame and is not supported.
                state = START_CHAR
        elif state == START_CHAR:
            address[0] = el
            state = ADDRESS1
        elif state == ADDRESS1:
            address[1] = el
            state = ADDRESS2
        elif state == ADDRESS2:
            address[2] = el
            state = ADDRESS3
        elif state == ADDRESS3:
            address[3] = el
            state = ADDRESS4
        elif state == ADDRESS4:
            address[4] = el
            state = COMMAND 
        elif state == COMMAND:
            command_byte = el
            state = BYTECOUNT
        elif state == BYTECOUNT:
            num_data_bytes = el-2 #remove the two status bytes
            data_bytes = bytearray(num_data_bytes)
            state = STATUS1
        elif state == STATUS1:
            status_bytes[0] = el
            state = STATUS2
        elif state == STATUS2:
            status_bytes[1] = el
            state = DATA
        elif state == DATA:
            data_bytes[data_bytes_read] = el
            data_bytes_read += 1
            if data_bytes_read == num_data_bytes:
                state = CHECKSUM
        elif state == CHECKSUM:
            return [address, command_byte,status_bytes,data_bytes]
        else:
            pass
    raise Exception('Failed to parse response.')    


flow_units_table = {
    17:     'Litres/minute',
    19:     'Cubic meters/hour',
    24:     'Litres/second',
    28:     'Cubic meters/second',
    57:     'Percent of flow range',
    131:    'Cubic meters/minute',
    139:    'Liters/hour',
    170:    'Millilitres/second',
    171:    'Millilitres/minute',
    172:    'Millilitres/hour'
    }
flow_ref_table = {
    0:  'Normal',
    1:  'Standard',
    2:  'Calibration'
    }
pressure_units_table = {
    1:      'In of H2O',
    2:      'In of Hg',
    3:      'ft of H2O',
    5:      'psi',
    6:      'psi',
    7:      'bar',
    8:      'mbar',
    11:     'Pa',
    12:     'kPa',
    13:     'Torr',
    14:     'Std Atmsopheres',
    227:    'cm of H2O',
    228:    'g/cm2',
    229:    'mm of Hg',
    230:    'mTorr',
    231:    'Kg/cm2',
    232:    'atm',
    233:    'Ft of H2O',
    234:    'In of H2O',
    235:    'In of Hg',
    236:    'Torr',
    237:    'mbar',
    238:    'bar',
    239:    'Pa',
    240:    'kPa',
    241:    'counts',
    242:    'Percent',
    243:    'Kg/cm2',
    244:    'mTorr',
    245:    'mm of Hg',
    246:    'Grams/cm2'
    }

pressure_type_table = {
    0:      'Absolute pressure',
    1:      'Effective pressure'
    }

temperature_unit_table = {
    32:     'Degrees Celsius',
    33:     'Degrees Fahrenheit',
    35:     'Kelvin'
    }

setpoint_source_table = {
    1:      'Analog Input',
    2:      'Analog Input',
    3:      'Digital Communications',
    10:     'Analog Input and Output 0-5V',
    11:     'Analog Input and Output 1-5V',
    12:     'Analog Input and Output 0-10V',
    20:     'Analog Input and Output 0-20mA',
    21:     'Analog Input and Output 4-20mA'
    }

totalizer_status_table = {
    0:      'Stop totalizer/stopped',
    1:      'Start totalizer/running',
    2:      'Reset totalier counter/resetting'
    }

totalizer_units_table = {
    40:     'Gallons',
    41:     'Liters',
    42:     'Imperial Gallons',
    43:     'Cubic Meters',
    46:     'Barrels',
    60:     'Grams',
    61:     'Kilograms',
    63:     'Pounds',
    112:     'Cubic Feet',
    113:     'Cubic Inches',
    125:     'Ounces',
    175:     'Milliliters',
    241:     'Cubic Centimeters',
    }

def units_from_int_flow(integer):
    units_lookup = flow_units_table
    try:
        units = units_lookup[integer]
    except KeyError:
        units = 'Undefined'
    return units
def units_from_flow_ref(integer):
    units_lookup = flow_ref_table
    try:
        units = units_lookup[integer]
    except KeyError:
        units = 'Undefined'
    return units

def units_from_int_pressure(integer):
    values_lookup = pressure_units_table
    try:
        value = values_lookup[integer]
    except KeyError:
        value = 'Undefined'
    return value

def pressure_type(integer):
    values_lookup = pressure_type_table
    try:
        value = values_lookup[integer]
    except KeyError:
        value = 'Undefined'
    return value

def units_from_int_temperature(integer):
    values_lookup = temperature_unit_table
    try:
        value = values_lookup[integer]
    except KeyError:
        value = 'Undefined'
    return value

def setpoint_source_from_int(integer):
    values_lookup = setpoint_source_table
    try:
        value = values_lookup[integer]
    except KeyError:
        value = 'Undefined'
    return value

def totalizer_status_from_int(integer):
    values_lookup = totalizer_status_table
    try:
        value = values_lookup[integer]
    except KeyError:
        value = 'Undefined'
    return value

def totalizer_units_from_int(integer):
    values_lookup = totalizer_units_table
    try:
        value = values_lookup[integer]
    except KeyError:
        value = 'Undefined'
    return value