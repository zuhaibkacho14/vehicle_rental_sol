from odoo import fields, models


class TestVehicleRental(models.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.company = self.env.company
        self.vehicle = self.env['fleet.vehicle'].create({
            'name': 'Test Rental Vehicle',
            'license_plate': 'ABC-123',
            'company_id': self.company.id,
            'rental_eligible': True,
        })

    def test_booking_overlap_is_blocked(self):
        booking1 = self.env['ws.vehicle.rental.booking'].create({
            'customer_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'company_id': self.company.id,
            'start_date': '2025-01-10 09:00:00',
            'end_date': '2025-01-12 09:00:00',
            'daily_rate': 80,
        })
        booking1.action_confirm()

        with self.assertRaises(Exception):
            self.env['ws.vehicle.rental.booking'].create({
                'customer_id': self.partner.id,
                'vehicle_id': self.vehicle.id,
                'company_id': self.company.id,
                'start_date': '2025-01-11 08:00:00',
                'end_date': '2025-01-13 08:00:00',
                'daily_rate': 80,
            })

    def test_booking_amount_calculation(self):
        booking = self.env['ws.vehicle.rental.booking'].create({
            'customer_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'company_id': self.company.id,
            'start_date': '2025-01-10 09:00:00',
            'end_date': '2025-01-12 09:00:00',
            'daily_rate': 100,
        })
        self.assertEqual(round(booking.duration_days, 2), 2.0)
        self.assertEqual(booking.amount_untaxed, 200.0)

    def test_booking_state_transition(self):
        booking = self.env['ws.vehicle.rental.booking'].create({
            'customer_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'company_id': self.company.id,
            'start_date': '2025-01-10 09:00:00',
            'end_date': '2025-01-12 09:00:00',
            'daily_rate': 80,
        })
        booking.action_confirm()
        self.assertEqual(booking.state, 'confirmed')
        booking.action_start_rental()
        self.assertEqual(booking.state, 'in_progress')
        booking.action_return_vehicle()
        self.assertEqual(booking.state, 'completed')
