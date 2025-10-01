import os
import requests
from dotenv import load_dotenv
import json
import time

class DatabricksAPI:
    def __init__(self, token=None, host=None, warehouse_id=None):
        load_dotenv()

        self.token = token or os.getenv("DATABRICKS_TOKEN")
        self.host = host or os.getenv("DATABRICKS_HOST")
        self.warehouse_id = warehouse_id or os.getenv("DATABRICKS_WAREHOUSE_ID")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def execute_sql(self, catalog, schema, statement):
        url = f"{self.host}/api/2.0/sql/statements/"
        payload = {
            "statement": statement,
            "warehouse_id": self.warehouse_id,
            "catalog": catalog,
            "schema": schema
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                response_data = response.json()
                return json.dumps(response_data)
            else:
                return json.dumps({'error': response.status_code, 'message': response.text})
                
        except requests.exceptions.Timeout as e:
            return json.dumps({'error': 'timeout', 'message': str(e)})
            
        except requests.exceptions.ConnectionError as e:
            return json.dumps({'error': 'connection_error', 'message': str(e)})
            
        except Exception as e:
            return json.dumps({'error': 'unexpected_error', 'message': str(e)})