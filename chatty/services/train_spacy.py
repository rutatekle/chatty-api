import spacy
from spacy.training.example import Example


class TrainSpacyPipeLine:

    @staticmethod
    def load_and_train(self):
        nlp = spacy.load('en_core_web_md')

        text = 'pizza is my favorite kind of food. Other food I enjoy are pasta and lasagna'
        doc = nlp(text)
        words = []
        labels = []
        foods = ["pizza", "lasagna", "pasta"]

        for token in doc:
            words.append(token.text)
            if token.text in foods:
                labels.append("U-FOOD")
            else:
                labels.append('O')

        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, {"entities": labels})

        add_ents = ['DATED']

        if "ner" not in nlp.pipe_names:
            ner = nlp.create_pipe("ner")
            nlp.add_pipe(ner)
        else:
            ner = nlp.get_pipe("ner")
        prev_ents = ner.move_names  # All the existing entities recognised by the model
        print('[Existing Entities] = ', ner.move_names)
        for ent in add_ents:
            ner.add_label(ent)

        new_ents = ner.move_names
        print('\n\n[New Entities] = ', list(set(new_ents) - set(prev_ents)))
        model = None
        n_iter = 20

        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
        with nlp.disable_pipes(*other_pipes):
            if not model:
                optimizer = nlp.create_optimizer()
            else:
                optimizer = nlp.resume_training()
            for i in range(n_iter):
                losses = {}
                nlp.update([example], losses=losses, drop=0.0)

        text = "My favorite food in the world is pizza by far and lasagna too"
        doc = nlp(text)
        for ent in doc.ents:
            print(ent.text, ent.label_)




