import os
import requests
from dotenv import load_dotenv
import json

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
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            return json.dumps(response.json())
        else:
            return json.dumps({'error': response.status_code, 'message': response.text})