# -*- coding: utf-8 -*-
# TinderBox AS - Addon, See LICENSE file for full copyright and licensing details.
import logging
from openerp import api, models, fields, _
from openerp.exceptions import ValidationError
import urllib2, urllib, httplib, urlparse, gzip, requests, json
from urllib2 import URLError

from consignor_request import ConsignorRequest


_logger = logging.getLogger(__name__)


class ProviderConsignor(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('consignor', "Consignor")])

    # TODO Set the needed properties for interacting with the Consignor API
    consignor_server_url = fields.Char(string="Server URL")
    consignor_server_key = fields.Char(string="Key")
    consignor_actor_id = fields.Char(string="Account ID")
    consignor_categ_id = fields.Many2one('product.category', 'Internal Category', required=True, change_default=True,
                               domain="[('type','=','normal')]", help="Select category for the delivery products")
    consignor_test_mode = fields.Boolean(default=True, string="Test Mode", help="Uncheck this box to use production Consignor Web Services")

    @api.multi
    def load_consignor_actor(self):
        print "load_consignor_actor"
        url = self.consignor_server_url
        values = {'actor': self.consignor_actor_id,
                  'key': self.consignor_server_key,
                  'command': 'GetProducts'}
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        result = response.read()
        res = json.loads(result)

        # Reading the Carriers information
        for Carrier in res['Carriers']:
            carrier_partner_id = self.insert_update_carrier(Carrier)

            # Reading the SubCarrier information - This is the high level services offered by the Carrier
            for SubCarrier in Carrier['Subcarriers']:
                sub_carrier_csid = SubCarrier['SubcarrierCSID']
                try:
                    sub_carrier_concept_id = SubCarrier['SubcarrierConceptID']
                except KeyError:
                    sub_carrier_concept_id = None
                sub_carrier_name = SubCarrier['SubcarrierName']
                print sub_carrier_name

                # Reading the product information within each service offered by the Carrier
                for Product in SubCarrier['Products']:
                    product_prod_csid = Product['ProdCSID']
                    try:
                        product_prod_concept_id = Product['ProdConceptID']
                    except KeyError:
                        product_prod_concept_id = None

                    product_prod_name = Product['ProdName']
                    print "  - ", product_prod_name

                    # Now we are able to create the delivery product in Odoo
                    delivery_product = self.env['product.template'].search([('consignor_sub_carrier_csid', '=',
                                                                             sub_carrier_csid), ('consignor_product_prod_csid', '=', product_prod_csid )])
                    if not delivery_product:
                        print "Insert product"
                        vals = {
                            'name': sub_carrier_name + " - " + product_prod_name,
                            'type': 'service',
                            'invoice_policy': 'order',
                            'purchase_method': 'receive',
                            'list_price': 0.00,
                            'consignor_sub_carrier_csid': sub_carrier_csid,
                            'consignor_product_prod_csid': product_prod_csid
                        }
                        if not self.consignor_test_mode:
                            delivery_product = self.env['product.template'].create(vals)
                            delivery_product_supplier = self.env['product.supplierinfo'].create({'name': carrier_partner_id,
                                                                                              'company_id': 1,
                                                                                              'product_tmpl_id': delivery_product.id})
                        # Insert or update the Delivery product in Delivery Carrier model
                        delivery_carrier = self.env['delivery.carrier'].search([('product_id', '=', delivery_product.id),
                                                                                ('partner_id', '=', carrier_partner_id)])
                        if not delivery_carrier:
                            vals = {
                                'delivery_type': 'consignor',
                                'product_id': delivery_product.id,
                                'shipping_enabled': True,
                                'free_if_more_than': False,
                                'partner_id': carrier_partner_id,
                                'consignor_server_url': self.consignor_server_url,
                                'consignor_server_key': self.consignor_server_key,
                                'consignor_actor_id': self.consignor_actor_id
                            }
                            if not self.consignor_test_mode:
                                delivery_carrier = self.env['delivery.carrier'].create(vals)
                            print delivery_carrier.id
                        else:
                            print "Delivery carrier update"
                        print delivery_product_supplier
                    else:
                        print "Update product"

        return []

    def insert_update_carrier(self,Carrier=[]):
        # Insert or update the Carrier information in res.partner model
        carrier_partner = self.env['res.partner'].search([('consignor_carrier_csid', '=', Carrier['CarrierCSID'])])
        if not carrier_partner:
            print "Insert ", Carrier['CarrierFullName']
            vals = {
                'company_type': 'company',
                'supplier': True, 'customer': False,
                'image': Carrier['Icon'],
                'name': Carrier['CarrierFullName'],
                'consignor_carrier_csid': Carrier['CarrierCSID'],
                'consignor_carrier_full_name': Carrier['CarrierFullName'],
                'consignor_carrier_short_name': Carrier['CarrierShortName']
            }
            if not self.consignor_test_mode:
                carrier_partner = self.env['res.partner'].create(vals)
                print carrier_partner.id
        else:
            print "Update ", Carrier['CarrierFullName']

        return carrier_partner.id

    def consignor_get_shipping_price_from_so(self, orders):
        res = []

        for order in orders:
            price = 123.0
            # Estimate weight of the sale order; will be definitely recomputed on the picking field "weight"
            # Odoo operates with weight expressed in KG, Consignor operates with wight expressed in grams.
            est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
            weight_value = _convert_weight(est_weight_value, "GR")

            # Get the Carrier product
            carrier_product = order.carrier_id

            url = self.consignor_server_url
            values = {'actor': self.consignor_actor_id,
                      'key': self.consignor_server_key,
                      'command': 'GetShipmentPrice'}
            sender = []
            sender = sender + ['hei:faen']
            senderAddress = {}
            senderAddress['Kind'] = '2'
            senderAddress['Name1'] = order.warehouse_id.partner_id.name
            senderAddress['Street1'] = order.warehouse_id.partner_id.street
            senderAddress['PostCode'] = order.warehouse_id.partner_id.zip
            senderAddress['City'] = order.warehouse_id.partner_id.city
            senderAddress['CountryCode'] = order.warehouse_id.partner_id.country_id.code

            receiverAddress = {}
            receiverAddress['Kind'] = '1'
            receiverAddress['Name1'] = order.partner_id.name
            receiverAddress['Street1'] = order.partner_id.street
            receiverAddress['PostalCode'] = order.partner_id.zip
            receiverAddress['City'] = order.partner_id.city
            receiverAddress['CountryCode'] = order.partner_id.country_id.code

            lines = {}
            lines['PkgWeight'] = weight_value
            lines['Pkgs'] = "[ { ItemNo: 1 } ]"

            getshipmentprice_data = {}
            getshipmentprice_data['Kind'] = '1'
            getshipmentprice_data['ActorCSID'] = self.consignor_actor_id
            getshipmentprice_data['ProdConceptID'] = order.carrier_id.consignor_product_prod_csid
            getshipmentprice_data['Addresses'] = '[' + json.dumps(senderAddress) + '],[' + json.dumps(receiverAddress) + ']'
            getshipmentprice_data['Lines'] = json.dumps(lines)
            getshipmentprice_data['shitty'] = json.dumps(sender)
            json_data = json.dumps(getshipmentprice_data)
            print json_data

            input_data = {
                'kind': 1,
                'ActorCSID': self.consignor_actor_id,
                'ProdConceptID': order.carrier_id.consignor_product_prod_csid
            }
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            result = response.read()
            js_res = json.loads(result)

            res = res + [price]

        return res

    def consignor_send_shipping(self, pickings):
        # Save Shipment or Submit Shipment?
        # If Save Shipment, implement a new Status,
        res = []
        shipping_data = {'exact_price': 123.0,
                         'tracking_number': '123456'}

        res = res + [shipping_data]
        return res

    def consignor_get_tracking_link(self, pickings):
        res = []
        return res

    def consignor_cancel_shipment(self, picking):
        res = []
        return res


def _convert_weight(weight, unit='KG'):
    ''' Convert picking weight (always expressed in KG) into the specified unit '''
    if unit == 'KG':
        return weight
    elif unit == 'GR':
        return weight * 1000.0
    else:
        raise ValueError
