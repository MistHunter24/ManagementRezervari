from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from datetime import datetime, date
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
import re
from datetime import datetime, time

def clean_text(form_text):
    return "".join([c for c in form_text if c.isalpha()])

def clean_numbers(form_numeric):
    return "".join([c for c in form_numeric if c.isnumeric()])

def remove_common_prefixes(name: str) -> str:
        name = re.sub(r"^(doctor|dr\.)\s*", "", name, flags=re.IGNORECASE)
        return name
    
def is_office_hours(time_str: str) -> bool:
    time_obj = datetime.strptime(time_str, "%H:%M").time()
    office_start = time(9, 0)  # Office hours start time
    office_end = time(17, 0)  # Office hours end time

    if office_start <= time_obj <= office_end:
        return True
    else:
        return False


class ValidationBookAppointmentForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_appointment_form"

    def validate_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        user_date = tracker.get_slot("date")
        current_month = date.today().month
        current_year = date.today().year
        date_format1 = "%Y-%m-%d"  # Date format: YYYY-MM-DD
        date_format2 = "%d/%m/%Y"  # Date format: DD/MM/YYYY
        date_format3 = "%d.%m"  # Date format: DD.MM

        if not slot_value:
            dispatcher.utter_message("Please provide a date.")
            return {"date": None}
        try:
            # Try parsing date using format1
            parsed_date = datetime.strptime(user_date, date_format1)
            validated_date = parsed_date.date().isoformat()
            return {"date": validated_date}

        except ValueError:
            try:
                # Try parsing date using format2
                parsed_date = datetime.strptime(user_date, date_format2)
                validated_date = parsed_date.date().isoformat()
                return {"date": validated_date}

            except ValueError:
                try:
                    # Try parsing date using format3
                    parsed_date = datetime.strptime(user_date, date_format3)
                    input_month = parsed_date.month
                    if input_month > current_month:
                        validated_date = f"{parsed_date.day:02d}-{parsed_date.month:02d}-{current_year}"
                    else:
                        validated_date = f"{parsed_date.day:02d}-{parsed_date.month:02d}-{current_year + 1}"
                    return {"date": validated_date}

                except ValueError:
                    # Invalid date format
                    dispatcher.utter_message("Invalid date format. Please provide a date in the format YYYY-MM-DD, DD/MM/YYYY, or DD.MM.")
                    return {"date": None}
                
    def validate_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        user_time = tracker.get_slot("time")
        time_format_1 = "%I:%M %p"  # Time format: HH:MM AM/PM
        time_format_2 = "%H:%M"  # Time format: HH:MM
        time_format_3 = "%H"  # Time format: HH

        if not slot_value:
            dispatcher.utter_message("Please provide a time.")
            return {"time": None}
        try:
             # Try parsing time_format_1
            parsed_time = datetime.strptime(user_time, time_format_1).time()
            converted_time = parsed_time.strftime("%I:%M %p")

            if not is_office_hours(converted_time):
                dispatcher.utter_message("Office hours are from 9 AM to 5 PM. Please provide a time within office hours.")
                return {"time": None}

            return {"time": converted_time}


        except ValueError:
            try:
                # Try parsing time_format_2
                parsed_time = datetime.strptime(user_time, time_format_2).time()
                converted_time = parsed_time.strftime("%H:%M")
                if not is_office_hours(converted_time):
                    dispatcher.utter_message("Office hours are from 9 AM to 5 PM. Please provide a time within office hours.")
                    return {"time": None}

                return {"time": converted_time}
            
            except ValueError:
                try:
                    # Try parsing time_format_3 (only hour provided)
                    parsed_time = datetime.strptime(user_time, time_format_3).time()
                    converted_time = parsed_time.replace(minute=0).strftime("%H:%M")
                    if not is_office_hours(converted_time):
                        dispatcher.utter_message("Office hours are from 9 AM to 5 PM. Please provide a time within office hours.")
                        return {"time": None}

                    return {"time": converted_time}

                except ValueError:
                    # Invalid time format
                    dispatcher.utter_message("Invalid time format. Please provide a time in the format HH:MM AM/PM, HH:MM, or HH.")
                    return {"time": None}
                
    def validate_doctor(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if not slot_value:
            dispatcher.utter_message("Please provide the name of the doctor.")
            return {"doctor": None}

        cleaned_name = remove_common_prefixes(slot_value)

        return {"doctor": cleaned_name}
    
    def validate_department(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        department_list = ["cardiologie", "dermatologie", "ortopedie", "pediatrie", "neurologie", "medicina generala", "oftalmologie"]
        
        if not slot_value:
            dispatcher.utter_message("Please provide the name of the department.")
            return {"department": None}
        
        if slot_value.lower() not in department_list:
            dispatcher.utter_message(
                "Invalid department selected. Please select a department from the provided list."
            )
            return {"department": None}

        return {"department": slot_value}
        