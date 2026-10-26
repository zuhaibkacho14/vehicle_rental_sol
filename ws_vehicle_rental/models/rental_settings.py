from odoo import fields, models


class RentalSettings(models.TransientModel):
    _name = 'ws.vehicle.rental.settings'
    _inherit = 'res.config.settings'

    default_daily_rate = fields.Monetary(
        string='Default Daily Rate',
        currency_field='currency_id',
        config_parameter='ws_vehicle_rental.default_daily_rate',
    )
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

