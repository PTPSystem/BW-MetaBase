#!/usr/bin/env python3
"""
Explore General folder in IT Project
"""

import os
import requests
from msal import ConfidentialClientApplication

class GeneralFolderExplorer:
    def __init__(self):
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID') 
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        self.access_token = None
        
    def get_access_token(self):
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

    def explore_general_folder(self):
        """Explore the General folder recursively"""
        if not self.access_token:
            return
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # IT Project site ID from previous discovery
        site_id = "netorgft3835860.sharepoint.com,1073ec41-fdcb-49a5-b7c3-8370f96b3dc0,005c711d-58c8-4271-88a8-6c9b4c0bcd76"
        
        # Get the Documents drive ID
        drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        response = requests.get(drives_url, headers=headers)
        
        if response.status_code == 200:
            drives = response.json()
            drive_id = drives['value'][0]['id']  # We know there's 1 drive called Documents
            
            print("🔍 Exploring General folder structure...")
            self.explore_folder_recursive(site_id, drive_id, "General", headers, depth=0)
            
        else:
            print(f"❌ Cannot get drives: {response.status_code}")

    def explore_folder_recursive(self, site_id, drive_id, folder_path, headers, depth=0):
        """Recursively explore folders"""
        if depth > 5:  # Prevent infinite recursion
            return
            
        indent = "  " * depth
        print(f"{indent}📁 Exploring: {folder_path}")
        
        try:
            folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{folder_path}:/children"
            response = requests.get(folder_url, headers=headers)
            
            if response.status_code == 200:
                items = response.json()
                print(f"{indent}   Found {len(items.get('value', []))} items:")
                
                folders_to_explore = []
                
                for item in items.get('value', []):
                    name = item.get('name', 'Unknown')
                    size = item.get('size', 0)
                    
                    if 'folder' in item:
                        print(f"{indent}   📁 {name}/")
                        
                        # Queue folders for exploration
                        new_path = f"{folder_path}/{name}"
                        folders_to_explore.append(new_path)
                        
                        # Special attention to BI-related folders
                        if any(keyword in name.lower() for keyword in ['bi', 'import', 'scale', 'data']):
                            print(f"{indent}   🎯 BI-related folder found: {name}")
                            
                    else:
                        file_type = "📄"
                        if name.endswith(('.xlsx', '.xls')):
                            file_type = "🎯 EXCEL"
                            download_url = item.get('@microsoft.graph.downloadUrl')
                            print(f"{indent}   {file_type} {name} ({size} bytes)")
                            if download_url:
                                print(f"{indent}      📥 Download: {download_url[:50]}...")
                        else:
                            print(f"{indent}   {file_type} {name} ({size} bytes)")
                
                # Explore subfolders
                for subfolder_path in folders_to_explore:
                    self.explore_folder_recursive(site_id, drive_id, subfolder_path, headers, depth + 1)
                    
            elif response.status_code == 404:
                print(f"{indent}   ❌ Folder not found: {folder_path}")
            else:
                print(f"{indent}   ❌ Error accessing {folder_path}: {response.status_code}")
                
        except Exception as e:
            print(f"{indent}   ❌ Error: {str(e)}")

def main():
    print("📁 General Folder Explorer")
    print("=" * 50)
    
    explorer = GeneralFolderExplorer()
    
    if explorer.get_access_token():
        explorer.explore_general_folder()
    else:
        print("❌ Failed to get access token")

if __name__ == "__main__":
    main()
