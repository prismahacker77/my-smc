import pandas as pd
import boto3
import os

# Initialize Pricing Client with the specified region
pricing_client = boto3.client('pricing', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Load the second sheet ("Inputs") without modifying the existing format
file_path = "vm_inventory.xlsx"  # Ensure this file is copied to Docker container
df = pd.read_excel(file_path, sheet_name="Inputs")  # Load the "Inputs" sheet

# Keep original columns intact; add only additional columns for AWS cost
df['aws_cost_per_instance'] = None
df['total_cost'] = None

# Function to get pricing for a given instance type
def get_instance_pricing(instance_type, region="us-east-1"):
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
            {"Type": "TERM_MATCH", "Field": "location", "Value": region}
        ],
        MaxResults=1
    )
    
    # Extract price from response
    for price_item in response['PriceList']:
        price_data = eval(price_item)
        on_demand = price_data['terms']['OnDemand']
        for term in on_demand.values():
            for price_dimension in term['priceDimensions'].values():
                return float(price_dimension['pricePerUnit']['USD'])
    
    return None

# Loop through each row (starting from row 4) and calculate AWS costs based on the instance type
for index, row in df.iterrows():
    # Skip header or unrelated rows
    if pd.isna(row['Instance_Type']):  # Ensure 'Instance_Type' is the correct column name
        continue

    instance_type = row['Instance_Type']
    region = row['AWS Region \n']  # Adjust this if the actual column name differs in structure

    # Get pricing and calculate total cost
    price = get_instance_pricing(instance_type, region)
    df.at[index, 'aws_cost_per_instance'] = price
    
    # Calculate total cost based on number of instances if available
    if pd.notna(row['Number of Instances']):
        df.at[index, 'total_cost'] = price * row['Number of Instances']
    else:
        df.at[index, 'total_cost'] = price

# Save to output folder without altering the original file format
output_path = "/app/output/aws_cost_estimate.csv"
df.to_csv(output_path, index=False)
print(f"CSV saved to {output_path}. Upload this to the AWS Pricing Calculator for final estimate and shareable link.")