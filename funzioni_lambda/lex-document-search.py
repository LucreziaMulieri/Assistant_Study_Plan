import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#client

logger.info("Module loading started")

dynamodb = boto3.resource("dynamodb")

logger.info("Boto3 client created")

#environment variables

COURSES_TABLE = os.getenv("COURSES_TABLE", "courses")

#dynamoDB table connection

table = dynamodb.Table(COURSES_TABLE)

#take values from the slots
def get_slot_values(slots, slot_name):
    slot = slots.get(slot_name)
    if not slot:
        return []
    value = slot.get("value", {})
    resolved = value.get("resolvedValues", [])
    if resolved:
        return resolved
    interpreted = value.get("interpretedValue")
    return [interpreted] if interpreted else []


def build_fulfillment_response(
    message: str,
    intent_name: str,
    session_attributes: dict,
    fulfillment_state: str = "Fulfilled",
) -> dict:
    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": intent_name,
                "state": fulfillment_state,
            },
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }


def normalize(text: str) -> str:
    """Normalize a string to lowercase and stripped for consistent comparison."""
    return text.lower().strip()


#gets information about the course

def get_course_info(course_name: str, specific: str = None) -> tuple[str, bool]:
    """
    Fetch course details from DynamoDB and format the response.
    Returns (message, found) so that client can manage correct state.
    """
    try:
        response = table.get_item(Key={"course_name": normalize(course_name)})
        item = response.get("Item")
    except Exception as e:
        logger.error(f"DynamoDB error for course '{course_name}': {e}")
        return (
            f"Sorry, I couldn't retrieve information about '{course_name}' at the moment.",
            False,
        )

    if not item:
        return f"Sorry, I don't have detailed information about '{course_name}'.", False

    display = item.get("display_name", course_name.title())

    # If the user asked for something specific
    if specific:
        specific_lower = normalize(specific)
        if any(w in specific_lower for w in ["exam", "test", "assessment", "evaluation"]):
            return f"Exam format for {display}:\n{item.get('exam_format', 'Information not available.')}", True
        if any(w in specific_lower for w in ["syllabus", "program", "content", "subjects"]):
            return f"Syllabus for {display}:\n{item.get('syllabus', 'not available')}", True
        if any(w in specific_lower for w in ["professor", "teacher", "instructor", "lecturer"]):
            return f"Professor for {display}: {item.get('professor', 'not available')}", True
        if any(w in specific_lower for w in ["prerequisite", "requirements", "required"]):
            prereqs = ", ".join(item.get("prerequisites", [])) or "none"
            return f"Prerequisites for {display}: {prereqs}", True
        if any(w in specific_lower for w in ["language", "taught in"]):
            return f"{display} is taught in: {item.get('language', 'not available')}", True
        if any(w in specific_lower for w in ["credit", "cfu", "ects"]):
            return f"{display} is worth {item.get('credits', 'n/a')} credits.", True

    # Full response if no specific info requested
    topics  = ", ".join(item.get("topics", [])) or "not specified"
    prereqs = ", ".join(item.get("prerequisites", [])) or "none"

    return (
        (
            f"{display} ({item.get('credits', '?')} credits)\n"
            f"Area: {item.get('area', 'n/a')}\n"
            f"Professor: {item.get('professor', 'n/a')}\n"
            f"Language: {item.get('language', 'n/a')}\n\n"
            f"Summary: {item.get('summary', 'n/a')}\n\n"
            f"Syllabus: {item.get('syllabus', 'n/a')}\n"
            f"Prerequisites: {prereqs}"
        ),
        True,
    )


def handle_specific_course(slots, session, intent: str) -> dict:
    path          = normalize(session.get("EducationalPathType", ""))
    master_year   = normalize(session.get("MasterYear", ""))
    bachelor_year = normalize(session.get("BachelorYear", ""))

    logger.info(f"Path: '{path}', MasterYear: '{master_year}', BachelorYear: '{bachelor_year}'")

    #if session attributes are missing
    if not path:
        logger.error("Missing session attribute: EducationalPathType")
        return build_fulfillment_response(
            "I'm sorry, something went wrong with your session. Please start over.",
            intent_name=intent,
            session_attributes=session,
            fulfillment_state="Failed",
        )

    # Pick the right slot based on educational path and year
    #master degree
    if path == "master degree":
        if master_year == "first year":
            course = get_slot_values(slots, "FirstYearMasterDegree")
        else:
            course = get_slot_values(slots, "SecondYearMasterDegree")
    else:  # bachelor degree
        if bachelor_year == "second year":
            course = get_slot_values(slots, "SecondYearBachelorDegree")
        else:
            course = get_slot_values(slots, "ThirdYearBachelorDegree")

    specific = get_slot_values(slots, "SpecificInformation")

    course_name   = course[0]   if course   else None
    specific_info = specific[0] if specific else None

    logger.info(f"Specific course request — course: {course_name}, specific: {specific_info}")

    if not course_name:
        updated_session = {
            **session,
            "CourseFound": "false",
            "CourseRequested": "",
        }
        return build_fulfillment_response(
            "Sorry, I couldn't identify the course you're interested in.",
            intent_name=intent,
            session_attributes=updated_session,
            fulfillment_state="Failed",
        )

    message, found = get_course_info(course_name, specific_info)

    updated_session = {
        **session,
        "CourseFound": "true" if found else "false",
        "CourseRequested": course_name,
    }

    return build_fulfillment_response(
        message,
        intent_name=intent,
        session_attributes=updated_session,
        fulfillment_state="Fulfilled" if found else "Failed",
    )

#handler

def lambda_handler(event, context=None):
    logger.info(f"Full event: {json.dumps(event)}")

    slots   = event["sessionState"]["intent"].get("slots", {})
    intent  = event["sessionState"]["intent"].get("name", "")
    session = event["sessionState"].get("sessionAttributes", {})

    logger.info(f"Intent: {intent}")
    logger.info(f"Session attributes: {json.dumps(session)}")
    logger.info(f"Slots: {json.dumps(slots)}")

    if intent == "Specific_Course":
        return handle_specific_course(slots, session, intent)

    logger.warning(f"Unhandled intent: {intent}")
    return build_fulfillment_response(
        "Sorry, I don't know how to handle this request.",
        intent_name=intent,
        session_attributes=session,
        fulfillment_state="Failed",
    )