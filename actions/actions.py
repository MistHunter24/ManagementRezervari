from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from datetime import datetime, date
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, ActiveLoop
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
        
class ValidationNameForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_name_form"
    def validate_first_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `first_name` value."""
        # We check for super short first_names
        name = clean_text(slot_value)
        if len(name) == 0:
            dispatcher.utter_message(text="Cred că ați greșit.")
            return {"first_name": None}
        return {"first_name": name}
    def validate_last_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `last_name` value."""
        name = clean_text(slot_value)
        if len(name) == 0:
            dispatcher.utter_message(text="Cred că ați greșit.")
            return{"last_name": None}
        first_name = tracker.get_slot("first_name")
        if len(first_name) + len(name) < 3:
            dispatcher.utter_message(
                text="Combinația nume/prenume este prea scurtă. Credem că s-a comis o eroare. Restartăm.")
            return {"first_name": None, "last_name": None}
        return {"last_name": name}
   
class ValidationPreliminaryQuestionForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_preliminary_questions_form"
    def validate_gender(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `gender` value."""
        gender = clean_text(slot_value)
        if len(gender) == 0:
            dispatcher.utter_message(text="Ați uitat sa completați sexul")
            return{"gender": None}
        return{"gender":gender}
    def validate_age(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `age` value."""
        age = clean_numbers(slot_value)
        if (int(age) <= 0 or int(age) > 100):
            dispatcher.utter_message(text = "Vă rog să introduceți o vârstă între 1-100 ani")
            return{"age":None}
        if (int(age) is None):
            dispatcher.utter_message(text = "Vă rog să introduceți o vârstă în cifre")
            return{"age":None}
        return{"age":age}
        
    def validate_weight_risk(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `weight_risk` value"""
        intent = tracker.latest_message["intent"].get("name")
        weight_risk = clean_text(slot_value)
        if len(weight_risk) == 0:
            dispatcher.utter_message(text = "Vă rog să răspundeți cu DA sau NU")
            return{"weight_risk":None}
        if intent == "weight_risk ":
            substring = "da"
            if substring in weight_risk:
                return{"weight_risk": True}
            else:
                return{"weight_risk": False} 
        return{"weight_risk":weight_risk}
    
    def validate_hypertension(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `hypertension` value"""
        intent = tracker.latest_message["intent"].get("name")
        hypertension = clean_text(slot_value)
        if len(hypertension) == 0:
            dispatcher.utter_message(text = "Vă rog să răspundeți cu DA sau NU")
            return{"hypertension":None}
        if intent == "hypertension":
            substring = "da"
            if substring in hypertension:
                return{"hypertension": True}
            else:
                return{"hypertension": False}
        return{"hypertension":hypertension}
    
    def validate_smoker(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `smoker` value"""
        intent = tracker.latest_message["intent"].get("name")
        smoker = clean_text(slot_value)
        if len(smoker) == 0:
            dispatcher.utter_message(text = "Vă rog să răspundeți cu DA sau NU")
            return{"smoker":None}
        if intent == "smoker":
            substring = "da"
            if substring in smoker:
                return{"smoker": True}
            else:
                return{"smoker": False}
        return{"smoker":smoker}    
        
    def validate_recent_surgeries(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `recent_surgeries` value"""
        intent = tracker.latest_message["intent"].get("name")
        recent_surgeries = clean_text(slot_value)
        if len(recent_surgeries) == 0:
            dispatcher.utter_message(text = "Vă rog să răspundeți cu DA sau NU")
            return{"recent_surgeries":None}
        elif intent == "recent_surgeries":
            substring = "da"
            if substring in recent_surgeries:
                return{"recent_surgeries": True}
            else:
                return{"recent_surgeries": False}
        return{"recent_surgeries":recent_surgeries}  
    
class CheckAppointmentFormFilled(Action):
    def name(self)->Text:
        return "action_check_appointment_form_filled"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        appointment_slots = ["date", "time", "doctor", "department"]
        if all(tracker.get_slot(slot) for slot in appointment_slots):
            dispatcher.utter_message("utter_ask_additional_info1")
            return [SlotSet("slot_ask_for_second_form", True)]
        else:
            # First form is not filled yet
            return [SlotSet("slot_ask_for_second_form", False)]

class CheckExtraDetailsFormFilled(Action):
    def name(self)->Text:
        return "action_check_extra_details_form_filled"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if (tracker.get_slot("slot_ask_for_second_form")== True):
            dispatcher.utter_message("utter_ask_additional_info2")
            return [SlotSet("slot_ask_for_third_form", True)]
        else:
            # Appointment form is not filled yet
            return [SlotSet("slot_ask_for_third_form", False)]
        
