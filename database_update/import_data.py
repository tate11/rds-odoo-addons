# -*- coding: utf-8 -*-

'''
Created on Apr 13, 2018

@author: daniel
'''
DEFAULT_SERVER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from DbWrapper.wrapperOpenERP import BaseDbIntegration
import csv
import os
import logging
import time
import xlrd
from xlrd.sheet import ctype_text
import datetime
from dateutil import parser
from gdata.tlslite.BaseDB import BaseDB

SERVER_PORT = '8069'
#SERVER_PORT = '8084'
BOH = ''
SCHEME = 'http'


#USER_NAME = 'administrator@rdsmoulding.com'
#USER_PASS = 'admin'

DB_NAME = 'rdsdb1'
DB_NAME = 'rdsdb2'
#DB_NAME = 'rdsdb'

#DB_NAME = 'rds_pretest'
# DB_NAME = 'rdsdb_2018-07-13_14-08-14.'
# DB_NAME = 'rds_real'
#DB_NAME = 'rds_real_5'

USER_NAME = 'administrator@rdsmoulding.com'

# USER_PASS = 'a'
USER_PASS = 'ace0896AC21??'



SERVER_IP = '10.15.0.112'
#SERVER_IP = '10.15.0.113'
#SERVER_IP = 'localhost'

IMP_STOCK_ID = 15

currentDir = os.getcwd()
logOutListBom = []
logOutListRouting = []
logOutListSaleOrder = []

DISTINTE_COMPLETE = os.path.join(currentDir, "DISTINTE_COMPLETE.TXT")
bomFilePath = os.path.join(currentDir, "distinte_rds.csv")
routingFilePath = os.path.join(currentDir, "cicli_rds_routing.csv")
saleOrderFilePath = os.path.join(currentDir, "ORDINI_APERTI.csv")
saleOrderFilePath = os.path.join(currentDir, "ORDINI_APERTI.xlsx")
mold_path = os.path.join(currentDir, "Attrezzature_20180625.xlsx")
ANA_FORM = os.path.join(currentDir, "AN_FOR.CSV")
ANA_ART = os.path.join(currentDir, "AN_ART.CSV")
STRUTTURE = os.path.join(currentDir, "STRUTTURE.CSV")
GIACENZE = os.path.join(currentDir, "GIACENZE.CSV")
DEPOSITI = os.path.join(currentDir, "DEPOSITI.CSV")
logOutBomFile = os.path.join(currentDir, "distinte_rds_log.txt")
logOutRoutingFile = os.path.join(currentDir, "routing_rds_log.txt")
logOutSaleOrderFile = os.path.join(currentDir, "sale_order_rds_log.txt")
COSTO_LAV_ESTERNE = os.path.join(currentDir, 'COSTO_LAV_ESTERNE.xlsx')
impronte_CSV = os.path.join(currentDir, "impronte.CSV")
ANAG_TOTALE = os.path.join(currentDir, "ANAG_TOTALE.xlsx")
UPDATE_VENDOR = os.path.join(currentDir, "UPDATE_VENDOR.CSV")
VEDNOR_ANAG_DIA_IVA = os.path.join(currentDir, "Clienti_Con_Esenzione-1.xlsx")
UPDATE_CAUSALI = os.path.join(currentDir, "Causali_DDT.xlsx")


def safetyGet(passDict, key, fcall):
    if key not in passDict:
        passDict[key] = fcall(key)
    return passDict[key]


def printAndLog(msg, typeAppend):
    '''
        Eventualmente abilitare il log per file  e abilitare le scritture in questa funzione al posto degli append
        E chiudere i file alla fine di tutto
    '''
    print (msg)
    logging.info(msg)
#     if typeAppend == 'bom':
#         logOutListBom.append(msg)
#     elif typeAppend == 'routing':
#         logOutListRouting.append(msg)
#     elif typeAppend == 'sale':
#         logOutListSaleOrder.append(msg)


def printAndLogBom(msg):
    printAndLog(msg, 'bom')


def printAndLogRouting(msg):
    printAndLog(msg, 'routing')


def printAndLogSale(msg):
    printAndLog(msg, 'sale')


textDelimiter = '|'
quoteChar = '^'

prodDict = {}
relationDict = {}

print ("Odoo Login")
BaseDbIntegration.create(USER_NAME, USER_PASS, DB_NAME, SERVER_IP, SERVER_PORT, BOH, SCHEME)
res = BaseDbIntegration.Search('res.users', [])
if not res:
    printAndLogBom('Cannot login to Odoo')
    raise Exception("Unable to login")
print ("Odoo Login done")

BY_RUTE = []


def getBuyRoute():
    global BY_RUTE
    if BY_RUTE:
        return BY_RUTE
    res = BaseDbIntegration.GetDetailsSearch('stock.location.route', queryFilter=[
        ('name', '=', 'Buy'),
        ('product_selectable', '=', True)], fields=['id'])
    for elem in res:
        BY_RUTE = [elem.get('id')]
        return BY_RUTE
    return []


def sanitizeString(val):
    return str(val).strip()


def sanitizeDiaId(val):
    out = sanitizeString(val)
    return out.split(" ")[-1] or out.split(" ")[0]


def sanitizeUpper(val):
    return sanitizeString(val).upper()


def sanitizeUpperCode(val):
    val = sanitizeString(val).upper()
    return val.split(" ")[-1]


def getRDSCategory():
    category_id = BaseDbIntegration.Search('product.uom.categ',
                                           [('name', '=', 'RDS')],
                                           onlyFirst=True)
    if not category_id:
        category_id = BaseDbIntegration.Create('product.uom.categ', {'name': 'RDS'})
    return category_id


def sanitizeDouble(val):
    return float(val)


def sanitizeDoubleITA1(val):
    val = val.replace(",", '')
    return float(val)


def sanitizeDoubleITA(val):
    val = val.replace(".", "").replace(",", '.')
    return float(val)


def sanitizeCustomerId(value):
    value = sanitizeXLSLSTRING(value)
    if len(value) == 7:
        value = "0" + value
    return value


def sanitizeXLSLSTRING(value):
    return str(value).strip().replace('.0', '')


def createUom(uomName):
    infoValue = {'name': uomName,
                 'category_id': getRDSCategory()}
    return BaseDbIntegration.Create('product.uom', infoValue)


def getManufactureRouteID():
    res = BaseDbIntegration.GetDetailsSearch('stock.location.route', queryFilter=[
        ('name', 'in', ['Manufacture', 'Make To Order']),
        ('product_selectable', '=', True)], fields=['id'])
    outList = []
    for elem in res:
        outList.append(elem.get('id'))
    return outList


def createProduct(infoValue, reorderingRule=True, create=True):
    prodId = False
    try:
        prodId = BaseDbIntegration.Search('product.product', [('default_code', '=', unicode(infoValue['default_code']).strip())])
        if not prodId:
            if create:
                infoValue['uom_po_id'] = infoValue.get('uom_id', False)
                prodId = BaseDbIntegration.Create('product.product', infoValue)
                if reorderingRule:
                    createReorderingRule(prodId)
        else:
            prodId = prodId[0]
    except Exception as ex:
        printAndLogBom('Errors during create product %r. Ex %r' % (infoValue, ex))
    return prodId


def createBuyProduct(vals):
    vals['purchase_ok'] = True
    vals['sale_ok'] = True
    vals['route_ids'] = [(6, 0, getBuyRoute())]
    return createProduct(vals)


def createProductionProduct(vals):
    vals['purchase_ok'] = True
    vals['sale_ok'] = True
    vals['route_ids'] = [(6, 0, manufactureRouteID)]
    return createProduct(vals, reorderingRule=False)


def getProductType(compName):
    firstLetter = compName[0]
    try:
        firstLetter = int(firstLetter)
        return 'buy'
    except Exception as _ex:
        pass
    return 'produce'


def createBOM(row, prodId, rootProdDesc):
    bomID = False
    tmplId = getProdTmplFromProdId(prodId)
    if not tmplId:
        printAndLogBom('Unable to get product template from product %r, prodId %r' % (row, prodId))
        return bomID
    vals = {
        'product_tmpl_id': tmplId,
        'type': 'normal',
        'state': 'draft',
        'description': rootProdDesc}
    try:
        bomID = BaseDbIntegration.Create('mrp.bom', vals)
    except Exception as ex:
        printAndLogBom('Unable to create BOM with values %r. Error %r' % (vals, ex))
    return bomID


def createBomLine(vals):
    bomID = False
    try:
        bomID = BaseDbIntegration.Create('mrp.bom.line', vals)
    except Exception as ex:
        printAndLogBom('Unable to create BOM line with values %r. Error %r' % (vals, ex))
    return bomID


def getProdTmplFromProdId(prodId):
    bomID = False
    try:
        res = BaseDbIntegration.GetDetailsSearch('product.product', [('id', '=', prodId)], fields=['product_tmpl_id'])
        bomID = res[0]['product_tmpl_id'][0]
    except Exception as ex:
        printAndLogBom('Unable to get product template %r. Error %r' % (prodId, ex))
    return bomID


def createReorderingRule(prodId):
    reorderId = False
    try:
        vals = {
            'product_id': prodId,
            'product_min_qty': 0,
            'product_max_qty': 0}
        reorderId = BaseDbIntegration.Create('stock.warehouse.orderpoint', vals)
    except Exception as ex:
        printAndLogBom('Unable to create reordering rule with values %r. Error %r' % (vals, ex))
    return reorderId


def createRootChildProducts(parentProdName, desc1, desc2, childCompName, descChildProd1, descChildProd2, row, uom_id):
    prodId = False
    prodChildId = False
    rootProdDesc = desc1 + ' ' + desc2
    if parentProdName not in prodDict.keys():
        vals = {'description': '',
                'name': rootProdDesc,
                'default_code': parentProdName,
                'uom_id': uom_id}
        prodType = getProductType(parentProdName)
        if prodType == 'buy':
            prodId = createBuyProduct(vals)
        elif prodType == 'produce':
            prodId = createProductionProduct(vals)
        if not prodId:
            printAndLogBom('Unable to get new product with vals %r' % (vals))
            return prodId, prodChildId
        vals['id'] = prodId
        prodDict[parentProdName] = vals
    else:
        prodId = prodDict[parentProdName]['id']
    if not prodId:
        printAndLogBom('Unable to get product ID with vals %r' % (row))
        return prodId, prodChildId
    childProdDesc = descChildProd1 + ' ' + descChildProd2
    if childCompName not in prodDict.keys():
        vals = {'description': '',
                'name': childProdDesc,
                'default_code': childCompName,
                'uom_id': uom_id}
        prodType = getProductType(childCompName)
        if prodType == 'buy':
            prodChildId = createBuyProduct(vals)
        elif prodType == 'produce':
            prodChildId = createProductionProduct(vals)
        if not prodChildId:
            printAndLogBom('Unable to get new product with vals %r' % (vals))
            return prodId, prodChildId
        vals['id'] = prodChildId
        prodDict[childCompName] = vals
    else:
        prodChildId = prodDict[childCompName]['id']
    if not prodChildId:
        printAndLogBom('Unable to get product ID with vals %r' % (row))
        return prodId, prodChildId
    return prodId, prodChildId


#manufactureRouteID = getManufactureRouteID()


def getIdName(model):
    out = {}
    res = BaseDbIntegration.GetDetailsSearch(model, [], ['Id', 'name'])
    for a in res:
        out[a.get('name')] = a.get('id')
    return out


def getIdField(model, field='name'):
    out = {}
    out_field = ['id']
    out_field.append(field)
    res = BaseDbIntegration.GetDetailsSearch(model, [], out_field)
    for a in res:
        out[a.get(field)] = a.get('id')
    return out

#questa e' la' trasformazione fatta per portare uom da odoo a dia o viceversa
# per questo i dati sono stati non letti + dal db ma messi hard coded
# 1    Unit(s)       20    PZ  22    CF 23    RT 21    N
# 3    kg            24    KG
# 4    g          26    GR
# 11    Liter(s)      25    LT


def getAllUom():  # queryFilter, fields
    return {'PZ': 1,
            'CF': 1,
            'RT': 1,
            'm': 1,
            'KG': 3,
            'GR': 4,
            'LT': 25}
#     for k, v in getIdName('product.uom'):
#         out[match.get(k)] = v
#    return out


def getAllAccountPaymentTerm():  # queryFilter, fields
    return getIdName('account.payment.term')


def impBom(parent_name=False):
    um = getAllUom()
    bomRoute = []
    printAndLogBom('Start reading Bom file')
    with open(bomFilePath, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=textDelimiter, quotechar=quoteChar)
        count = 0
        for row in spamreader:
            try:
                print ("BOM compute  row-%r" % (int(spamreader.line_num)))
                if count == 0:
                    count = count + 1
                    continue
                if len(row) != 10:
                    printAndLogBom('Line read in wrong model %r' % (row))
                    continue
                parentProdName, desc1, desc2, level, childCompName, descChildProd1, descChildProd2, unitMeasure, qtyImpiegata, _qtyEffettiva = row
                uom_id = um.get(unicode(unitMeasure).strip(), 1)
                parentProdName = unicode(parentProdName).strip()
                if parent_name != parentProdName:
                    continue
                childCompName = unicode(childCompName).strip()
                print ('%s --> %s' % (parentProdName, childCompName))
                level = int(level)
                # Create product
                rootProdDesc = unicode(desc1).strip() + ' ' + unicode(desc2).strip()
                prodId, prodChildId = createRootChildProducts(parentProdName, desc1, desc2, childCompName, descChildProd1, descChildProd2, row, uom_id)
                if not prodId or not prodChildId:
                    continue
                if bomRoute and prodId != bomRoute[0]:
                    bomRoute = [prodId, prodChildId]
                # Create BOM
                if level == 1:
                    if prodId not in relationDict.keys():   # New BOM:
                        bomID = createBOM(row, prodId, rootProdDesc)
                        if not bomID:
                            continue
                        relationDict[prodId] = bomID
                    else:
                        bomID = relationDict[prodId]
                else:
                    if len(bomRoute) >= level - 1:
                        lastProdId = bomRoute[level - 1]
                        if lastProdId not in relationDict.keys():   # New BOM:
                            bomID = createBOM(row, lastProdId, rootProdDesc)
                            if not bomID:
                                continue
                            relationDict[lastProdId] = bomID
                        else:
                            bomID = relationDict[lastProdId]
                    else:
                        pass
                # Add bom line
                bomLineVals = {
                    'product_id': prodChildId,
                    'type': 'normal',
                    'product_qty': float(qtyImpiegata.replace(".", "").replace(",", ".").strip()),
                    'bom_id': bomID,
                    'product_uom_id': uom_id}
                bomLineID = createBomLine(bomLineVals)
                if not bomLineID:
                    printAndLogBom('Unable to create BOM Line with values %r' % bomLineVals)
                if level == 1:
                    bomRoute = [prodId, prodChildId]
                else:   # Restore route based on level
                    bomRoute = bomRoute[:level]
                    bomRoute.append(prodChildId)
            except Exception as ex:
                print (ex)
    printAndLogBom('End Reading Bom file')


def createRouting(vals, create=True):
    routingId = False
    try:
        routingId = BaseDbIntegration.Search('mrp.routing', [('name', '=', vals['name'])])
        if not routingId and create:
            routingId = BaseDbIntegration.Create('mrp.routing', vals)
        else:
            routingId = routingId[0]
    except Exception as ex:
        printAndLogRouting('Errors during create routing %r. Ex %r' % (vals, ex))
    return routingId


def createOperation(vals):
    operationId = False
    try:
        operationId = BaseDbIntegration.Create('mrp.routing.workcenter', vals)
    except Exception as ex:
        printAndLogRouting('Errors during create operation %r. Ex %r' % (vals, ex))
    return operationId


def createWorkCenter(vals):
    wcId = False
    try:
        wcId = BaseDbIntegration.Search('mrp.workcenter', [('code', '=', vals['code'])])
        if not wcId:
            wcId = BaseDbIntegration.Create('mrp.workcenter', vals)
        else:
            wcId = wcId[0]
    except Exception as ex:
        printAndLogRouting('Errors during create workcenter %r. Ex %r' % (vals, ex))
    return wcId


def addRoutingToBom(productName, routing_id):
    try:
        product_id = BaseDbIntegration.Search('product.template', [('default_code', '=', productName)])
        bom_id = BaseDbIntegration.Search('mrp.bom', [('product_tmpl_id', '=', product_id)])
        values = {'routing_id': routing_id}
        BaseDbIntegration.UpdateValue('mrp.bom', bom_id, values)
    except Exception as ex:
        print ("Unable to create routing", ex)


def impRouting():
    printAndLogRouting('Start reading routing file')
    workcenter_spool = {}
    wcVals = {'name': 'Centro Di Pesatura Alluminio',
              'code': 'CPA'}
    wc_pesa_id = createWorkCenter(wcVals)
    wcVals = {'name': 'Area Preparazione Stampi',
              'code': 'APS'}
    wc_aps_id = createWorkCenter(wcVals)
    with open(routingFilePath, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for row in spamreader:
            print ("Routing compute  row-%r" % (int(spamreader.line_num)))
            if count == 0:
                count = count + 1
                continue
            if len(row) != 26:
                printAndLogRouting('Unable to find correct formatting %r' % (row))
            proName = unicode(row[0]).strip()
            sequence = int(row[3])
            #   prodDesc = row[1]
            operazione = unicode(row[4]).strip()
            wcName = unicode(row[5]).strip() or 'MISSING WORKCENTER'
            tempoLavoroMacchina = (sanitizeDoubleITA1(row[11]) / 1000.0) / 60.0
            tempoPrepMacchina = (sanitizeDoubleITA1(row[9]) / 1000.0) / 60.0
            try:
                noteFase = unicode(row[13]).strip()
            except Exception:
                noteFase = row[13]
            vals = {
                'name': "R-" + proName}
            routingId = createRouting(vals)
            if not routingId:
                ERROR_BUF.append("Unable to create routing with vals %r" % vals)
                continue
            wcVals = {
                'name': wcName,
                'code': wcName}
            wc_id = workcenter_spool.get(wcName)
            if not wc_id:
                wc_id = createWorkCenter(wcVals)
            workcenter_spool[wcName] = wc_id
            valsOperation = {
                'name': operazione,
                'routing_id': routingId,
                'time_cycle_manual': tempoLavoroMacchina,
                'time_mount_machine': tempoPrepMacchina,
                'note': noteFase,
                'workcenter_id': wc_id,
                'sequence': sequence,
                'time_mode': 'manual'}
            if operazione == 'ALPREP':
                valsOperation['workcenter_id'] = wc_aps_id
            createOperation(valsOperation)
            if operazione == 'ALAUT':
                valsOperation = {'name': 'PESA',
                                 'routing_id': routingId,
                                 'time_cycle_manual': 0.0,
                                 'time_mount_machine': 0.0,
                                 'note': 'Pesa Materiale',
                                 'workcenter_id': wc_pesa_id,
                                 'sequence': sequence + 10,
                                 'time_mode': 'manual'}
                createOperation(valsOperation)
            addRoutingToBom(proName, routingId)
    printAndLogRouting('End reading routing file')


def createSaleOrder(vals, err=[]):
    orderId = False
    try:
        orderId = BaseDbIntegration.Search('sale.order', [('name', '=', vals.get('name'))], onlyFirst=True)
        if not orderId:
            orderId = BaseDbIntegration.Create('sale.order', vals)
    except Exception as ex:
        msg = 'Errors during create sale order %r. Ex %r' % (vals, ex)
        err.append(msg)
        printAndLogSale(msg)
    return orderId


def createSaleOrderLine(vals, err=[]):
    orderId = False
    try:
        orderId = BaseDbIntegration.Create('sale.order.line', vals)
    except Exception as ex:
        msg = 'Errors during create sale order line %r. Ex %r' % (vals, ex)
        printAndLogSale(msg)
        err.append(msg)
    return orderId


def confirmSaleOrder(order_ids):
    for order_id in order_ids:
        BaseDbIntegration.callCustomMethod('sale.order', 'action_confirm', order_id)


def createPartner(vals):
    wcId = False
    try:
        wcId = BaseDbIntegration.Search('res.partner', [('name', 'like', vals['name'])])
        if not wcId:
            wcId = BaseDbIntegration.Create('res.partner', vals)
        else:
            wcId = wcId[0]
    except Exception as ex:
        printAndLogSale('Errors during create partner %r. Ex %r' % (vals, ex))
    return wcId


def getPartnerFromPartnerId(partner_name):
    return BaseDbIntegration.Search('res.partner',
                                    [('dia_ref_customer', 'like', partner_name)],
                                    onlyFirst=True)


def getCreatePartnerLocation(partner_id, location_name, location_id, full_anag):
    oldLocId = getPartnerFromPartnerId(location_id)
    if not oldLocId:
        vals = {'name': location_name,
                'type': 'delivery',
                'parent_id': partner_id,
                'dia_ref_customer': location_id}
        oldLocId = BaseDbIntegration.Create('res.partner', vals)
        full_anag.odooCreate(location_id)
    return oldLocId


def getOdooCodes():
    odoo_ref = {}
    odoo_ref['00068620392'] = '142'
    odoo_ref['00121890933'] = '29'
    odoo_ref['00142500354'] = '21'
    odoo_ref['00165200270'] = '23'
    odoo_ref['00197370281'] = '109'
    odoo_ref['00476190012'] = '61'
    odoo_ref['00500551205'] = '25'
    odoo_ref['00557280989'] = '98'
    odoo_ref['00572250983'] = '160'
    odoo_ref['00576020267'] = '194'
    odoo_ref['00593101207'] = '122'
    odoo_ref['00637130360'] = '89'
    odoo_ref['00656900271'] = '220'
    odoo_ref['00658500236'] = '100'
    odoo_ref['00681370268'] = '37'
    odoo_ref['00681370268'] = '38'
    odoo_ref['00879740264'] = '2283'
    odoo_ref['00879740264'] = '54'
    odoo_ref['00888520244'] = '144'
    odoo_ref['00957910284'] = '228'
    odoo_ref['00973000284'] = '188'
    odoo_ref['01047610595'] = '168'
    odoo_ref['01147330284'] = '189'
    odoo_ref['01234660221'] = '76'
    odoo_ref['02157220241'] = '171'
    odoo_ref['02161730243'] = '123'
    odoo_ref['02318160286'] = '185'
    odoo_ref['02353470285'] = '225'
    odoo_ref['02490560287'] = '116'
    odoo_ref['02494540285'] = '108'
    odoo_ref['02506060280'] = '33'
    odoo_ref['02639920244'] = '219'
    odoo_ref['02647040233'] = '26'
    odoo_ref['03332370281'] = '177'
    odoo_ref['03336810274'] = '126'
    odoo_ref['03481280265'] = '63'
    odoo_ref['03481280265'] = '62'
    odoo_ref['03495150280'] = '181'
    odoo_ref['03775610235'] = '80'
    odoo_ref['03906220284'] = '186'
    odoo_ref['04002310169'] = '96'
    odoo_ref['04216230286'] = '180'
    odoo_ref['04218710962'] = '86'
    odoo_ref['04599890268'] = '145'
    odoo_ref['04706800267'] = '78'
    odoo_ref['05398731009'] = '67'
    odoo_ref['05968260488'] = '140'
    odoo_ref['07847800013'] = '24'
    odoo_ref['10123720962'] = '120'
    odoo_ref['10889761'] = '157'
    odoo_ref['129274202'] = '211'
    odoo_ref['144425382'] = '105'
    odoo_ref['144425382'] = '1963'
    odoo_ref['146892876'] = '91'
    odoo_ref['34464692'] = '32'
    odoo_ref['4860152547'] = '143'
    return odoo_ref


def dia_ref():
    dia_ref = {}
    dia_ref['01897630289'] = '08001705'
    dia_ref['01147330284'] = '08001808'
    dia_ref['00973000284'] = '08002927'
    dia_ref['00142500354'] = '08003098'
    dia_ref['01234660221'] = '08003215'
    dia_ref['02494540285'] = '08003223'
    dia_ref['02490560287'] = '08003290'
    dia_ref['00888520244'] = '08003778'
    dia_ref['02157220241'] = '08004114'
    dia_ref['00637130360'] = '08004126'
    dia_ref['02639920244'] = '08004193'
    dia_ref['00810620286'] = '08004206'
    dia_ref['00165200270'] = '08004278'
    dia_ref['03481280265'] = '08004303'
    dia_ref['00681370268'] = '08004305'
    dia_ref['00879740264'] = '08004321'
    dia_ref['03495150280'] = '08004411'
    dia_ref['03336810274'] = '08004484'
    dia_ref['00500551205'] = '08004521'
    dia_ref['00957910284'] = '08004594'
    dia_ref['00210530283'] = '08004628'
    dia_ref['00197370281'] = '08004645'
    dia_ref['03332370281'] = '08004691'
    dia_ref['00557280989'] = '08004704'
    dia_ref['04216230286'] = '08004718'
    dia_ref['00476190012'] = '08004722'
    dia_ref['00593101207'] = '08004724'
    dia_ref['05398731009'] = '08004735'
    dia_ref['05968260488'] = '08004750'
    dia_ref['00658500236'] = '08004753'
    dia_ref['00576020267'] = '08004765'
    dia_ref['02506060280'] = '08004782'
    dia_ref['00068620392'] = '08004789'
    dia_ref['01047610595'] = '08004798'
    dia_ref['02353470285'] = '08004799'
    dia_ref['01698760939'] = '08004806'
    dia_ref['03775610235'] = '08004819'
    dia_ref['02204030288'] = '08004863'
    dia_ref['04218710962'] = '08004869'
    dia_ref['03906220284'] = '08004872'
    dia_ref['00270140288'] = '08004888'
    dia_ref['01732330939'] = '08004902'
    dia_ref['04599890268'] = '08004905'
    dia_ref['02161730243'] = '08004950'
    dia_ref['00572250983'] = '08004954'
    dia_ref['01505160299'] = '08004985'
    dia_ref['04552520266'] = '08005008'
    dia_ref['00300430931'] = '08005009'
    dia_ref['04706800267'] = '08005010'
    dia_ref['02318160286'] = '08005012'
    dia_ref['04002310169'] = '08005020'
    dia_ref['09106940969'] = '08005023'
    dia_ref['03575230044'] = '08005026'
    dia_ref['02647040233'] = '08005027'
    dia_ref['03542620376'] = '08005031'
    dia_ref['07847800013'] = '08005033'
    dia_ref['05122150724'] = '08005052'
    dia_ref['00656900271'] = '08005053'
    dia_ref['00737950253'] = '08005060'
    dia_ref['03537790267'] = '08005061'
    dia_ref['01605000338'] = '08005063'
    dia_ref['00641550983'] = '08005069'
    dia_ref['01603000215'] = '08005071'
    dia_ref['03496521208'] = '08005081'
    dia_ref['01827200989'] = '08005082'
    dia_ref['01498810280'] = '08005095'
    dia_ref['04160730968'] = '08005102'
    dia_ref['10123720962'] = '08005108'
    dia_ref['00121890933'] = '08005110'
    dia_ref['06251041007'] = '08010179'
    dia_ref['144425382'] = '09010067'
    dia_ref['809900786B01'] = '09010663'
    dia_ref['12398300'] = '09010740'
    dia_ref['10889761'] = '09010751'
    dia_ref['129274202'] = '09010758'
    dia_ref['7761698420'] = '09010764'
    dia_ref['RO18152257'] = '09010793'
    dia_ref['556297766901'] = '09010817'
    dia_ref['129274202'] = '09010846'
    dia_ref['109261949'] = '09010850'
    dia_ref['4860152547'] = '09010855'
    dia_ref['146546189'] = '09010856'
    dia_ref['146892876'] = '09010859'
    dia_ref['34464692'] = '09010862'
    dia_ref['0451868065'] = '09010871'
    dia_ref['SE556059357'] = '09010885'
    return dia_ref


def updateCustomerRef():
    dia_refs = dia_ref()
    for vat, partner_id in getOdooCodes().items():
        dia_code = dia_refs.get(vat)
        if dia_code:
            BaseDbIntegration.UpdateValue('res.partner', int(partner_id), {'dia_ref_customer': dia_code})
            continue
        ERROR_BUF.append("Unable to update %r" % partner_id)

#0"CODICE RDS"
#1"DESCRIZIONE"
#2
#3"N.ORDINE RDS"
#4"ANNO"
#5"RIGA ORDINE"
#6"CODICE CLIENTE "
#7"CLIENTE"
#8"UM"
#9"Q.TA'ORDINATA"
#10"Q.TA RESIDUA"
#11"DATA CONSEGNA"
#12"VALORE"
#13"DEPOSITO"
#14"CODICE CLIENTE"
#15"N.ORD.CLIENTE"
#16"CONSEGNA RICHIESTA"


def impSo(onlyOrder=False):
    o = DiaAnag()
    printAndLogSale('Start Reading sale order file')
    um = getAllUom()
    payTerm = getAllAccountPaymentTerm()
    global ERROR_BUF
    xl_workbook = xlrd.open_workbook(saleOrderFilePath)
    xl_sheet = xl_workbook.sheet_by_index(0)
    count = -1
    for row in xl_sheet.get_rows():
        count = count + 1
        to_confirm = []
        try:
            print ("SaleOrder compute  row-%r error %r " % (int(count), len(ERROR_BUF)))
            if count == 0:
                continue
            order_name = row[2].value
            if onlyOrder:
                if order_name != onlyOrder:
                    continue
            else:
                if order_name.find('S') == 0 or order_name.find('P') == 0:
                    continue
            #order_name = order_name + "_" + str(int(row[3].value))
            product_name = sanitizeXLSLSTRING(row[0].value)
            codice_cliente = sanitizeCustomerId(row[5].value)
            codice_ref_cliente = row[16].value
            if len(codice_cliente) == 0:
                ERROR_BUF.append("%r : Order: %r Unable to create Sale Order %r" % (count, order_name, codice_cliente))
            uom_id = um.get(row[7].value)
            if not uom_id:
                raise "Missing uom"
            qty_ordered = float(row[8].value)
            qty_remaining = float(row[9].value)
            if qty_remaining <= 0.0001:
                continue
            #
            dataRichiesta_dt = xlrd.xldate.xldate_as_datetime(row[11].value, xl_workbook.datemode)
            dataRichiesta = dataRichiesta_dt.strftime("%Y-%m-%d %H:%M:%S")
            imponibile = sanitizeDouble(row[12].value)
            #
            dataConsegna = row[18].value
            if isinstance(dataConsegna, float):
                dataConsegna = xlrd.xldate.xldate_as_datetime(row[18].value, xl_workbook.datemode)
                dataConsegna = dataConsegna.strftime("%Y-%m-%d %H:%M:%S")
            else:
                dataConsegna = False
            partner_id = getPartnerFromPartnerId(codice_cliente)
            if not partner_id:
                ERROR_BUF.append("%r Order: %r Unable to create partner %r" % (count, order_name, codice_cliente))
                continue
            partner_shipping_id = False
            codice_destinazione = sanitizeCustomerId(str(row[21].value))
            if len(codice_destinazione):
                location_name = row[22].value.strip()
                partner_shipping_id = getCreatePartnerLocation(partner_id, location_name, codice_destinazione, o)
            payment_term_id = payTerm.get(row[23].value.strip(), False)
            if not partner_shipping_id:
                partner_shipping_id = partner_id
            difference = dataRichiesta_dt.date() - datetime.datetime.now().date()
            vals = {
                'partner_id': partner_id,
                'partner_shipping_id': partner_shipping_id,
                'name': order_name,
                'order_date': dataConsegna,
                'confirmation_date': dataConsegna,
                'validity_date': dataConsegna,
                'commitment_date': dataConsegna,
                'requested_date': dataRichiesta,
                'client_order_ref': codice_ref_cliente,
                'payment_term_id': payment_term_id}
            orderId = createSaleOrder(vals, ERROR_BUF)
            if not orderId:
                ERROR_BUF.append("%r Order %r Unable to create Sale Order %r" % (count, order_name, codice_cliente))
                continue
            to_confirm.append(orderId)
            productIds = BaseDbIntegration.GetDetailsSearch('product.product',
                                                            [('default_code', '=', product_name)],
                                                            ['name'])
            product_id = False
            product_name_row = product_name
            product_name = ''
            for s_product_id in productIds:
                product_name = s_product_id.get('name')
                product_id = s_product_id.get('id')
                break
            if not product_id:
                ERROR_BUF.append("%r Order: %r Unable to create Sale Order no product found %r" % (count, order_name, product_name_row))
                continue
            imponibile = imponibile / qty_remaining * 1.0
            sale_order_line_vals = {
                'name': product_name,
                'order_id': orderId,
                'price_unit': imponibile,
                'product_id': product_id,
                'product_uom_id': uom_id,
                'product_old_dia_qty': qty_ordered,
                'product_uom_qty': qty_remaining,
                'requested_date': dataRichiesta,
                'dia_product_delivery_date': dataConsegna,
                'customer_lead': difference.days}
            createSaleOrderLine(sale_order_line_vals, ERROR_BUF)
            BaseDbIntegration.callCustomMethod('sale.order', 'action_confirm', orderId)
        except Exception, ex:
            ERROR_BUF.append("%r Order %r Unable to create Sale Order %r" % (count, order_name, str(ex)))
            continue
    to_confirm = list(set(to_confirm))
    printAndLogSale('End Reading sale order file')


def createMold(vals):
    wcId = False
    try:
        wcId = BaseDbIntegration.Search('maintenance.equipment', [('name', '=', vals['name'])])
        if not wcId:
            wcId = BaseDbIntegration.Create('maintenance.equipment', vals)
        else:
            wcId = wcId[0]
    except Exception as ex:
        printAndLogSale('Errors during create partner %r. Ex %r' % (vals, ex))
    return wcId


def createMoldConfiguration(vals):
    try:
        mcId = BaseDbIntegration.Create('omnia_mold.mold_configuration', vals)
    except Exception as ex:
        printAndLogSale('Errors during create partner %r. Ex %r' % (vals, ex))
    return mcId


def writeAttrezzatura(product_name, mold_name, processed_product, processed_key, processed_mold, index, number_of_cavity=1, operation='ALAUT'):
    if operation != 'ALAUT':
            return
        #  Work with Product
    print ("%r Work on %r %r" % (index, product_name, mold_name))
    product_vals = {'name': product_name,
                    'default_code': product_name}
    product_id = processed_product.get(product_name)
    if not product_id:
        product_id = createProduct(product_vals, create=False)
    if not product_id:
        ERROR_BUF.append("Unable to crate product %r on line %r" % (product_name, index))
        return
    processed_product[product_name] = product_id
    #  Work with mold
    key = "K_%r_%r" % (mold_name, product_name)
    if key in processed_key:
        return
    else:
        processed_key.append(key)
    moldVals = {'name': mold_name,
                'is_mold': True,
                'mold_configuration': []}
    mold_id = processed_mold.get(mold_name)
    if not mold_id:
        mold_id = createMold(moldVals)
    processed_mold[mold_name] = mold_id
    to_delete_id = BaseDbIntegration.Search('omnia_mold.mold_configuration', [('mold_id', '=', mold_id),
                                                                              ('product_id', '=', product_id)])
    if to_delete_id:
        BaseDbIntegration.Delete('omnia_mold.mold_configuration', to_delete_id)
    for _i in range(0, number_of_cavity):
        mold_configuration_vals = {'mold_id': mold_id,
                                   'product_id': product_id,
                                   'description': product_name,
                                   #'product_production_qty': 1,
                                   }
        createMoldConfiguration(mold_configuration_vals)


def fixAttrezza():
    processed_product = {}
    processed_mold = {}
    processed_key = []
    with open(impronte_CSV, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for row in spamreader:
            try:
                product_name = row[0]
                mold_name = row[1]
                number_of_cavity = int(row[2])
                writeAttrezzatura(product_name,
                                  mold_name,
                                  processed_product,
                                  processed_key,
                                  processed_mold,
                                  index=count,
                                  number_of_cavity=number_of_cavity)
            except Exception as ex:
                print (ex)
                ERROR_BUF.append(ex)


def impAttrezza():
    printAndLogSale('Start Reading Mold file')
    xl_workbook = xlrd.open_workbook(mold_path)
    xl_sheet = xl_workbook.sheet_by_index(0)
    processed_product = {}
    processed_mold = {}
    processed_key = []
    for i, row in enumerate(xl_sheet.get_rows()):
        if int(i) == 0:
            continue
        printAndLog("Work On %r errors %r" % (i, len(ERROR_BUF)), 'impAttrezza')
        if str(row[4].value).strip().replace('.0', '') != 'ALAUT':
            continue
        #  Work with Product
        product_name = str(row[0].value).strip().replace('.0', '')
        product_vals = {'name': product_name,
                        'default_code': product_name}
        product_id = processed_product.get(product_name)
        if not product_id:
            product_id = createProduct(product_vals, create=False)
        if not product_id:
            ERROR_BUF.append("Unable to crate product %r on line %r" % (product_name, i))
            continue
        processed_product[product_name] = product_id
        #  Work with mold
        mold_name = str(row[8].value).strip().replace('.0', '')
        key = "K_%r_%r" % (mold_name, product_name)
        if key in processed_key:
            continue
        else:
            processed_key.append(key)
        moldVals = {'name': mold_name,
                    'is_mold': True,
                    'mold_configuration': []}
        mold_id = processed_mold.get(mold_name)
        if not mold_id:
            mold_id = createMold(moldVals)
        processed_mold[mold_name] = mold_id
        for i in range(0, int(row[23].value)):
            mold_configuration_vals = {'mold_id': mold_id,
                                       'product_id': product_id,
                                       'description': product_name,
                                       #'product_production_qty': 1,
                                       }
            createMoldConfiguration(mold_configuration_vals)


def fixAtterzzaRoutings():
    BaseDbIntegration.callCustomMethod("maintenance.equipment", 'fixMoldRoutings')


def fixAtterzzaRoutingsConsums():
    BaseDbIntegration.callCustomMethod("maintenance.equipment", 'fixMoldConsumes')

#     01 - RDS
#     12 - V.I.V. SRL
#     16 - ERREDUE SNC
#     29 - MICROMAX
#     91 - ZETA DUE SRL


def impGiacenze():
    pass
#AN_FOR
#row[0]=CONTO
#row[1]=R_SOC
#row[2]=R_SOC2
#row[3]=IND
#row[4]=CAP
#row[5]=LOC
#row[6]=PV
#row[7]=NAZIONE
#row[8]=MEMO_CF
#row[9]=P_FISICA
#row[10]=CF_ESTERO
#row[11]=CF_CEE
#row[12]=CF_ELENCHI_IVA_ON
#row[13]=CF_BLACK_LIST_ON
#row[14]=CFIS
#row[15]=P_IVA
#row[16]=IVA
#row[17]=DICH_IVA
#row[18]=SCAD_DICH_IVA
#row[19]=TELEFONO
#row[20]=TELEX
#row[21]=TELEFAX
#row[22]=R_SOC_O
#row[23]=R_SOC2_O
#row[24]=IND_O
#row[25]=CAP_O
#row[26]=LOC_O
#row[27]=PV_O
#row[28]=NAZIONE_O
#row[29]=VALUTA
#row[30]=SPEDIZIONE
#row[31]=PAGAMENTO
#row[32]=BANCA
#row[33]=AGZ_BANCA
#row[34]=CAB
#row[35]=CIRCUITO
#row[36]=TIPO_PRES
#row[37]=BANCA_F
#row[38]=AGZ_BANCA_F
#row[39]=CAB_F
#row[40]=C_CORRENTE
#row[41]=IBAN
#row[42]=ZONA
#row[43]=NOTE_CF_1
#row[44]=NOTE_CF_2
#row[45]=SETTORE
#row[46]=CATEGORIA
#row[47]=GRUPPO
#row[48]=MERCATO_CF
#row[49]=VOLUME_ACQ_RIF
#row[50]=TITOLARE
#row[51]=RESP_COMM
#row[52]=RESP_TEC
#row[53]=MAIL_TITOLARE
#row[54]=MAIL_RESP_COMM
#row[55]=MAIL_RESP_TEC
#row[56]=NS_CODICE
#row[57]=RESA
#row[58]=COD_RESA
#row[59]=CHIUSO_IL
#row[60]=NAZIONE_L
#row[61]=LINGUA_ART1
#row[62]=LINGUA_ART2
#row[63]=STAMPA_770
#row[64]=REG_AGEVOLATO_RA
#row[65]=IS_AGENTE
#row[66]=CAU_PAG_CU15_STD
#row[67]=CATEGORIA_CU15
#row[68]=C_MERCI_FOR
#row[69]=CC_MERCI_FOR
#row[70]=BLOCCO_ORDINI
#row[71]=BLOCCO_CONS
#row[72]=SBLOCCO_ART
#row[73]=DATA_INS


def getStateCountry(state_code, country_code):
    country_id = BaseDbIntegration.Search('res.country',
                                          [('code', '=', unicode(country_code).strip().upper())],
                                          onlyFirst=True)
    state_id = BaseDbIntegration.Search('res.country.state',
                                        [('code', '=', unicode(state_code).strip().upper()),
                                         ('country_id', '=', country_id)],
                                        onlyFirst=True)
    return (state_id, country_id)


RES_PARTNER = {}


def getResPartner(ref):
    ref = sanitizeUpper(ref)
    if len(ref) == 0:
        return []
    if ref not in RES_PARTNER:
        RES_PARTNER[ref] = BaseDbIntegration.Search('res.partner',
                                                    [('dia_ref_vendor', '=', sanitizeUpper(ref))],
                                                    onlyFirst=True)
    return RES_PARTNER[ref]


def create_company_and_user(values_partner, users, create=True, update=False):
    customer_id = getResPartner(values_partner.get('dia_ref_vendor'))
    if customer_id:
        if update:
            BaseDbIntegration.UpdateValue('res.partner', customer_id, values_partner)
        return
    if not create:
        return
    customer_id = BaseDbIntegration.Create('res.partner', values_partner)
    for user in users:
        if user.get('name', '') == '':
            if user.get('email', '') == '':
                continue
            else:
                user['name'] = user.get('email', '')
        user['parent_id'] = customer_id
        user['company_type'] = 'person'
        BaseDbIntegration.Create('res.partner', user)


def getResCustomer(ref):
    ref = sanitizeUpper(ref)
    if len(ref) == 0:
        return []
    if ref not in RES_PARTNER:
        partner_id = BaseDbIntegration.Search('res.partner',
                                              [('dia_ref_customer', '=', sanitizeUpper(ref))],
                                              onlyFirst=True)
        if partner_id:
            RES_PARTNER[ref] = partner_id
        else:
            return []
    return RES_PARTNER[ref]


def create_customer_and_user(values_partner, users, update=False, create=True):
    customer_id = getResCustomer(values_partner.get('dia_ref_customer'))
    if not customer_id:
        customer_id = BaseDbIntegration.Search('res.partner',
                                               [('vat', '=', values_partner.get('vat'))],
                                               onlyFirst=True)
    if customer_id:
        if update:
            BaseDbIntegration.UpdateValue('res.partner', customer_id, values_partner)
            print "Updated", values_partner.get('name')
            return
        else:
            print "Customer already in odoo", values_partner.get('name')
            return
    else:
        if not create:
            return
        customer_id = BaseDbIntegration.Create('res.partner', values_partner)
    print "Customer Created in odoo", values_partner.get('name')
    for user in users:
        if user.get('name', '') == '':
            if user.get('email', '') == '':
                continue
            else:
                user['name'] = user.get('email', '')
        user['parent_id'] = customer_id
        user['company_type'] = 'person'
        BaseDbIntegration.Create('res.partner', user)


def impo_ana_for(startFrom=0, update=False):
    global ERROR_BUF
    all_state = {}
    with open(ANA_FORM, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            try:
                if int(spamreader.line_num) == 1 or int(spamreader.line_num) < startFrom:
                    continue
                print ("import row %r error %r " % (spamreader.line_num, len(ERROR_BUF)))
                if row[1][0] == '-':  # Fornitori obsoleti
                    continue
                if row[7].strip() == "" or row[7].upper().strip() == "I":
                    row[7] = "IT"
                key = row[7].strip() + "_" + row[6].strip()
                if not all_state.get(key, False):
                    all_state[key] = getStateCountry(row[6], row[7])
                values_partner = {'dia_ref_vendor': sanitizeDiaId(row[0]),
                                  'name': row[1] + " " + row[2],
                                  'street': row[3],
                                  'zip': row[4],
                                  'city': row[5],
                                  'state_id': all_state[key][0],
                                  'country_id': all_state[key][1],
                                  'fiscalcode': row[14],
                                  'vat': row[15],
                                  'phone': row[19],  # TELEFONO
                                  'company_type': 'company',
                                  'supplier': True,
                                  'customer': False,
                                  }
                # row[31]=PAGAMENTO
                # row[37]=BANCA_F
                # row[38]=AGZ_BANCA_F
                # row[39]=CAB_F
                # row[40]=C_CORRENTE
                # row[41]=IBAN
                users = [{'name': row[50],          # row[50]=TITOLARE
                          'email': row[53],
                          'function': 'Titolare'},  # row[53]=MAIL_TITOLARE
                         {'name': row[51],          # RESP_COMM
                          'email': row[54],         # MAIL_RESP_COMM
                          'function': 'Responsabile Commerciale'},
                         {'name': row[52],                          # RESP_TEC
                          'email': row[55],                         # MAIL_RESP_TEC
                          'function': 'Responsabile Tecnico'},
                         ]
                if update:
                    create_company_and_user(values_partner, users, create=False, update=True)
                else:
                    create_company_and_user(values_partner, users)
            except Exception as ex:
                ERROR_BUF.append(str(ex))
# Name = row[0]=  # ARTICOLO
# Name = row[1]=  # DES_ART
# Name = row[2]=  # DES_ART2
# Name = row[3]=  # UMIS
# Name = row[4]=  # IVA
# Name = row[5]=  # CLASSE_EQ
# Name = row[6]=  # SOTTOCLASSE
# Name = row[7]=  # GRUPPO_MERC
# Name = row[8]=  # CLASSE_PROV
# Name = row[9]=  # CLASSE_SCONTO
# Name = row[10]=  # MODELLO_ART
# Name = row[11]=  # GRUPPO_ART1
# Name = row[12]=  # GRUPPO_ART2
# Name = row[13]=  # GRUPPO_ART3
# Name = row[14]=  # GRUPPO_ART4
# Name = row[15]=  # GRUPPO_ART5
# Name = row[16]=  # GRUPPO_ART6
# Name = row[17]=  # GRUPPO_ART7
# Name = row[18]=  # GRUPPO_ART8
# Name = row[19]=  # GRUPPO_ART9
# Name = row[20]=  # GRUPPO_ART10
# Name = row[21]=  # GRUPPO_ART11
# Name = row[22]=  # GRUPPO_ART12
# Name = row[23]=  # ARTICOLO_CLI
# Name = row[24]=  # FORNITORI_1
# Name = row[25]=  # FORNITORI_2
# Name = row[26]=  # FORNITORI_3
# Name = row[27]=  # ART_FORNITORI_1
# Name = row[28]=  # ART_FORNITORI_2
# Name = row[29]=  # ART_FORNITORI_3
# Name = row[30]=  # PREZZI_FOR_1
# Name = row[31]=  # PREZZI_FOR_2
# Name = row[32]=  # PREZZI_FOR_3
# Name = row[33]=  # VALUTE_FOR_1
# Name = row[34]=  # VALUTE_FOR_2
# Name = row[35]=  # VALUTE_FOR_3
# Name = row[36]=  # PREZZI_FOR_VAL_1
# Name = row[37]=  # PREZZI_FOR_VAL_2
# Name = row[38]=  # PREZZI_FOR_VAL_3
# Name = row[39]=  # DATA_PREZZI_FOR_1
# Name = row[40]=  # DATA_PREZZI_FOR_2
# Name = row[41]=  # DATA_PREZZI_FOR_3
# Name = row[42]=  # ULTIMO_COSTO
# Name = row[43]=  # ULTIMO_ACQ
# Name = row[44]=  # ULTIMO_PREZZO
# Name = row[45]=  # ULTIMA_VEND
# Name = row[46]=  # UMIS_VEND
# Name = row[47]=  # CONV_UM
# Name = row[48]=  # UMIS_ACQ
# Name = row[49]=  # CONV_UM_ACQ
# Name = row[50]=  # COLLOCAZIONE
# Name = row[51]=  # PEZZI_CONF
# Name = row[52]=  # PEZZI_SUBC
# Name = row[53]=  # DIMS_1
# Name = row[54]=  # DIMS_2
# Name = row[55]=  # DIMS_3
# Name = row[56]=  # DIMS_EXTRA_1
# Name = row[57]=  # DIMS_EXTRA_2
# Name = row[58]=  # DIMS_EXTRA_3
# Name = row[59]=  # PESO
# Name = row[60]=  # PESO_LORDO_ART
# Name = row[61]=  # TARA_ART
# Name = row[62]=  # CAPACITA_ART
# Name = row[63]=  # SCORTA_MINIMA
# Name = row[64]=  # SCORTA_LIMITE
# Name = row[65]=  # TEMPO_RIORDINO
# Name = row[66]=  # LOTTO_RIORDINO
# Name = row[67]=  # TIPO_LOTTO_RIORD
# Name = row[68]=  # INTERVALLO_RIORD
# Name = row[69]=  # G_MESE_RIORD
# Name = row[70]=  # G_WEEK_RIORD
# Name = row[71]=  # PIANIFICATORE
# Name = row[72]=  # MATERIALE_ART
# Name = row[73]=  # CODICE_VINO
# Name = row[74]=  # TIPO_ACCISA
# Name = row[75]=  # COSTO_PRODUZIONE
# Name = row[76]=  # QT_LOGISTICA
# Name = row[77]=  # GIORNI_VAL
# Name = row[78]=  # MESI_SCAD_REV_IMP
# Name = row[79]=  # MESI_SCAD_COLL_IMP
# Name = row[80]=  # DES_CONFEZIONE_STD
# Name = row[81]=  # NUM_CONF_BANCALE
# Name = row[82]=  # ALTEZZA_CONF_STD
# Name = row[83]=  # NUM_CONF_STRATO
# Name = row[84]=  # MAG_LOGISTICA_STD
# Name = row[85]=  # FILA_STD
# Name = row[86]=  # PIANO_STD
# Name = row[87]=  # BOX_STD
# Name = row[88]=  # TIPO_IMBALLO_STD
# Name = row[89]=  # ANNO_LIFO
# Name = row[90]=  # NAZIONE_PROD
# Name = row[91]=  # BAR_CODE_EAN13
# Name = row[92]=  # MOV_MAG
# Name = row[93]=  # ORDINABILE
# Name = row[94]=  # PRODUCIBILE
# Name = row[95]=  # CONSEGNABILE_CLI
# Name = row[96]=  # ARTICOLO_AP
# Name = row[97]=  # PRODOTTO_IE
# Name = row[98]=  # ART_FANTASMA
# Name = row[99]=  # ART_OPZIONE
# Name = row[100]=  # SCONTABILE
# Name = row[101]=  # APPL_PROV
# Name = row[102]=  # CONTROLLO_QUAL
# Name = row[103]=  # CONTROLLO_LOTTO
# Name = row[104]=  # SER_NUM_LOTTI_ON
# Name = row[105]=  # RICALCOLO_LOTTO
# Name = row[106]=  # RICALCOLO_SCORTA
# Name = row[107]=  # RICALCOLO_T_RIORD
# Name = row[108]=  # INTRASTAT_ON
# Name = row[109]=  # MAG_LOGISTICA_ON
# Name = row[110]=  # MRP_IGNORA_MAG
# Name = row[111]=  # ART_CONSUMO_DB
# Name = row[112]=  # ART_NO_PREL_RPRO
# Name = row[113]=  # ARTICOLO_KIT
# Name = row[114]=  # ART_PEZZE
# Name = row[115]=  # ART_COLORATO
# Name = row[116]=  # DATA_INS
# Name = row[117]=  # OP_AN_ART
# Name = row[118]=  # rowID


def create_vendor_odoo(vendor_name, vendor_product_name, product_id, price):
    partner_id = getResPartner(vendor_name)
    if partner_id:
        vals = {'name': partner_id,  # res partner id
                'product_name': vendor_product_name,
                'product_id': product_id,
                # 'product_tmpl_id': product_tmpl_id,
                'price': price
                }
        return BaseDbIntegration.Create('product.supplierinfo', vals)


def inport_an_art():
    um = getAllUom()
    with open(ANA_ART, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            if int(spamreader.line_num) == 1:
                continue
            print ("import row", spamreader.line_num)
            uomName = sanitizeUpper(row[3])                         # UMIS
            pType = 'product'
            if row[92] == 'S':  # MOV_MAG
                pType = 'consu'
            vals = {'legacy_code': row[0][2:],                     # ARTICOLO
                    'default_code': row[0][2:],                     # ARTICOLO
                    'name': row[1] + " " + row[2],                  # DES_ART DES_ART2
                    'uom_id': safetyGet(um, uomName, createUom),    # UMIS
                    #'customer_code': row[23],                       # ARTICOLO_CLI
                    'standard_price': sanitizeDouble(row[42]),      # ULTIMO_COSTO
                    'list_price': sanitizeDouble(row[44]),          # ULTIMO_PREZZO
                    'weight': sanitizeDouble(row[59]),              # PESO KG ??
                    'type': pType,
                    'dia_row_id': row[118]                          # row id
                    }
            if len(sanitizeString(row[91])) > 0:
                vals['barcode'] = row[91],                             # BAR_CODE_EAN13
            if row[96] == 'P':  # ‘’: row[96],  # ARTICOLO_AP #P prodotto di produzione
                product_id = createProductionProduct(vals)
            elif row[96] == 'A':  # A prodotto di acq
                product_id = createBuyProduct(vals)
            else:
                product_id = False
            if product_id:
                create_vendor_odoo(row[24],    # ‘’: row[24],  # FORNITORI_1
                                   row[27],    # ‘’: row[27],  # ART_FORNITORI_1
                                   product_id,
                                   row[30])   # ‘’: row[30],  # PREZZI_FOR_1
                create_vendor_odoo(row[25],    # ‘’: row[25],  # FORNITORI_2
                                   row[28],    # ‘’: row[28],  # ART_FORNITORI_2
                                   product_id,
                                   row[31])   # ‘’: row[31],  # PREZZI_FOR_2
                create_vendor_odoo(row[26],    # ‘’: row[26],  # FORNITORI_3
                                   row[29],    # ‘’: row[29],  # ART_FORNITORI_3
                                   product_id,
                                   row[32])   # ‘ ’: row[32],  # PREZZI_FOR_3
"""
select
ARTICOLO,
DES_ART,
DES_ART2,
UMIS,
IVA,
CLASSE_EQ,
SOTTOCLASSE,
GRUPPO_MERC,
CLASSE_PROV,
CLASSE_SCONTO,
MODELLO_ART,
GRUPPO_ART1,
GRUPPO_ART2,
GRUPPO_ART3,
GRUPPO_ART4,
GRUPPO_ART5,
GRUPPO_ART6,
GRUPPO_ART7,
GRUPPO_ART8,
GRUPPO_ART9,
GRUPPO_ART10,
GRUPPO_ART11,
GRUPPO_ART12,
ARTICOLO_CLI,
FORNITORI_1,
FORNITORI_2,
FORNITORI_3,
ART_FORNITORI_1,
ART_FORNITORI_2,
ART_FORNITORI_3,
PREZZI_FOR_1,
PREZZI_FOR_2,
PREZZI_FOR_3,
VALUTE_FOR_1,
VALUTE_FOR_2,
VALUTE_FOR_3,
PREZZI_FOR_VAL_1,
PREZZI_FOR_VAL_2,
PREZZI_FOR_VAL_3,
DATA_PREZZI_FOR_1,
DATA_PREZZI_FOR_2,
DATA_PREZZI_FOR_3,
ULTIMO_COSTO,
ULTIMO_ACQ,
ULTIMO_PREZZO,
ULTIMA_VEND,
UMIS_VEND,
CONV_UM,
UMIS_ACQ,
CONV_UM_ACQ,
COLLOCAZIONE,
PEZZI_CONF,
PEZZI_SUBC,
DIMS_1,
DIMS_2,
DIMS_3,
DIMS_EXTRA_1,
DIMS_EXTRA_2,
DIMS_EXTRA_3,
PESO,
PESO_LORDO_ART,
TARA_ART,
CAPACITA_ART,
SCORTA_MINIMA,
SCORTA_LIMITE,
TEMPO_RIORDINO,
LOTTO_RIORDINO,
TIPO_LOTTO_RIORD,
INTERVALLO_RIORD,
G_MESE_RIORD,
G_WEEK_RIORD,
PIANIFICATORE,
MATERIALE_ART,
CODICE_VINO,
TIPO_ACCISA,
COSTO_PRODUZIONE,
QT_LOGISTICA,
GIORNI_VAL,
MESI_SCAD_REV_IMP,
MESI_SCAD_COLL_IMP,
DES_CONFEZIONE_STD,
NUM_CONF_BANCALE,
ALTEZZA_CONF_STD,
NUM_CONF_STRATO,
MAG_LOGISTICA_STD,
FILA_STD,
PIANO_STD,
BOX_STD,
TIPO_IMBALLO_STD,
ANNO_LIFO,
NAZIONE_PROD,
BAR_CODE_EAN13,
MOV_MAG,
ORDINABILE,
PRODUCIBILE,
CONSEGNABILE_CLI,
ARTICOLO_AP,
PRODOTTO_IE,
ART_FANTASMA,
ART_OPZIONE,
SCONTABILE,
APPL_PROV,
CONTROLLO_QUAL,
CONTROLLO_LOTTO,
SER_NUM_LOTTI_ON,
RICALCOLO_LOTTO,
RICALCOLO_SCORTA,
RICALCOLO_T_RIORD,
INTRASTAT_ON,
MAG_LOGISTICA_ON,
MRP_IGNORA_MAG,
ART_CONSUMO_DB,
ART_NO_PREL_RPRO,
ARTICOLO_KIT,
ART_PEZZE,
ART_COLORATO,
DATA_INS,
OP_AN_ART,
ROWID
from XLDB01.AN_ART A
where EXISTS (SELECT D.ARTICOLO FROM XLDB01.MOVIMENTI_M D WHERE A.ARTICOLO=D.ARTICOLO AND D_REG>='20160101' AND D_REG<='20181231' AND QUANTITA<>0)
order by ARTICOLO; 
"""

# ‘’: row[46],  # UMIS_VEND sono solo 300 articoli da capire se importrli  select ARTICOLO,DES_ART,DES_ART2,UMIS , UMIS_VEND from "XLDB01"."AN_ART" where UMIS <> UMIS_VEND and UMIS_VEND<>' ';
# ‘’: row[48],  # UMIS_ACQ solo 10 articoli select ARTICOLO,DES_ART,DES_ART2,UMIS , UMIS_VEND,CONV_UM,UMIS_ACQ from "XLDB01"."AN_ART" where UMIS <> UMIS_ACQ and UMIS_ACQ<>' ';
# ‘’: row[49],  # CONV_UM_ACQ
# ‘’: row[50],  # COLLOCAZIONE
# ‘’: row[51],  # PEZZI_CONF
# ‘’: row[52],  # PEZZI_SUBC
# 
# 
# 
# ‘’: row[60],  # PESO_LORDO_ART
# ‘’: row[61],  # TARA_ART
# ‘’: row[62],  # CAPACITA_ART
# ‘’: row[63],  # SCORTA_MINIMA
# ‘’: row[64],  # SCORTA_LIMITE
# ‘’: row[65],  # TEMPO_RIORDINO gg ??
# ‘’: row[66],  # LOTTO_RIORDINO
# ‘’: row[67],  # TIPO_LOTTO_RIORD
# ‘’: row[68],  # INTERVALLO_RIORD
# ‘’: row[69],  # G_MESE_RIORD
# ‘’: row[70],  # G_WEEK_RIORD
# ‘’: row[71],  # PIANIFICATORE
# ‘’: row[72],  # MATERIALE_ART non usato
# ‘’: row[73],  # CODICE_VINO
# ‘’: row[74],  # TIPO_ACCISA
# ‘’: row[75],  # COSTO_PRODUZIONE e' settato
# ‘’: row[76],  # QT_LOGISTICA
# ‘’: row[77],  # GIORNI_VAL
# ‘’: row[78],  # MESI_SCAD_REV_IMP
# ‘’: row[79],  # MESI_SCAD_COLL_IMP
# ‘’: row[80],  # DES_CONFEZIONE_STD
# ‘’: row[81],  # NUM_CONF_BANCALE
# ‘’: row[82],  # ALTEZZA_CONF_STD
# ‘’: row[83],  # NUM_CONF_STRATO
# ‘’: row[84],  # MAG_LOGISTICA_STD
# ‘’: row[85],  # FILA_STD
# ‘’: row[86],  # PIANO_STD
# ‘’: row[87],  # BOX_STD
# ‘’: row[88],  # TIPO_IMBALLO_STD
# ‘’: row[89],  # ANNO_LIFO
# ‘’: row[90],  # NAZIONE_PROD
#-> ‘’: row[91],  # BAR_CODE_EAN13
# ‘’: row[92],  # MOV_MAG
# ‘’: row[93],  # ORDINABILE
# ‘’: row[94],  # PRODUCIBILE
# ‘’: row[95],  # CONSEGNABILE_CLI
# ‘’: row[96],  # ARTICOLO_AP
# ‘’: row[97],  # PRODOTTO_IE
# ‘’: row[98],  # ART_FANTASMA
# ‘’: row[99],  # ART_OPZIONE
# ‘’: row[100],  # SCONTABILE
# ‘’: row[101],  # APPL_PROV
# ‘’: row[102],  # CONTROLLO_QUAL
# ‘’: row[103],  # CONTROLLO_LOTTO
# ‘’: row[104],  # SER_NUM_LOTTI_ON
# ‘’: row[105],  # RICALCOLO_LOTTO
# ‘’: row[106],  # RICALCOLO_SCORTA
# ‘’: row[107],  # RICALCOLO_T_RIORD
# ‘’: row[108],  # INTRASTAT_ON
# ‘’: row[109],  # MAG_LOGISTICA_ON
# ‘’: row[110],  # MRP_IGNORA_MAG
# ‘’: row[111],  # ART_CONSUMO_DB
# ‘’: row[112],  # ART_NO_PREL_RPRO
# ‘’: row[113],  # ARTICOLO_KIT
# ‘’: row[114],  # ART_PEZZE
# ‘’: row[115],  # ART_COLORATO
# ‘’: row[116],  # DATA_INS
# ‘’: row[117],  # OP_AN_ART
# ‘’: row[118],  # ROWID


PARENT_BOMS = {}


def get_bom_id(product_tmpl_id):
    global PARENT_BOMS
    bom_id = PARENT_BOMS.get(product_tmpl_id, False)
    if not bom_id:
        bom_id = BaseDbIntegration.Search('mrp.bom',
                                          [('product_tmpl_id', '=', product_tmpl_id)],
                                          onlyFirst=True)
        if not bom_id:
            product_vals = BaseDbIntegration.GetDetailsSearch('product.template', [('id', '=', product_tmpl_id)], ['uom_id'])
            vals = {'product_tmpl_id': product_tmpl_id,
                    'type': 'normal',
                    'state': 'draft',
                    'product_uom_id': product_vals[0].get('uom_id')[0]}
            bom_id = BaseDbIntegration.Create('mrp.bom', vals)
    PARENT_BOMS[product_tmpl_id] = bom_id
    return bom_id


PRODUCT_TMPL_ID = {}


def get_product_tmpl_id(name):
    global PRODUCT_TMPL_ID
    product_tmpl_id = PRODUCT_TMPL_ID.get(name, False)
    if not product_tmpl_id:
        product_tmpl_id = BaseDbIntegration.Search('product.template',
                                                   [('default_code', '=', name)],
                                                   onlyFirst=False)
    PRODUCT_TMPL_ID[name] = product_tmpl_id
    if isinstance(product_tmpl_id, list):
        for pid in product_tmpl_id:
            return pid
    return product_tmpl_id


PRODUCT_ID = {}


def get_product_id(name):
    global PRODUCT_ID
    product_id = PRODUCT_ID.get(name, False)
    if not product_id:
        product_id = BaseDbIntegration.Search('product.product',
                                              [('default_code', '=', name)],
                                              onlyFirst=False)
    PRODUCT_ID[name] = product_id
    if isinstance(product_id, list):
        for pid in product_id:
            return pid
    return product_id


OLD_BOM_LINE = []


def getAlreadyDoneLine():
    global OLD_BOM_LINE
    for bom_line in BaseDbIntegration.GetDetailsSearch('mrp.bom.line',
                                                       [('dia_row_id', '!=', False)],
                                                       ['dia_row_id']):
        OLD_BOM_LINE.append(bom_line.get('dia_row_id'))


def createBomLineNew(parent, child, qty, row_id):
    global ERROR_BUF
#     if row_id in OLD_BOM_LINE:
#         return
    parent = sanitizeUpperCode(parent)
    child = sanitizeUpperCode(child)
    qty = sanitizeDouble(qty)
    parent_id = get_product_tmpl_id(parent)
    child_id = get_product_id(child)
    if not child_id:
        infoValue = {'name': 'Prodotto non importato in Odoo Da DIA',
                     'default_code': child,
                     'uom_po_id': 1,
                     'uom_id': 1,
                     'type': 'product'}
        child_id = createProduct(infoValue,
                                 reorderingRule=False)
    if not parent_id or not child_id:
        msg = "parent_id %r child_id %r one is missing check" % (parent_id, child_id)
        print (msg)
        ERROR_BUF.append(msg)
        return
    bom_id = get_bom_id(parent_id)
    bom_line_vals = {'bom_id': bom_id,
                     'product_id': child_id,
                     'type': 'normal',
                     'product_qty': qty,
                     'dia_row_id': row_id
                     }  # 'product_uom_id': uom_id
    BaseDbIntegration.Create('mrp.bom.line', bom_line_vals)


def inport_an_art_bom():
    # ‘’:  row[0]   # PADRE
    # ‘’:  row[1]   # ID_STRUTTURA
    # ‘’:  row[2]   # PADRE_ID_STR
    # ‘’:  row[3]   # COMPONENTE
    # ‘’:  row[4]   # SEQ_COMPONENTE
    # ‘’:  row[5]   # QUANTITA
    # ‘’:  row[6]   # SCARTO_MAT
    # ‘’:  row[7]   # SCARTO_QT
    # ‘’:  row[8]   # ID_STRUTTURA_COMP
    # ‘’:  row[9]   # ID_CICLO_COMP
    # ‘’:  row[10]   # POS_DISEGNO
    # ‘’:  row[11]   # INIZIO_VAL
    # ‘’:  row[12]   # FINE_VAL
    # ‘’:  row[13]   # NOTE1_COMP
    # ‘’:  row[14]   # NOTE2_COMP
    # ‘’:  row[15]   # DATA_REV
    # ‘’:  row[16]   # NUM_FASE_PREL
    # ‘’:  row[17]   # LEAD_TIME_COMP
    # ‘’:  row[18]   # COMP_DESCRITTIVO
    # ‘’:  row[19]   # COMP_TERZI
    # ‘’:  row[20]   # DEP_PRELIEVO_TERZI
    # ‘’:  row[21]   # PERC_RIP_PREZZO
    # ‘’:  row[22]   # STR_TIME_MOD
    # ‘’:  row[23]   # STR_USER_MOD
    # ‘’:  row[24]   # ROWID
    #um = getAllUom()
    with open(STRUTTURE, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            if int(spamreader.line_num) == 1:
                continue
            print ("import row", spamreader.line_num)
            # ‘’:  row[0]   # PADRE
            # ‘’:  row[3]   # COMPONENTE
            # ‘’:  row[5]   # QUANTITA
            # ‘’: row[24],  # ROWID
            createBomLineNew(row[0], row[3], row[5], "")


def imp_giacenze(limit=None):
    out = []
    global ERROR_BUF
    with open(GIACENZE, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            try:
                if int(spamreader.line_num) == 1:
                    continue
                if limit:
                    if int(spamreader.line_num) > limit:
                        break
                print ("import row", spamreader.line_num)
                qty = round(float(row[2]), 3)
                out.append({'product_name': row[0],
                            'product_qty': qty,
                            'rds_location_name': row[1]})
            except Exception as ex:
                msg = "Row %r with error: %r" % (spamreader.line_num, ex)
                print (msg)
                ERROR_BUF.append(msg)

    invendory_name = "Upload_str(%s)" % str(datetime.datetime.now())
    invendory_name = invendory_name.replace(" ", "_")
    ERROR_BUF += BaseDbIntegration.callCustomMethod('stock.inventory', 'uploadInventory', (invendory_name, out, IMP_STOCK_ID))

# new import


print (">>>>" * 20)


def imp_location():
    out = []
    with open(DEPOSITI, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            if int(spamreader.line_num) == 1:
                continue
            print ("import row", spamreader.line_num)
            out.append({'dia_ref': row[0],
                        'ref_name': row[1],
                        'customer_id': sanitizeDiaId(row[2])
                        })
    BaseDbIntegration.callCustomMethod('stock.location', 'import_dia', out)


def imp_subcontracting_price():
    global ERROR_BUF
    xl_workbook = xlrd.open_workbook(COSTO_LAV_ESTERNE)
    xl_sheet = xl_workbook.sheet_by_index(0)
    toPush = []
    counter = 0
    for row in xl_sheet.get_rows():
        print '%s -- %s' % (counter, row)
        toPush.append({'fornitore': str(row[0].value).split('.')[0],
                       'codice_articolo': row[2].value,
                       'descrizione': row[3].value,
                       'operazione': row[4].value,
                       'unita_misura': row[5].value,
                       'costo': row[6].value})
        counter = counter + 1
    ERROR_BUF += BaseDbIntegration.callCustomMethod('mrp.bom', 'uploadSubcontracting', toPush)


def updateRoutingDocuments():
    BaseDbIntegration.callCustomMethod('mrp.bom', 'uploadRoutindDocuments')


def fixUomBom():
    um = getAllUom()
    printAndLogBom('Updating bom')
    TO_FIX = []
    with open(DISTINTE_COMPLETE, 'rb') as f:
        for row in f:
            row = row.split("\t")
            uom = row[7].strip()
            uom_id = um.get(uom.upper())
            if not uom_id:
                msg = "Uom not found %r" % uom
                if msg not in ERROR_BUF:
                    ERROR_BUF.append(msg)
            else:
                TO_FIX.append((row[0].strip(), row[4].strip(), uom_id))
    ret = BaseDbIntegration.callCustomMethod('mrp.bom.line', 'fixUomId', TO_FIX)
    for r in set(ret):
        print (r)


def fixMaterozza():
    return BaseDbIntegration.callCustomMethod("omnia_mold.mold_configuration", 'createMaterozza')


class DiaAnag():
    def __init__(self):
        self.load_data()

    def load_data(self):
        self.data = {}
        self.datavat = {}
        global ERROR_BUF
        xl_workbook = xlrd.open_workbook(ANAG_TOTALE)
        xl_sheet = xl_workbook.sheet_by_index(0)
        all_state = {}
        counter = 0
        for row in xl_sheet.get_rows():
            if counter == 0:
                counter += 1
                continue
            counter += 1
            print '%s -- %s' % (counter, row)
            codice = row[0].value  # CODICE
            nazione = row[7].value  # NAZ.
            provincia = row[6].value  # PROV.
            if nazione == u" " or nazione == u"" or nazione == "I":
                nazione = "IT"
            key = nazione.strip() + "_" + provincia.strip()
            if not all_state.get(key, False):
                all_state[key] = getStateCountry(provincia, nazione)
            vat = row[15].value  # PARTITA IVA
            toCreate = {'dia_ref_customer': codice,
                        'name': row[1].value + row[2].value,  # RAGIONE SOCIALE 1    RAGIONE SOCIALE 2
                        'street': row[3].value,  # INDIRIZZO (VIA)
                        'zip': row[4].value,  # CAP
                        'city': row[5].value,  # LOCALITA'
                        'state_id': all_state[key][0],
                        'country_id': all_state[key][1],
                        'comment': row[8].value,  # MEMO
                        'vat': vat
                        }
            self.data[codice] = toCreate
            self.datavat[vat] = toCreate

    def odooCreate(self, diaCode, update=False, vat=False, create=True):
        toCreate = self.data.get(diaCode)
        if not toCreate:
            if vat != '' and vat is not False:
                for s_vat in self.datavat.keys():
                    if vat in s_vat:
                        create_customer_and_user(self.datavat[vat], [],
                                                 update=update,
                                                 create=create)
                        return True
            return False
        else:
            create_customer_and_user(toCreate, [],
                                     update=update,
                                     create=create)
            #row[14].value,  #  CODICE FISCALE
            #row[15].value,  #  PARTITA IVA
            return True


def icdia():
    o = DiaAnag()
    while 1:
        m = raw_input('Dia Code:')
        if m == 'o':
            break
        o.odooCreate(m, update=True)


def fixAddress():
    a = ['09995020',
         '09994521',
         '08999943',
         '08999910',
         '08994114',
         '08999922',
         '08999944',
         '09904303',
         '09943031',
         '08999991',
         '09994303',
         '08994905',
         '09932151',
         '09932152',
         '09994954',
         '09910859',
         '08995063',
         '09994950']
    o = DiaAnag()
    for dia_code in a:
        o.odooCreate(dia_code, update=True)


def fixAddress1():
    o = DiaAnag()
    with open(UPDATE_VENDOR, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for row in spamreader:
            dia_code = sanitizeCustomerId(row[1])
            vat = row[0]
            if not o.odooCreate(dia_code,
                                update=True,
                                vat=vat,
                                create=False):
                ERROR_BUF.append("Unable to update %r" % str(row))


def getOrderDate(order_id):
    for order in BaseDbIntegration.GetDetails('sale.order', ['date_order'], [order_id]):
        return order['date_order']


def fixOrderDeliveryDate():
    order_dates = {}
    for line in BaseDbIntegration.GetDetailsSearch('sale.order.line',
                                                   #[('id', '>', 1133)],
                                                   [],
                                                   ['customer_lead', 'order_id', 'requested_date']):
        order_id = line.get('order_id')[0]
        if order_id in order_dates:
            order_date = order_dates[order_id]
        else:
            order_dates[order_id] = getOrderDate(order_id)
            order_date = order_dates[order_id]
        #customer_lead = line.get('customer_lead')
        requested_date = line.get('requested_date')
        line_id = line.get('id')
        if order_date and requested_date:
            order_date = datetime.datetime.strptime(order_date, DEFAULT_SERVER_DATETIME_FORMAT)
            requested_date = datetime.datetime.strptime(requested_date, DEFAULT_SERVER_DATETIME_FORMAT)
            difference = requested_date.date() - order_date.date()
            BaseDbIntegration.UpdateValue('sale.order.line', line_id, {'customer_lead': difference.days})
            print "Update line id ", line_id
        else:
            print "Jump"


def getOrderLineTrubleDate():
    for line in BaseDbIntegration.GetDetailsSearch('sale.order.line',
                                                   [],
                                                   ['requested_date', 'product_delivery_date']):
        requested_date = line.get('requested_date')
        product_delivery_date = line.get('product_delivery_date')
        if requested_date and product_delivery_date:
            requested_date = datetime.datetime.strptime(requested_date, DEFAULT_SERVER_DATETIME_FORMAT)
            product_delivery_date = datetime.datetime.strptime(product_delivery_date, DEFAULT_SERVER_DATETIME_FORMAT)
            if requested_date.date() != product_delivery_date.date():
                print requested_date, product_delivery_date, line.get('id')


def checkordermove():
    count = 0
    for move in BaseDbIntegration.GetDetailsSearch('stock.move',
                                                   [('sale_line_id', '!=', False)],
                                                   ['sale_line_id', 'date']):
        sale_line_id = move.get('sale_line_id')[0]
        move_id = move.get('id')
        for sale_order_line in BaseDbIntegration.GetDetails('sale.order.line', ['requested_date'], sale_line_id):
            requested_date = sale_order_line.get('requested_date')
            date = move.get('date')
            if date and requested_date:
                requested_date = datetime.datetime.strptime(requested_date, DEFAULT_SERVER_DATETIME_FORMAT)
                date = datetime.datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
                if requested_date.date() != date.date():
                    count += 1
                    #  print count, requested_date, move_date, move_id
                    print "update stock_move set date = %r where id = %r;" % (requested_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT), move_id)


def fix_fornitore_field(column_number, odoo_field_name):
    global ERROR_BUF
    missing_payment = []
    all_payment = getIdName('account.payment.term')
    with open(ANA_FORM, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in spamreader:
            try:
                if int(spamreader.line_num) == 1:
                    continue
                print ("import row %r error %r " % (spamreader.line_num, len(ERROR_BUF)))
                if row[1][0] == '-':  # Fornitori obsoleti
                    continue
                res_partner_id = BaseDbIntegration.Search('res.partner', ('dia_ref_vendor', '=', sanitizeDiaId(row[0])))
                if res_partner_id:
                    payment_id = all_payment.get(row[column_number])
                    if not payment_id:
                        msg = "no Payment found for row %r" % row
                        print msg
                        ERROR_BUF.append(msg)
                        missing_payment.append(row[column_number])
                        continue
                    BaseDbIntegration.UpdateValue('res.partner',
                                                  res_partner_id,
                                                  {odoo_field_name: payment_id})
            except Exception as ex:
                msg = "Error: %r on wor: %r" % (ex, row)
                print msg
                ERROR_BUF.append(msg)

    missing_payment = set(missing_payment)
    for pay in missing_payment:
        print(pay)



def fixMoveLine(ids, qty):
    BaseDbIntegration.UpdateValue('stock.move', ids, {'quantity_done': qty})


def check_machine(mail_to):
    BaseDbIntegration.callCustomMethod('mrp.workcenter', 'check_machine_electronic_boards', (mail_to))


def update_vendor_dia_iva():
    fiscal_position = getIdField('account.fiscal.position', 'dia_code')
    counter = 0
    xl_workbook = xlrd.open_workbook(VEDNOR_ANAG_DIA_IVA)
    xl_sheet = xl_workbook.sheet_by_index(0)
    for row in xl_sheet.get_rows():
        if counter == 0:
            counter += 1
            continue
        counter += 1
        try:
            print '%s -- %s' % (counter, row)
            codice = row[0].value  # CODICE
            codice_iva = row[4].value  # CODICE IVA
            fiscal_position_id = fiscal_position.get(codice_iva)
            res = BaseDbIntegration.callCustomMethod('res.partner', 'fix_fiscal_position_dia', (codice, fiscal_position_id))
            if not res:
                msg = "Codice Client %r non aggiornato " % (codice)
                ERROR_BUF.append(msg)
        except Exception as ex:
            msg = "Codice Client %r , %r" % (codice, ex)
            ERROR_BUF.append(msg)

def updateCausaleDIAType():
    def getCausaleIDFromDB(causaleCode):
        res = BaseDbIntegration.Search('dia.causale', queryFilter=[('name', '=', causaleCode)])
        for elem in res:
            return elem
        return False
    def updateCausaleType(causaleID, causaleType):
        if not causaleID:
            return
        mapping = {
            'nessuno': 'nessuno',
            'scarico+carico': 'scarico_carico',
            'scarico': 'scarico'
            }
        odooVal = mapping.get(causaleType, 'nessuno')
        print ('Update Causale ID %r with type %r' % (causaleID, odooVal))
        BaseDbIntegration.UpdateValue('dia.causale', [causaleID], {'causale_type': odooVal})
    xl_workbook = xlrd.open_workbook(UPDATE_CAUSALI)
    xl_sheet = xl_workbook.sheet_by_index(0)
    counter = 0
    for row in xl_sheet.get_rows():
        if counter == 0:
            counter += 1
            continue
        counter += 1
        print '%s -- %s' % (counter, row)
        causaleName = row[0].value
        _causaleDesc = row[1].value
        causaleTipo = row[2].value
        _void = row[3].value

        causaleID = getCausaleIDFromDB(causaleName)
        updateCausaleType(causaleID, causaleTipo)


def updatePickingMove():
    global ERROR_BUF
    valsdict = {'N0000235': [{'num_ddt': 'N0000235',
                              'data_ddt': '09/08/2018',
                              'prod_code': 'A284971',
                              'prod_qty': 978,
                              'prod_price': 1.405,
                              'sale_number': 'A0000469',
                              'dest_loc_id': 15,  # WH Stock
                              'uom': 1,  # Units
                              }],
                'N0000236': [{'num_ddt': 'N0000236',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A283681',
                             'prod_qty': 320,
                             'prod_price': 2.242,
                             'sale_number': 'A0000546',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'N0000236',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A288260',
                             'prod_qty': 1980,
                             'prod_price': 0.770,
                             'sale_number': 'A0000554',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'N0000236',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A284971',
                             'prod_qty': 1022,
                             'prod_price': 1.405,
                             'sale_number': 'A0000613',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'N0000237': [{'num_ddt': 'N0000237',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A286280',
                             'prod_qty': 340,
                             'prod_price': 3.453,
                             'sale_number': 'A0000551',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'N0000237',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A286280',
                             'prod_qty': 404,
                             'prod_price': 3.453,
                             'sale_number': 'A0000574',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'N0000237',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A215702',
                             'prod_qty': 120,
                             'prod_price': 1.101,
                             'sale_number': 'A0000581',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'N0000237',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A215701',
                             'prod_qty': 240,
                             'prod_price': 1.094,
                             'sale_number': 'A0000636',
                             'dest_loc_id': 15,
                             'uom': 1,
    
    },
                            ],
                'N0000238': [{'num_ddt': 'N0000238',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A285000',
                             'prod_qty': 2000,
                             'prod_price': 0.355,
                             'sale_number': 'A0000634',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'N0000238',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A285010',
                             'prod_qty': 2000,
                             'prod_price': 0.355,
                             'sale_number': 'A0000634',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'N0000239': [{'num_ddt': 'N0000239',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A285000',
                             'prod_qty': 2000,
                             'prod_price': 0.355,
                             'sale_number': 'A0000635',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'N0000240': [{'num_ddt': 'N0000240',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A214602',
                             'prod_qty': 2880,
                             'prod_price': 0.667,
                             'sale_number': 'A0000635',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001583': [{'num_ddt': 'U0001583',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A237850',
                             'prod_qty': 599,
                             'prod_price': 4.831,
                             'sale_number': 'A0000054',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001584': [{'num_ddt': 'U0001584',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A237330',
                             'prod_qty': 384,
                             'prod_price': 7.904,
                             'sale_number': 'A0000258',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001584',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A237380',
                             'prod_qty': 99,
                             'prod_price': 7.085,
                             'sale_number': 'A0000494',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001585': [{'num_ddt': 'U0001585',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A285271',
                             'prod_qty': 7296,
                             'prod_price': 1.333,
                             'sale_number': 'A0000514',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001586': [{'num_ddt': 'U0001586',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A287020',
                             'prod_qty': 3334,
                             'prod_price': 0.914,
                             'sale_number': 'A0000526',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001586',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A287010',
                             'prod_qty': 6932,
                             'prod_price': 0.942,
                             'sale_number': 'A0000526',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001587': [{'num_ddt': 'U0001587',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A215601',
                             'prod_qty': 381,
                             'prod_price': 3.467,
                             'sale_number': 'A0000273',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001587',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A215601',
                             'prod_qty': 1598,
                             'prod_price': 3.467,
                             'sale_number': 'A0000499',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001587',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A219901',
                             'prod_qty': 843,
                             'prod_price': 3.858,
                             'sale_number': 'A0000614',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001588': [{'num_ddt': 'U0001588',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A288231',
                             'prod_qty': 155,
                             'prod_price': 6.060,
                             'sale_number': 'A0000593',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001588',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A288230',
                             'prod_qty': 76,
                             'prod_price': 7.140,
                             'sale_number': 'A0000596',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001589': [{'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A501780',
                             'prod_qty': 2210,
                             'prod_price': 0.567,
                             'sale_number': 'P0000397',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A612330',
                             'prod_qty': 10500,
                             'prod_price': 0.121,
                             'sale_number': 'P0000397',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A612340',
                             'prod_qty': 10500,
                             'prod_price': 0.108,
                             'sale_number': 'P0000397',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A612370',
                             'prod_qty': 10000,
                             'prod_price': 0.039,
                             'sale_number': 'P0000397',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A670710',
                             'prod_qty': 3000,
                             'prod_price': 0.352,
                             'sale_number': 'P0000397',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A678001',
                             'prod_qty': 945,
                             'prod_price': 3.364,
                             'sale_number': 'P0000396',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A681320',
                             'prod_qty': 1680,
                             'prod_price': 4.177,
                             'sale_number': 'P0000396',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001589',
                             'data_ddt': '09/08/2018',
                             'prod_code': 'A684680',
                             'prod_qty': 260,
                             'prod_price': 1.357,
                             'sale_number': 'P0000361',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                'U0001590': [{'num_ddt': 'U0001590',
                             'data_ddt': '10/08/2018',
                             'prod_code': 'A284670',
                             'prod_qty': 1720,
                             'prod_price': 1.661,
                             'sale_number': '',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                              {'num_ddt': 'U0001590',
                             'data_ddt': '10/08/2018',
                             'prod_code': 'A284670',
                             'prod_qty': 2000,
                             'prod_price': 1.661,
                             'sale_number': '',
                             'dest_loc_id': 15,
                             'uom': 1,
    },
                            ],
                
        }
    #BaseDbIntegration.callCustomMethod('stock.move', 'createDiaPickingAndMove', [valsdict])
    res = BaseDbIntegration.callCustomMethod('stock.move', 'updateSaleOrderLineFromPicking', [valsdict])
    ERROR_BUF.extend(res)


ERROR_BUF = []
#impo_ana_for(update=True)
#imp_location()
#inport_an_art()
#imp_giacenze()
#inport_an_art_bom()
#fixUomBom()
#impRouting()
#impAttrezza()
#fixAttrezza()
#fixMaterozza()
#fixAtterzzaRoutings()
#-> manca in produzione da qui 
#fixAtterzzaRoutingsConsums()
#updateCustomerRef()
#imp_subcontracting_price()
#updateRoutingDocuments()
#impSo()
#icdia()
#fixAddress()
#fixAddress1()
#fixOrderDeliveryDate()
#getOrderLineTrubleDate()

#checkordermove()

#fix_fornitore_field(31, 'property_supplier_payment_term_id')
#impSo("P0000479")

#check_machine(['matteo.boscolo@omniasolutions.eu'])
#update_vendor_dia_iva()
#fixMoveLine([14114], 269.28)

#updateCausaleDIAType()

updatePickingMove()
#moveID = 16413
#BaseDbIntegration.callCustomMethod('stock.move', 'clientActionConfirm', [moveID])
#BaseDbIntegration.callCustomMethod('stock.move', 'clientActionDone', [moveID])
#BaseDbIntegration.UpdateValue('stock.move', [moveID], {'date': '2018-09-15 08:43:06'})

new_file_name = "import_data_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".err"
with open(new_file_name, 'wb') as f:
    for err in ERROR_BUF:
        err = str(err) + "\r"
        print (err)
        f.write(err)
print ("<<<" * 20)
print ("Numero di errori", len(ERROR_BUF))
print ("<<<" * 20)
# old import

# impBom()
#
# impSo()
# impAttrezza()

