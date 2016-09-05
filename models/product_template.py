# -*- coding: utf-8 -*-

from openerp import api, fields, models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    consignor_sub_carrier_csid = fields.Integer(string="Sub Carrier CSID")
    consignor_sub_carrier_name = fields.Char(string="Sub Carrier Name")
    consignor_product_prod_csid = fields.Integer(string="Product CSID")
    consignor_product_prod_name = fields.Char(string="Product Name")