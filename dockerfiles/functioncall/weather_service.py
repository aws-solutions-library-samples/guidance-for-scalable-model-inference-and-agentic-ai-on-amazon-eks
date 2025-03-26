# weather_service.py

import requests
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

@dataclass
class WeatherData:
    temperature: float
    description: str
    humidity: float
    wind_speed: float

@dataclass
class ForecastData:
    date: str
    max_temp: float
    min_temp: float
    precipitation: float
    wind_speed: float

class WeatherService:
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
    
    def _get_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a given city name
        """
        try:
            params = {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                print(f"City '{city}' not found")
                return None
            
            location = data["results"][0]
            return location["latitude"], location["longitude"]
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting coordinates: {e}")
            return None

    def get_current_weather(self, city: str) -> Optional[WeatherData]:
        """
        Get current weather for a given city
        """
        coordinates = self._get_coordinates(city)
        if not coordinates:
            return None
        
        lat, lon = coordinates
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "hourly": ["temperature_2m", "relative_humidity_2m", "windspeed_10m"],
                "timezone": "auto"
            }
            
            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current_hour = datetime.now().hour
            
            weather = WeatherData(
                temperature=data["hourly"]["temperature_2m"][current_hour],
                description=self._get_weather_description(
                    data["hourly"]["temperature_2m"][current_hour]
                ),
                humidity=data["hourly"]["relative_humidity_2m"][current_hour],
                wind_speed=data["hourly"]["windspeed_10m"][current_hour]
            )
            
            return weather
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching current weather: {e}")
            return None

    def get_forecast(self, city: str, days: int = 5) -> Optional[List[ForecastData]]:
        """
        Get weather forecast for a given city
        """
        if days > 16:
            days = 16
            print("Maximum forecast days is 16, adjusting to 16 days")
            
        coordinates = self._get_coordinates(city)
        if not coordinates:
            return None
            
        lat, lon = coordinates
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": ["temperature_2m_max", 
                         "temperature_2m_min",
                         "precipitation_sum",
                         "windspeed_10m_max"],
                "timezone": "auto",
                "forecast_days": days
            }
            
            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            daily_data = data['daily']
            forecast_list = []
            
            for i in range(days):
                forecast = ForecastData(
                    date=datetime.fromisoformat(daily_data['time'][i]).strftime('%Y-%m-%d'),
                    max_temp=daily_data['temperature_2m_max'][i],
                    min_temp=daily_data['temperature_2m_min'][i],
                    precipitation=daily_data['precipitation_sum'][i],
                    wind_speed=daily_data['windspeed_10m_max'][i]
                )
                forecast_list.append(forecast)
                
            return forecast_list
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching forecast: {e}")
            return None

    def _get_weather_description(self, temperature: float) -> str:
        """Simple helper to generate weather description based on temperature"""
        if temperature > 30:
            return "Hot"
        elif temperature > 20:
            return "Warm"
        elif temperature > 10:
            return "Mild"
        else:
            return "Cold"
