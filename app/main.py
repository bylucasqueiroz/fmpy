import pandas as pd
import re

from datetime import datetime
from fastapi import FastAPI, HTTPException
from app.google_drive import download_csv, list_files_in_folder, upload_csv

app = FastAPI()

GOOGLE_DRIVE_FOLDER_ID = "MY_ID"

@app.get("/")
async def read_root():
    return {"message": "Welcome to the CSV API using Google Drive"}

@app.get("/generate_expense/")
async def generate_expense():
    try:
        # Get current and next month names
        current_month_name = datetime.now().strftime("%B").lower()  # Current month in lowercase
        next_month_name = (datetime.now().month % 12) + 1  # Calculate next month
        next_month_name = datetime(datetime.now().year, next_month_name, 1).strftime("%B").lower()  # Get next month name

        # Download CSV content for the current month
        csv_content = download_csv(current_month_name, GOOGLE_DRIVE_FOLDER_ID)
        
        # Read the CSV content into a DataFrame
        df = pd.read_csv(csv_content)
        
        # Clean the DataFrame: Replace NaN and infinite values
        df = df.replace([float('inf'), float('-inf')], None)  # Replace inf/-inf with None
        df = df.where(pd.notnull(df), None)  # Replace NaN with None

        # Filter out rows where current installment equals final installment
        def extract_data(entry):
            """Extract actual and number of installments from the entry."""
            actual = 1
            installments = 1
            
            # Regular expression to match the pattern "xx/yy"
            pattern = r'(\d{2})/(\d{2})'
            match = re.search(pattern, entry)

            if match:
                actual = int(match.group(1))  # Actual number
                installments = int(match.group(2))  # Number of installments

            return actual, installments

        # Add new columns for installments
        df['CurrentInstallment'] = 1  # Default value
        df['FinalInstallment'] = 1  # Default value

        # Process each row and update the installments
        for index, row in df.iterrows():
            entry = row.get("Description")  # Replace 'Description' with the actual column name
            if entry:
                current_installment, final_installment = extract_data(entry)
                df.at[index, 'CurrentInstallment'] = current_installment
                df.at[index, 'FinalInstallment'] = final_installment
        
        # Filter out rows where CurrentInstallment equals FinalInstallment
        df_filtered = df[~(df['CurrentInstallment'] == df['FinalInstallment'])]

        # Save the filtered DataFrame to a new CSV file
        output_csv_path = f"{next_month_name}.csv"
        df_filtered.to_csv(output_csv_path, index=False)

        # Upload the new CSV to Google Drive
        upload_csv(output_csv_path, next_month_name, GOOGLE_DRIVE_FOLDER_ID)

        return {"message": f"Filtered CSV for {next_month_name} created successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/current_expense/")
async def get_current_expense():
    try:
        # Get Year
        current_year = datetime.year

        # Get actual month
        current_month_name = datetime.now().strftime("%B")

        folder_name = f'${current_year}_${current_month_name}'

        # Download CSV content from Google Drive
        csv_content = download_csv(folder_name, GOOGLE_DRIVE_FOLDER_ID)
        
        # Read the CSV content into a DataFrame
        df = pd.read_csv(csv_content)
        
        # Clean the DataFrame: Replace NaN and infinite values
        df = df.replace([float('inf'), float('-inf')], None)  # Replace inf/-inf with None
        df = df.where(pd.notnull(df), None)  # Replace NaN with None

        # Convert the DataFrame to a list of dictionaries
        data = df.to_dict(orient="records")

        def extract_data(entry):
            """Extract actual and number of installments from the entry."""
            actual = 1
            installments = 1
            
            # Regular expression to match the pattern "xx/yy"
            pattern = r'(\d{2})/(\d{2})'
            match = re.search(pattern, entry)

            if match:
                actual = int(match.group(1))  # Actual number
                installments = int(match.group(2))  # Number of installments

            return actual, installments

        # Process each entry in the data
        for d in data:
            entry = d.get("Description")  # Replace 'column_name' with the actual column name containing the data
            if entry:
                current_installment, final_installment = extract_data(entry)
                d["CurrentInstallment"] = current_installment
                d["FinalInstallment"] = final_installment
        
        return data  # Returning JSON by default

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_files/")
async def list_files():
    try:
        # List all files in the specified folder
        files = list_files_in_folder(GOOGLE_DRIVE_FOLDER_ID)

        return files  # Return the list of files as JSON

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))