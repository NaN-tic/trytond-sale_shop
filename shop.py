# This file is part sale_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import If, Eval, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool

__all__ = ['SaleShop', 'SaleShopResUser']


class SaleShop(ModelSQL, ModelView):
    'Sale Shop'
    __name__ = 'sale.shop'

    name = fields.Char('Shop Name', required=True, select=True)
    users = fields.Many2Many('sale.shop-res.user', 'shop', 'user', 'Users')
    address = fields.Many2One('party.address', 'Address', domain=[
            ('party', '=', Eval('company_party')),
            ], depends=['company_party'])
    warehouse = fields.Many2One('stock.location', "Warehouse", required=True,
        domain=[('type', '=', 'warehouse')])
    price_list = fields.Many2One('product.price_list', 'Pricelist',
        required=True)
    payment_term = fields.Many2One('account.invoice.payment_term',
        'Payment Term', required=True)
    sale_sequence = fields.Property(fields.Many2One('ir.sequence',
            'Sale Reference Sequence', domain=[
                ('company', 'in', [Eval('context', {}).get('company', 0),
                        None]),
                ('code', '=', 'sale.sale'),
                ], required=True))
    sale_invoice_method = fields.Property(fields.Selection([
                ('manual', 'Manual'),
                ('order', 'On Order Processed'),
                ('shipment', 'On Shipment Sent')
                ], 'Sale Invoice Method', states={
                'required': Bool(Eval('context', {}).get('company', 0)),
                }))
    sale_shipment_method = fields.Property(fields.Selection([
                ('manual', 'Manual'),
                ('order', 'On Order Processed'),
                ('invoice', 'On Invoice Paid'),
                ], 'Sale Shipment Method', states={
                'required': Bool(Eval('context', {}).get('company', 0)),
                }))
    company = fields.Many2One('company.company', 'Company', required=True,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', 0)),
            ], select=True)
    company_party = fields.Function(fields.Many2One('party.party',
            'Company Party'),
        'on_change_with_company_party')
    active = fields.Boolean('Active', select=True)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def sale_configuration():
        Config = Pool().get('sale.configuration')
        config = Config(1)
        return config

    @fields.depends('company')
    def on_change_with_company_party(self, name=None):
        Company = Pool().get('company.company')
        company = self.company
        if not company:
            company = Company(SaleShop.default_company())
        return company and company.party.id or None


class SaleShopResUser(ModelSQL):
    'Sale Shop - Res User'
    __name__ = 'sale.shop-res.user'
    _table = 'sale_shop_res_user'

    shop = fields.Many2One('sale.shop', 'Shop', ondelete='CASCADE',
        select=True, required=True)
    user = fields.Many2One('res.user', 'User', ondelete='RESTRICT',
        required=True)
