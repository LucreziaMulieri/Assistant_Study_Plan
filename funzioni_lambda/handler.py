import json
import boto3
import os

lambda_client = boto3.client("lambda")

DOCUMENT_SEARCH = os.getenv("DOCUMENT_SEARCH",    "lex-document-search")
SELECTED_COURSES = os.getenv("SELECTED_COURSES", "courses-selction")



def _invoke(fn_name, event):
    resp = lambda_client.invoke(
        FunctionName=fn_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode("utf-8"),
    )

    if resp.get("FunctionError"):
        print(f"Error in Lambda function {fn_name}: {resp['Payload'].read()}")
        return {
            "sessionState": {"dialogAction": {"type": "ElicitIntent"}},
            "messages": [{
                "contentType": "PlainText",
                "content": "An error occurred, please try again.",
            }],
        }

    payload = resp["Payload"].read()
    return json.loads(payload.decode("utf-8") or "{}")


def lambda_handler(event, context):
    print(event)

    intent = (
        event.get("sessionState", {})
             .get("intent", {})
             .get("name", "")
    )
    
    if intent in ("Old_Choices_Second_Master", "Assistance_Choices_Courses"):
        return _invoke(SELECTED_COURSES, event)
    if intent == "Specific_Course":
        return _invoke(DOCUMENT_SEARCH, event)

    return {
        "sessionState": {"dialogAction": {"type": "ElicitIntent"}},
        "messages": [{
            "contentType": "PlainText",
            "content": (
                "Hello! Welcome to the help desk for computer and automation engineering courses, how can I help you? "
                "Do you need information on a specific course or assistance in composing a study plan?"
            ),
        }],
    }
