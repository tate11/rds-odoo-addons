#---------------------------------------------------------------------------# 
#---------------------------------------------------------------------------# 
# import the python libraries we need
#---------------------------------------------------------------------------# 
from multiprocessing import Queue, Process
import sys

from datetime import datetime as dt

#---------------------------------------------------------------------------# 
# configure the service logging
#---------------------------------------------------------------------------# 
import configparser
try:
    config = configparser.ConfigParser()
    config.read('config.ini')
except IOError:
    raise IOError("Configuration file not found!")

#---------------------------------------------------------------------------# 
# configure the service logging
#---------------------------------------------------------------------------# 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

from server import environment, modbus
from lib import signals


environment.initENV(**config['DB'])
ENV = environment.getEnv()

#---------------------------------------------------------------------------# 
# Initialize Data
#---------------------------------------------------------------------------# 

signals = signals.load_signals(ENV,ENV.get_signal_raw())

#---------------------------------------------------------------------------# 
# Prepare the process
#---------------------------------------------------------------------------# 

queue = Queue()

def Worker(queue):
    ''' A worker process that processes new messages
    from a queue.

    :param queue: The queue to get new messages from
    '''
    while True:
        if queue:
            sigid, dt, value = queue.get()
            signals[sigid].signal(dt, value)

p = Process(target=Worker, args=(queue,))

#---------------------------------------------------------------------------# 
# Server Start
#---------------------------------------------------------------------------#

boot_msg ="""\n
      ___           ___           ___           ___           ___           ___           ___           ___     
     /\__\         /\  \         /\__\         /\  \         /\  \         /\  \         /\  \         /\__\    
    /:/  /        /::\  \       /::|  |        \:\  \       /::\  \       /::\  \       /::\  \       /:/  /    
   /:/__/        /:/\:\  \     /:|:|  |         \:\  \     /:/\:\  \     /:/\:\  \     /:/\:\  \     /:/  /     
  /::\__\____   /:/  \:\  \   /:/|:|  |__       /::\  \   /::\~\:\  \   /:/  \:\  \   /::\~\:\  \   /:/  /  ___ 
 /:/\:::::\__\ /:/__/ \:\__\ /:/ |:| /\__\     /:/\:\__\ /:/\:\ \:\__\ /:/__/ \:\__\ /:/\:\ \:\__\ /:/__/  /\__\\
 \/_|:|~~|~    \:\  \ /:/  / \/__|:|/:/  /    /:/  \/__/ \/_|::\/:/  / \:\  \ /:/  / \/_|::\/:/  / \:\  \ /:/  /
    |:|  |      \:\  /:/  /      |:/:/  /    /:/  /         |:|::/  /   \:\  /:/  /     |:|::/  /   \:\  /:/  / 
    |:|  |       \:\/:/  /       |::/  /     \/__/          |:|\/__/     \:\/:/  /      |:|\/__/     \:\/:/  /  
    |:|  |        \::/  /        /:/  /                     |:|  |        \::/  /       |:|  |        \::/  /   
     \|__|         \/__/         \/__/                       \|__|         \/__/         \|__|         \/__/    

============== Welcome to KONTRORU. Preparing to launch server with the following configuration: ==============\n\n
"""

conn_dict = ENV.__dict__
boot_msg += "Database:\n\tType: {},\n\tAddress: {}\n\tUUID: {}\n\n".format(conn_dict['db_type'], conn_dict['db_address'], conn_dict['UUID'])

boot_msg += "Signals:\n"
for key in signals.keys():
    boot_msg += "\t[{}] {}\n\t\tType: {}\n\t\tCoil: {}\n".format(signals[key].id, signals[key].name, signals[key].__class__.__name__, key)

modbus_data = modbus.build_server(queue, list(signals.keys()), config['MODBUS'])

print("\n"*100)
print(boot_msg)
print("\n\nModbus server and callback subprocess will now start on {}:{}.\n\n".format(modbus_data['address'][0],modbus_data['address'][1]))

del boot_msg
del conn_dict

try:
    p.start()
    modbus.StartTcpServer(**modbus_data)
except Exception as e:
    sys.exit(e)