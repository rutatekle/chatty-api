import random
import re
import spacy
import json
import os
from typing import List, Tuple, Dict


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
            return_val = self.action_planner(intent_data, user_intent, original_statement)
        else:
            print(return_val)

        return return_val

    def action_planner(self, intent_data: Dict, user_intent: List, statement: str) -> str:
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
            return self.answer_construction(greeting, goodbye, thanks, payments, hours, menu, statement)

        if order or book:
            return self.question_construction(order, book, statement)

    def answer_construction(
            self, greeting: str, goodbye: str, thanks: str, payments: str, hours: str, menu: str, statement: str
    ) -> str:
        statement = nlp(statement)
        name = ""
        response = ""

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
        # 3. retrive the list of menus for the user to see through the action executor from the database
        if thanks:
            response = response + ", " + thanks
        if goodbye:
            response = response + ", " + goodbye

        if response:
            print(statement)
            print(response)
        return response

    def question_construction(self, order: str, book: str, statement: str) -> str:
        statement = nlp(statement)
        name = ""
        food = ""
        quantity = ""
        date = ""
        time = ""
        response = ""
        confirm = None
        email = ""

        if order:
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

            if name and food and quantity and (date or time):
                # retrieve the menu from database
                menu = ["pizza", "pasta", "lasagna"]
                while food not in menu:
                    # flag here
                    response = "Opps! Sorry, we don't serve " + food + " .Here is our menu. Please choose meal from our menu."
                    food = "user input with meal type"
                    food = food.lower()

                response = "Great, You want to order " + quantity + " " + food + " for " + date + time + \
                           " and the name for the order is " + name + " .Please enter yes or no for confirmation"

                # flag here()
                confirm = "what ever user inputs"
                while confirm not in {"yes", "no"}:
                    response = "Please enter yes or no to confirm if your order is correct"
                    # flag here()
                    confirm = "what ever user inputs"
                    confirm = confirm.lower()

                if confirm == "yes":
                    response = "Please provide a valid email address to send the confirmation email to"
                    # flag here()
                    email = "user response with/without email here"

                    # if email is valid
                    while not self.extract_email(email):
                        response = "Please enter a valid email"
                        email = "user response with/without email here"

                    # send confirmation email to user with order and save order in database
                    response = "Confirmation email has been sent to your email, The order will be ready for pickup at the specified time."

                else:
                    response = "I haven't figured out what to do in here???"

            elif not name:
                response = "Please provide a name for the order."

            elif not food:
                response = "Please provide what you like to order"

            elif not quantity:
                response = "Please provide quantity for your order."

            elif not date and not time:
                response = "Please provide a date and time of pickup for your order."
        if book:
            response = response + ", " + book

        return response

    @classmethod
    def extract_email(cls, doc: List) -> str:
        email = ""
        for token in doc:
            if token.like_email:
                email = token.text
        return email


# 1. if we can put this in a public class that can only be loaded once and can be access everywhere
nlp = spacy.load("en_core_web_md")

# 2. if we can put this in a public class that can only be loaded once and can be access everywhere


