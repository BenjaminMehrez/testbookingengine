from django.test import TestCase, Client, override_settings
from django.urls import reverse
from datetime import date, timedelta
from pms.models import Booking, Customer, Room, Room_type
from django.contrib.messages import get_messages

# We use this to avoid static file errors during tests
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class EditBookingDatesViewTest(TestCase):
    """
    Test suite for EditBookingDatesView.
    Covers validation logic, availability checks, and price recalculation.
    """
    
    def setUp(self):
        self.client = Client()
        
        # 1. Setup basic data (Room Type, Room, Customer)
        self.rt = Room_type.objects.create(name="Double", price=50.0, max_guests=2)
        self.room = Room.objects.create(room_type=self.rt, name="101", description="Test Room")
        self.customer = Customer.objects.create(name="Ben Test", email="ben@test.com", phone="123456")

        # 2. MAIN BOOKING (The one we will edit)
        # Initial dates: Today until +2 days (2 nights)
        self.booking = Booking.objects.create(
            customer=self.customer,
            room=self.room,
            checkin=date.today(),
            checkout=date.today() + timedelta(days=2),
            guests=2,
            total=100.0, # 2 nights * 50
            state="NEW",
            code="RES-001"
        )

        # Construct the URL based on your view's redirect logic: /booking/{pk}/edit-dates
        # (Ideally this should use reverse(), but we match your hardcoded redirect for now)
        self.url = f"/booking/{self.booking.id}/edit-dates"

    def test_get_edit_page(self):
        """Test 1: Verify the page loads correctly (GET)"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_booking_dates.html")
        self.assertEqual(response.context['booking'], self.booking)

    def test_post_success_update_dates_and_price(self):
        """Test 2: Success - Update dates and recalculate price"""
        # Change to start 5 days from now, stay for 3 nights
        new_checkin = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        new_checkout = (date.today() + timedelta(days=8)).strftime('%Y-%m-%d')

        response = self.client.post(self.url, {
            'checkin': new_checkin,
            'checkout': new_checkout
        })

        # Expect redirect to home ("/") as per your view
        self.assertRedirects(response, "/")
        
        # Verify DB updates
        self.booking.refresh_from_db()
        self.assertEqual(str(self.booking.checkin), new_checkin)
        self.assertEqual(str(self.booking.checkout), new_checkout)
        
        # Verify Price Recalculation: 3 nights * 50 = 150
        self.assertEqual(self.booking.total, 150.0)

        # Verify Success Message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Booking updated successfully.")

    def test_post_error_empty_dates(self):
        """Test 3: Error if dates are empty"""
        response = self.client.post(self.url, {
            'checkin': '',
            'checkout': ''
        })
        
        # Should redirect back to edit page
        self.assertRedirects(response, self.url)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "You must provide both check-in and check-out dates.")

    def test_post_error_invalid_format(self):
        """Test 4: Error if dates are not valid dates (ValueError check)"""
        response = self.client.post(self.url, {
            'checkin': 'not-a-date',
            'checkout': '2025-99-99'
        })
        
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Invalid date format provided.")

    def test_post_error_checkout_before_checkin(self):
        """Test 5: Error if checkout is before checkin"""
        checkin = date.today().strftime('%Y-%m-%d')
        checkout = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d') # Yesterday

        response = self.client.post(self.url, {
            'checkin': checkin,
            'checkout': checkout
        })
        
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Checkout date must be after check-in date.")

    def test_post_error_room_taken(self):
        """Test 6: Error if room is occupied by ANOTHER booking"""
        
        # Create a conflicting booking for next week
        conflict_start = date.today() + timedelta(days=10)
        conflict_end = date.today() + timedelta(days=12)
        
        Booking.objects.create(
            customer=self.customer,
            room=self.room,
            checkin=conflict_start,
            checkout=conflict_end,
            state="NEW",
            total=100,
            code="CONFLICT",
            guests=1
        )

        # Try to move our booking to overlap with the conflict
        response = self.client.post(self.url, {
            'checkin': conflict_start.strftime('%Y-%m-%d'),
            'checkout': conflict_end.strftime('%Y-%m-%d')
        })
        
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("No availability", str(messages[0]))

    def test_post_success_self_overlap(self):
        """Test 7: Edge Case - Extending my own booking (self-overlap) should work"""
        # Current booking ends in +2 days. Extend to +4 days.
        # This technically overlaps with the old dates, but .exclude(id=pk) handles it.
        
        new_checkout = (date.today() + timedelta(days=4)).strftime('%Y-%m-%d')
        
        response = self.client.post(self.url, {
            'checkin': date.today().strftime('%Y-%m-%d'),
            'checkout': new_checkout
        })
        
        self.assertRedirects(response, "/")
        
        self.booking.refresh_from_db()
        self.assertEqual(str(self.booking.checkout), new_checkout)