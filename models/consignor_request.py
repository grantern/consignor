# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import logging
import os
import suds  # should work with suds or its fork suds-jurko

from datetime import datetime
from suds.client import Client
import urllib2,  httplib, urlparse, gzip, requests, json
from urllib2 import URLError


_logger = logging.getLogger(__name__)
# uncomment to enable logging of SOAP requests and responses
# logging.getLogger('suds.client').setLevel(logging.DEBUG)


class ConsignorRequest():
    """ Low-level object intended to interface Odoo recordsets with Consignor,
        through appropriate SOAP requests """

    def loadactor(self, actor_id, key):
        res = []
        httplib.HTTPConnection._http_vsn = 10
        httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'
        req = urllib2.Request("http://sstest.consignor.com/ship/ShipmentServerModule.dll")
        req.add_header('actor', '63')
        req.add_header('key', 'sample')
        req.add_header('command', 'GetProducts')
        try:
            resp = urllib2.urlopen(req)
        except StandardError:
            print "error connecting to Consignor"
            return False

        return res

    # def __init__(self, request_type="shipping", test_mode=True):
    #     self.hasCommodities = False
    #     self.hasOnePackage = False
    #
    #     # TODO - Add the correct wsdl files for Consignor or change to http post messages
    #     if request_type == "shipping":
    #         if test_mode:
    #             wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                                      '../api/test/ShipService_v15.wsdl')
    #         else:
    #             wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                                      '../api/prod/ShipService_v15.wsdl')
    #         self.start_shipping_transaction(wsdl_path)
    #
    #     elif request_type == "rating":
    #         if test_mode:
    #             wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                                      '../api/test/RateService_v16.wsdl')
    #         else:
    #             wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                                      '../api/prod/RateService_v16.wsdl')
    #         self.start_rating_transaction(wsdl_path)