# This file is part sale_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond import backend
from trytond.model import fields, Unique
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval, Or
import logging

__all__ = ['Sale']
__metaclass__ = PoolMeta

logger = logging.getLogger(__name__)


class Sale:
    __name__ = 'sale.sale'
    shop = fields.Many2One('sale.shop', 'Shop', required=True, domain=[
            ('id', 'in', Eval('context', {}).get('shops', [])),
            ],
        states={
            'readonly': Or(Bool(Eval('reference')), Bool(Eval('lines'))),
            }, depends=['reference', 'lines'])
    shop_address = fields.Function(fields.Many2One('party.address',
            'Shop Address'),
        'on_change_with_shop_address')

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints.extend([
            ('reference_uniq', Unique(t, t.shop, t.reference),
                'There is another sale with the same reference.\n'
                'The reference of the sale must be unique!')
            ])

        shipment_addr_domain = cls.shipment_address.domain[:]
        if shipment_addr_domain:
            cls.shipment_address.domain = [
                'OR',
                shipment_addr_domain,
                [('id', '=', Eval('shop_address', 0))],
                ]
        else:
            cls.shipment_address.domain = [('id', '=', Eval('shop_address'))]
        cls.shipment_address.depends.append('shop_address')

        cls.currency.states['readonly'] |= Eval('shop')
        cls.currency.depends.append('shop')

        cls._error_messages.update({
                'not_sale_shop': (
                    'Go to user preferences and select a shop ("%s")'),
                'sale_not_shop': (
                    'Sale have not related a shop'),
                'edit_sale_by_shop': ('You cannot edit this order because you '
                    'do not have permission to edit in this shop.'),
            })


    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().cursor
        table = TableHandler(cursor, cls, module_name)
        if not table.column_exist('shop'):
            table.add_raw_column(
                    'shop',
                    cls.shop.sql_type(),
                    cls.shop.sql_format, None, None
                    )
            logger.warning(
                'Create a Sale Shop and assign current sales with this shop '
                    'with SQL:')
            logger.warning(
                'UPDATE sale_sale set shop = 1;')
        super(Sale, cls).__register__(module_name)

    @staticmethod
    def default_company():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return user.shop.company.id if user.shop else \
            Transaction().context.get('company')

    @staticmethod
    def default_shop():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return user.shop.id if user.shop else None

    @staticmethod
    def default_invoice_method():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if not user.shop:
            Config = Pool().get('sale.configuration')
            config = Config(1)
            return config.sale_invoice_method
        return user.shop.sale_invoice_method

    @staticmethod
    def default_shipment_method():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if not user.shop:
            Config = Pool().get('sale.configuration')
            config = Config(1)
            return config.sale_shipment_method
        return user.shop.sale_shipment_method

    @staticmethod
    def default_warehouse():
        pool = Pool()
        User = pool.get('res.user')
        Shop =  pool.get('sale.shop')
        Location = pool.get('stock.location')

        if Transaction().context.get('shop'):
            shop = Shop(Transaction().context.get('shop'))
            return shop.warehouse.id

        user = User(Transaction().user)
        if user.shop:
            return user.shop.warehouse.id

        warehouse, = Location.search([
            ('type', '=', 'warehouse'),
            ], limit=1)
        return warehouse.id

    @staticmethod
    def default_price_list():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return user.shop.price_list.id if user.shop else None

    @staticmethod
    def default_payment_term():
        User = Pool().get('res.user')
        Shop = Pool().get('sale.shop')
        user = User(Transaction().user)
        context = Transaction().context
        if 'shop' in context:
            shop = Shop(context['shop'])
            if shop.payment_term:
            	return shop.payment_term.id
        return user.shop.payment_term.id if user.shop else None

    @staticmethod
    def default_shop_address():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return (user.shop and user.shop.address and
            user.shop.address.id or None)

    @fields.depends('shop', 'party')
    def on_change_shop(self):
        if not self.shop:
            return
        for fname in ('company', 'warehouse', 'currency', 'payment_term'):
            fvalue = getattr(self.shop, fname)
            if fvalue:
                setattr(self, fname, fvalue.id)
        if ((not self.party or not self.party.sale_price_list)
                and self.shop.price_list):
            self.price_list = self.shop.price_list.id
        if self.shop.sale_invoice_method:
            self.invoice_method = self.shop.sale_invoice_method
        if self.shop.sale_shipment_method:
            self.shipment_method = self.shop.sale_shipment_method

    @fields.depends('shop')
    def on_change_with_shop_address(self, name=None):
        return (self.shop and self.shop.address and
            self.shop.address.id or None)

    @fields.depends('shop')
    def on_change_party(self):
        super(Sale, self).on_change_party()

        if self.shop:
            if not self.price_list and self.invoice_address:
                self.price_list = self.shop.price_list.id
                self.price_list.rec_name = self.shop.price_list.rec_name
            if not self.payment_term and self.invoice_address:
                self.payment_term = self.shop.payment_term.id
                self.payment_term.rec_name = self.shop.payment_term.rec_name

    @classmethod
    def set_reference(cls, sales):
        '''
        Fill the reference field with the sale shop or sale config sequence
        '''
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('sale.configuration')
        User = Pool().get('res.user')

        config = Config(1)
        user = User(Transaction().user)
        for sale in sales:
            if sale.reference:
                continue
            if sale.shop:
                reference = Sequence.get_id(sale.shop.sale_sequence.id)
            elif user.shop:
                reference = Sequence.get_id(user.shop.sale_sequence.id)
            else:
                reference = Sequence.get_id(config.sale_sequence.id)
            cls.write([sale], {
                    'reference': reference,
                    })

    @classmethod
    def create(cls, vlist):
        vlist2 = []
        for vals in vlist:
            User = Pool().get('res.user')
            user = User(Transaction().user)
            vals = vals.copy()
            if not 'shop' in vals:
                if not user.shop:
                    cls.raise_user_error('not_sale_shop', (
                            user.rec_name,)
                            )
                vals['shop'] = user.shop.id
            vlist2.append(vals)
        return super(Sale, cls).create(vlist2)

    @classmethod
    def write(cls, *args):
        '''
        Only edit Sale users available edit in this shop
        '''
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if user.id != 0:
            actions = iter(args)
            for sales, _ in zip(actions, actions):
                for sale in sales:
                    if not sale.shop:
                        cls.raise_user_error('sale_not_shop')
                    if not sale.shop in user.shops:
                        cls.raise_user_error('edit_sale_by_shop')
        super(Sale, cls).write(*args)
