#!/usr/bin/env python3
"""
Test script to explore BI Dimensions Excel file structure
"""

import os
import sys
import re
import pandas as pd
from msal import ConfidentialClientApplication
import requests
import tempfile

class BIDimensionsExplorer:
    def __init__(self):
        # Azure AD Configuration
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        # SharePoint Configuration
        self.site_id = "netorgft3835860.sharepoint.com:/sites/ITProject:"
        self.access_token = None
        self.drive_id = None

    def get_access_token(self):
        """Get access token from Azure AD"""
        try:
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Request token with Microsoft Graph scope
            result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                print("✅ Successfully obtained access token")
                return True
            else:
                print(f"❌ Failed to get access token: {result.get('error_description')}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting access token: {str(e)}")
            return False

    def get_drive_id(self):
        """Get the Documents drive ID for the IT Project site"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                drives = response.json().get('value', [])
                for drive in drives:
                    if drive.get('name') == 'Documents':
                        self.drive_id = drive.get('id')
                        print(f"✅ Found Documents drive ID: {self.drive_id}")
                        return True
                        
                print("❌ Documents drive not found")
                return False
            else:
                print(f"❌ Failed to get drives: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting drive ID: {str(e)}")
            return False

    def download_bi_dimensions(self):
        """Download and explore BI Dimensions file"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            file_path = "General/BI Import/BI Dimensions.xlsx"
            
            print(f"📥 Downloading BI Dimensions.xlsx...")
            
            # Get file metadata and download URL
            file_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root:/{file_path}"
            response = requests.get(file_url, headers=headers)
            
            if response.status_code == 200:
                file_data = response.json()
                download_url = file_data.get('@microsoft.graph.downloadUrl')
                
                if download_url:
                    # Download the actual file content
                    file_response = requests.get(download_url)
                    
                    if file_response.status_code == 200:
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                            temp_file.write(file_response.content)
                            temp_file_path = temp_file.name
                            
                        print(f"✅ Downloaded BI Dimensions.xlsx ({len(file_response.content)} bytes)")
                        return temp_file_path
                    else:
                        print(f"❌ Failed to download file content: {file_response.status_code}")
                        return None
                else:
                    print(f"❌ No download URL available")
                    return None
            else:
                print(f"❌ Failed to get file metadata: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading BI Dimensions: {str(e)}")
            return None

    def explore_sheets(self, file_path):
        """Explore all sheets in the BI Dimensions file"""
        try:
            print(f"\n📊 Exploring sheets in BI Dimensions.xlsx...")
            
            # Get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            print(f"📋 Found {len(sheet_names)} sheets: {sheet_names}")
            
            for i, sheet_name in enumerate(sheet_names):
                print(f"\n📄 Sheet {i+1}: '{sheet_name}'")
                print("-" * 50)
                
                try:
                    # Read the sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    if df.empty:
                        print(f"⚠️ Sheet is empty")
                        continue
                    
                    print(f"📊 Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
                    print(f"📝 Column names: {list(df.columns)}")
                    
                    # Show first few rows
                    print(f"📋 First 3 rows:")
                    print(df.head(3).to_string())
                    
                    # Generate clean table name
                    clean_sheet_name = re.sub(r'[^a-zA-Z0-9]', '_', sheet_name.lower())
                    table_name = f"bi_dimensions_{clean_sheet_name}"
                    print(f"🏷️ Proposed table name: {table_name}")
                    
                except Exception as e:
                    print(f"❌ Error reading sheet '{sheet_name}': {str(e)}")
                    continue
            
        except Exception as e:
            print(f"❌ Error exploring sheets: {str(e)}")

    def run_exploration(self):
        """Run the exploration process"""
        print("🔍 Starting BI Dimensions Exploration")
        print(f"📅 {pd.Timestamp.now()}")
        print("-" * 60)
        
        # Step 1: Get access token
        if not self.get_access_token():
            print("❌ Failed to get access token")
            return False
        
        # Step 2: Get drive ID
        if not self.get_drive_id():
            print("❌ Failed to get drive ID")
            return False
        
        # Step 3: Download and explore BI Dimensions
        temp_file_path = self.download_bi_dimensions()
        if temp_file_path:
            self.explore_sheets(temp_file_path)
            
            # Clean up
            try:
                os.unlink(temp_file_path)
                print(f"\n🧹 Cleaned up temporary file")
            except Exception as e:
                print(f"⚠️ Warning: Could not clean up temp file: {e}")
                
            return True
        else:
            print("❌ Failed to download BI Dimensions file")
            return False

def main():
    """Main exploration process"""
    explorer = BIDimensionsExplorer()
    success = explorer.run_exploration()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
