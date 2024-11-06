import pandas as pd
import boto3
import os

# Initialize Pricing Client with the specified region
pricing_client = boto3.client('pricing', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Load VM Inventory Data
df = pd.read_csv("vm_inventory.csv")  # Ensure this file is copied to Docker container

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
    
    # Extract price
    for price_item in response['PriceList']:
        price_data = eval(price_item)
        on_demand = price_data['terms']['OnDemand']
        for term in on_demand.values():
            for price_dimension in term['priceDimensions'].values():
                return float(price_dimension['pricePerUnit']['USD'])
    
    return None

# Add cost data to each VM row
for index, row in df.iterrows():
    instance_type = row['instance_type']
    region = os.getenv('AWS_REGION', 'us-east-1')  # Use region from environment variable if available
    price = get_instance_pricing(instance_type, region)
    df.at[index, 'aws_cost'] = price

# Save for AWS Pricing Calculator upload
df.to_csv("aws_cost_estimate.csv", index=False)
print("CSV saved. Upload this to the AWS Pricing Calculator for final estimate and shareable link.")