#!/usr/bin/env python
#This file is part sale_shop module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.

import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends, doctest_dropdb
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class SaleShopTestCase(unittest.TestCase):
    '''
    Test SaleShop module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('sale_shop')
        self.company = POOL.get('company.company')
        self.user = POOL.get('res.user')
        self.shop = POOL.get('sale.shop')
        self.location = POOL.get('stock.location')
        self.price_list = POOL.get('product.price_list')
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.sequence = POOL.get('ir.sequence')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('sale_shop')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def test0010_create_shop(self):
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            #This is needed in order to get default values for other test
            #executing in the same database
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            with transaction.set_context(company=company.id):
                sequence, = self.sequence.search([
                        ('code', '=', 'sale.sale'),
                        ], limit=1)
                warehouse, = self.location.search([
                        ('code', '=', 'WH'),
                        ])
                price_list, = self.price_list.create([{
                            'name': 'Test',
                            }])
                term, = self.payment_term.create([{
                            'name': 'Payment term',
                            'lines': [
                                ('create', [{
                                            'sequence': 0,
                                            'type': 'remainder',
                                            'days': 0,
                                            'months': 0,
                                            'weeks': 0,
                                            }])]
                            }])
                shop, = self.shop.create([{
                            'name': 'Shop',
                            'warehouse': warehouse.id,
                            'price_list': price_list.id,
                            'payment_term': term.id,
                            'sale_sequence': sequence.id,
                            'sale_invoice_method': 'order',
                            'sale_invoice_method': 'order',
                            }])
                user = self.user(USER)
                self.user.write([user], {
                        'shops': [('add', [shop])],
                        'shop': shop.id,
                         })
            transaction.cursor.commit()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        SaleShopTestCase))
    suite.addTests(doctest.DocFileSuite(
            'scenario_sale_shop.rst',
            setUp=doctest_dropdb, tearDown=doctest_dropdb, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
