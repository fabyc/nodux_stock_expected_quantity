#This file is part of Tryton.  The COPYRIGHT file at the top level
#of this repository contains the full copyright notices and license terms.
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Not, Equal, Eval, Or, Bool
from trytond import backend
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = [ 'InventoryLine']
__metaclass__ = PoolMeta

class InventoryLine():
    'Stock Inventory Line'
    __name__ = 'stock.inventory.line'

    @classmethod
    def __setup__(cls):
        super(InventoryLine, cls).__setup__()
        cls.expected_quantity.readonly = False

    @classmethod
    def validate(cls, lines):
        pool = Pool()
        Product = pool.get('product.product')
        product_qty = {}
        for line in lines:
            if line.inventory.date:
                if line.inventory.location:
                    with Transaction().set_context(stock_date_end = line.inventory.date):
                        pbl = Product.products_by_location([line.inventory.location.id])
                    if pbl:
                        for (location, product), quantity in pbl.iteritems():
                            product_qty[product] = (quantity)
                    for product_id in product_qty:
                        if product_id == line.product.id:
                            quantity = product_qty[product_id]
                if quantity == line.expected_quantity:
                    pass
                else:
                    line.raise_user_error('Cantidad Esperada del producto:\n%s debe ser %s', (line.product.template.name,str(quantity)))

    @fields.depends('product', '_parent_inventory.date',
    '_parent_inventory.location', 'expected_quantity')
    def on_change_product(self):
        pool = Pool()
        Product = pool.get('product.product')
        Line = pool.get('stock.inventory.line')
        product_qty = {}
        to_create = []
        if self.product:
            if self.inventory.date:
                if self.inventory.location:
                    with Transaction().set_context(stock_date_end=self.inventory.date):
                        pbl = Product.products_by_location([self.inventory.location.id])
                    if pbl:
                        for (location, product), quantity in pbl.iteritems():
                            product_qty[product] = (quantity)
                    for product_id in product_qty:
                        if product_id == self.product.id:
                            quantity = product_qty[product_id]
                else:
                    self.raise_user_error('Ingrese la bodega para el inventario')
            else:
                self.raise_user_error('Ingrese la fecha del inventario')
            change = {}
            change['unit_digits'] = 2
            if self.product:
                change['uom'] = self.product.default_uom.id
                change['uom.rec_name'] = self.product.default_uom.rec_name
                change['unit_digits'] = self.product.default_uom.digits
                change['expected_quantity'] = quantity
            return change
