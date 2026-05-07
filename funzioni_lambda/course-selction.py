import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("Module loading started")
#client
lex_client = boto3.client("lexv2-models")

logger.info("Boto3 client created")

#enviroment variables
try:
    BOT_ID = os.environ["BOT_ID"]
    logger.info(f"BOT_ID loaded: {BOT_ID}")
except KeyError:
    raise EnvironmentError("Missing required environment variable: BOT_ID")

BOT_VERSION = os.getenv("BOT_VERSION", "DRAFT")
LOCALE_ID   = os.getenv("LOCALE_ID",   "en_US")

SLOT_TYPE_ID_B2 = os.getenv("SLOT_TYPE_ID_B2")
SLOT_TYPE_ID_B3 = os.getenv("SLOT_TYPE_ID_B3")
SLOT_TYPE_ID_M1 = os.getenv("SLOT_TYPE_ID_M1")
SLOT_TYPE_ID_M2 = os.getenv("SLOT_TYPE_ID_M2")

#cache manage
_courses_cache = {}

#gets courses from lex slots
def get_courses_from_lex(slot_type_id: str) -> list:
    if not slot_type_id:
        return []
    if slot_type_id in _courses_cache:
        return _courses_cache[slot_type_id]
    try:
        response = lex_client.describe_slot_type(
            botId=BOT_ID,
            botVersion=BOT_VERSION,
            localeId=LOCALE_ID,
            slotTypeId=slot_type_id,
        )
        values = [v["sampleValue"]["value"] for v in response.get("slotTypeValues", [])]
        _courses_cache[slot_type_id] = values
        return values
    except Exception as e:
        logger.error(f"describe_slot_type failed for slot_type_id={slot_type_id}: {e}")
        return []


def get_all_courses() -> dict:
    return {
        "bachelor_year_2": get_courses_from_lex(SLOT_TYPE_ID_B2),
        "bachelor_year_3": get_courses_from_lex(SLOT_TYPE_ID_B3),
        "master_year_1":   get_courses_from_lex(SLOT_TYPE_ID_M1),
        "master_year_2":   get_courses_from_lex(SLOT_TYPE_ID_M2),
    }

#gets values from slots
def get_slot_values(slots, slot_name):
    slot = slots.get(slot_name)
    if not slot:
        return []

    
    values = slot.get("values")
    if values:
        result = []
        for v in values:
            val = v.get("value", {})
            resolved = val.get("resolvedValues", [])
            if resolved:
                result.append(resolved[0])
            else:
                interpreted = val.get("interpretedValue")
                if interpreted:
                    result.append(interpreted)
        return result

    
    value = slot.get("value", {})
    resolved = value.get("resolvedValues", [])
    if resolved:
        return resolved
    interpreted = value.get("interpretedValue")
    return [interpreted] if interpreted else []


def build_close_response(
    message: str,
    intent_name: str,
    session_attributes: dict = None,
    fulfillment_state: str = "Fulfilled",
) -> dict:
    return {
        "sessionState": {
            "sessionAttributes": session_attributes or {},
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": intent_name,
                "state": fulfillment_state,
            },
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }


def format_list(items: list) -> str:
    return ", ".join(items) if items else "none"


def normalize(text: str) -> str:
    """Normalize a course name to lowercase and stripped for consistent comparison."""
    return text.lower().strip()


# Keys are already lowercase — normalize() on input will match reliably
AREA_MAP = {
    "cybersecurity for networks":                                "cybersecurity",
    "ethical hacking":                                           "cybersecurity",
    "advanced programming": "cybersecurity",
    "software security and blockchain": "cybersecurity",
    "advanced cybersecurity for it":                             "cybersecurity",
    "big data analytics and machine learning":                   "ai_ml",
    "computer vision and deep learning":                         "ai_ml",
    "artificial intelligence":                                   "ai_ml",
    "digital adaptive circuits and learning systems":            "ai_ml",
    "data science":                                              "ai_ml",
    "new generation databases":                                  "ai_ml",
    "computer graphics and multimedia":                          "ai_ml",
    "nonlinear control":                                         "automatica",
    "dynamics and control of intelligent robots and vehicles":   "automatica",
    "optimal filtering and control of stochastic processes":     "automatica",
    "mechanics of automatic machinery":                          "automatica",
    "advanced control, optimization and process analysis":        "automatica",
    "laboratory of mechatronics and cyber-physical systems":     "automatica",
    "drive systems for automation and robotics":                 "automatica",
    "special purpose operating systems":                         "automatica",
    "industrial automation":                                     "automatica",
    "modeling and identification of dynamic processes":          "automatica",
    "computer aided control design":                             "automatica",
    "digital control systems":                                   "automatica",
    "automation laboratory":                                     "automatica",
}

# All course names stored in lowercase for consistent comparison and suggestion
AREA_SUGGESTIONS = {
    "cybersecurity": {
        "master_year_1":   ["cybersecurity for networks", "ethical hacking",
                            "advanced programming", "software security and blockchain"],
        "master_year_2":   ["advanced cybersecurity for it", "special purpose operating systems"],
        "bachelor_year_3": ["operating systems", "computer architecture and cloud computing"],
        "bachelor_year_2" : ["software engineering", "algebra and logics", "probability and statistics"],
    },
    "ai_ml": {
        "master_year_1":   ["big data analytics and machine learning",
                            "computer vision and deep learning", "artificial intelligence",
                            "digital adaptive circuits and learning systems"],
        "master_year_2":   ["data science", "new generation databases",
                            "computer graphics and multimedia"],
        "bachelor_year_3": ["databases", "web technologies", "mobile programming"],
        "bachelor_year_2" : ["software engineering", "algebra and logics", "probability and statistics"],
    },
    "automatica": {
        "master_year_1":   ["nonlinear control",
                            "dynamics and control of intelligent robots and vehicles",
                            "optimal filtering and control of stochastic processes",
                            "mechanics of automatic machinery"],
        "master_year_2":   ["advanced control", "optimization and process analysis",
                            "laboratory of mechatronics and cyber-physical systems",
                            "drive systems for automation and robotics"],
        "bachelor_year_3": ["industrial automation", "digital control systems",
                            "modeling and identification of dynamic processes",
                            "computer aided control design", "automation laboratory"],
        "bachelor_year_2" : ["mathematical methods for automation engineering", "numerical analysis", "analytical mechanics"],
    },
}

AREA_LABELS = {
    "cybersecurity": "Cybersecurity",
    "ai_ml":         "AI / Machine Learning",
    "automatica":    "Automatica and Control",
}


#detect the areas
def detect_areas(chosen_courses: list) -> set:
    areas = set()
    for course in chosen_courses:
        area = AREA_MAP.get(normalize(course))
        if area:
            areas.add(area)
    return areas


def _get_candidates(areas: set, year_key: str, chosen_lower: set) -> list:
    """Return suggested courses for the given areas and year, excluding already chosen ones."""
    candidates = []
    for area in areas:
        for course in AREA_SUGGESTIONS.get(area, {}).get(year_key, []):
            if course not in chosen_lower:
                candidates.append(course.title())
    return candidates

#build the response based on the slots
def _build_lines(slots, session, include_bachelor_y3: bool, include_master_y1: bool, include_bachelor_y2: bool) -> list:
    """
    Unified builder for response lines.
    Reads course data from sessionAttributes, flags from slots or sessionAttributes
    depending on the intent.
    """

    def get_session_courses(key: str) -> list:
        value = session.get(key, "")
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    m2 = get_session_courses("ChosenCoursesSecondYearMaster")
    m1 = get_session_courses("ChosenCourseFirstYear")           if include_master_y1   else []
    b3 = get_session_courses("ChosenCoursesThirdYear")          if include_bachelor_y3 else []
    b2 = get_session_courses("ChosenCoursesSecondYearBachelor") if include_bachelor_y2 else []

    all_chosen   = m2 + m1 + b3 + b2
    areas        = detect_areas(all_chosen)
    chosen_lower = {normalize(c) for c in all_chosen}

    lines = []

    # Master year 2 
    candidates = _get_candidates(areas, "master_year_2", chosen_lower)
    lines.append(
        f"Since you're interested in {format_list(m2)} for your second year of your master's degree, "
        f"you could choose from the following courses: {format_list(candidates)}."
    )

    # Master year 1
    candidates = _get_candidates(areas, "master_year_1", chosen_lower)
    if include_master_y1:
        lines.append(
            f"Since you took (or intend to take) {format_list(m1)} for your first year of your master's degree, "
            f"you could choose from: {format_list(candidates)}."
        )
    else:
        lines.append(
            f"Since you haven't specified any courses for the first year of your master's degree, "
            f"you could choose from the following: {format_list(candidates)}."
        )

    # Bachelor year 3
    candidates = _get_candidates(areas, "bachelor_year_3", chosen_lower)
    if include_bachelor_y3:
        lines.append(
            f"For your third year of your bachelor's degree, you said you're interested in {format_list(b3)}, "
            f"you could opt for: {format_list(candidates)}."
        )
    else:
        lines.append(
            f"Since you haven't specified any courses for the third year of your bachelor's degree, "
            f"you could choose from the following: {format_list(candidates)}."
        )

    # Bachelor year 2
    candidates = _get_candidates(areas, "bachelor_year_2", chosen_lower)
    if include_bachelor_y2:
        lines.append(
            f"For your second year of your bachelor's degree, you're interested in {format_list(b2)}, "
            f"you could choose from the following: {format_list(candidates)}."
        )
    else:
        lines.append(
            f"Since you haven't specified any courses for the second year of your bachelor's degree, "
            f"you could choose from the following: {format_list(candidates)}."
        )

    return lines


#handler
def lambda_handler(event, context=None):
    logger.info(f"Full event: {json.dumps(event)}")

    slots   = event["sessionState"]["intent"].get("slots", {})
    intent  = event["sessionState"]["intent"].get("name", "")
    session = event["sessionState"].get("sessionAttributes", {})

    logger.info(f"Intent: {intent}")
    logger.info(f"Session attributes: {json.dumps(session)}")
    logger.info(f"Slots: {json.dumps(slots)}")

    def read_yes_session(key: str) -> bool:
        value = session.get(key, "")
        return normalize(value) in ("yes", "sì", "si", "true")

    #read the slots and update the session
    def merge_courses_from_slot(slot_name: str, session_key: str) -> dict:
        """
        read the multi-value from the slots and adds it to the session,
        merging the ones already existing.
        """
        from_slot = get_slot_values(slots, slot_name)
        if not from_slot:
            return {}
        existing = [v.strip() for v in session.get(session_key, "").split(",") if v.strip()]
        merged = list(dict.fromkeys(existing + from_slot))  #remove duplicates while preserving order
        return {session_key: ", ".join(merged)}

    updated_session = {
        **session,
        **merge_courses_from_slot("SecondYearMasterDegree",  "ChosenCoursesSecondYearMaster"),
        **merge_courses_from_slot("FirstYearMasterDegree",   "ChosenCourseFirstYear"),
        **merge_courses_from_slot("ThirdYearBachelorDegree", "ChosenCoursesThirdYear"),
        **merge_courses_from_slot("SecondYearBachelorDegree","ChosenCoursesSecondYearBachelor"),
    }

    if intent == "Assistance_Choices_Courses":
        return build_close_response(
            "\n".join(_build_lines(
                slots, updated_session,
                include_bachelor_y3=False,
                include_master_y1=read_yes_session("PossibleCoursesFirstYear"),
                include_bachelor_y2=read_yes_session("PossibleCoursesSecondYear"),
            )),
            intent_name=intent,
            session_attributes=updated_session,
        )

    if intent == "Old_Choices_Second_Master":
        return build_close_response(
            "\n".join(_build_lines(
                slots, updated_session,
                include_bachelor_y3=read_yes_session("PossibleCoursesThirdYear"),
                include_master_y1=read_yes_session("PossibleCoursesFirstYear"),
                include_bachelor_y2=read_yes_session("PossibleCoursesSecondYear"),
            )),
            intent_name=intent,
            session_attributes=updated_session,
        )

    logger.warning(f"Unhandled intent: {intent}")
    return build_close_response(
        "Sorry, I don't know how to handle this request.",
        intent_name=intent,
        session_attributes=updated_session,
        fulfillment_state="Failed",
    )