# This file is part sale_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import PoolMeta


class User(metaclass=PoolMeta):
    __name__ = "res.user"
    shops = fields.Many2Many('sale.shop-res.user', 'user', 'shop', 'Shops')
    shop = fields.Many2One('sale.shop', 'Shop', domain=[
            ('id', 'in', Eval('shops', [])),
            ('company', '=', Eval('company', -1),)
            ], depends=['shops', 'company'])

    @classmethod
    def __setup__(cls):
        super(User, cls).__setup__()
        cls._context_fields.insert(0, 'shop')
        cls._context_fields.insert(0, 'shops')

    def get_status_bar(self, name):
        status = super(User, self).get_status_bar(name)
        if self.shop:
            status += ' - %s' % (self.shop.rec_name)
        return status

    @fields.depends('shops')
    def on_change_company(self):
        super().on_change_company()
        self.shop = None

        if self.company:
            shops = [shop for shop in self.shops
                        if shop.company == self.company]
            if len(shops) == 1:
                self.shop = shops[0]

    @classmethod
    def _get_preferences(cls, user, context_only=False):
        res = super(User, cls)._get_preferences(user,
            context_only=context_only)
        if not context_only:
            res['shops'] = [c.id for c in user.shops]
            res['shop'] = user.shop and user.shop.id or None
        return res
