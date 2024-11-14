import json
import logging
import requests
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from datetime import datetime
from decouple import config

logger = logging.getLogger('user_activity')


class UserActivityLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Process the incoming request and log the IP, location, and engagement time
        when the user first visits the site.
        """
        # Only log for non-logged in users
        if not request.user.is_authenticated:
            # Check if the user has already visited and logged their details in this session
            if not request.session.get('user_logged', False):
                ip = self.get_client_ip(request)
                location = self.get_user_location(ip)
                request.session['user_ip'] = ip
                request.session['user_location'] = location
                request.session['entry_time'] = timezone.now().isoformat()
                request.session['user_logged'] = True
                # Log user details
                logger.info(f"New User - IP: {ip}, Location: {location}")

    def process_response(self, request, response):
        """
        Process the response, calculate total engagement time, and log it.
        """
        if 'entry_time' in request.session:
            entry_time_str = request.session['entry_time']
            try:
                entry_time = datetime.fromisoformat(entry_time_str) 
                time_spent = timezone.now() - entry_time

                time_spent_seconds = time_spent.total_seconds()  # Converts timedelta to total seconds

                # Use json.dumps to handle datetime and timedelta serialization errors
                user_activity_data = {
                    "user_ip": request.session.get('user_ip'),
                    "entry_time": entry_time_str,  # This is now serializable as a string
                    "time_spent_seconds": time_spent_seconds  # This is now serializable
                }

                # Convert the user activity data to a JSON string safely
                user_activity_json = json.dumps(user_activity_data, indent=4, sort_keys=True, default=str)
                # Log the user activity data in JSON format
                logger.info(f"User activity data: {user_activity_json}")
            except Exception as e:
                logger.error(f"Error parsing entry_time or serializing user activity: {e}")
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_user_location(self, ip):
        api_key = config('API_KEY') 
        url = f'https://api.ipstack.com/{ip}?access_key={api_key}'
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("city"):
                return f"{data.get('city')}, {data.get('country_name')}"
            return "Unknown location"
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user location for IP {ip}: {e}")
            logger.error('from the get user location')
            return "Unknown location"
