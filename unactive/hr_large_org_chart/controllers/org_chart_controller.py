# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.http import request, route

import xml.etree.ElementTree as ET
from lxml import etree
import lxml.html

import base64
import logging


class ExOrgChartBuilder(http.Controller):
    
    def get_employees_xml_tree(self):

        def build_element(e, xml_e):
            
            def build_extended_array(e):
                jobs = []
                
                for child in e.child_ids:
                    if not (child.job_id in jobs):
                        jobs += child.job_id
                jobs.sort(key=lambda j: j.priority)

                expanded_children = request.env['hr.employee'].search(['&', ('parent_id', '=', e.ids[0]), ('child_ids', '!=', False)]).sorted(key=lambda e: e.job_id.priority)
                
                collapsed_children = []

                for job in jobs:
                    employees_in_job = request.env['hr.employee'].search(['&', '&', ('parent_id', '=', e.ids[0]), ('job_id', '=', job.ids[0]), ('child_ids', '=', False)])
                    if not job.collapse_on_org_chart:
                        expanded_children += employees_in_job
                    elif len(employees_in_job) >= 1:
                        collapsed_children += [(job, employees_in_job)]

                return expanded_children, collapsed_children

            ec, cc = build_extended_array(e)

            for child in ec:
                xml_child = ET.SubElement(xml_e, 'employee', {'name': child.name,
                                                    'job': str(child.job_id.name), 
                                                    'dept': str(child.department_id.name),
                                                    'dept_color': str(child.department_id.color), 
                                                    'id': str(child.ids[0]),
                                                    'position': ''      + ('leftmost'  if (len(e.child_ids) > 1) & (len(xml_e.getchildren()) == 0) else '')
                                                                        + (' rightmost' if (len(e.child_ids) > 1) & (len(xml_e.getchildren()) == (len(e.child_ids) - 1)) else '')
                                                                        + (' single'    if len(e.child_ids) == 1 else ''),
                                                    'hierarchy': 'ischild' + (' haschildren'  if len(child.child_ids) else ' chart_end'),
                                                    'tag_id': ''
                                                    })
                if len(child.child_ids):
                    build_element(child, xml_child)
            
            if cc:
                xml_cc = ET.SubElement(xml_e, 'collapsed-children', {'position': ''  
                                                                        + ('leftmost'   if (len(ec) > 0) & (len(xml_e.getchildren()) == 0) else '')
                                                                        + (' rightmost' if (len(ec) > 0) & (len(xml_e.getchildren()) == (len(ec))) else '')
                                                                        + (' single'    if len(ec) == 0 else ''),
                                                                        'dept_color': str(e.department_id.color),
                                                    })
            cc_clearer_bg = False
            for child in cc: 
                for empl in child[1]:
                    ET.SubElement(xml_cc, 'collapsed-employee', {'name': empl.name, 
                                                    'job': str(empl.job_id.name),
                                                    'dept': str(empl.department_id.name),
                                                    'id': str(empl.ids[0]),
                                                    'tag_id': '',
                                                    'add_cls': '' + ('clearer-bg' if cc_clearer_bg else '')
                                                    })
                    cc_clearer_bg = (not cc_clearer_bg)

                                                    
                
            
        root_employee = request.env['hr.employee'].search([('parent_id', '=', False)])[0]
        xml_root_employee = ET.Element('employee', {'name': root_employee.name, 
                                                    'job': str(root_employee.job_id.name), 
                                                    'dept': str(root_employee.department_id.name),
                                                    'dept_color': str(root_employee.department_id.color),
                                                    'id': str(root_employee.ids[0]),
                                                    'position': 'single',
                                                    'hierarchy': 'haschildren',
                                                    'tag_id': 'root-emp'})

        build_element(root_employee, xml_root_employee)

        xslt_doc = etree.fromstring(''' 
            <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="https://www.w3.org/TR/html401/">
                <xsl:output method="html"/>
                <xsl:template match="employee">
                    <div>
                        <xsl:attribute name="class">wrapper <xsl:value-of select="@position"/> dept-color-<xsl:value-of select="@dept_color"/></xsl:attribute>

                        <div class="container">
                            <div>
                                <xsl:attribute name="class">kanban-employee <xsl:value-of select="@hierarchy"/> dept-color-<xsl:value-of select="@dept_color"/></xsl:attribute>
                                <xsl:attribute name="id"><xsl:value-of select="@tag_id"/></xsl:attribute>

                                <span class="employee-image">
                                    <xsl:attribute name="style">background-image: url(/web/image/hr.employee/<xsl:value-of select="@id"/>/image/)</xsl:attribute>
                                    <xsl:attribute name="class">employee-image dept-color-<xsl:value-of select="@dept_color"/></xsl:attribute>

                                    <xsl:comment/>
                                </span>
                                
                                <h1><xsl:comment/><xsl:value-of select="@name"/></h1>
                                <p1><xsl:comment/><xsl:value-of select="@job"/></p1>
                            </div>                         
                        </div>

                        <xsl:apply-templates/>
                    </div>
                </xsl:template>
                <xsl:template match="collapsed-children">
                    <div>
                        <xsl:attribute name="class">wrapper cc <xsl:value-of select="@position"/> dept-color-<xsl:value-of select="@dept_color"/></xsl:attribute>

                        <div class="container">
                            <div>
                                <xsl:attribute name="class">kanban-cc ischild chart_end dept-color-<xsl:value-of select="@dept_color"/></xsl:attribute>

                                <xsl:apply-templates/>
                            </div>                         
                        </div>
                    </div>
                </xsl:template>
                <xsl:template match="collapsed-employee">
                    <div>
                        <xsl:attribute name="class">collapsed-employee <xsl:value-of select="@add_cls"/></xsl:attribute>

                        <span class="employee-image">
                            <xsl:attribute name="style">background-image: url(/web/image/hr.employee/<xsl:value-of select="@id"/>/image/)</xsl:attribute>

                            <xsl:comment/>
                        </span>                
                        <h2><xsl:comment/><xsl:value-of select="@name"/></h2>
                        <p2><xsl:comment/><xsl:value-of select="@job"/></p2>
                    </div>
                </xsl:template>
            </xsl:stylesheet>
        ''')

        xslt_transformer = etree.XSLT(xslt_doc)

        org_chart = xslt_transformer(etree.fromstring(ET.tostring(xml_root_employee)))
        
        return (etree.tostring(org_chart)).decode('utf-8')


    @http.route('/hr/org_chart', type='http', auth='public', website=True)
    def show_org_chart(self):

        return '''
            <html>
                <head>
                    <title>Organigramma</title>
	                <link type="text/css" rel="stylesheet" href="/rds_hr/static/report/css/org_chart.css" />
                    <style>body { width: ''' + str(self.get_employees_xml_tree().count('chart_end')*280) + '''px}</style>
                </head>
                <body>
                    <div class="main_wrapper">
                        ''' + self.get_employees_xml_tree() + '''
                    </div>
                </body>
            </html>
        '''
