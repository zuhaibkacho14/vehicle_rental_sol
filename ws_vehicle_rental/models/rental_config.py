from odoo import api, fields, models


class RentalConfig(models.Model):
    _name = 'ws.vehicle.rental.config'
    _description = 'Vehicle Rental Configuration'
    _order = 'name asc'

    name = fields.Char(required=True, default='Default Configuration')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    default_daily_rate = fields.Monetary(currency_field='currency_id', default=0.0)
    default_weekly_rate = fields.Monetary(currency_field='currency_id', default=0.0)
    default_monthly_rate = fields.Monetary(currency_field='currency_id', default=0.0)
    allow_public_booking = fields.Boolean(default=False)

    _sql_constraints = [
        ('unique_company_config', 'UNIQUE(company_id)', 'Only one rental configuration is allowed per company.'),
    ]

    @api.model
    def get_default_config(self):
        config = self.search([('company_id', '=', self.env.company.id)], limit=1)
        if not config:
            config = self.create({'name': 'Default', 'company_id': self.env.company.id})
        return config

