from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from datetime import datetime, date, time
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, ActiveLoop
import re
from database_connection import DbReservationSave

def clean_text(form_text):
    return "".join([c for c in form_text if c.isalpha()])

def clean_numbers(form_numeric):
    return "".join([c for c in form_numeric if c.isnumeric()])

def remove_common_prefixes(name: str) -> str:
        name = re.sub(r"^(doctor|dr\.)\s*", "", name, flags=re.IGNORECASE)
        return name
    
def is_office_hours(time_str: str) -> bool:
    time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
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
            dispatcher.utter_message("Vă rog să introduceți o dată")
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
                    if input_month >= current_month:
                        validated_date = f"{current_year}-{parsed_date.month:02d}-{parsed_date.day:02d}"
                    else:
                        validated_date = f"{current_year + 1}-{parsed_date.month:02d}-{parsed_date.day:02d}"
                    return {"date": validated_date}

                except ValueError:
                    # Invalid date format
                    dispatcher.utter_message("Format invalid. Vă rugăm sa introduceți data sub următoarele forme: YYYY-MM-DD, DD/MM/YYYY, or DD.MM.")
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
            dispatcher.utter_message("Vă rog să introduceți ora")
            return {"time": None}
        try:
             # Try parsing time_format_1
            parsed_time = datetime.strptime(user_time, time_format_1).time()
            converted_time = parsed_time.strftime("%I:%M %p")
            
            if not is_office_hours(converted_time):
                dispatcher.utter_message("Orele de muncă sunt între 9-17. Vă rog să introduceți o oră în acest interval.")
                return {"time": None}

            return {"time": converted_time}


        except ValueError:
            try:
                # Try parsing time_format_2
                parsed_time = datetime.strptime(user_time, time_format_2).time()
                converted_time = parsed_time.strftime("%H:%M:%S")
                if not is_office_hours(converted_time):
                    dispatcher.utter_message("Orele de muncă sunt între 9-17. Vă rog să introduceți o oră în acest interval.")
                    return {"time": None}

                return {"time": converted_time}
            
            except ValueError:
                try:
                    # Try parsing time_format_3 (only hour provided)
                    parsed_time = datetime.strptime(user_time, time_format_3).time()
                    converted_time = parsed_time.replace(minute=0).strftime("%H:%M:%S")
                    if not is_office_hours(converted_time):
                        dispatcher.utter_message("Orele de muncă sunt între 9-17. Vă rog să introduceți o oră în acest interval.")
                        return {"time": None}

                    return {"time": converted_time}

                except ValueError:
                    # Invalid time format
                    dispatcher.utter_message("Format invalid. Vă rugăm sa introduceți ora sub următoarele forme HH:MM AM/PM, HH:MM, or HH.")
                    return {"time": None}
                
    def validate_doctor(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        if not slot_value:
            dispatcher.utter_message("Vă rugăm să introduceți numele medicului dorit.")
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
            dispatcher.utter_message("Vă rugăm să introduceți numele departmentului.")
            return {"department": None}
        
        if slot_value.lower() not in department_list:
            dispatcher.utter_message(
                "Departament invalid selectat. Puteți alege doar între: Cardiologie, Dermatologie, Ortopedie, Pediatrie, Neurologie, Medicina generala, Oftalmologie"
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
        if intent == "affirm":
            return{"weight_risk": True}
        elif intent == "deny":
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
        if intent == "affirm":
            return{"hypertension": True}
        elif intent == "deny":
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
        if intent == "affirm":
            return{"smoker": True}
        elif intent == "deny":
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
        if intent == "affirm":
            return{"recent_surgeries": True}
        elif intent == "deny":
            return{"recent_surgeries": False}
        return{"recent_surgeries":recent_surgeries}  
    
class CheckAppointmentFormFilled(Action):
    def name(self)->Text:
        return "action_check_appointment_form_filled"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        appointment_slots = ["date", "time", "doctor", "department"]
        if all(tracker.get_slot(slot) for slot in appointment_slots):
            # dispatcher.utter_message("utter_ask_additional_info1")
            return [SlotSet("slot_ask_for_second_form", True)]
        else:
            # First form is not filled yet
            return [SlotSet("slot_ask_for_second_form", False)]

class CheckExtraDetailsFormFilled(Action):
    def name(self)->Text:
        return "action_check_extra_details_form_filled"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name_slots = ["first_name", "last_name"]
        if all(tracker.get_slot(slot) for slot in name_slots):
            # dispatcher.utter_message("utter_ask_additional_info2")
            return [SlotSet("slot_ask_for_third_form", True)]
        else:
            # Appointment form is not filled yet
            return [SlotSet("slot_ask_for_third_form", False)]
        
class SaveAppointmentInDatabase(Action):
    def name(self)-> Text:
        return "action_save_in_database"
    
    
    def run(self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        connection = DbReservationSave()    
        cursor = connection.cursor()
        if self.allSlotsFilled(tracker):
            
            # dbs = DbReservationSave.execute('show databases')
            createPatientsTable = """CREATE TABLE IF NOT EXISTS patients(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, first_name varchar(255), last_name varchar(255))"""
            createDoctorsTable = """CREATE TABLE IF NOT EXISTS doctors(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, doctor_name varchar(255))"""
            createPatientExtraInfo = """CREATE TABLE IF NOT EXISTS patients_extra_info(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, patient_id INT, gender varchar(255), age INT, weight_risk varchar(255), hypertension varchar(255), smoker varchar(255), recent_surgeries varchar(255), FOREIGN KEY (patient_id) REFERENCES patients(id))"""
            createSpecialtiesTable = """CREATE TABLE IF NOT EXISTS medical_specialties(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, specialty varchar(255))"""
            createAppointmentsTable = """CREATE TABLE IF NOT EXISTS appointments(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, patient_id INT, date DATE, time TIME, doctor_id INT, specialty_id INT, FOREIGN KEY (patient_id) REFERENCES patients(id), FOREIGN KEY (specialty_id) REFERENCES medical_specialties(id), status varchar(255) DEFAULT 'active')"""
            
        
            cursor.execute(createPatientsTable)
            connection.commit()

            cursor.execute(createDoctorsTable)
            connection.commit()

            cursor.execute(createPatientExtraInfo)
            connection.commit()

            cursor.execute(createSpecialtiesTable)
            connection.commit()

            cursor.execute(createAppointmentsTable)
            connection.commit()

            # Extract from slots
            first_name = tracker.get_slot('first_name')
            last_name = tracker.get_slot('last_name')
            gender = tracker.get_slot('gender')
            age = tracker.get_slot('age')
            weight_risk = tracker.get_slot('weight_risk')
            hypertension = tracker.get_slot('hypertension')
            smoker = tracker.get_slot('smoker')
            recent_surgeries = tracker.get_slot('recent_surgeries')
            date = tracker.get_slot('date')
            time = tracker.get_slot('time')
            doctor = tracker.get_slot('doctor')
            department = tracker.get_slot('department')
        

            # Insert data into the 'patients' table
            insert_patient_query = """
            INSERT INTO patients (first_name, last_name)
            VALUES (%s, %s)
            """
            patient_data = (first_name, last_name)
            cursor.execute(insert_patient_query, patient_data)
            connection.commit()

            # Retrieve the auto-generated patient_id
            patient_id = cursor.lastrowid

            # Insert data into the 'patients_extra_info' table
            insert_extra_info_query = """
            INSERT INTO patients_extra_info (patient_id, gender, age, weight_risk, hypertension, smoker, recent_surgeries)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            extra_info_data = (patient_id, gender, age, weight_risk, hypertension, smoker, recent_surgeries)
            cursor.execute(insert_extra_info_query, extra_info_data)
            connection.commit()

            # Check if the doctor already exists
            select_doctor_query = "SELECT id FROM doctors WHERE doctor_name = %s"
            cursor.execute(select_doctor_query, (doctor,))
            existing_doctor = cursor.fetchone()

            if existing_doctor:
                # Doctor already exists, retrieve the doctor_id
                doctor_id = existing_doctor[0]
            else:
                # Insert data into the 'doctors' table
                insert_doctor_query = """
                INSERT INTO doctors (doctor_name)
                VALUES (%s)
                """
                cursor.execute(insert_doctor_query, (doctor,))
                connection.commit()

                # Retrieve the auto-generated doctor_id
                doctor_id = cursor.lastrowid

            # Check if the specialty already exists
            select_specialty_query = "SELECT id FROM medical_specialties WHERE specialty = %s"
            cursor.execute(select_specialty_query, (department,))
            existing_specialty = cursor.fetchone()

            if existing_specialty:
                # Specialty already exists, retrieve the specialty_id
                specialty_id = existing_specialty[0]
            else:
                # Insert data into the 'medical_specialties' table
                insert_specialty_query = """
                INSERT INTO medical_specialties (specialty)
                VALUES (%s)
                """
                cursor.execute(insert_specialty_query, (department,))
                connection.commit()

                # Retrieve the auto-generated specialty_id
                specialty_id = cursor.lastrowid

            # Insert data into the 'appointments' table
            insert_appointment_query = """
            INSERT INTO appointments (patient_id, date, time, doctor_id, specialty_id)
            VALUES (%s, %s, %s, %s, %s)
            """
            appointment_data = (patient_id, date, time, doctor_id, specialty_id)
            cursor.execute(insert_appointment_query, appointment_data)
            connection.commit()

            # Close the DbReservationSave and the connection
            cursor.close()
            connection.close()

            dispatcher.utter_message("Programare salvată cu succes.")
        else:
            dispatcher.utter_message("A apărut o eroare.")

        return []
    
    def allSlotsFilled(self, tracker: Tracker) -> bool:
        required_slots = ['first_name', 'last_name', 'gender', 'age', 'weight_risk', 'hypertension',
                          'recent_surgeries', 'date', 'time', 'doctor', 'department']

        for slot_name in required_slots:
            if tracker.get_slot(slot_name) is None:
                return False

        return True
    
class ValidationCancelAppointmentForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cancel_appointment_form"

    def validate_cancel_date(
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
            dispatcher.utter_message("Vă rog să introduceți o dată")
            return {"cancel_date": None}
        try:
            # Try parsing date using format1
            parsed_date = datetime.strptime(user_date, date_format1)
            validated_date = parsed_date.date().isoformat()
            return {"cancel_date": validated_date}

        except ValueError:
            try:
                # Try parsing date using format2
                parsed_date = datetime.strptime(user_date, date_format2)
                validated_date = parsed_date.date().isoformat()
                return {"cancel_date": validated_date}

            except ValueError:
                try:
                    # Try parsing date using format3
                    parsed_date = datetime.strptime(user_date, date_format3)
                    input_month = parsed_date.month
                    if input_month >= current_month:
                        validated_date = f"{current_year}-{parsed_date.month:02d}-{parsed_date.day:02d}"
                    else:
                        validated_date = f"{current_year + 1}-{parsed_date.month:02d}-{parsed_date.day:02d}"
                    return {"cancel_date": validated_date}

                except ValueError:
                    # Invalid date format
                    dispatcher.utter_message("Format invalid. Vă rugăm sa introduceți data sub următoarele forme: YYYY-MM-DD, DD/MM/YYYY, or DD.MM.")
                    return {"cancel_date": None}
    
    def validate_cancel_first_name(
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
            return {"cancel_first_name": None}
        return {"cancel_first_name": name}
    def validate_cancel_last_name(
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
            return{"cancel_last_name": None}
        first_name = tracker.get_slot("cancel_last_name")
        if len(first_name) + len(name) < 3:
            dispatcher.utter_message(
                text="Combinația nume/prenume este prea scurtă. Credem că s-a comis o eroare. Restartăm.")
            return {"cancel_first_name": None, "cancel_last_name": None}
        return {"cancel_last_name": name}
    
    def validate_cancel_department(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        department_list = ["cardiologie", "dermatologie", "ortopedie", "pediatrie", "neurologie", "medicina generala", "oftalmologie"]
        
        if not slot_value:
            dispatcher.utter_message("Vă rugăm să introduceți numele departmentului.")
            return {"cancel_department": None}
        
        if slot_value.lower() not in department_list:
            dispatcher.utter_message(
                "Departament invalid selectat. Puteți alege doar între: Cardiologie, Dermatologie, Ortopedie, Pediatrie, Neurologie, Medicina generala, Oftalmologie"
            )
            return {"cancel_department": None}

        return {"cancel_department": slot_value}
    
class CancelAppointmentInDatabase(Action):
    def name(self)->Text:
        return "action_cancel_appointment_in_database"
    
    def run(self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        connection = DbReservationSave()    
        cursor = connection.cursor()
        if self.allSlotsFilled(tracker):
            
            cancel_first_name = tracker.get_slot('cancel_first_name')
            cancel_last_name = tracker.get_slot('cancel_last_name')
            cancel_date = tracker.get_slot('cancel_date')
            cancel_department = tracker.get_slot('cancel_department')
            
            query = """
            UPDATE appointments AS a
            JOIN patients AS p ON a.patient_id = p.id
            JOIN doctors AS d ON a.doctor_id = d.id
            JOIN medical_specialties AS s ON a.specialty_id = s.id
            SET a.status = 'canceled'
            WHERE
                p.first_name = %s
                AND p.last_name = %s
                AND a.date = %s
                AND s.specialty = %s
                AND a.status = 'active'
                """
            cursor.execute(query, (cancel_first_name, cancel_last_name, cancel_date, cancel_department))
            if cursor.rowcount > 0:
                # Changes were made, appointment was found and canceled
                dispatcher.utter_message("Programare anulată cu succes")
            else:
                # No changes were made, appointment not found or already canceled
                dispatcher.utter_message("Nu există programări pentru această dată")
            connection.commit()
            
            cursor.close()
            connection.close()
        return [] 
    
    def allSlotsFilled(self, tracker: Tracker) -> bool:
        required_slots = ['cancel_first_name', 'cancel_last_name', 'cancel_date', 'cancel_department']

        for slot_name in required_slots:
            if tracker.get_slot(slot_name) is None:
                return False

        return True