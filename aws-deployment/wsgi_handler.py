"""
WSGI Handler for AWS Lambda deployment
"""

import os
import sys

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, parent_dir)
sys.path.insert(0, src_dir)

try:
    from serverless_wsgi import handle_request
    from src.main import create_app
    
    # Create the Flask app
    app = create_app()
    
    def handler(event, context):
        """
        AWS Lambda handler function
        """
        return handle_request(app, event, context)
        
except ImportError as e:
    print(f"Import error: {e}")
    
    def handler(event, context):
        return {
            'statusCode': 500,
            'body': f'Import error: {str(e)}'
        }

