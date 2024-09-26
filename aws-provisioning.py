import boto3
from datetime import datetime, timedelta

# Initialize AWS clients
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')
ce_client = boto3.client('ce')  # Cost Explorer client for billing information

# Function to check EC2 instance status
def check_ec2_status():
    instances = ec2_client.describe_instances()
    instance_data = []
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            state = instance['State']['Name']
            
            print(f"Instance ID: {instance_id}, Type: {instance_type}, State: {state}")
            
            instance_data.append({
                "instance_id": instance_id,
                "instance_type": instance_type,
                "state": state
            })
    
    return instance_data

# Function to check EC2 instance utilization
def check_ec2_utilization(instance_id):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)  # Check utilization for the last 24 hours
    
    response = cloudwatch_client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,  # Data points every hour
        Statistics=['Average']
    )
    
    if response['Datapoints']:
        average_utilization = sum([dp['Average'] for dp in response['Datapoints']]) / len(response['Datapoints'])
        print(f"Instance {instance_id} Average CPU Utilization (last 24h): {average_utilization:.2f}%")
        return average_utilization
    else:
        print(f"No utilization data available for instance {instance_id}")
        return None

# Function to check billing details for the past month
def check_billing():
    start_time = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_time = datetime.utcnow().strftime('%Y-%m-%d')
    
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_time,
            'End': end_time
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )
    
    cost = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
    print(f"Total cost for the last month: ${cost}")
    return float(cost)

# Main function
def main():
    # Check EC2 provisioning status
    instance_data = check_ec2_status()
    
    # Check utilization for each running instance
    for instance in instance_data:
        if instance['state'] == 'running':
            utilization = check_ec2_utilization(instance['instance_id'])
            if utilization is not None and utilization < 20:  # Example threshold
                print(f"Warning: Instance {instance['instance_id']} is underutilized with {utilization:.2f}% CPU.")
    
    # Check billing information
    total_cost = check_billing()
    print(f"Customer has been billed ${total_cost:.2f} in the past month.")
    
if __name__ == "__main__":
    main()
