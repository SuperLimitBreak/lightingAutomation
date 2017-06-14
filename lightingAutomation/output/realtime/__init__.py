import logging

log = logging.getLogger(__name__)

from .dmx import RealtimeOutputDMX
from .json import RealtimeOutputJSON


class RealtimeOutputManager(object):
    def __init__(self, device_collection, options):
        self.device_collection = device_collection
        self._output = {}

        # With options init the required renderers
        if options.get('dmx_host') and options.get('dmx_mapping'):
            self._output['dmx'] = RealtimeOutputDMX(device_collection, options['dmx_host'], options['dmx_mapping'])
        if options.get('json_send'):
            self._output['json'] = RealtimeOutputJSON(device_collection, options['json_send'])

    def close(self):
        """
        Clear all of the outputs and send a final blank state
        """
        self.device_collection.reset()
        self.update()

    def update(self):
        """
        Output the state of the device_collection to the registered output renderers
        """
        for output in self._output.values():
            output.update()