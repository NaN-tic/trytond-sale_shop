#This file is part sale_shop module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields
from trytond.tools import safe_eval, datetime_strftime
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import Eval, Bool

class SaleShop(ModelSQL, ModelView):
    'Sale Shop'
    _name = 'sale.shop'
    _description = __doc__
    name = fields.Char('Shop Name', required=True, select=True)
    users = fields.Many2Many('sale.shop-res.user', 'shop', 'user', 'Users')
    warehouse = fields.Many2One('stock.location', "Warehouse", required=True,
        domain=[('type', '=', 'warehouse')])
    price_list = fields.Many2One('product.price_list', 'Pricelist', required=True)
    payment_term = fields.Many2One('account.invoice.payment_term',
        'Payment Term', required=True)
    sale_sequence = fields.Property(fields.Many2One('ir.sequence',
            'Sale Reference Sequence', domain=[
                ('company', 'in', [Eval('context', {}).get('company', 0),
                        False]),
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

SaleShop()

class SaleShopResUserRel(ModelSQL):
    'Sale Shop - Res User'
    _name = 'sale.shop-res.user'
    _table = 'sale_shop_res_user_rel'
    _description = __doc__
    shop = fields.Many2One('sale.shop', 'Shop',
            ondelete='RESTRICT', select=1, required=True)
    user = fields.Many2One('res.user', 'User',
            ondelete='RESTRICT', required=True)

SaleShopResUserRel()
