from django.test import TestCase, Client, override_settings
from django.urls import reverse
from pms.models import Room, Room_type, Booking, Customer
from datetime import date, timedelta

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class DashboardOccupancyTest(TestCase):
    """
    Test suite for Task 2: Occupancy Rate Widget on Dashboard.
    Formula: (Confirmed Bookings / Total Rooms) * 100
    """

    def setUp(self):
        self.client = Client()
        # 1. Create Room Type
        self.rt = Room_type.objects.create(name="Standard", price=100, max_guests=2)
        
        # 2. Create 4 Rooms
        # We create 4 rooms to make math easy (1 booking = 25%, 2 bookings = 50%)
        for i in range(4):
            Room.objects.create(name=f"Room {i}", room_type=self.rt, description="Desc")

        # 3. Create a Customer
        self.customer = Customer.objects.create(name="Test User", email="test@test.com", phone="123")

        self.url = reverse('dashboard') 

    def test_occupancy_rate_zero(self):
        """Test that occupancy is 0% when there are no bookings."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('dashboard', response.context)
        self.assertEqual(response.context['dashboard']['occupancy_rate'], 0)

    def test_occupancy_rate_calculation(self):
        """Test that occupancy is calculated correctly (e.g. 2 bookings / 4 rooms = 50%)."""
        
        # Create 2 Confirmed Bookings
        Booking.objects.create(
            room=Room.objects.first(),
            customer=self.customer,
            checkin=date.today(),
            checkout=date.today() + timedelta(days=1), # 1 night stay
            guests=1, 
            state="NEW", 
            code="B1",
            total=100
        )
        
        Booking.objects.create(
            room=Room.objects.last(),
            customer=self.customer,
            checkin=date.today(),
            checkout=date.today() + timedelta(days=1),
            guests=1,
            state="NEW",
            code="B2",
            total=100
        )

        response = self.client.get(self.url)
        
        self.assertEqual(response.context['dashboard']['occupancy_rate'], 50)

    def test_ignore_cancelled_bookings(self):
        """Test that CANCELLED bookings do not count towards occupancy."""
        
        # Create 1 Cancelled booking
        Booking.objects.create(
            room=Room.objects.first(),
            customer=self.customer,
            checkin=date.today(),
            checkout=date.today() + timedelta(days=1),
            guests=1,
            state="DEL",
            code="B_CANCEL",
            total=0
        )

        response = self.client.get(self.url)
        
        # Should be 0% because the only booking is cancelled
        self.assertEqual(response.context['dashboard']['occupancy_rate'], 0)