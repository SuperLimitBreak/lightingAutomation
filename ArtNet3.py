## -*- coding: utf-8 -*-

from struct import Struct
from collections import namedtuple
import socket
import threading

from udp import UDPMixin


OpCodeDefinition = namedtuple('OpCodeDefinition', ('name', 'opcode', 'fields', 'struct'))


class Datagram(object):

    def __init__(self,  opcode_defenitions):
        self.lookup_opcode = {}
        self.lookup_namedtuple = {}
        self.lookup_struct = {}
        for opcode in opcode_defenitions:
            opcode_namedtuple = namedtuple(opcode.name, opcode.fields)
            self.lookup_opcode[opcode.opcode] = opcode_namedtuple
            self.lookup_opcode[opcode_namedtuple] = opcode.opcode
            self.lookup_namedtuple[opcode.name] = opcode_namedtuple
            self.lookup_struct[opcode_namedtuple] = Struct(opcode.struct)

    def get_namedtuple(self, index):
        if (isinstance(index, int)):
            return self.lookup_opcode[index]
        else:
            return self.lookup_namedtuple[index]

    def get_struct(self, opcode_namedtuple):
        return self.lookup_struct[opcode_namedtuple]

    def get_opcode(self, opcode_namedtuple):
        return self.lookup_opcode[opcode_namedtuple]


class ArtNe3tDatagram(Datagram):
    """
    A datagram handler that matches the spec at a binary level.
    A separate layer should be implemented above this class to support more complex decoding and deriving fields:
      e.g. calculating the payload length field OR combining Lo/Hi tuple items to form a single coheran value
    """
    header_id = b'Art-Net\x00'
    header_ProtVer = 14

    opcode_definitions = (
        OpCodeDefinition('Header', None, ('ID', 'OpCode', 'ProtVer'), '>8sHxB'),  # The ProtVer in the spec is a differnt endian to the OpCode - as the Hi byte is never used I've skipped the hi bype with 'xB' rather than 'H'
        OpCodeDefinition('Poll', 0x2000, (), ''),
        OpCodeDefinition('PollReply', 0x2100, (), ''),
        OpCodeDefinition('DiagData', 0x2300, (), ''),
        OpCodeDefinition('Command', 0x2400, (), ''),
        OpCodeDefinition('Output', 0x5000, ('Sequence', 'Physical', 'SubUni', 'Net', 'Length'), '>BBBBH'),
        OpCodeDefinition('Nzs', 0x5100, (), ''),
        OpCodeDefinition('Address', 0x6000, (), ''),
        OpCodeDefinition('Input', 0x7000, (), ''),
        OpCodeDefinition('TodRequest', 0x8000, (), ''),
        OpCodeDefinition('TodData', 0x8100, (), ''),
        OpCodeDefinition('TodControl', 0x8200, (), ''),
        OpCodeDefinition('Rdm', 0x8300, (), ''),
        OpCodeDefinition('RdmSub', 0x8400, (), ''),
        OpCodeDefinition('VideoSetup', 0xa010, (), ''),
        OpCodeDefinition('VideoPalette', 0xa020, (), ''),
        OpCodeDefinition('VideoData', 0xa040, (), ''),
        OpCodeDefinition('MacMaster', 0xf000, (), ''),
        OpCodeDefinition('MacSlave', 0xf100, (), ''),
        OpCodeDefinition('FirmwareMaster', 0xf200, (), ''),
        OpCodeDefinition('FirmwareReply', 0xf300, (), ''),
        OpCodeDefinition('FileTnMaster', 0xf400, (), ''),
        OpCodeDefinition('FileFnMaster', 0xf500, (), ''),
        OpCodeDefinition('FileFnReply', 0xf600, (), ''),
        OpCodeDefinition('IpProg', 0xf800, (), ''),
        OpCodeDefinition('IpProgReply', 0xf900, (), ''),
        OpCodeDefinition('Media', 0x9000, (), ''),
        OpCodeDefinition('MediaPatch', 0x9100, (), ''),
        OpCodeDefinition('MediaControl', 0x9200, (), ''),
        OpCodeDefinition('MediaContrlReply', 0x9300, (), ''),
        OpCodeDefinition('TimeCode', 0x9700, ('Frames', 'Seconds', 'Minutes', 'Hours', 'Type'), 'xxBBBBB'),
        OpCodeDefinition('TimeSync', 0x9800, (), ''),
        OpCodeDefinition('Trigger', 0x9900, (), ''),
        OpCodeDefinition('Directory', 0x9a00, (), ''),
        OpCodeDefinition('DirectoryReply', 0x9b00, (), ''),
    )

    def __init__(self):
        Datagram.__init__(self, ArtNe3tDatagram.opcode_definitions)

    def decode(self, raw_data):
        r"""
        >>> datagram = ArtNe3tDatagram()
        >>> datagram.decode(b'Art-Net\x00\x97\x00\x00\x0e\x00\x00\x18\x3C\x3C\x18\x00')
        (TimeCode(Frames=24, Seconds=60, Minutes=60, Hours=24, Type=0), b'')
        """
        # Decode Header
        header_namedtuple = self.get_namedtuple('Header')
        header_struct = self.get_struct(header_namedtuple)
        header_data = header_namedtuple._make(header_struct.unpack(raw_data[0:header_struct.size]))
        # Check Header
        assert header_data.ID == ArtNe3tDatagram.header_id
        assert header_data.ProtVer == ArtNe3tDatagram.header_ProtVer
        #assert header_data.ProtVerLo == ArtNe3tDatagram.header_ProtVerLo

        # Decode Structured Data (now we know what opcode is being performed)
        data_namedtuple = self.get_namedtuple(header_data.OpCode)
        data_struct = self.get_struct(data_namedtuple)
        data = data_namedtuple._make(data_struct.unpack(raw_data[header_struct.size:]))

        return data, raw_data[header_struct.size + data_struct.size:]

    def encode(self, opcode_namedtuple_data, data=b''):
        r"""
        >>> datagram = ArtNe3tDatagram()
        >>> datagram.encode(datagram.get_namedtuple('TimeCode')(Frames=24, Seconds=60, Minutes=60, Hours=24, Type=0))
        b'Art-Net\x00\x97\x00\x00\x0e\x00\x00\x18<<\x18\x00'
        """
        opcode = self.get_opcode(opcode_namedtuple_data.__class__)
        data_struct = self.get_struct(opcode_namedtuple_data.__class__)

        # Encode Header
        header_namedtuple = self.get_namedtuple('Header')
        header_struct = self.get_struct(header_namedtuple)
        header_data = header_struct.pack(*header_namedtuple(
            ID=ArtNe3tDatagram.header_id,
            OpCode=opcode,
            ProtVer=ArtNe3tDatagram.header_ProtVer,
        ))

        # Encode Data
        payload_data = data_struct.pack(*opcode_namedtuple_data)

        return header_data + payload_data + data


class ArtNet3(UDPMixin):
    DATAGRAM = ArtNe3tDatagram()
    PORT = 0x1936

    def __init__(self):
        UDPMixin.__init__(self, port=ArtNet3.PORT)

    # Recieve ----------

    def _recieve(self, addr, raw_data):
        data, payload = self.DATAGRAM.decode(raw_data)
        if isinstance(data, self.get_namedtuple('Output')):
            self.recieve_dmx(payload)
        else:
            self.recieve(data, payload)

    def recieve(self, data, payload):
        print('received {0}: {1}'.format(data, payload))

    def recieve_dmx(self, data):
        print(data)

    # Data handling ------

    def get_namedtuple(self, name):
        return self.DATAGRAM.get_namedtuple(name)

    def _dmx(self, data):
        r"""
        >>> art3 = ArtNet3()
        >>> art3._dmx(b'\x00\x01\x02\x03')
        b'Art-Net\x00P\x00\x00\x0e\x00\x00\x00\x00\x00\x04\x00\x01\x02\x03'
        """
        assert len(data) % 2 == 0, "data payload must be an even length"  # Todo: padd data to an even length automatically
        output_data = self.get_namedtuple('Output')(
            Sequence=0,
            Physical=0,
            SubUni=0,
            Net=0,
            Length=len(data)
        )
        return self.DATAGRAM.encode(output_data, data)

    def dmx(self, data):
        self._send(self._dmx(data))
