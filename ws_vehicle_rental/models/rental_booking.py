from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RentalBooking(models.Model):
    _name = 'ws.vehicle.rental.booking'
    _description = 'Vehicle Rental Booking'
    _order = 'start_date asc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('ws.vehicle.rental.booking'))
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, tracking=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    start_date = fields.Datetime(string='Start Date', required=True, tracking=True)
    end_date = fields.Datetime(string='End Date', required=True, tracking=True)
    pickup_date = fields.Datetime(string='Pickup Date')
    return_date = fields.Datetime(string='Return Date')
    duration_days = fields.Float(string='Duration (days)', compute='_compute_duration', store=True, digits=(16, 2))
    daily_rate = fields.Monetary(string='Daily Rate', currency_field='currency_id', default=0.0)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', currency_field='currency_id', readonly=True, compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Taxes', currency_field='currency_id', readonly=True, compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Total', currency_field='currency_id', readonly=True, compute='_compute_amounts', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    cancel_reason = fields.Text(string='Cancellation Reason')
    notes = fields.Text(string='Notes')
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('check_dates', "CHECK (start_date < end_date)", 'The end date must be after the start date.'),
    ]

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                delta = rec.end_date - rec.start_date
                rec.duration_days = max(delta.total_seconds() / 86400.0, 0.0)
            else:
                rec.duration_days = 0.0

    @api.depends('duration_days', 'daily_rate')
    def _compute_amounts(self):
        for rec in self:
            untaxed = rec.duration_days * rec.daily_rate
            rec.amount_untaxed = untaxed
            rec.amount_tax = 0.0
            rec.amount_total = untaxed

    @api.constrains('customer_id', 'vehicle_id', 'state')
    def _check_customer_vehicle(self):
        for rec in self:
            if rec.vehicle_id and not rec.vehicle_id.rental_eligible:
                raise ValidationError(_('This vehicle is not eligible for rental.'))

    @api.constrains('start_date', 'end_date')
    def _check_valid_period(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date >= rec.end_date:
                raise ValidationError(_('The rental end date must be after the start date.'))

    @api.model
    def _get_overlap_domain(self, vehicle_id, start_date, end_date, ignore_id=False):
        domain = [
            ('vehicle_id', '=', vehicle_id),
            ('state', 'not in', ['draft', 'cancelled']),
            ('start_date', '<', end_date),
            ('end_date', '>', start_date),
        ]
        if ignore_id:
            domain.append(('id', '!=', ignore_id))
        return domain

    @api.model
    def check_vehicle_availability(self, vehicle_id, start_date, end_date, ignore_booking_id=False):
        if not vehicle_id or not start_date or not end_date:
            return True
        domain = self._get_overlap_domain(vehicle_id, start_date, end_date, ignore_booking_id)
        return not self.search(domain, limit=1)

    def _validate_booking_for_confirmation(self):
        self.ensure_one()
        if not self.customer_id or not self.vehicle_id:
            raise UserError(_('Customer and vehicle are required before confirmation.'))
        if self.state != 'draft':
            raise UserError(_('Only draft bookings can be confirmed.'))
        if not self.check_vehicle_availability(
            self.vehicle_id.id,
            self.start_date,
            self.end_date,
            ignore_booking_id=self.id,
        ):
            raise UserError(_('The selected vehicle is already booked for the requested period.'))

    def action_confirm(self):
        for rec in self:
            rec._validate_booking_for_confirmation()
            rec.write({'state': 'confirmed'})
        return True

    def action_start_rental(self):
        for rec in self:
            if rec.state not in ['confirmed']:
                raise UserError(_('Only confirmed bookings can be started.'))
            rec.write({'state': 'in_progress', 'pickup_date': fields.Datetime.now()})
        return True

    def action_return_vehicle(self):
        for rec in self:
            if rec.state not in ['in_progress']:
                raise UserError(_('Only active rentals can be returned.'))
            rec.write({'state': 'completed', 'return_date': fields.Datetime.now()})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state in ['cancelled']:
                return True
            if rec.state in ['completed']:
                raise UserError(_('Completed bookings cannot be cancelled.'))
            rec.write({'state': 'cancelled', 'cancel_reason': rec.cancel_reason or _('Cancelled by user')})
        return True

    def action_create_invoice(self):
        for rec in self:
            if rec.invoice_id:
                continue
            if rec.state not in ['confirmed', 'in_progress', 'completed']:
                raise UserError(_('Only non-draft bookings can be invoiced.'))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': rec.customer_id.id,
                'company_id': rec.company_id.id,
                'invoice_date': fields.Date.context_today(self),
                'currency_id': rec.currency_id.id,
                'invoice_origin': rec.name,
                'invoice_line_ids': [(0, 0, {
                    'name': _('Vehicle rental: %s', rec.vehicle_id.name),
                    'quantity': 1,
                    'price_unit': rec.amount_untaxed,
                    'account_id': self.env['account.account'].search([
                        ('account_type', '=', 'income'),
                        ('company_id', '=', rec.company_id.id),
                    ], limit=1).id,
                })],
            })
            rec.write({'invoice_id': invoice.id})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.daily_rate:
                config = self.env['ws.vehicle.rental.config'].search([
                    ('company_id', '=', rec.company_id.id),
                ], limit=1)
                rec.daily_rate = config.default_daily_rate if config else 0.0
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self:
            if rec.state in ['completed', 'cancelled']:
                rec.active = False
        return result
