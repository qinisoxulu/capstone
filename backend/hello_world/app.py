import json

def lambda_handler(event, context):
    person_id = event['queryStringParameters']['personId']
    return {
        "statusCode": 200,
        "body": json.dumps({
            "person_id": person_id + " from Lambda" ,
        }),
    }