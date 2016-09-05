# -*- coding: utf-8 -*-

from openerp import api, fields, models


class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    consignor_carrier_csid = fields.Integer(string="Carrier CSID")
    consignor_carrier_concept_id = fields.Integer(string="Carrier Concept ID")
    consignor_carrier_full_name = fields.Char(string="Carrier Full Name")
    consignor_carrier_short_name = fields.Char(string="Carrier Short Name")

