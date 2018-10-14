#!/usr/bin/python3
'''
Created on Jun 4, 2018

@author: daniel
'''
# Create crontab linux
# crontab -e
# 15     17     *     *     *  python /srv/workspace/clienti/nardo_vetro/addons/mrp_extension/chronoJob/chrono_job.py

import datetime
import time
import logging
import os
import socket
import xmlrpc.client

modulePath = os.path.dirname(__file__)
logfile = os.path.join(modulePath, 'chronojob_cronMachineClient.log')
logging.basicConfig(filename=logfile,
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s]%(name)s - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('Start updating Odoo Machine Client')

# userName = 'administrator@rdsmoulding.com'
# userPassword = 'ace0896AC21??'
# databaseName = 'rds_real_2'
# xmlrpcPort = '8069'
# xmlrpcServerIP = '127.0.0.1'
# scheme = 'http'
# connectionType = 'xmlrpc'

userName = 'administrator@rdsmoulding.com'
userPassword = 'ace0896AC21??'
databaseName = 'rdsdb2'
xmlrpcPort = '8069'
xmlrpcServerIP = '127.0.0.1'
scheme = 'http'
connectionType = 'xmlrpc'

urlCommon = scheme + '://' + str(xmlrpcServerIP) + ':' + str(xmlrpcPort) + '/xmlrpc/'
urlNoLogin = urlCommon + 'common'
urlYesLogin = urlCommon + 'object'


def callOdooFunction(odooObj, functionName, parameters=[], kwargParameters={}):
    '''
        @odooObj: product.product, product.template ...
        @functionName: 'search', 'read', ...
        @parameters: [val1, val2, ...]
        @kwargParameters: {'context': {}, limit: val, 'order': val,...}
    '''
    try:
        return socketYesLogin.execute_kw(databaseName,
                                         userId,
                                         userPassword,
                                         odooObj,
                                         functionName,
                                         parameters,
                                         kwargParameters)
    except socket.error as err:
        logging.error('Unable to communicate with the server: %r' % err)
    except xmlrpc.client.Fault as err:
        try:
            return socketYesLogin.execute(databaseName, userId, userPassword, odooObj, functionName, parameters)
        except Exception as ex:
            logging.error('Unable to communicate with the server: %r' % ex.faultCode)
    except Exception as ex:
        logging.error(ex)
    return False


while True:
    try:
        socketNoLogin = xmlrpc.client.ServerProxy(urlNoLogin)
        userId = socketNoLogin.login(databaseName, userName, userPassword)
        if userId:
            socketYesLogin = xmlrpc.client.ServerProxy(urlYesLogin)
            logging.info('Calling method cronMachineClient')
            try:
                res = callOdooFunction(odooObj='mrp.workcenter', functionName='cronMachineClient')
                if not res:
                    logging.error('Unable to call server')
            except Exception as ex:
                logging.error(ex)
        else:
            logging.info('User not logged')
        logging.info('Datetime %s' % (datetime.datetime.now()))
    except Exception as ex:
        logging.error(ex)
    time.sleep(30)  # Not 20 because the procedure spend itself 2-3 seconds

logging.info('CLOSED CONNECTION')
