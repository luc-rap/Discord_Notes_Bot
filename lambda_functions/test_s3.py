import boto3

s3 = boto3.client('s3')
BUCKET = 'dnd-notes-luciaw'

# upload a test file

with open('transcripts/fake-dnd-dialogue.txt', 'rb') as f:
    s3.put_object(Bucket=BUCKET, Key='transcripts/test.txt', Body=f)

print('File uploaded successfully.')

response = s3.get_object(Bucket=BUCKET, Key='transcripts/test.txt')
content = response['Body'].read().decode('utf-8')
print(f"Downloaded: {content}")

response = s3.list_objects_v2(Bucket=BUCKET, Prefix='transcripts/')
for obj in response.get('Contents', []):
    print(f"Found: {obj['Key']}")