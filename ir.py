# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import (
    EvalEnvironment, ModelSQL, ModelView, dualmethod, fields)
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class Rule(metaclass=PoolMeta):
    __name__ = 'ir.rule'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.domain.help += '\n- "shops" from the current user'

    @classmethod
    def _get_cache_key(cls):
        key = super(Rule, cls)._get_cache_key()
        # XXX Use shop from context instead of browse to prevent infinite
        # loop, but the cache is cleared when User is written.
        context = Transaction().context
        return key + (
            context.get('shop'),
            )

    @classmethod
    def _get_context(cls):
        pool = Pool()
        User = pool.get('res.user')
        Employee = pool.get('company.employee')
        context = super()._get_context()
        # Use root to avoid infinite loop when accessing user attributes
        user_id = Transaction().user
        with Transaction().set_user(0):
            user = User(user_id)
        context['shop'] = user.shop.id if user.shop else []
        context['shops'] = [c.id for c in user.shops]
        return context
