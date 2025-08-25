#!/usr/bin/env python3
"""
BW-MetaBase ETL Script
Access SharePoint/OneDrive files and import to PostgreSQL
"""

import os
import sys
import pandas as pd
import psycopg2
from msal import ConfidentialClientApplication
import requests
from datetime import datetime

class SharePointETL:
    def __init__(self):
        # Azure AD Configuration - MUST be provided via environment variables
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            print("❌ Missing required Azure AD environment variables")
            print("Required: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET")
            return
        
        # Database Configuration
        self.db_host = os.getenv('DB_HOST', 'postgres')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'bw_sample_data')
        self.db_user = os.getenv('DB_USER', 'metabase')
        self.db_password = os.getenv('DB_PASSWORD')
        
        if not self.db_password:
            print("❌ Missing required DB_PASSWORD environment variable")
            return
        
        # MSAL App
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
        
        self.access_token = None

    def get_access_token(self):
        """Get access token for Microsoft Graph API"""
        try:
            result = self.app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                print("✅ Successfully obtained access token")
                return True
            else:
                print(f"❌ Failed to obtain access token: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting access token: {str(e)}")
            return False

    def test_permissions(self):
        """Test what permissions we have"""
        try:
            if not self.access_token:
                print("❌ No access token available")
                return False
                
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test: List sites
            sites_url = "https://graph.microsoft.com/v1.0/sites"
            sites_response = requests.get(sites_url, headers=headers)
            
            if sites_response.status_code == 200:
                sites = sites_response.json()
                print(f"✅ Can access {len(sites.get('value', []))} sites")
                for site in sites.get('value', [])[:3]:  # Show first 3
                    print(f"  🏢 {site.get('displayName', 'Unknown')} - {site.get('webUrl', 'No URL')}")
            else:
                print(f"❌ Cannot list sites: {sites_response.status_code} - {sites_response.text}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error testing permissions: {str(e)}")
            return False

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            print("✅ Connected to PostgreSQL database")
            return conn
        except Exception as e:
            print(f"❌ Error connecting to database: {str(e)}")
            return None

    def run_etl(self):
        """Main ETL process"""
        print("🚀 Starting BW-MetaBase ETL Process")
        print(f"📅 {datetime.now()}")
        print("-" * 50)
        
        # Step 1: Get access token
        print("1️⃣ Getting access token...")
        if not self.get_access_token():
            return False
            
        # Step 2: Test permissions
        print("\n2️⃣ Testing permissions...")
        self.test_permissions()
        
        # Step 3: Test database connection
        print(f"\n3️⃣ Testing database connection...")
        conn = self.connect_to_database()
        if conn:
            conn.close()
            
        return True

def main():
    """Main function"""
    print("🔧 BW-MetaBase ETL Container Starting...")
    
    try:
        # Initialize ETL
        etl = SharePointETL()
        
        # Run ETL process
        success = etl.run_etl()
        
        if success:
            print("\n✅ ETL process completed")
        else:
            print("\n❌ ETL process failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 ETL initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
