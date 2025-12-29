"""
Admin endpoints for API key management.
Add these routes to your Flask app.
"""

import os
import hashlib
from flask import Flask, request, jsonify
from secure_api_keys import SecureAPIKeyManager

# Initialize the secure key manager
secure_key_manager = SecureAPIKeyManager()

# This would normally be imported from your main app
# For now, we'll create a blueprint or assume app is passed in
def register_admin_routes(app: Flask):
    """Register admin routes with the Flask app."""
    
    @app.route('/api/admin/api-keys', methods=['GET'])
    def admin_get_api_keys():
        """Admin endpoint to view all stored API keys."""
        try:
            # Simple admin authentication - in production, use proper authentication
            admin_token = request.headers.get('X-Admin-Token')
            if admin_token != os.getenv('ADMIN_TOKEN', 'admin-secret-key'):
                return jsonify({"error": "Unauthorized"}), 403
            
            all_keys = secure_key_manager.list_stored_keys('Eggp1an1F2shCvrry1!')
            return jsonify({"api_keys": all_keys})
            
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve API keys: {str(e)}"}), 500

    @app.route('/api/admin/api-keys/logs', methods=['GET'])
    def admin_get_api_key_logs():
        """Admin endpoint to view API key access logs."""
        try:
            # Simple admin authentication
            admin_token = request.headers.get('X-Admin-Token')
            if admin_token != os.getenv('ADMIN_TOKEN', 'admin-secret-key'):
                return jsonify({"error": "Unauthorized"}), 403
            
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Note: This method doesn't exist in our current implementation
            # logs = secure_key_manager.export_logs(start_date, end_date)
            logs = []  # Placeholder
            return jsonify({"logs": logs})
            
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve logs: {str(e)}"}), 500

    @app.route('/api/user/api-keys/summary', methods=['GET'])
    def get_user_api_keys_summary():
        """Get summary of current user's API keys."""
        try:
            # Generate user ID from request
            user_ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            user_id = hashlib.sha256(f"{user_ip}:{user_agent}".encode()).hexdigest()[:16]
            
            # Note: This method doesn't exist in our current implementation
            # summary = secure_key_manager.get_user_keys_summary(user_id)
            summary = []  # Placeholder
            return jsonify({"summary": summary})
            
        except Exception as e:
            return jsonify({"error": f"Failed to get summary: {str(e)}"}), 500
