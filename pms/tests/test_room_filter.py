from django.test import TestCase, Client, override_settings
from django.urls import reverse
from pms.models import Room, Room_type

# We override the static storage setting to avoid errors with missing manifest files during testing
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class RoomFilterTest(TestCase):
    """
    Test suite for the Room Filter functionality (Task 1).
    Verifies that the room list can be filtered by name via GET parameters.
    """
    def setUp(self):
        self.client = Client()
        
        # 1. Setup required dependencies (Room Type)
        self.rt = Room_type.objects.create(name="Standard", price=50.0, max_guests=2)
        
        # 2. Create dummy rooms with distinct names for filtering tests
        Room.objects.create(name="Room 101", room_type=self.rt, description="Test Desc")
        Room.objects.create(name="Room 102", room_type=self.rt, description="Test Desc")
        Room.objects.create(name="Suite Alpha", room_type=self.rt, description="Test Desc")

        # Define the URL for the room list
        self.url = reverse('rooms') 

    def test_filter_rooms_by_exact_name(self):
        """
        Test that searching for an exact name returns only the matching room.
        """
        response = self.client.get(self.url, {'search': 'Room 101'})
        
        self.assertEqual(response.status_code, 200)
        
        # Extract the list of rooms from the context
        # Since the view uses .values(), 'rooms' is a list of dictionaries
        rooms_list = list(response.context['rooms'])
        
        # Verify 'Room 101' is present
        self.assertTrue(any(r['name'] == 'Room 101' for r in rooms_list))
        
        # Verify 'Suite Alpha' is NOT present
        self.assertFalse(any(r['name'] == 'Suite Alpha' for r in rooms_list))

    def test_filter_case_insensitive(self):
        """
        Test that the search query is case-insensitive (e.g., 'suite' finds 'Suite').
        """
        # Search using lowercase
        response = self.client.get(self.url, {'search': 'suite'})
        
        self.assertEqual(response.status_code, 200)
        rooms_list = list(response.context['rooms'])
        
        # Should find 'Suite Alpha'
        self.assertTrue(any(r['name'] == 'Suite Alpha' for r in rooms_list))

    def test_filter_partial_match(self):
        """
        Test that partial strings return all matching rooms (icontains behavior).
        """
        # Search for '10', which should match 'Room 101' and 'Room 102'
        response = self.client.get(self.url, {'search': '10'})
        
        self.assertEqual(response.status_code, 200)
        rooms_list = list(response.context['rooms'])
        
        self.assertEqual(len(rooms_list), 2)
        self.assertTrue(any(r['name'] == 'Room 101' for r in rooms_list))
        self.assertTrue(any(r['name'] == 'Room 102' for r in rooms_list))

    def test_empty_search_returns_all(self):
        """
        Test that providing an empty search query returns the full list of rooms.
        """
        response = self.client.get(self.url, {'search': ''})
        
        self.assertEqual(response.status_code, 200)