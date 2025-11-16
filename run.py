#!/usr/bin/env python
"""
Entry point for the RSS Intelligent Reader application.
Runs the Flask development server with the single-process frontend + backend.
"""

import os
from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print(f"\n{'='*60}")
    print(f"RSS Intelligent Reader")
    print(f"{'='*60}")
    print(f"Starting Flask server on http://{host}:{port}")
    print(f"Press CTRL+C to stop the server")
    print(f"{'='*60}\n")
    
    app.run(host=host, port=port, debug=debug)
