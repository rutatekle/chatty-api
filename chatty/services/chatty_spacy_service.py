import random
import re
import spacy
import json
import os
from typing import List, Tuple, Dict

from chatty.database.chatty_db import ChattyDatabase


class ChattySpacyService:

    def __init__(self, conn):
        self.chatty_database = ChattyDatabase(conn)

    @staticmethod
    def load_nlp():
        return spacy.load("en_core_web_md")

    @staticmethod
    def get_docx_and_docy(nlp) -> Tuple:
        docs_x = []
        docs_y = []

        absolute_path = f'{os.path.dirname(__file__)}/../data/intents2.json'

        with open(absolute_path) as file:
            intent_data = json.load(file)

        for intent in intent_data['intents']:
            for pattern in intent['patterns']:
                words = ChattySpacyService.pre_process(nlp, pattern)
                docs_x.append(words)
                docs_y.append(intent['tag'])

        return docs_x, docs_y, intent_data

    @staticmethod
    def pre_process(nlp, data):
        data = re.sub('\W+', ' ', data.lower())
        data = nlp(data)
        return nlp(' '.join([str(t) for t in data if not t.is_stop]))

    def chatbot(self, nlp, docs_x, docs_y, intent_data, statement: str) -> Tuple:
        original_statement = statement
        statement = self.pre_process(nlp, statement)
        min_similarity = 0.95
        user_intent = []

        for word in statement:

            for wr in docs_x:
                if word and wr:
                    lem = nlp(word.lemma_)
                    if wr.similarity(lem) >= min_similarity:

                        index = docs_x.index(wr)
                        tag = docs_y[index]
                        if tag not in user_intent:
                            user_intent.append(tag)
                            break

        return_val = "I didn't quite get that. would you please try again"
        db_menu = False
        if user_intent:
            return_val, db_menu = self.action_planner(nlp, intent_data, user_intent, original_statement)

        return return_val, db_menu

    def action_planner(self, nlp, intent_data: Dict, user_intent: List, statement: str) -> Tuple:
        answer_actions = {
            "greeting": None, "goodbye": None, "thanks": None, "payments": None,
            "hours": None, "menu": None
        }
        question_actions = {"order": None, "book": None}
        is_answer = False
        is_question = False

        for usr_intent in user_intent:
            for tg in intent_data['intents']:
                if tg['tag'] == usr_intent:
                    if tg['tag'] in answer_actions:
                        responses = tg['responses']
                        answer_actions[tg['tag']] = random.choice(responses)
                        is_answer = True
                        break
                    elif tg['tag'] in question_actions:
                        responses = tg['responses']
                        question_actions[tg['tag']] = random.choice(responses)
                        is_question = True
                        break

        if is_answer:
            return self.answer_construction(nlp, answer_actions, statement)

        if is_question:
            return self.question_construction(nlp, question_actions, statement)

    def answer_construction(self, nlp, answer_action: Dict[str, str], statement: str) -> Tuple:
        statement = nlp(statement)
        name = ""
        response = ""

        for ent in statement.ents:
            if ent.label_ == "PERSON":
                name = f",{ent.text}"
                break

        db_menu = None
        for key, val in answer_action.items():
            if val:
                if key == 'greeting':
                    response = f"{val}{name}"
                elif key == 'menu':
                    response = response + ", " + val if response else val
                    db_menu = self.chatty_database.retrieve_all_menu()
                    response = response
                else:
                    response = response + ", " + val if response else val

        return response, db_menu

    @classmethod
    def extracting_order_information(cls, nlp, statement):
        statement = nlp(statement)
        response_given = {"name": "", "food": "", "quantity": 1, "date": "", "time": ""}

        for ent in statement.ents:
            if ent.label_ == "PERSON":
                response_given['name'] = ent.text
            elif ent.label_ == "FOOD":
                response_given['food'] = ent.text
            elif ent.label_ == "CARDINAL":
                response_given['quantity'] = ent.text
            elif ent.label_ == "DATE":
                response_given['date'] = ent.text
            elif ent.label_ == "TIME":
                response_given['time'] = ent.text

        response_missing = [key for key, value in response_given.items() if not value]
        for missing in response_missing:
            response_given.pop(missing)

        return response_missing, response_given

    @classmethod
    def extracting_booking_information(cls, nlp, statement):
        statement = nlp(statement)

        response_given = {"name": "", "chair_count": 0, "date": "", "time": "time"}
        for ent in statement.ents:
            if ent.label_ == "PERSON":
                response_given["name"] = ent.text
            elif ent.label_ == "CARDINAL":
                response_given["chair_count"] = ent.text
            elif ent.label_ == "DATE":
                response_given["date"] = ent.text
            elif ent.label_ == "TIME":
                response_given["time"] = ent.text

        response_missing = [key for key, value in response_given.items() if not value]
        for missing in response_missing:
            response_given.pop(missing)

        return response_missing, response_given

    def update_order_information(self, nlp, statement):
        # get this value from memory
        response = ""
        previous_response_missing = []
        previous_response_given = {}

        response_missing, response_given = self.extracting_order_information(nlp, statement)

        if response_given:
            for res in previous_response_missing:
                if res == "name":
                    if response_given["name"]:
                        previous_response_missing.remove("name")
                        previous_response_given["name"] = response_given["name"]
                elif res == "food":
                    if response_given["food"]:
                        previous_response_missing.remove("food")
                        previous_response_given["food"] = response_given["food"]
                elif res == "quantity":
                    if response_given["quantity"]:
                        previous_response_missing.remove("quantity")
                        previous_response_given["quantity"] = response_given["quantity"]
                elif res == "date":
                    if response_given["date"]:
                        previous_response_missing.remove("date")
                        previous_response_given["date"] = response_given["date"]
                elif res == "time":
                    if response_given["time"]:
                        previous_response_missing.remove("time")
                        previous_response_given["time"] = response_given["time"]

        if previous_response_missing:
            response = "Please provide"
            for res in previous_response_missing:
                response = response + " " + str(res)
            response = response + " to complete your order."

            # save previous_response_missing and previous_response_given in memory
            # state = update_order_information
            return response
        else:
            response = "Great, You want to order " + previous_response_given["quantity"] + " " + \
                       previous_response_given["food"] + " for " + previous_response_given["date"] + " and " + \
                       previous_response_given["time"] + \
                       " and the name for the order is " + previous_response_given[
                           "name"] + " .Please enter yes or no for confirmation"
            # state = confirm_order
            return response

    def update_booking_information(self, nlp, statement):
        # get this value from memory
        response = ""
        previous_response_missing = []
        previous_response_given = {}

        response_missing, response_given = self.extracting_booking_information(nlp, statement)

        if response_given:
            for res in previous_response_missing:
                if res == "name":
                    if response_given["name"]:
                        previous_response_missing.remove("name")
                        previous_response_given["name"] = response_given["name"]
                elif res == "chair_count":
                    if response_given["chair_count"]:
                        previous_response_missing.remove("chair_count")
                        previous_response_given["chair_count"] = response_given["chair_count"]
                elif res == "date":
                    if response_given["date"]:
                        previous_response_missing.remove("date")
                        previous_response_given["date"] = response_given["date"]
                elif res == "time":
                    if response_given["time"]:
                        previous_response_missing.remove("time")
                        previous_response_given["time"] = response_given["time"]

        if previous_response_missing:
            response = "Please provide"
            for res in previous_response_missing:
                response = response + " " + str(res)
            response = response + " to complete your booking."

            # save previous_response_missing and previous_response_given in memory
            # state = update_booking_information
            return response
        else:
            response = "Great, You want to book a table for " + previous_response_given["chair_count"] + " " + \
                       " for " + previous_response_given["date"] + " and " + previous_response_given["time"] + \
                       " and your name is " + previous_response_given["name"] + ".Please enter yes or no for " \
                                                                                "confirmation "
            # state = confirm_booking
            return response

    def confirm_booking(self, nlp, statement):
        statement = nlp(statement)
        statement = statement.lower()

        if statement == "yes":
            response = "Please enter your email address to get confirmation email"
            # state = confirm_email_booking
            return response
        elif statement == "no":
            response = "Please enter the correct booking information"
            # state = "update_booking_information"
            return response
        else:
            response = "Please enter yes or no for confirmation"
            # state = confirm_booking
            return response

    def confirm_order(self, nlp, statement):
        statement = nlp(statement)
        statement = statement.lower()

        if statement == "yes":
            response = "Please enter your email address to get confirmation email"
            # state = confirm_email
            return response
        elif statement == "no":
            response = "Please enter the correct order information"
            # state = "update_order_information"
            return response
        else:
            response = "Please enter yes or no for confirmation"
            # state = confirm_order
            return response

    def confirm_email_booking(self, nlp, statement):
        statement = nlp(statement)
        email = ""
        for token in statement:
            if token.like_email:
                email = token.text
                break

        if email:
            self.save_booking(email)
        else:
            # state = confirm_email_booking
            response = "Please enter your email address to get confirmation email"
            return response

    def confirm_email_order(self, nlp, statement):
        statement = nlp(statement)
        email = ""
        for token in statement:
            if token.like_email:
                email = token.text
                break

        if email:
            self.save_order(email)
        else:
            # state = confirm_email
            response = "Please enter your email address to get confirmation email"
            return response

    def save_booking(self, email):
        # get this value from memory
        previous_response_given = {}

        self.chatty_database.save_booking_db(previous_response_given["name"],
                                                 email, previous_response_given["chair_count"],
                                                 previous_response_given["date"],
                                                 previous_response_given["time"])
        #  send confirmation email to users email
        response = "Table has been booked successfully. Confirmation text has been sent to your email. Thank you for " \
                   "choosing us. "
        # state = intial state
        return response

    def save_order(self, email):
        # get this value from memory
        previous_response_given = {}
        meal = self.chatty_database.retrieve_single_menu(previous_response_given["food"])
        price = meal["price"].value
        total = price * previous_response_given["quantity"]

        self.chatty_database.save_order_db(previous_response_given["name"],
                                               email, previous_response_given["food"],
                                               previous_response_given["quantity"],
                                               total, previous_response_given["date"],
                                               previous_response_given["time"])
        #  send confirmation email to users email
        response = "The total will be " + str(total) + ".Confirmation text has been sent to your email. The order " \
                                                       "will be ready for pick up at the " \
                                                       "specified time. Thank you for shopping with us."
        # state = intial state
        return response

    def question_construction(self, nlp, question_actions: Dict[str, str] , statement: str) -> Tuple:
        db_menu = False

        if question_actions.get('order', False):
            response_missing, response_given = self.extracting_order_information(nlp, statement)

            if response_missing:
                response = "Please provide"
                for res in response_missing:
                    response = response + " " + str(res)
                    if res == "FOOD" and not db_menu:
                        db_menu = self.chatty_database.retrieve_all_menu()
                response = response + " to complete your order."
                # save the previous statement such as response_missing, response_given in memory
                # state = update_order_information
        elif question_actions.get('book', False):
            response_missing, response_given = self.extracting_booking_information(nlp, statement)
            if response_missing:
                response = "Please provide"
                for res in response_missing:
                    response = response + " " + str(res)

                response = response + " to complete your booking."

                # save the previous statement such as response_missing, response_given in memory
                # state = update_booking_information
        return response, db_menu
