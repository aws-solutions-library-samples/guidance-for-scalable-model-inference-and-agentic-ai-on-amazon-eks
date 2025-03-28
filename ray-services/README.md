# Function Calling Support for VLLM Model Inference

This README explains how to use the function calling capabilities added to the VLLM model inference service.

## Overview

The modified VLLM service now supports function calling, allowing models to invoke functions based on user input. This is implemented through a custom parser that extracts function calls from the model's output and formats them in a structured way.

## How It Works

1. The service accepts function definitions in the request payload as `tools`
2. The function definitions are formatted and included in the prompt
3. The model generates responses that may include function calls in a specific format
4. The service parses these function calls and returns them in a structured format

## Request Format

To use function calling, include a `tools` array in your request:

```json
{
  "prompt": "What's the weather like in Seattle?",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g. San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"],
              "description": "The temperature unit to use"
            }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "stream": false
}
```

## Response Format

The response will include any function calls detected in the model's output:

```json
{
  "text": "I'll check the weather for you.\n<function_call name=\"get_weather\">\n{\n  \"location\": \"Seattle, WA\",\n  \"unit\": \"celsius\"\n}\n</function_call>",
  "function_calls": [
    {
      "name": "get_weather",
      "arguments": {
        "location": "Seattle, WA",
        "unit": "celsius"
      }
    }
  ]
}
```

## Function Call Format

The model will format function calls as:

```
<function_call name="function_name">
{
  "param1": "value1",
  "param2": "value2"
}
</function_call>
```

## Implementation Details

The implementation uses a regex-based parser to extract function calls from the model's output. This approach works with models that don't natively support function calling but can be instructed to follow a specific format.

## Environment Variables

- `ENABLE_FUNCTION_CALLING`: Set to "true" to enable function calling support
