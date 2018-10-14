from pymodbus.server.async import StartTcpServer

from pymodbus.device import ModbusDeviceIdentification

from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext


##LOGGING
import logging, datetime
log = logging.getLogger(__name__)


class CallbackDataBlock(ModbusSparseDataBlock):
    ''' A datablock that stores the new value in memory
    and passes the operation to a message queue for further
    processing.
    '''

    def __init__(self, values, queue, signals_ids):
        self.queue = queue
        self.signals = signals_ids

        super(CallbackDataBlock, self).__init__(values)

    def setValues(self, address, value):
        ''' Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        '''
        try:
            super(CallbackDataBlock, self).setValues(address, value)
            if address in self.signals:
                self.queue.put([address, datetime.datetime.utcnow(), value])
        except Exception as e:
            logging.exception(e)


def build_server(queue, signals, config):
    args = [[17]*100, queue, signals]

    store = ModbusSlaveContext(
        di = CallbackDataBlock(*args),
        co = CallbackDataBlock(*args),
        hr = CallbackDataBlock(*args),
        ir = CallbackDataBlock(*args)
    )
    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()

    identity.VendorName  = config.get('vendor_name','Pymodbus')
    identity.ProductCode = config.get('product_code','PM')
    identity.VendorUrl   = config.get('vendor_url', 'http://github.com/bashwork/pymodbus/')
    identity.ProductName = config.get('product_name', 'Pymodbus Server')
    identity.ModelName   = config.get('model_name','Pymodbus Server')
    identity.MajorMinorRevision = config.get('version','1.0')
    
    return {'context': context, 'identity': identity, 'address': ( config.get('address', "10.15.0.125"), int(config.get('port', 502)) )}