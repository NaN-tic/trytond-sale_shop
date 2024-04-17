
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase


class SaleShopCompanyTestMixin(CompanyTestMixin):

    @property
    def _skip_company_rule(self):
        return super()._skip_company_rule | {
            ('sale.shop', 'company'),
            }


class SaleShopTestCase(SaleShopCompanyTestMixin, ModuleTestCase):
    'Test SaleShop module'
    module = 'sale_shop'


del ModuleTestCase
