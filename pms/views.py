from django.db.models import F, Q, Count, Sum
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction, InterfaceError
from django.contrib import messages
from django.core.exceptions import ValidationError


from .form_dates import Ymd
from .forms import *
from .models import Room
from .reservation_code import generate


class BookingSearchView(View):
    # renders search results for bookingings
    def get(self, request):
        query = request.GET.dict()
        if (not "filter" in query):
            return redirect("/")
        bookings = (Booking.objects
                    .filter(Q(code__icontains=query['filter']) | Q(customer__name__icontains=query['filter']))
                    .order_by("-created"))
        room_search_form = RoomSearchForm()
        context = {
            'bookings': bookings,
            'form': room_search_form,
            'filter': True
        }
        return render(request, "home.html", context)


class RoomSearchView(View):
    # renders the search form
    def get(self, request):
        room_search_form = RoomSearchForm()
        context = {
            'form': room_search_form
        }

        return render(request, "booking_search_form.html", context)

    # renders the search results of available rooms by date and guests
    def post(self, request):
        query = request.POST.dict()
        # calculate number of days in the hotel
        checkin = Ymd.Ymd(query['checkin'])
        checkout = Ymd.Ymd(query['checkout'])
        total_days = checkout - checkin
        # get available rooms and total according to dates and guests
        filters = {
            'room_type__max_guests__gte': query['guests']
        }
        exclude = {
            'booking__checkin__lte': query['checkout'],
            'booking__checkout__gte': query['checkin'],
            'booking__state__exact': "NEW"
        }
        rooms = (Room.objects
                 .filter(**filters)
                 .exclude(**exclude)
                 .annotate(total=total_days * F('room_type__price'))
                 .order_by("room_type__max_guests", "name")
                 )
        total_rooms = (Room.objects
                       .filter(**filters)
                       .values("room_type__name", "room_type")
                       .exclude(**exclude)
                       .annotate(total=Count('room_type'))
                       .order_by("room_type__max_guests"))
        # prepare context data for template
        data = {
            'total_days': total_days
        }
        # pass the actual url query to the template
        url_query = request.POST.urlencode()
        context = {
            "rooms": rooms,
            "total_rooms": total_rooms,
            "query": query,
            "url_query": url_query,
            "data": data
        }
        return render(request, "search.html", context)


class HomeView(View):
    # renders home page with all the bookingings order by date of creation
    def get(self, request):
        bookings = Booking.objects.all().order_by("-created")
        context = {
            'bookings': bookings
        }
        return render(request, "home.html", context)


class BookingView(View):
    @method_decorator(ensure_csrf_cookie)
    def post(self, request, pk):
        # check if customer form is ok
        customer_form = CustomerForm(request.POST, prefix="customer")

        try:
            room = Room.objects.get(id=pk)
        except Room.DoesNotExist: 
            return redirect("/")

        if customer_form.is_valid():

            try:
                with transaction.atomic():
                    # save customer data
                    customer = customer_form.save()

                    # add the customer id to the booking form
                    temp_POST = request.POST.copy()
                    temp_POST.update({
                        'booking-customer': customer.id,
                        'booking-room': pk,
                        'booking-code': generate.get()})

                    # if ok, save booking data
                    booking_form = BookingForm(temp_POST, prefix="booking")

                    if booking_form.is_valid():
                        # Verification of the booking is correct
                        # Get the room info with saved data
                        checkin_date = booking_form.cleaned_data['checkin']
                        checkout_date = booking_form.cleaned_data['checkout']

                        # Looking for if existing bookings (overlap)
                        is_taken = Booking.objects.select_for_update().filter(
                            room_id=pk,
                            state="NEW",
                            checkin__lt=checkout_date,
                            checkout__gt=checkin_date
                        ).exists()

                        if is_taken:
                            # If it is taken, return an error and the atomic transaction is rolled back
                            raise ValidationError(
                                "¡Lo sentimos! La habitación acaba de ser reservada por otro usuario.")

                        # If it is not taken, save the booking
                        booking_form.save()

                        messages.success(request, "¡Reserva creada con éxito!")
                        return redirect("/")
                        # Return to home page
                    else:
                        # Show error message
                        messages.error(request, "Error en los datos de la reserva.")
                    
            except ValidationError as e:
                # Show error message
                messages.error(request, f"Error: {e.message if hasattr(e, 'message') else e}")
                # Return to home page
                return redirect('/')
        else:
            # Show error message
            messages.error(request, "Por favor corrige los errores señalados.")
            
        booking_form_visual = BookingFormExcluded(request.POST, prefix="booking")

        return render(request, "booking.html", {
            "customer_form": customer_form, # Este trae los errores (rojo)
            "booking_form": booking_form_visual, 
            "room": room,
            "url_query": request.GET.urlencode()
        })

    def get(self, request, pk):
        # renders the form for booking confirmation.
        # It returns 2 forms, the one with the booking info is hidden
        # The second form is for the customer information

        query = request.GET.dict()
        room = Room.objects.get(id=pk)
        checkin = Ymd.Ymd(query['checkin'])
        checkout = Ymd.Ymd(query['checkout'])
        total_days = checkout - checkin
        total = total_days * room.room_type.price  # total amount to be paid
        query['total'] = total
        url_query = request.GET.urlencode()
        booking_form = BookingFormExcluded(prefix="booking", initial=query)
        customer_form = CustomerForm(prefix="customer")
        context = {
            "url_query": url_query,
            "room": room,
            "booking_form": booking_form,
            "customer_form": customer_form
        }
        return render(request, "booking.html", context)


class DeleteBookingView(View):
    # renders the booking deletion form
    def get(self, request, pk):
        booking = Booking.objects.get(id=pk)
        context = {
            'booking': booking
        }
        return render(request, "delete_booking.html", context)

    # deletes the booking
    def post(self, request, pk):
        Booking.objects.filter(id=pk).update(state="DEL")
        return redirect("/")


class EditBookingView(View):
    # renders the booking edition form
    def get(self, request, pk):
        booking = Booking.objects.get(id=pk)
        booking_form = BookingForm(prefix="booking", instance=booking)
        customer_form = CustomerForm(
            prefix="customer", instance=booking.customer)
        context = {
            'booking_form': booking_form,
            'customer_form': customer_form,
            'booking': booking

        }
        return render(request, "edit_booking.html", context)

    # updates the customer form
    @method_decorator(ensure_csrf_cookie)
    def post(self, request, pk):
        booking = Booking.objects.get(id=pk)

        customer_form = CustomerForm(request.POST, prefix="customer", instance=booking.customer)
        if customer_form.is_valid():
            customer_form.save()
            return redirect("/")
        else:
            messages.error(request, "No se pudo actualizar, Por favor corrige los errores señalados.")

            booking_form = BookingForm(prefix='booking', instance=booking)
            context = {
                'booking_form': booking_form,
                'customer_form': customer_form,
                'booking': booking
            }
            return render(request, 'edit_booking.html', context)

class DashboardView(View):
    def get(self, request):
        from datetime import date, time, datetime

        # Get date of url parameter, if is not exists, get today
        date_param = request.GET.get('date')
        if date_param:
            try:
                # Try to parse the date
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                # If put invalid date, return today
                target_date = date.today()
        else:
            target_date = date.today()

        # get bookings created today
        today_min = datetime.combine(target_date, time.min)
        today_max = datetime.combine(target_date, time.max)
        today_range = (today_min, today_max)

        new_bookings = (Booking.objects
                        .filter(created__range=today_range)
                        .values("id")
                        ).count()

        # get incoming guests
        incoming = (Booking.objects
                    .filter(checkin=target_date)
                    .exclude(state="DEL")
                    .values("id")
                    ).count()

        # get outcoming guests
        outcoming = (Booking.objects
                     .filter(checkout=target_date)
                     .exclude(state="DEL")
                     .values("id")
                     ).count()

        # get outcoming guests
        invoiced = (Booking.objects
                    .filter(created__range=today_range)
                    .exclude(state="DEL")
                    .aggregate(Sum('total'))
                    )

        # preparing context data
        dashboard = {
            'new_bookings': new_bookings,
            'incoming_guests': incoming,
            'outcoming_guests': outcoming,
            'invoiced': invoiced,
            'current_date': target_date # Get date
        }

        context = {
            'dashboard': dashboard
        }
        return render(request, "dashboard.html", context)


class RoomDetailsView(View):
    def get(self, request, pk):
        # renders room details
        room = Room.objects.get(id=pk)
        bookings = room.booking_set.all()
        context = {
            'room': room,
            'bookings': bookings}
        print(context)
        return render(request, "room_detail.html", context)


class RoomsView(View):
    def get(self, request):
        # renders a list of rooms
        rooms = Room.objects.all().values("name", "room_type__name", "id")
        context = {
            'rooms': rooms
        }
        return render(request, "rooms.html", context)
