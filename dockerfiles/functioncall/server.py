from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os
import asyncio
import logging
import time
from weather_service import WeatherService, WeatherData, ForecastData

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
LLM_SERVER_URL = os.environ.get("LLM_SERVER_URL", "http://172.31.78.247:8080/v1/chat/completions")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-1234")
CONNECT_TIMEOUT = int(os.environ.get("CONNECT_TIMEOUT", 10))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", 300))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", 3))

# Pydantic models
class WeatherRequest(BaseModel):
    city: str

class ForecastRequest(BaseModel):
    city: str
    days: Optional[int] = 5

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict] = None

class CustomLLMClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=LLM_MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504],
        )
        
        # Create session with retry strategy
        self.session = requests.Session()
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=100
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    async def create_chat_completion(self, messages: List[Dict], functions: List[Dict] = None, 
                                   function_call: str = "auto") -> Dict:
        try:
            start_time = time.time()
            payload = {
                "messages": messages,
                "functions": functions,
                "function_call": function_call,
                "temperature": 0.7,
                "max_tokens": 1000
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                )
            )
            
            response.raise_for_status()
            duration = time.time() - start_time
            logger.info(f"LLM request completed in {duration:.2f} seconds")
            return response.json()

        except requests.exceptions.ConnectTimeout:
            logger.error(f"Connection timeout after {CONNECT_TIMEOUT} seconds")
            raise HTTPException(
                status_code=504,
                detail=f"Failed to connect to LLM server within {CONNECT_TIMEOUT} seconds"
            )
        except requests.exceptions.ReadTimeout:
            logger.error(f"Read timeout after {READ_TIMEOUT} seconds")
            raise HTTPException(
                status_code=504,
                detail=f"LLM server response timeout after {READ_TIMEOUT} seconds"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"LLM Server Error: {str(e)}"
            )

# Initialize services
weather_service = WeatherService()
llm_client = CustomLLMClient(LLM_SERVER_URL, LLM_API_KEY)

# Function definitions for LLM
weather_functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather for a specific city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to get weather for"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_weather_forecast",
        "description": "Get the weather forecast for a specific city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to get forecast for"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to forecast (max 16)",
                    "minimum": 1,
                    "maximum": 16
                }
            },
            "required": ["city"]
        }
    }
]

# Function mapping
def function_map(name: str, args: Dict[str, Any]) -> Any:
    if name == "get_current_weather":
        current_weather = weather_service.get_current_weather(args["city"])
        if current_weather:
            return {
                "temperature": current_weather.temperature,
                "description": current_weather.description,
                "humidity": current_weather.humidity,
                "wind_speed": current_weather.wind_speed
            }
        return None

    elif name == "get_weather_forecast":
        days = args.get("days", 5)
        forecast = weather_service.get_forecast(args["city"], days)
        if forecast:
            return [{
                "date": f.date,
                "max_temp": f.max_temp,
                "min_temp": f.min_temp,
                "precipitation": f.precipitation,
                "wind_speed": f.wind_speed
            } for f in forecast]
        return None

    return None

# API endpoints
@app.post("/weather/current")
async def current_weather(request: WeatherRequest):
    result = weather_service.get_current_weather(request.city)
    if not result:
        raise HTTPException(status_code=404, detail="Weather data not found")
    return result

@app.post("/weather/forecast")
async def weather_forecast(request: ForecastRequest):
    result = weather_service.get_forecast(request.city, request.days)
    if not result:
        raise HTTPException(status_code=404, detail="Forecast data not found")
    return result

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful weather assistant. Use the provided functions to get weather information."
            },
            {
                "role": "user",
                "content": request.message
            }
        ]
        
        response = await llm_client.create_chat_completion(
            messages=messages,
            functions=weather_functions,
            function_call="auto"
        )
        
        response_message = response["choices"][0]["message"]
        
        if "function_call" in response_message:
            function_name = response_message["function_call"]["name"]
            function_args = json.loads(response_message["function_call"]["arguments"])
            
            function_response = function_map(function_name, function_args)
            
            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(function_response)
            })
            
            second_response = await llm_client.create_chat_completion(
                messages=messages
            )
            
            return ChatResponse(
                response=second_response["choices"][0]["message"]["content"],
                data=function_response
            )
        
        return ChatResponse(response=response_message["content"])
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/llm")
async def llm_health_check():
    try:
        response = await llm_client.create_chat_completion(
            messages=[{"role": "user", "content": "test"}]
        )
        return {"status": "healthy", "latency": response.get("latency", None)}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM server unhealthy: {str(e)}"
        )

# Logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"Path: {request.url.path} Duration: {duration:.2f}s Status: {response.status_code}")
    return response

# Startup message
print(f"Server started with Connect Timeout: {CONNECT_TIMEOUT}s, Read Timeout: {READ_TIMEOUT}s")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
