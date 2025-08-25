#!/usr/bin/env python3
"""
Explore the IT Project Site
"""

import os
import sys
import requests
from msal import ConfidentialClientApplication

class ITProjectExplorer:
    def __init__(self):
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID') 
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.access_token = None
        
    def get_access_token(self):
        """Get access token"""
        try:
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                print("✅ Got access token")
                return True
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

    def explore_itproject_site(self):
        """Explore the IT Project site specifically"""
        if not self.access_token:
            return
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get IT Project site info
        itproject_url = "https://graph.microsoft.com/v1.0/sites/netorgft3835860.sharepoint.com:/sites/ITProject:"
        print(f"🎯 Getting IT Project site details...")
        
        response = requests.get(itproject_url, headers=headers)
        if response.status_code == 200:
            site_data = response.json()
            site_id = site_data['id']
            print(f"✅ IT Project Site ID: {site_id}")
            
            # Explore drives in IT Project
            self.explore_itproject_drives(site_id, headers)
            
        else:
            print(f"❌ Cannot access IT Project site: {response.text}")

    def explore_itproject_drives(self, site_id, headers):
        """Explore drives in IT Project site"""
        try:
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
            response = requests.get(drives_url, headers=headers)
            
            if response.status_code == 200:
                drives = response.json()
                print(f"💾 IT Project has {len(drives.get('value', []))} drives:")
                
                for drive in drives.get('value', []):
                    drive_name = drive.get('name', 'Unknown')
                    drive_id = drive['id']
                    print(f"  💽 {drive_name}")
                    
                    # Explore root of this drive
                    self.explore_drive_root(site_id, drive_id, headers, drive_name)
                    
                    # Look specifically for BI Imports folder
                    self.search_for_bi_imports(site_id, drive_id, headers)
                    
            else:
                print(f"❌ Cannot get IT Project drives: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def explore_drive_root(self, site_id, drive_id, headers, drive_name):
        """Explore root of a drive"""
        try:
            root_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
            response = requests.get(root_url, headers=headers)
            
            if response.status_code == 200:
                items = response.json()
                print(f"    📁 {drive_name} root has {len(items.get('value', []))} items:")
                
                for item in items.get('value', []):
                    name = item.get('name', 'Unknown')
                    size = item.get('size', 0)
                    
                    if 'folder' in item:
                        print(f"      📁 {name}/")
                        
                        # If this is BI Imports, explore it!
                        if 'BI Imports' in name or 'BI' in name:
                            print(f"        🎯 Found BI-related folder! Exploring...")
                            self.explore_folder_path(site_id, drive_id, name, headers)
                            
                    else:
                        file_type = "📄"
                        if name.endswith(('.xlsx', '.xls')):
                            file_type = "🎯 EXCEL"
                            print(f"      {file_type} {name} ({size} bytes)")
                            download_url = item.get('@microsoft.graph.downloadUrl')
                            if download_url:
                                print(f"        📥 Download: {download_url}")
                        else:
                            print(f"      {file_type} {name} ({size} bytes)")
                            
            else:
                print(f"    ❌ Cannot explore {drive_name} root: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")

    def search_for_bi_imports(self, site_id, drive_id, headers):
        """Search for BI Imports folder specifically"""
        try:
            # Try direct path access
            paths_to_try = [
                "BI Imports",
                "BI%20Imports",
                "/BI Imports",
                "/BI%20Imports"
            ]
            
            for path in paths_to_try:
                try:
                    path_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{path}:/children"
                    print(f"    🔍 Trying path: {path}")
                    
                    response = requests.get(path_url, headers=headers)
                    if response.status_code == 200:
                        items = response.json()
                        print(f"    ✅ Found {path}! Has {len(items.get('value', []))} items:")
                        
                        for item in items.get('value', []):
                            name = item.get('name', 'Unknown')
                            if 'folder' in item:
                                print(f"      📁 {name}/")
                                
                                # Look for "BI At Scale Import" folder
                                if 'BI At Scale' in name or 'Scale' in name:
                                    print(f"        🎯 Found target folder: {name}")
                                    self.explore_folder_path(site_id, drive_id, f"{path}/{name}", headers)
                            else:
                                print(f"      📄 {name}")
                                
                    elif response.status_code == 404:
                        print(f"    ❌ Path not found: {path}")
                    else:
                        print(f"    ❌ Error accessing {path}: {response.status_code}")
                        
                except Exception as e:
                    print(f"    ❌ Error with path {path}: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Search error: {str(e)}")

    def explore_folder_path(self, site_id, drive_id, folder_path, headers):
        """Explore a specific folder path"""
        try:
            folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{folder_path}:/children"
            response = requests.get(folder_url, headers=headers)
            
            if response.status_code == 200:
                items = response.json()
                print(f"        📁 {folder_path}/ has {len(items.get('value', []))} items:")
                
                for item in items.get('value', []):
                    name = item.get('name', 'Unknown')
                    size = item.get('size', 0)
                    
                    if 'folder' in item:
                        print(f"          📁 {name}/")
                    else:
                        file_type = "📄"
                        if name.endswith(('.xlsx', '.xls')):
                            file_type = "🎯 EXCEL FILE FOUND!"
                            download_url = item.get('@microsoft.graph.downloadUrl')
                            print(f"          {file_type} {name} ({size} bytes)")
                            if download_url:
                                print(f"            📥 DOWNLOAD: {download_url}")
                        else:
                            print(f"          {file_type} {name} ({size} bytes)")
                            
            else:
                print(f"        ❌ Cannot access folder {folder_path}: {response.status_code}")
                
        except Exception as e:
            print(f"        ❌ Error exploring {folder_path}: {str(e)}")

def main():
    print("🎯 IT Project Site Explorer")
    print("=" * 50)
    
    explorer = ITProjectExplorer()
    
    if explorer.get_access_token():
        explorer.explore_itproject_site()
    else:
        print("❌ Failed to get access token")

if __name__ == "__main__":
    main()
