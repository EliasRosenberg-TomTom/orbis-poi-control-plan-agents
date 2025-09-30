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
        print(f"🔍 [DATABRICKS DEBUG] Starting SQL execution request...")
        print(f"🔍 [DATABRICKS DEBUG] Catalog: {catalog}, Schema: {schema}")
        print(f"🔍 [DATABRICKS DEBUG] Statement length: {len(statement)} characters")
        print(f"🔍 [DATABRICKS DEBUG] Statement preview: {statement[:200]}{'...' if len(statement) > 200 else ''}")
        
        url = f"{self.host}/api/2.0/sql/statements/"
        payload = {
            "statement": statement,
            "warehouse_id": self.warehouse_id,
            "catalog": catalog,
            "schema": schema
        }
        
        print(f"🔍 [DATABRICKS DEBUG] Request URL: {url}")
        print(f"🔍 [DATABRICKS DEBUG] Warehouse ID: {self.warehouse_id}")
        print(f"🔍 [DATABRICKS DEBUG] Payload size: {len(json.dumps(payload))} bytes")
        
        start_time = time.time()
        print(f"🔍 [DATABRICKS DEBUG] Making HTTP POST request at {time.strftime('%H:%M:%S')}...")
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            elapsed_time = time.time() - start_time
            
            print(f"🔍 [DATABRICKS DEBUG] HTTP request completed in {elapsed_time:.2f} seconds")
            print(f"🔍 [DATABRICKS DEBUG] Response status: {response.status_code}")
            print(f"🔍 [DATABRICKS DEBUG] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"🔍 [DATABRICKS DEBUG] Response data keys: {list(response_data.keys())}")
                print(f"🔍 [DATABRICKS DEBUG] Response size: {len(json.dumps(response_data))} bytes")
                print(f"✅ [DATABRICKS DEBUG] SQL execution successful!")
                return json.dumps(response_data)
            else:
                print(f"❌ [DATABRICKS DEBUG] SQL execution failed!")
                print(f"🔍 [DATABRICKS DEBUG] Error response: {response.text}")
                return json.dumps({'error': response.status_code, 'message': response.text})
                
        except requests.exceptions.Timeout as e:
            elapsed_time = time.time() - start_time
            error_msg = f"⏰ [DATABRICKS DEBUG] Request timed out after {elapsed_time:.2f} seconds: {e}"
            print(error_msg)
            return json.dumps({'error': 'timeout', 'message': error_msg})
            
        except requests.exceptions.ConnectionError as e:
            elapsed_time = time.time() - start_time
            error_msg = f"🔌 [DATABRICKS DEBUG] Connection error after {elapsed_time:.2f} seconds: {e}"
            print(error_msg)
            return json.dumps({'error': 'connection_error', 'message': error_msg})
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"💥 [DATABRICKS DEBUG] Unexpected error after {elapsed_time:.2f} seconds: {e}"
            print(error_msg)
            return json.dumps({'error': 'unexpected_error', 'message': error_msg})