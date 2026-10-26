from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    rental_eligible = fields.Boolean(string='Eligible for Rental', default=True)
    rental_daily_rate = fields.Monetary(string='Rental Daily Rate', currency_field='currency_id')
    rental_notes = fields.Text(string='Rental Notes')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True, store=True)

