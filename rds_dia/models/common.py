'''
Created on 2 Aug 2018

@author: mboscolo
'''
import logging
from unidecode import unidecode
UOM_MATCH = {1: 'PZ',
             3: 'KG',
             4: 'GR',
             11: 'LT'}


def getDiaUOM(odooUomId):
    if odooUomId not in UOM_MATCH:
        raise Exception("Unable to find uom id in dia match for odoo id %r" % odooUomId)
    return UOM_MATCH.get(odooUomId)


def FTCL(value, size):
    value = str(value)
    value = unidecode(value)
    if not value or value.upper() == "FALSE":
        value = ""
    return value[:size].ljust(size)


def safeFTCL(value, size):
    try:
        return FTCL(value, size)
    except Exception as ex:
        logging.warning(ex)
    return " " * size
