# Copyright 2020 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _create_return(self):
        # Restrict the quantity of the return moves to what was actually
        # delivered, when the picking type enforces it.
        restrict = self.picking_type_id.restrict_return_qty
        if restrict:
            precision = self.env["decimal.precision"].precision_get(
                "Product Unit of Measure"
            )
            for move in self.move_ids.filtered(lambda m: m.state != "cancel"):
                max_qty = self.env["stock.move"].get_returned_restricted_quantity(move)
                if (
                    float_compare(move.quantity, max_qty, precision_digits=precision)
                    > 0
                ):
                    raise UserError(
                        self.env._(
                            "Return more quantities than delivered is not allowed."
                        )
                    )
        new_picking = super()._create_return()
        if restrict:
            # Clamp the demand of the generated return moves as well.
            for new_move in new_picking.move_ids:
                origin_move = new_move.origin_returned_move_id
                if not origin_move:
                    continue
                max_qty = self.env[
                    "stock.move"
                ].get_returned_restricted_quantity(origin_move)
                if max_qty < new_move.product_uom_qty:
                    new_move.product_uom_qty = max_qty
        return new_picking
