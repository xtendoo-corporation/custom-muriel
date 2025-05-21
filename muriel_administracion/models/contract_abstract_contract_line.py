from odoo import models, fields



class ContractAbstractContractLine(models.AbstractModel):
    _inherit = "contract.abstract.contract.line"

    price_unit = fields.Float(
        string="Unit Price",
        compute="_compute_price_unit",
        inverse="_inverse_price_unit",
        digits='Product Price',
    )
