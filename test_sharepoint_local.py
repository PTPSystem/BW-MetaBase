#!/usr/bin/env python3
"""
Local SharePoint Test Script
Test SharePoint access and file discovery locally
"""

import os
import sys
import requests
from msal import ConfidentialClientApplication
import json
from urllib.parse import quote

class SharePointTester:
    def __init__(self):
        # You'll need to set these environment variables locally
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID') 
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            print("❌ Please set environment variables:")
            print("export AZURE_TENANT_ID='your_tenant_id'")
            print("export AZURE_CLIENT_ID='your_client_id'")
            print("export AZURE_CLIENT_SECRET='your_client_secret'")
            sys.exit(1)
            
        self.access_token = None
        
    def get_access_token(self):
        """Get access token from Azure AD"""
        try:
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            scopes = ['https://graph.microsoft.com/.default']
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                print("✅ Got access token")
                return True
            else:
                print(f"❌ Token error: {result.get('error_description', 'Unknown')}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

    def explore_site_structure(self):
        """Explore the SharePoint site structure"""
        if not self.access_token:
            return
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        hostname = "netorgft3835860.sharepoint.com"
        
        # 1. Get main site
        print(f"\n1️⃣ Getting main site info...")
        site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}"
        site_response = requests.get(site_url, headers=headers)
        
        if site_response.status_code == 200:
            site_data = site_response.json()
            print(f"✅ Site: {site_data.get('displayName', 'Unknown')}")
            site_id = site_data['id']
            
            # 2. Look for subsites
            print(f"\n2️⃣ Looking for subsites...")
            self.find_subsites(site_id, headers)
            
            # 3. Explore drives
            print(f"\n3️⃣ Exploring drives...")
            self.explore_drives(site_id, headers)
            
            # 4. Try different path approaches
            print(f"\n4️⃣ Trying path-based access...")
            self.try_path_access(hostname, headers)
            
        else:
            print(f"❌ Cannot access site: {site_response.text}")

    def find_subsites(self, site_id, headers):
        """Find subsites, especially ITProject"""
        try:
            subsites_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/sites"
            response = requests.get(subsites_url, headers=headers)
            
            if response.status_code == 200:
                subsites = response.json()
                print(f"📂 Found {len(subsites.get('value', []))} subsites:")
                
                for subsite in subsites.get('value', []):
                    name = subsite.get('displayName', 'Unknown')
                    web_url = subsite.get('webUrl', '')
                    print(f"  🏢 {name} - {web_url}")
                    
                    if 'ITProject' in name or 'IT Project' in name:
                        print(f"  🎯 Found ITProject subsite!")
                        self.explore_drives(subsite['id'], headers, name)
            else:
                print(f"❌ Cannot get subsites: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error finding subsites: {str(e)}")

    def explore_drives(self, site_id, headers, site_name="main site"):
        """Explore drives in a site"""
        try:
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            response = requests.get(drives_url, headers=headers)
            
            if response.status_code == 200:
                drives = response.json()
                print(f"💾 {site_name} has {len(drives.get('value', []))} drives:")
                
                for drive in drives.get('value', []):
                    drive_name = drive.get('name', 'Unknown')
                    drive_type = drive.get('driveType', 'Unknown')
                    print(f"  💽 {drive_name} ({drive_type})")
                    
                    # Explore this drive
                    self.explore_drive_contents(site_id, drive['id'], headers, drive_name)
                    
            else:
                print(f"❌ Cannot get drives for {site_name}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error exploring drives: {str(e)}")

    def explore_drive_contents(self, site_id, drive_id, headers, drive_name, path="root"):
        """Explore contents of a drive"""
        try:
            if path == "root":
                items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
            else:
                items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{path}:/children"
                
            response = requests.get(items_url, headers=headers)
            
            if response.status_code == 200:
                items = response.json()
                print(f"    📁 {drive_name}/{path} has {len(items.get('value', []))} items:")
                
                for item in items.get('value', []):
                    name = item.get('name', 'Unknown')
                    size = item.get('size', 0)
                    
                    if 'folder' in item:
                        print(f"      📁 {name}/")
                        
                        # If it matches our target folders, explore deeper
                        if name in ['IT Project', 'BI Imports', 'BI At Scale Import']:
                            new_path = f"{path}/{name}" if path != "root" else name
                            print(f"        🎯 Exploring target folder: {name}")
                            self.explore_drive_contents(site_id, drive_id, headers, drive_name, new_path)
                            
                    else:
                        file_type = "📄"
                        if name.endswith(('.xlsx', '.xls')):
                            file_type = "🎯 EXCEL"
                            download_url = item.get('@microsoft.graph.downloadUrl')
                            if download_url:
                                print(f"      {file_type} {name} ({size} bytes) - CAN DOWNLOAD!")
                        print(f"      {file_type} {name} ({size} bytes)")
                        
            else:
                print(f"    ❌ Cannot explore {drive_name}/{path}: {response.status_code}")
                if response.status_code == 404:
                    print(f"    ℹ️ Path not found: {path}")
                    
        except Exception as e:
            print(f"    ❌ Error exploring {drive_name}: {str(e)}")

    def try_path_access(self, hostname, headers):
        """Try different path-based approaches"""
        paths_to_try = [
            "/sites/ITProject",
            ":/sites/ITProject:",
            "/IT Project",
            ":/IT Project:",
        ]
        
        for path in paths_to_try:
            try:
                if path.startswith(':') and path.endswith(':'):
                    url = f"https://graph.microsoft.com/v1.0/sites/{hostname}{path}"
                else:
                    url = f"https://graph.microsoft.com/v1.0/sites/{hostname}{path}"
                    
                print(f"🔍 Trying: {url}")
                response = requests.get(url, headers=headers)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found: {data.get('displayName', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")

def main():
    print("🚀 SharePoint Local Tester")
    print("=" * 50)
    
    tester = SharePointTester()
    
    if tester.get_access_token():
        tester.explore_site_structure()
    else:
        print("❌ Failed to get access token")

if __name__ == "__main__":
    main()
