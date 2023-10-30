# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta


class Rule(metaclass=PoolMeta):
    __name__ = 'ir.rule'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.domain.help += '\n- "shops" from the current user'

    @classmethod
    def _get_cache_key(cls, model_name):
        pool = Pool()
        User = pool.get('res.user')
        key = super()._get_cache_key(model_name)
        return (*key, User.get_shop())

    @classmethod
    def _get_context(cls, model_name):
        pool = Pool()
        User = pool.get('res.user')
        context = super()._get_context(model_name)
        context['shop'] = User.get_shop()
        context['shops'] = User.get_shops()
        return context
