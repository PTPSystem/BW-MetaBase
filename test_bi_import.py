#!/usr/bin/env python3
"""
Test the production BI Daily Import script locally
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the docker/etl directory to path so we can import our production script
sys.path.append('/Users/howardshen/Library/CloudStorage/OneDrive-Personal/Github/BW-MetaBase/BW-MetaBase/docker/etl')

from msal import ConfidentialClientApplication
import requests

class BIImportTester:
    def __init__(self):
        # Load environment variables from .env file if available
        env_file = '/Users/howardshen/Library/CloudStorage/OneDrive-Personal/Github/BW-MetaBase/BW-MetaBase/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Azure AD Configuration
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        # SharePoint Configuration (IT Project site)
        self.site_id = "netorgft3835860.sharepoint.com:/sites/ITProject:"
        
        # Target files from screenshot
        self.target_files = [
            'BI Dimensions.xlsx',
            'BI At Scale Import.xlsx'
        ]
        
        self.access_token = None
        self.drive_id = None
        
        print(f"🧪 BIImportTester initialized")
        print(f"🎯 Target files: {', '.join(self.target_files)}")

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
                print(f"❌ Failed to get token: {result.get('error_description')}")
                return False
                
        except Exception as e:
            print(f"❌ Token error: {str(e)}")
            return False

    def get_site_info(self):
        """Get IT Project site information"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get IT Project site
            site_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}"
            response = requests.get(site_url, headers=headers)
            
            if response.status_code == 200:
                site_data = response.json()
                actual_site_id = site_data['id']
                print(f"✅ IT Project site: {site_data.get('displayName')}")
                print(f"📍 Site ID: {actual_site_id}")
                
                # Get Documents drive
                drives_url = f"https://graph.microsoft.com/v1.0/sites/{actual_site_id}/drives"
                drives_response = requests.get(drives_url, headers=headers)
                
                if drives_response.status_code == 200:
                    drives = drives_response.json()
                    for drive in drives.get('value', []):
                        if drive.get('name') == 'Documents':
                            self.drive_id = drive['id']
                            self.site_id = actual_site_id  # Update to actual site ID
                            print(f"✅ Documents drive: {self.drive_id}")
                            return True
                    
                    print("❌ Documents drive not found")
                    return False
                else:
                    print(f"❌ Failed to get drives: {drives_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to get site: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Site info error: {str(e)}")
            return False

    def list_bi_import_files(self):
        """List files in General/BI Import folder"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Access General/BI Import folder
            folder_path = "General/BI Import"
            folder_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root:/{folder_path}:/children"
            
            print(f"🔍 Accessing folder: {folder_path}")
            print(f"📡 URL: {folder_url}")
            
            response = requests.get(folder_url, headers=headers)
            
            if response.status_code == 200:
                items = response.json()
                files = items.get('value', [])
                
                print(f"\n📁 Found {len(files)} items in BI Import folder:")
                print("-" * 60)
                
                target_found = []
                
                for item in files:
                    name = item.get('name', 'Unknown')
                    size = item.get('size', 0)
                    modified = item.get('lastModifiedDateTime', 'Unknown')
                    is_file = 'file' in item
                    
                    icon = "📄" if is_file else "📁"
                    print(f"{icon} {name}")
                    print(f"   Size: {size:,} bytes")
                    print(f"   Modified: {modified}")
                    
                    if name in self.target_files:
                        target_found.append(name)
                        print(f"   🎯 TARGET FILE FOUND!")
                        
                        # Get download URL
                        download_url = item.get('@microsoft.graph.downloadUrl')
                        if download_url:
                            print(f"   📥 Download URL available")
                        else:
                            print(f"   ❌ No download URL")
                    
                    print()
                
                print(f"📊 Summary:")
                print(f"   Total files in folder: {len(files)}")
                print(f"   Target files found: {len(target_found)}/{len(self.target_files)}")
                print(f"   Found files: {', '.join(target_found)}")
                
                missing = [f for f in self.target_files if f not in target_found]
                if missing:
                    print(f"   Missing files: {', '.join(missing)}")
                
                return len(target_found) == len(self.target_files)
                
            else:
                print(f"❌ Failed to list BI Import files: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error listing BI Import files: {str(e)}")
            return False

    def test_file_download(self, filename):
        """Test downloading a specific file"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            file_path = f"General/BI Import/{filename}"
            file_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives/{self.drive_id}/root:/{file_path}"
            
            print(f"📥 Testing download of {filename}...")
            
            response = requests.get(file_url, headers=headers)
            
            if response.status_code == 200:
                file_data = response.json()
                download_url = file_data.get('@microsoft.graph.downloadUrl')
                
                if download_url:
                    # Test actual download
                    file_response = requests.get(download_url)
                    
                    if file_response.status_code == 200:
                        size = len(file_response.content)
                        print(f"✅ Successfully downloaded {filename} ({size:,} bytes)")
                        
                        # Save to temp file to test
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                            temp_file.write(file_response.content)
                            temp_path = temp_file.name
                        
                        print(f"💾 Saved to temp file: {temp_path}")
                        
                        # Try to read with pandas to verify it's a valid Excel file
                        try:
                            import pandas as pd
                            df = pd.read_excel(temp_path)
                            print(f"📊 Excel validation: {len(df)} rows, {len(df.columns)} columns")
                            print(f"📝 Columns: {list(df.columns)[:5]}...")  # First 5 columns
                            
                            # Clean up
                            os.unlink(temp_path)
                            return True
                            
                        except Exception as excel_error:
                            print(f"❌ Excel read error: {str(excel_error)}")
                            os.unlink(temp_path)
                            return False
                    else:
                        print(f"❌ Download failed: {file_response.status_code}")
                        return False
                else:
                    print(f"❌ No download URL for {filename}")
                    return False
            else:
                print(f"❌ Failed to get file info: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Download test error: {str(e)}")
            return False

    def run_test(self):
        """Run complete test"""
        print("🧪 Starting BI Import Test")
        print(f"📅 {datetime.now()}")
        print("=" * 60)
        
        # Step 1: Get access token
        if not self.get_access_token():
            print("❌ Test failed: Cannot get access token")
            return False
        
        # Step 2: Get site and drive info
        if not self.get_site_info():
            print("❌ Test failed: Cannot access IT Project site")
            return False
        
        # Step 3: List files in BI Import folder
        if not self.list_bi_import_files():
            print("❌ Test failed: Cannot find all target files")
            return False
        
        # Step 4: Test downloading each target file
        print("\n🔽 Testing file downloads...")
        print("-" * 40)
        
        download_success = 0
        for filename in self.target_files:
            if self.test_file_download(filename):
                download_success += 1
                print(f"✅ {filename} download test passed")
            else:
                print(f"❌ {filename} download test failed")
            print()
        
        print(f"📊 Download Test Summary: {download_success}/{len(self.target_files)} successful")
        
        if download_success == len(self.target_files):
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Ready for production deployment")
            return True
        else:
            print("\n❌ Some tests failed")
            return False

def main():
    tester = BIImportTester()
    success = tester.run_test()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
