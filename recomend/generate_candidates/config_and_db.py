"""基本設定とデータベース操作"""
import json
import boto3
from decimal import Decimal
import logging
from typing import Dict, List
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
EMPLOYEES_TABLE = os.environ.get('EMPLOYEES_TABLE', 'Employees')
PROJECTS_TABLE = os.environ.get('PROJECTS_TABLE', 'Projects')

def decimal_to_float(obj):
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def fetch_employees_from_dynamodb():
    try:
        table = dynamodb.Table(EMPLOYEES_TABLE)
        response = table.scan()
        employees = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            employees.extend(response.get('Items', []))
        logger.info(f"Fetched {len(employees)} employees")
        return employees
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

def fetch_project_from_dynamodb(project_id):
    try:
        table = dynamodb.Table(PROJECTS_TABLE)
        response = table.get_item(Key={'project_id': project_id})
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

def group_employees_by_role(employees):
    grouped = {}
    for emp in employees:
        role = emp.get('role', 'Unknown')
        if role not in grouped:
            grouped[role] = []
        grouped[role].append(emp)
    return grouped