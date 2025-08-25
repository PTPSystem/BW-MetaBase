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
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime

class SharePointETL:
    def __init__(self):
        # Azure AD Configuration - MUST be provided via environment variables
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Missing required Azure AD environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET")
        
        # Database Configuration
        self.db_host = os.getenv('DB_HOST', 'postgres')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'bw_sample_data')
        self.db_user = os.getenv('DB_USER', 'metabase')
        self.db_password = os.getenv('DB_PASSWORD')
        
        if not self.db_password:
            raise ValueError("Missing required DB_PASSWORD environment variable")
        
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
            # Get token for Microsoft Graph
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

    def parse_sharepoint_url(self, url):
        """Parse SharePoint sharing URL to get site and file info"""
        try:
            # Example URL: https://netorgft3835860.sharepoint.com/:x:/s/ITProject/EWpbznFTspFPuqW9htsCyPQBipG9KfFhY7wCASWmifeaHw?e=sRdUM1
            parsed = urlparse(url)
            
            # Extract hostname
            hostname = parsed.hostname  # netorgft3835860.sharepoint.com
            
            # Extract path parts
            path_parts = parsed.path.split('/')
            
            if len(path_parts) >= 4 and path_parts[3] == 's':
                site_name = path_parts[4]  # ITProject
                
                # Parse query parameters
                query_params = parse_qs(parsed.query)
                
                return {
                    'hostname': hostname,
                    'site_name': site_name,
                    'url': url
                }
            else:
                print(f"❌ Could not parse SharePoint URL structure: {url}")
                return None
                
        except Exception as e:
            print(f"❌ Error parsing SharePoint URL: {str(e)}")
            return None

    def get_file_from_sharepoint(self, sharepoint_url):
        """Download file from SharePoint using sharing URL"""
        try:
            if not self.access_token:
                print("❌ No access token available")
                return None
                
            # Parse the SharePoint URL
            url_info = self.parse_sharepoint_url(sharepoint_url)
            if not url_info:
                return None
                
            print(f"📁 Attempting to access file from site: {url_info['site_name']}")
            
            # Try to get site information
            site_url = f"https://graph.microsoft.com/v1.0/sites/{url_info['hostname']}:/sites/{url_info['site_name']}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(site_url, headers=headers)
            
            if response.status_code == 200:
                site_info = response.json()
                print(f"✅ Found site: {site_info.get('displayName', 'Unknown')}")
                site_id = site_info['id']
                
                # List files in the site
                files_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
                files_response = requests.get(files_url, headers=headers)
                
                if files_response.status_code == 200:
                    files = files_response.json()
                    print(f"📂 Found {len(files.get('value', []))} items in site")
                    
                    # List file names
                    for file_item in files.get('value', []):
                        print(f"  📄 {file_item.get('name', 'Unknown')} ({file_item.get('size', 0)} bytes)")
                    
                    return files.get('value', [])
                else:
                    print(f"❌ Failed to list files: {files_response.status_code} - {files_response.text}")
                    
            else:
                print(f"❌ Failed to access site: {response.status_code} - {response.text}")
                
                # Try alternative approach - search for the site
                search_url = f"https://graph.microsoft.com/v1.0/sites?search={url_info['site_name']}"
                search_response = requests.get(search_url, headers=headers)
                
                if search_response.status_code == 200:
                    sites = search_response.json()
                    print(f"🔍 Found {len(sites.get('value', []))} sites matching '{url_info['site_name']}':")
                    for site in sites.get('value', []):
                        print(f"  🏢 {site.get('displayName', 'Unknown')} - {site.get('webUrl', 'No URL')}")
                
        except Exception as e:
            print(f"❌ Error accessing SharePoint file: {str(e)}")
            
        return None

    def test_sharepoint_access(self, sharepoint_url):
        """Test accessing specific SharePoint file"""
        try:
            if not self.access_token:
                print("❌ No access token available")
                return False
                
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            print(f"🔗 Testing access to: {sharepoint_url}")
            
            # Try method 1: Direct site access by hostname
            try:
                hostname = "netorgft3835860.sharepoint.com"
                site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}"
                print(f"📡 Trying to access site: {site_url}")
                
                site_response = requests.get(site_url, headers=headers)
                print(f"Site response: {site_response.status_code}")
                
                if site_response.status_code == 200:
                    site_data = site_response.json()
                    print(f"✅ Found site: {site_data.get('displayName', 'Unknown')}")
                    return self.explore_site_drives(site_data['id'], headers)
                else:
                    print(f"❌ Cannot access site directly: {site_response.text}")
            except Exception as e:
                print(f"⚠️ Method 1 failed: {str(e)}")
            
            # Try method 2: Search for ITProject site
            try:
                search_url = "https://graph.microsoft.com/v1.0/sites?search=ITProject"
                print(f"🔍 Searching for ITProject site...")
                
                search_response = requests.get(search_url, headers=headers)
                print(f"Search response: {search_response.status_code}")
                
                if search_response.status_code == 200:
                    sites = search_response.json()
                    print(f"🎯 Found {len(sites.get('value', []))} sites matching 'ITProject':")
                    
                    for site in sites.get('value', []):
                        site_name = site.get('displayName', 'Unknown')
                        web_url = site.get('webUrl', 'No URL')
                        print(f"  🏢 {site_name} - {web_url}")
                        
                        if 'ITProject' in site_name or 'ITProject' in web_url:
                            print(f"✅ Found matching site: {site_name}")
                            return self.explore_site_drives(site['id'], headers)
                else:
                    print(f"❌ Search failed: {search_response.text}")
            except Exception as e:
                print(f"⚠️ Method 2 failed: {str(e)}")
            
            # Try method 2.5: Direct access to ITProject site using path
            try:
                itproject_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/ITProject"
                print(f"🎯 Trying ITProject site path: {itproject_url}")
                
                itproject_response = requests.get(itproject_url, headers=headers)
                print(f"ITProject response: {itproject_response.status_code}")
                
                if itproject_response.status_code == 200:
                    site_data = itproject_response.json()
                    print(f"✅ Found ITProject site: {site_data.get('displayName', 'Unknown')}")
                    return self.explore_site_drives(site_data['id'], headers)
                else:
                    print(f"❌ Cannot access ITProject site: {itproject_response.text}")
            except Exception as e:
                print(f"⚠️ Method 2.5 failed: {str(e)}")
            
            # Try method 3: List all accessible sites
            try:
                sites_url = "https://graph.microsoft.com/v1.0/sites"
                print(f"📋 Listing all accessible sites...")
                
                sites_response = requests.get(sites_url, headers=headers)
                print(f"Sites list response: {sites_response.status_code}")
                
                if sites_response.status_code == 200:
                    sites = sites_response.json()
                    print(f"📂 Can access {len(sites.get('value', []))} total sites:")
                    
                    for site in sites.get('value', []):
                        site_name = site.get('displayName', 'Unknown')
                        web_url = site.get('webUrl', 'No URL')
                        print(f"  🏢 {site_name} - {web_url}")
                else:
                    print(f"❌ Cannot list sites: {sites_response.text}")
            except Exception as e:
                print(f"⚠️ Method 3 failed: {str(e)}")
            # Try method 4: Direct file access using sharing URL
            try:
                if self.try_direct_file_access(sharepoint_url, headers):
                    return True
            except Exception as e:
                print(f"⚠️ Method 4 failed: {str(e)}")
                
            return False
            
        except Exception as e:
            print(f"❌ Error testing SharePoint access: {str(e)}")
            return False

    def explore_site_drives(self, site_id, headers):
        """Explore drives and files in a SharePoint site"""
        try:
            print(f"📁 Exploring drives for site: {site_id}")
            
            # Get site drives
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            drives_response = requests.get(drives_url, headers=headers)
            
            if drives_response.status_code == 200:
                drives = drives_response.json()
                print(f"💾 Found {len(drives.get('value', []))} drives:")
                
                for drive in drives.get('value', []):
                    drive_name = drive.get('name', 'Unknown')
                    drive_type = drive.get('driveType', 'Unknown')
                    print(f"  💽 {drive_name} ({drive_type})")
                    
                    # List files in each drive
                    self.list_drive_files(site_id, drive['id'], headers)
                    
                return True
            else:
                print(f"❌ Cannot access drives: {drives_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error exploring drives: {str(e)}")
            return False

    def list_drive_files(self, site_id, drive_id, headers):
        """List files in a SharePoint drive"""
        try:
            files_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
            files_response = requests.get(files_url, headers=headers)
            
            if files_response.status_code == 200:
                files = files_response.json()
                print(f"    📄 Found {len(files.get('value', []))} items:")
                
                for file_item in files.get('value', []):
                    item_name = file_item.get('name', 'Unknown')
                    item_size = file_item.get('size', 0)
                    item_type = "📁 Folder" if 'folder' in file_item else "📄 File"
                    print(f"      {item_type} {item_name} ({item_size} bytes)")
                    
                    # If it's an Excel file, try to download it
                    if item_name.endswith(('.xlsx', '.xls')):
                        print(f"🎯 Found Excel file: {item_name}")
                        download_url = file_item.get('@microsoft.graph.downloadUrl')
                        if download_url:
                            print(f"📥 Download URL available: {download_url[:50]}...")
                    
                    # If it's a folder, explore it
                    if 'folder' in file_item:
                        self.explore_folder(site_id, drive_id, file_item['id'], headers, depth=1)
                        
            else:
                print(f"    ❌ Cannot list files: {files_response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Error listing files: {str(e)}")

    def explore_folder(self, site_id, drive_id, folder_id, headers, depth=0):
        """Explore a folder in SharePoint"""
        if depth > 2:  # Limit recursion depth
            return
            
        try:
            folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{folder_id}/children"
            folder_response = requests.get(folder_url, headers=headers)
            
            if folder_response.status_code == 200:
                items = folder_response.json()
                indent = "  " * (depth + 2)
                print(f"{indent}📁 Exploring folder with {len(items.get('value', []))} items:")
                
                for item in items.get('value', []):
                    item_name = item.get('name', 'Unknown')
                    item_size = item.get('size', 0)
                    item_type = "📁 Folder" if 'folder' in item else "📄 File"
                    print(f"{indent}  {item_type} {item_name} ({item_size} bytes)")
                    
                    # If it's an Excel file, show download info
                    if item_name.endswith(('.xlsx', '.xls')):
                        print(f"{indent}  🎯 Excel file found: {item_name}")
                        download_url = item.get('@microsoft.graph.downloadUrl')
                        if download_url:
                            print(f"{indent}  📥 Can download: {download_url[:50]}...")
                    
                    # Recurse into subfolders
                    if 'folder' in item and depth < 2:
                        self.explore_folder(site_id, drive_id, item['id'], headers, depth + 1)
                        
        except Exception as e:
            print(f"    ❌ Error exploring folder: {str(e)}")

    def try_direct_file_access(self, sharepoint_url, headers):
        """Try to access file directly using sharing URL"""
        try:
            print(f"🔗 Trying direct file access...")
            
            # Extract file ID from sharing URL if possible
            if 'EWpbznFTspFPuqW9htsCyPQBipG9KfFhY7wCASWmifeaHw' in sharepoint_url:
                # This appears to be the file/item ID
                file_id = 'EWpbznFTspFPuqW9htsCyPQBipG9KfFhY7wCASWmifeaHw'
                
                # Try to get file info using Graph API
                file_url = f"https://graph.microsoft.com/v1.0/shares/u!{file_id}/driveItem"
                print(f"📡 Trying file URL: {file_url}")
                
                file_response = requests.get(file_url, headers=headers)
                print(f"Direct file response: {file_response.status_code}")
                
                if file_response.status_code == 200:
                    file_data = file_response.json()
                    file_name = file_data.get('name', 'Unknown')
                    file_size = file_data.get('size', 0)
                    print(f"✅ Found file: {file_name} ({file_size} bytes)")
                    
                    download_url = file_data.get('@microsoft.graph.downloadUrl')
                    if download_url:
                        print(f"📥 Download URL: {download_url[:50]}...")
                        return True
                else:
                    print(f"❌ Cannot access file directly: {file_response.text}")
                    
        except Exception as e:
            print(f"❌ Error in direct file access: {str(e)}")
            
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

    def run_etl(self, sharepoint_url):
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
        
        # Step 3: Try to access the SharePoint file
        print(f"\n3️⃣ Accessing SharePoint file...")
        files = self.get_file_from_sharepoint(sharepoint_url)
        
        # Step 4: Test database connection
        print(f"\n4️⃣ Testing database connection...")
        conn = self.connect_to_database()
        if conn:
            conn.close()
            
        return True

def main():
    """Main ETL process"""
    print("� Starting BW-MetaBase ETL Process")
    
    etl = SharePointETL()
    
    # Step 1: Get access token
    if not etl.get_access_token():
        print("❌ Failed to get access token")
        return
    
    # Step 2: Test SharePoint access with specific URL
    sharepoint_url = "https://netorgft3835860.sharepoint.com/:x:/s/ITProject/EWpbznFTspFPuqW9htsCyPQBipG9KfFhY7wCASWmifeaHw?e=DgpJHN"
    etl.test_sharepoint_access(sharepoint_url)
    
    # Step 3: Test database connection
    etl.connect_to_database()
    
    print("✅ ETL process completed")

if __name__ == "__main__":
    main()
