'''
Created on 2 Aug 2018

@author: mboscolo
'''
import logging, os

UOM_MATCH = {1: 'PZ',
             3: 'KG',
             4: 'GR',
             11: 'LT'}

from_path = '/mnt/dia/odoo'
if not os.path.exists(from_path):
    logging.warning("Path /mnt/dia/odoo not mounted. Using /tmp/ instead.")
    from_path = '/tmp/'

PRODUCT_FILE = os.path.join(from_path, 'prodotti.txt')
UPDATE_PRODUCT_FILE = os.path.join(from_path, 'u_prodotti.txt')

FILE_CLIENTI = os.path.join(from_path, 'clienti.txt')
UPDATE_FILE_CLIENTI = os.path.join(from_path, 'u_clienti.txt')
FILE_FORNITORI = os.path.join(from_path, 'fornitori.txt')
UPDATE_FILE_FORNITORI = os.path.join(from_path, 'u_fornitori.txt')

WRITE_PICK_OUT_PATH = os.path.join(from_path, 'ddt_vendite.txt')
WRITE_PICK_IN_PATH = os.path.join(from_path, 'ddt_acquisti.txt')

def getDiaUOM(odooUomId):
    if odooUomId not in UOM_MATCH:
        raise Exception("Unable to find uom id in dia match for odoo id %r" % odooUomId)
    return UOM_MATCH.get(odooUomId)


def FTCL(value, size):
    value = str(value)
    if not value or value.upper() == "FALSE":
        value = ""
    return value[:size].ljust(size)


def safeFTCL(value, size):
    try:
        return FTCL(value, size)
    except Exception as ex:
        logging.warning(ex)
    return " " * size
