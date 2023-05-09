from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


def clean_text(form_text):
    return "".join([c for c in form_text if c.isalpha()])
def clean_numbers(form_numeric):
    return "".join([c for c in form_numeric if c.isnumeric()])


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

    def validate_age(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `age` value."""
        age = clean_numbers(slot_value)
        if (age <= 0 or age > 100 or isinstance(age, str)):
            dispatcher.utter_message(text = "Vă rog să introduceți o vârstă între 1-100 ani")
            return{"age":None}
        
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
            return{"age":None}
        if intent == "affirm":
            return{"weight_risk": True}
        elif intent == "deny":
            return{"weight_risk": False} 
    
    # def validate_hypertension()
    # def validate_smoker()
    # def validate_recent_lesions()
