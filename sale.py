# This file is part sale_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond import backend
from trytond.model import fields, Unique
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval

__all__ = ['Sale']


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    shop = fields.Many2One('sale.shop', 'Shop', required=True, domain=[
            ('id', 'in', Eval('context', {}).get('shops', [])),
            ],
        states={
            'readonly': (Eval('state') != 'draft') | Bool(Eval('number')),
        }, depends=['number', 'state'])
    shop_address = fields.Function(fields.Many2One('party.address',
            'Shop Address'),
        'on_change_with_shop_address')

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints.extend([
            ('number_uniq', Unique(t, t.shop, t.number),
                'There is another sale with the same number.\n'
                'The number of the sale must be unique!')
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
        if 'shop' not in cls.party.on_change:
            cls.party.on_change.add('shop')

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        table = TableHandler(cls, module_name)
        # Migration from 3.8: remove reference constraint
        if not table.column_exist('number'):
            table.drop_constraint('reference_uniq')

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
        Shop = pool.get('sale.shop')
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
        pool = Pool()
        User = pool.get('res.user')
        Shop = pool.get('sale.shop')

        user = User(Transaction().user)
        context = Transaction().context
        if context.get('shop'):
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
        if not hasattr(self, 'shop') or not self.shop:
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

    def on_change_party(self):
        super(Sale, self).on_change_party()

        if hasattr(self, 'shop') and self.shop:
            if not self.price_list and self.invoice_address:
                self.price_list = self.shop.price_list.id
                self.price_list.rec_name = self.shop.price_list.rec_name
            if not self.payment_term and self.invoice_address:
                self.payment_term = self.shop.payment_term.id
                self.payment_term.rec_name = self.shop.payment_term.rec_name

    @classmethod
    def set_number(cls, sales):
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
            if sale.number:
                continue
            if sale.shop:
                number = Sequence.get_id(sale.shop.sale_sequence.id)
            elif user.shop:
                number = Sequence.get_id(user.shop.sale_sequence.id)
            else:
                number = Sequence.get_id(config.sale_sequence.id)
            cls.write([sale], {
                    'number': number,
                    })
