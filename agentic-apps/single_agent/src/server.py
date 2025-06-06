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
LLM_SERVER_URL = os.environ.get("LLM_SERVER_URL", "http://:8080/v1/chat/completions")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-1234")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3")
CONNECT_TIMEOUT = int(os.environ.get("CONNECT_TIMEOUT", 10))
READ_TIMEOUT = int(os.environ.get("READ_TIMEOUT", 300))
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", 3))

# Pydantic models
class WeatherRequest(BaseModel):
    city: str

class ForecastRequest(BaseModel):
    city: str
    days: Optional[int] = 5

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict] = None

class CustomLLMClient:
    def __init__(self, base_url: str, api_key: str, model: str = "llama3"):
        self.base_url = base_url
        self.model = model
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
                                   function_call: str = "auto", model: str = None) -> Dict:
        try:
            start_time = time.time()
            payload = {
                "model": model or self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # Only add functions if they are provided
            if functions:
                payload["functions"] = functions
                payload["function_call"] = function_call

            logger.info(f"Sending payload to LLM server: {json.dumps(payload, default=str)}")

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
            
            # Log raw response text for debugging
            logger.info(f"Raw response text: {response.text}")
            
            # Parse JSON response safely
            try:
                response_json = response.json()
                return response_json
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid JSON response from LLM server: {str(e)}"
                )

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
llm_client = CustomLLMClient(LLM_SERVER_URL, LLM_API_KEY, LLM_MODEL)

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
        # Convert Pydantic models to dictionaries
        messages = [message.dict(exclude_none=True) for message in request.messages]
        
        # Use model from request if provided, otherwise use default
        model = request.model if request.model else LLM_MODEL
        
        # Log the request being sent to the LLM server
        logger.info(f"Sending request to LLM server: {LLM_SERVER_URL}")
        logger.info(f"Using model: {model}")
        logger.info(f"Request messages: {json.dumps(messages)}")
        logger.info(f"Functions: {json.dumps(weather_functions)}")
        
        response = await llm_client.create_chat_completion(
            messages=messages,
            functions=weather_functions,
            function_call="auto",
            model=model
        )
        
        # Log the raw response for debugging
        logger.info(f"Raw LLM response: {json.dumps(response, default=str)}")
        
        # Check if response has the expected structure
        if not response:
            raise ValueError("LLM server returned None response")
        if "choices" not in response:
            raise ValueError(f"LLM response missing 'choices' field: {response}")
        if not response["choices"] or len(response["choices"]) == 0:
            raise ValueError(f"LLM response has empty 'choices' array: {response}")
        if "message" not in response["choices"][0]:
            raise ValueError(f"LLM response missing 'message' in first choice: {response['choices'][0]}")
        
        response_message = response["choices"][0]["message"]
        
        if "function_call" in response_message:
            try:
                # Function call detected, execute it and append result
                function_name = response_message["function_call"]["name"]
                
                # Safely parse function arguments with better error handling
                try:
                    function_args_str = response_message["function_call"]["arguments"]
                    function_args = json.loads(function_args_str)
                except (KeyError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to parse function arguments: {e}")
                    logger.error(f"Raw arguments: {response_message.get('function_call', {}).get('arguments', 'N/A')}")
                    raise ValueError(f"Invalid function arguments: {str(e)}")
                
                logger.info(f"Function call detected: {function_name} with args: {function_args}")
                
                function_response = function_map(function_name, function_args)
                
                if function_response is None:
                    logger.warning(f"Function {function_name} returned None response")
                    function_response = {"error": f"No data found for {function_args.get('city', 'unknown location')}"}
                
                # Add function response to messages
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
                
                logger.info(f"Sending second request to LLM with function response")
                second_response = await llm_client.create_chat_completion(
                    messages=messages,
                    model=model
                )
                
                # Check second response structure with detailed error handling
                if not second_response:
                    raise ValueError("Second LLM request returned None response")
                if "choices" not in second_response:
                    raise ValueError(f"Second LLM response missing 'choices' field: {second_response}")
                if not second_response["choices"] or len(second_response["choices"]) == 0:
                    raise ValueError(f"Second LLM response has empty 'choices' array: {second_response}")
                if "message" not in second_response["choices"][0]:
                    raise ValueError(f"Second LLM response missing 'message' in first choice: {second_response['choices'][0]}")
                
                return ChatResponse(
                    response=second_response["choices"][0]["message"]["content"],
                    data=function_response
                )
            except Exception as e:
                logger.error(f"Error processing function call: {str(e)}", exc_info=True)
                # Fallback to original response if function call processing fails
                return ChatResponse(
                    response=f"I tried to get weather information, but encountered an error: {str(e)}. Please try again with a specific city name.",
                    data={"error": str(e)}
                )
        
        return ChatResponse(response=response_message["content"])
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
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
        # Check if response has expected structure
        if not response or "choices" not in response or not response["choices"]:
            return {
                "status": "unhealthy", 
                "reason": f"LLM server returned unexpected response format: {json.dumps(response, default=str)}"
            }
        return {"status": "healthy", "latency": response.get("latency", None)}
    except Exception as e:
        logger.error(f"LLM health check failed: {str(e)}", exc_info=True)
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
