#!/usr/bin/env python3
"""
BW-MetaBase Production ETL Script
Daily import of BI Dimensions and BI At Scale Import files from SharePoint to PostgreSQL
"""

import os
import sys
import re
import pandas as pd
import psycopg2
from msal import ConfidentialClientApplication
import requests
from datetime import datetime
import tempfile

class SharePointETL:
    def __init__(self):
        # Azure AD Configuration
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        # Database Configuration
        self.db_host = os.getenv('POSTGRES_HOST', 'postgres')
        self.db_port = os.getenv('POSTGRES_PORT', '5432')
        self.db_name = os.getenv('POSTGRES_DB', 'bw_sample_data')
        self.db_user = os.getenv('POSTGRES_USER', 'postgres')
        self.db_password = os.getenv('POSTGRES_PASSWORD')
        
        # SharePoint Configuration
        self.site_id = "netorgft3835860.sharepoint.com,1073ec41-fdcb-49a5-b7c3-8370f96b3dc0,005c711d-58c8-4271-88a8-6c9b4c0bcd76"
        self.drive_id = None
        
        # Files to import daily
        self.target_files = [
            {
                'filename': 'BI Dimensions.xlsx',
                'path': 'General/BI Import/BI Dimensions.xlsx',
                'table_name': 'bi_dimensions',
                'import_type': 'multi_sheet'  # This file has multiple sheets to import
            },
            {
                'filename': 'BI At Scale Import.xlsx',
                'path': 'General/BI Import/BI At Scale Import.xlsx',
                'table_name': 'bi_at_scale_import',
                'import_type': 'single_sheet'  # This is a single sheet file
            }
        ]
        
        # Validate required environment variables
        required_vars = [
            ('AZURE_TENANT_ID', self.tenant_id),
            ('AZURE_CLIENT_ID', self.client_id),
            ('AZURE_CLIENT_SECRET', self.client_secret),
            ('POSTGRES_PASSWORD', self.db_password)
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
        
        self.access_token = None
        print("✅ SharePointETL initialized")

    def get_access_token(self):
        """Get access token from Azure AD using MSAL"""
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
                print("✅ Successfully obtained access token")
                return True
            else:
                print(f"❌ Failed to obtain access token: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting access token: {str(e)}")
            return False

    def get_drive_id(self):
        """Get the Documents drive ID from IT Project site"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            drives_url = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"
            response = requests.get(drives_url, headers=headers)
            
            if response.status_code == 200:
                drives = response.json()
                for drive in drives.get('value', []):
                    if drive.get('name') == 'Documents':
                        self.drive_id = drive['id']
                        print(f"✅ Found Documents drive: {self.drive_id}")
                        return True
                        
                print("❌ Documents drive not found")
                return False
            else:
                print(f"❌ Failed to get drives: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting drive ID: {str(e)}")
            return False

    def download_file(self, file_config):
        """Download a specific file from SharePoint"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            file_path = file_config['path']
            filename = file_config['filename']
            
            print(f"📥 Downloading {filename}...")
            
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
                            
                        print(f"✅ Downloaded {filename} ({len(file_response.content)} bytes)")
                        return temp_file_path
                    else:
                        print(f"❌ Failed to download file content: {file_response.status_code}")
                        return None
                else:
                    print(f"❌ No download URL available for {filename}")
                    return None
            else:
                print(f"❌ Failed to get file metadata for {filename}: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading {filename}: {str(e)}")
            return None

    def import_excel_to_postgres(self, file_path, file_info):
        """Import Excel file to PostgreSQL with proper column handling"""
        try:
            print(f"📊 Importing {file_info['filename']} to PostgreSQL...")
            
            if file_info['import_type'] == 'multi_sheet':
                # Handle multi-sheet files (BI Dimensions)
                return self.import_multi_sheet_excel(file_path, file_info)
            else:
                # Handle single sheet files (BI At Scale Import)
                return self.import_single_sheet_excel(file_path, file_info)
                
        except Exception as e:
            print(f"❌ Error importing {file_info['filename']}: {str(e)}")
            return False

    def import_multi_sheet_excel(self, file_path, file_info):
        """Import all sheets from a multi-sheet Excel file"""
        try:
            # First, get all sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            print(f"📋 Found {len(sheet_names)} sheets in {file_info['filename']}: {sheet_names}")
            
            success_count = 0
            for i, sheet_name in enumerate(sheet_names):
                try:
                    # Create table name from base name and sheet name
                    clean_sheet_name = re.sub(r'[^a-zA-Z0-9]', '_', sheet_name.lower())
                    table_name = f"{file_info['table_name']}_{clean_sheet_name}"
                    
                    print(f"� Processing sheet '{sheet_name}' -> table '{table_name}'")
                    
                    # Read the sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    if df.empty:
                        print(f"⚠️ Sheet '{sheet_name}' is empty, skipping...")
                        continue
                    
                    # Import this sheet to database
                    if self.import_dataframe_to_db(df, table_name):
                        success_count += 1
                        print(f"✅ Successfully imported sheet '{sheet_name}' ({len(df)} rows) to table '{table_name}'")
                    else:
                        print(f"❌ Failed to import sheet '{sheet_name}'")
                    
                except Exception as e:
                    print(f"❌ Error processing sheet '{sheet_name}': {str(e)}")
                    continue
            
            print(f"📊 Multi-sheet import summary: {success_count}/{len(sheet_names)} sheets imported successfully")
            return success_count > 0
                    
        except Exception as e:
            print(f"❌ Error reading multi-sheet Excel file: {str(e)}")
            return False

    def import_single_sheet_excel(self, file_path, file_info):
        """Import a single sheet Excel file"""
        try:
            table_name = file_info['table_name']
            filename = file_info['filename']
            
            # Read Excel file with specific handling for each file type
            print(f"🔍 Processing file: {filename}")
            if 'BI At Scale Import' in filename:
                # BI At Scale Import: Row 4 has column headers, data starts at row 5
                print("📋 Using row 4 as headers for BI At Scale Import file")
                df = pd.read_excel(file_path, skiprows=3, header=0)  # Skip 3 rows, use row 4 as header
                print(f"📄 Loaded {len(df)} rows, {len(df.columns)} columns (headers from row 4)")
                print(f"📝 Column names: {list(df.columns)[:5]}...")  # Show first 5 column names
            else:
                # Other files start at row 1
                print("📋 Reading file from row 1")
                df = pd.read_excel(file_path)
                print(f"📄 Loaded {len(df)} rows, {len(df.columns)} columns")
            
            if df.empty:
                print(f"⚠️ File {filename} is empty, skipping...")
                return False
            
            # Import to database
            return self.import_dataframe_to_db(df, table_name)
            
        except Exception as e:
            print(f"❌ Error importing single sheet Excel file: {str(e)}")
            return False

    def import_dataframe_to_db(self, df, table_name):
        """Import a pandas DataFrame to PostgreSQL"""
        try:
            # Handle NaT (Not a Time) values and other problematic data
            # Replace NaT with None for proper NULL handling
            df = df.replace({pd.NaT: None})
            
            # Replace NaN with None for proper NULL handling
            df = df.where(pd.notnull(df), None)
            
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            
            # Clean column names for PostgreSQL (more aggressive cleaning)
            cleaned_columns = []
            for col in df.columns:
                # Convert to string first
                col_str = str(col)
                # Replace problematic characters and patterns
                cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', col_str)  # Replace non-alphanumeric with underscore
                cleaned = re.sub(r'^[0-9]', 'col_\\g<0>', cleaned)  # Prefix numbers with 'col_'
                cleaned = re.sub(r'_+', '_', cleaned)  # Replace multiple underscores with single
                cleaned = cleaned.strip('_').lower()  # Remove leading/trailing underscores and lowercase
                
                # Ensure it's not empty and not a PostgreSQL reserved word
                if not cleaned or cleaned in ['user', 'order', 'group', 'table', 'index']:
                    cleaned = f'column_{len(cleaned_columns)}'
                
                cleaned_columns.append(cleaned)
            
            df.columns = cleaned_columns
            
            # Add import timestamp
            df['import_timestamp'] = datetime.now()
            
            cursor = conn.cursor()
            
            # Drop existing table and recreate
            drop_sql = f"DROP TABLE IF EXISTS {table_name}"
            cursor.execute(drop_sql)
            print(f"🗑️ Dropped existing table {table_name}")
            
            # Create table dynamically based on DataFrame
            create_sql = f"CREATE TABLE {table_name} (\n"
            columns = []
            
            for col in df.columns:
                if col == 'import_timestamp':
                    columns.append(f"    {col} TIMESTAMP")
                else:
                    # Use TEXT for all data columns to avoid type issues
                    columns.append(f"    {col} TEXT")
            
            create_sql += ",\n".join(columns) + "\n)"
            cursor.execute(create_sql)
            print(f"✅ Created table {table_name}")
            
            # Insert data
            for index, row in df.iterrows():
                # Convert NaT and NaN to None for SQL NULL
                clean_row = []
                for value in row:
                    if pd.isna(value) or (hasattr(value, '__str__') and str(value) == 'NaT'):
                        clean_row.append(None)
                    else:
                        clean_row.append(value)
                
                placeholders = ', '.join(['%s'] * len(clean_row))
                insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                cursor.execute(insert_sql, tuple(clean_row))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Imported {len(df)} rows to {table_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error importing to PostgreSQL: {str(e)}")
            return False

    def run_daily_import(self):
        """Run the daily import process"""
        print("🚀 Starting Daily BI Import Process")
        print(f"📅 {datetime.now()}")
        print("-" * 60)
        
        # Step 1: Get access token
        if not self.get_access_token():
            print("❌ Failed to get access token")
            return False
        
        # Step 2: Get drive ID
        if not self.get_drive_id():
            print("❌ Failed to get drive ID")
            return False
        
        # Step 3: Process each target file
        success_count = 0
        for file_config in self.target_files:
            print(f"\n📂 Processing {file_config['filename']}...")
            
            # Download file
            temp_file_path = self.download_file(file_config)
            if temp_file_path:
                # Import to PostgreSQL
                if self.import_excel_to_postgres(temp_file_path, file_config):
                    success_count += 1
                    print(f"✅ Successfully processed {file_config['filename']}")
                else:
                    print(f"❌ Failed to import {file_config['filename']}")
                    
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                    print(f"🧹 Cleaned up temporary file")
                except Exception as e:
                    print(f"⚠️ Warning: Could not clean up temp file: {e}")
            else:
                print(f"❌ Failed to download {file_config['filename']}")
        
        print(f"\n📊 Import Summary: {success_count}/{len(self.target_files)} files processed successfully")
        
        if success_count == len(self.target_files):
            print("✅ Daily import completed successfully!")
            return True
        else:
            print("⚠️ Daily import completed with errors")
            return False

def main():
    """Main ETL process"""
    etl = SharePointETL()
    success = etl.run_daily_import()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
