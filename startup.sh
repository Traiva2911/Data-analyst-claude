#!/bin/bash
# Startup command for Azure App Service (Linux, Python).
# Streamlit must listen on port 8000 and address 0.0.0.0 for App Service.
# In Azure, set the Startup Command to:  bash startup.sh
python -m streamlit run src/dashboard.py \
    --server.port 8000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection true
