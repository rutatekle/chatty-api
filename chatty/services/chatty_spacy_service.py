import random
import re
import spacy
import json
import os
from typing import List, Tuple, Dict

from chatty.services import chatty_db


class ChattySpacyService:

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

    def chatbot(self, nlp, docs_x, docs_y, intent_data, statement: str) -> str:
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
        if user_intent:
            print(user_intent)
            return_val = self.action_planner(nlp, intent_data, user_intent, original_statement)
        else:
            print(return_val)

        return return_val

    def action_planner(self, nlp, intent_data: Dict, user_intent: List, statement: str) -> str:
        greeting = ""
        goodbye = ""
        thanks = ""
        payments = ""
        hours = ""
        menu = ""
        order = ""
        book = ""

        for usr_intent in user_intent:
            for tg in intent_data['intents']:
                if tg['tag'] == usr_intent:
                    if tg['tag'] == "greeting":
                        responses = tg['responses']
                        greeting = random.choice(responses)
                        break
                    elif tg['tag'] == "goodbye":
                        responses = tg['responses']
                        goodbye = random.choice(responses)
                        break
                    elif tg['tag'] == "thanks":
                        responses = tg['responses']
                        thanks = random.choice(responses)
                        break
                    elif tg['tag'] == "payments":
                        responses = tg['responses']
                        payments = random.choice(responses)
                        break
                    elif tg['tag'] == "hours":
                        responses = tg['responses']
                        hours = random.choice(responses)
                        break
                    elif tg['tag'] == "menu":
                        responses = tg['responses']
                        menu = random.choice(responses)
                        break
                    elif tg['tag'] == "order":
                        responses = tg['responses']
                        order = random.choice(responses)
                        break
                    elif tg['tag'] == "book":
                        responses = tg['responses']
                        book = random.choice(responses)
                        break

        if greeting or goodbye or thanks or payments or hours or menu:
            return self.answer_construction(nlp, greeting, goodbye, thanks, payments, hours, menu, statement)

        if order or book:
            return self.question_construction(nlp, order, book, statement)

    def answer_construction(self, nlp, greeting: str, goodbye: str, thanks: str, payments: str, hours: str, menu: str, statement: str) -> str:
        statement = nlp(statement)
        name = ""
        response = ""
        flag_menu = False
        menu = []

        for ent in statement.ents:
            if ent.label_ == "PERSON":
                name = ent.text

        if greeting:
            if name:
                response = greeting + ", " + name
            else:
                response = greeting
        if hours:
            response = response + ", " + hours
        if payments:
            response = response + ", " + payments
        if menu:
            response = response + ", " + menu
            flag_menu = True
            menu = chatty_db.ChattyDatabase.retrieve_all_menu(None)
        if thanks:
            response = response + ", " + thanks
        if goodbye:
            response = response + ", " + goodbye

        if response:
            print(statement)
            print(response)

        if flag_menu:
            return response + menu
        else:
            return response

    def extracting_order_information(self, nlp, statement):
        statement = nlp(statement)
        name = ""
        food = ""
        quantity = 1
        date = ""
        time = ""
        response_missing = []
        response_given = {}

        for ent in statement.ents:
            if ent.label_ == "PERSON":
                name = ent.text
            elif ent.label_ == "FOOD":
                food = ent.text
            elif ent.label_ == "CARDINAL":
                quantity = ent.text
            elif ent.label_ == "DATE":
                date = ent.text
            elif ent.label_ == "TIME":
                time = ent.text

        if not name:
            response_missing.append("name")
        else:
            response_given.update({"name": name})

        if not food:
            response_missing.append("food")
        else:
            response_given.update({"food": food})

        if not quantity:
            response_missing.append("quantity")
        else:
            response_given.update({"quantity": quantity})

        if not date:
            response_missing.append("date")
        else:
            response_given.update({"date": date})

        if not time:
            response_missing.append("time")
        else:
            response_given.update({"time": time})
        return response_missing, response_given

    def extracting_booking_information(self, nlp, statement):
        statement = nlp(statement)
        name = ""
        chair_count = 0
        date = ""
        time = ""

        response_missing = []
        response_given = {}

        for ent in statement.ents:
            if ent.label_ == "PERSON":
                name = ent.text
            elif ent.label_ == "CARDINAL":
                chair_count = ent.text
            elif ent.label_ == "DATE":
                date = ent.text
            elif ent.label_ == "TIME":
                time = ent.text

        if not name:
            response_missing.append("name")
        else:
            response_given.update({"name": name})

        if not chair_count:
            response_missing.append("chair_count")
        else:
            response_given.update({"chair_count": chair_count})

        if not date:
            response_missing.append("date")
        else:
            response_given.update({"date": date})

        if not time:
            response_missing.append("time")
        else:
            response_given.update({"time": time})
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

        chatty_db.ChattyDatabase.save_booking_db(None,previous_response_given["name"],
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
        meal = chatty_db.ChattyDatabase.retrieve_single_menu(previous_response_given["food"])
        price = meal["price"].value
        total = price * previous_response_given["quantity"]

        chatty_db.ChattyDatabase.save_order_db(previous_response_given["name"],
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

    def question_construction(self, nlp, order: str, book: str, statement: str) -> str:
        response = ""
        flag_menu= False
        menu=[]

        if order:
            response_missing, response_given = self.extracting_order_information(nlp, statement)

            if response_missing:
                response = "Please provide"
                for res in response_missing:
                    response = response + " " + str(res)
                    if res == "FOOD":
                        flag_menu = True
                response = response + " to complete your order."

                # save the previous statement such as response_missing, response_given in memory
                # state = update_order_information
                if flag_menu is True:
                    menu = chatty_db.ChattyDatabase.retrieve_all_menu(None)
                    return response + menu
                else:
                    return response

        elif book:
            response_missing, response_given = self.extracting_booking_information(nlp, statement)
            if response_missing:
                response = "Please provide"
                for res in response_missing:
                    response = response + " " + str(res)

                response = response + " to complete your booking."

                # save the previous statement such as response_missing, response_given in memory
                # state = update_booking_information
                return response










