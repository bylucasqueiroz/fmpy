import pandas as pd
import re
import os

from datetime import datetime
from fastapi import FastAPI, HTTPException
from app.google_drive import download_csv, list_files_in_folder, upload_csv
from app.helper import get_file_name, clen_file

app = FastAPI()

GOOGLE_DRIVE_FOLDER_ID = "MY_ID"

@app.get("/")
async def read_root():
    return {"message": "Welcome to the CSV API using Google Drive"}

@app.get("/generate_expense_report/")
async def generate_expense_report(person: str = None, category: str = None, payment_type: str = None):
    try:
        # Get the current month and year
        current_month_name = datetime.now().strftime("%B").lower()
        current_year = datetime.now().year
        file_name = f"{current_year}_{current_month_name}"
        
        # Download CSV content from Google Drive
        csv_content = download_csv(file_name, GOOGLE_DRIVE_FOLDER_ID)
        
        # Read the CSV content into a DataFrame
        df = pd.read_csv(csv_content)
        
        # Clean the DataFrame: Replace NaN and infinite values
        df = df.replace([float('inf'), float('-inf')], None)  # Replace inf/-inf with None
        df = df.where(pd.notnull(df), None)  # Replace NaN with None

        # Filter by person and category if provided
        if person:
            df = df[df['Person'] == person]
        if category:
            df = df[df['Category'] == category]
        if payment_type:
            df = df[df['PaymentType'] == payment_type]

        # Clean the 'Amount' column: Remove 'R$ ' and commas, then convert to float
        df['Amount'] = df['Amount'].replace({'R\$ ': '', '\.': '', ',': '.'}, regex=True).astype(float)

        # Group by ExpenseType and calculate the total Amount
        result = df.groupby('ExpenseType')['Amount'].sum().reset_index()

        # Convert the result to a list of dictionaries for JSON response
        result_json = result.to_dict(orient='records')

        # Generate the result CSV file
        result_file_name = f"{current_year}_{current_month_name}_result"
        
        # Check if the result file already exists
        existing_files = list_files_in_folder(GOOGLE_DRIVE_FOLDER_ID)
        existing_file = next((f for f in existing_files if f['name'] == result_file_name), None)

        if existing_file:
            # Update the existing file
            file_id = existing_file['id']
            # Save the result to a local CSV file first
            result.to_csv(result_file_name, index=False)
            upload_csv(result_file_name, GOOGLE_DRIVE_FOLDER_ID, file_id)
        else:
            # Create a new file
            result.to_csv(result_file_name, index=False)
            upload_csv(result_file_name, GOOGLE_DRIVE_FOLDER_ID)

        clen_file(result_file_name)

        # Return the result in JSON format
        return {"message": "Expense report generated successfully", "data": result_json}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/generate_expense/")
async def generate_expense():
    try:
        last_month_name = (datetime.now().month % 12) - 1  # Calculate last month
        last_month_name = datetime(datetime.now().year, last_month_name, 1).strftime("%B").lower() 
        
        # Get current and next month names
        current_month_name = datetime.now().strftime("%B").lower()  # Current month in lowercase

        # Get Year
        current_year = datetime.now().strftime("%Y")

        # Download CSV content from Google Drive
        csv_content = download_csv(get_file_name(current_year, last_month_name), GOOGLE_DRIVE_FOLDER_ID)
        
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
        df_filtered = df[~(df['CurrentInstallment'] == df['FinalInstallment']) | (df['ExpenseType'] == 'Fixed')]

        # Save the filtered DataFrame to a new CSV file
        output_csv_path = get_file_name(current_year, current_month_name)
        df_filtered.to_csv(output_csv_path, index=False)

        # Upload the new CSV to Google Drive
        upload_csv(output_csv_path, GOOGLE_DRIVE_FOLDER_ID)

        clen_file(output_csv_path)

        return {"message": f"Filtered CSV for {output_csv_path} created successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/current_expense/")
async def get_current_expense():
    try:
        # Get Year
        current_year = datetime.now().strftime("%Y")

        # Get actual month
        current_month_name = datetime.now().strftime("%B").lower()

        # Download CSV content from Google Drive
        csv_content = download_csv(get_file_name(current_year, current_month_name), GOOGLE_DRIVE_FOLDER_ID)
        
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