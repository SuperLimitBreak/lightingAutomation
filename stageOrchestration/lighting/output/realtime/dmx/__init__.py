import logging

import yaml
from pysistence import make_dict

from .ArtNet3 import ArtNet3

from . import dmx_devices

log = logging.getLogger(__name__)


class RealtimeOutputDMX(object):
    def __init__(self, host='localhost', mapping_config_filename=None):
        """
        Mapping config is a YAML file with the following format

            alias_name_for_light:
                type: FunctionNameIn_dmx_devices
                index: 183

            # Optional - special control (will default to 512 if omitted)
            dmx_size: 256

        """
        log.info(f'Init DMX Output {host}')
        self.artnet = ArtNet3(host)
        with open(mapping_config_filename, 'rt') as filehandle:
            self.mapping = make_dict(yaml.safe_load(filehandle))
        assert self.mapping, f'No DMX Mappings loaded from {mapping_config_filename}'
        self.buffer = bytearray(self.mapping.get('dmx_size', 512))

    def send(self, device_collection):
        self.artnet.dmx(self._render_dmx(device_collection, self.mapping, self.buffer))

    @staticmethod
    def _render_dmx(device_collection, mapping, buffer):
        """
        With mapping, convert device_collection to dmx bytes
        """
        for device_name, device in device_collection._devices.items():
            dmx_device_type, dmx_index = (mapping[device_name][attribute] for attribute in ('type', 'index'))
            dmx_bytes = getattr(dmx_devices, dmx_device_type)(device)
            buffer[dmx_index:dmx_index+len(dmx_bytes)] = dmx_bytes
        return buffer
