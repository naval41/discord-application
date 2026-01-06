import boto3
import json
import os

class BedrockService:
    def __init__(self):
        # Load configuration
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            with open(config_path, "r") as f:
                config = json.load(f)
                self.model_id = config.get("bedrock", {}).get("model_id", "anthropic.claude-3-5-sonnet-20240620-v1:0")
                self.region = config.get("bedrock", {}).get("region", "us-east-1")
                self.access_key = config.get("bedrock", {}).get("aws_access_key_id")
                self.secret_key = config.get("bedrock", {}).get("aws_secret_access_key")
        except FileNotFoundError:
            print("Warning: config.json not found in utils directory. Relying on default AWS credentials.")
            self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
            self.region = "us-east-1"
            self.access_key = None
            self.secret_key = None

        # Initialize boto3 client
        client_kwargs = {"service_name": "bedrock-runtime", "region_name": self.region}
        if self.access_key and self.secret_key:
            client_kwargs["aws_access_key_id"] = self.access_key
            client_kwargs["aws_secret_access_key"] = self.secret_key
            
        self.client = boto3.client(**client_kwargs)

    def converse(self, messages, tool_config=None, inference_config=None):
        """
        Generic wrapper for Bedrock converse API.
        
        Args:
            messages (list): List of message objects [{"role": "user", "content": [...]}]
            tool_config (dict, optional): Tool configuration with 'tools' and 'toolChoice'.
            inference_config (dict, optional): Inference parameters like maxTokens, temperature.
        
        Returns:
            dict: The full response from Bedrock.
        """
        if inference_config is None:
            inference_config = {"maxTokens": 4096, "temperature": 0}

        kwargs = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": inference_config
        }
        
        if tool_config:
            kwargs["toolConfig"] = tool_config

        try:
            response = self.client.converse(**kwargs)
            return response
        except Exception as e:
            print(f"Bedrock Service Error: {e}")
            raise e

    def extract_tool_result(self, response):
        """
        Helper to extract tool input from a Bedrock response.
        """
        if not response or 'output' not in response:
            return None
            
        output_msg = response['output']['message']
        content_blocks = output_msg['content']
        tool_use = next((b['toolUse'] for b in content_blocks if 'toolUse' in b), None)
        
        if tool_use:
            return tool_use['input']
        return None
