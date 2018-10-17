from __future__ import print_function
import requests
from language_codes import language_codes

# --------------- Helpers that build all of the responses ----------------------
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Smart Apertium Translator. " \
                    "You can ask me to translate a sentence, " \
                    "translate a document or identify the language of speech. " \
                    "You can also know what type of language translations " \
                    "are currently available in the skill. " \
                    "So what do you want to do for now?"
    reprompt_text = "You can try out some of these commands like, " \
                    "Alexa ask Smart Apertium to translate I won a match to Catalan " \
                    "or Alexa ask Smart Apertium hola amigos is in which language " \
                    "or Alexa ask Smart Apertium can you translate English " \
                    "So what do you want to do for now?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying out the Smart Apertium Translator. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def url(path):
    response = requests.get('https://www.apertium.org/apy' + path)
    response = response.json()
    return response


def language_detect(sentence):
    lang_dict = url('/identifyLang?q=' + sentence)
    max_val = 0.0
    for key, value in lang_dict.items():
        if(value > max_val):
            max_val = value
            lang_iso = key
    return lang_iso


def translate_voice(intent, session):
    card_title = "Voice Translate"
    session_attributes = {}
    should_end_session = False
    reprompt_text = None

    if 'sentence' in intent['slots']:
        sentence = intent['slots']['sentence']['value']
        sentence = sentence.strip('.').strip('?')
        lang_process = sentence.split()
        if(lang_process[-2] == 'in' or lang_process[-2] == 'to' or lang_process[-2] == 'into'):
            language = lang_process[-1]
            lang_process.pop()
            lang_process.pop()
        elif(lang_process[-3] == 'in' or lang_process[-3] == 'to' or lang_process[-3] == 'into'):
            if(lang_process[-1] == 'language'):
                language = lang_process[-2]
            else:
                language = lang_process[-2] + ' ' + lang_process[-1]
            lang_process.pop()
            lang_process.pop()
            lang_process.pop()
        sentence = ' '.join(lang_process)
        lang_iso = language_detect(sentence)
        lang_iso = 'eng' if lang_iso == 'nob' else lang_iso
        language_iso = [code['iso'] for code in language_codes if code['language'].lower() == language.lower()]
        if language_iso == []:
            speech_output = "Sorry, but Apertium currently does not supports " + \
                            language + " language."
            reprompt_text = "Please try some other language for now."
        else:
            language_iso = language_iso[0]
            list_pairs = url('/listPairs')['responseData']
            if {"sourceLanguage": lang_iso, "targetLanguage": language_iso} not in list_pairs:
                speech_output = "Sorry but the translation is currently not available."
                should_end_session = True
            else:
                try:
                    translation = url("/translate?langpair=" + lang_iso + "|" + language_iso + "&q=" + sentence)['responseData']['translatedText']
                    speech_output = translation
                except KeyError:
                    speech_output = "Sorry but the translation is currently not available."
                should_end_session = True
    else:
        speech_output = "I'm not sure but either the sentence or the language is missing. " \
                        "Please try again giving a proper command like, " \
                        "Alexa ask Smart Apertium how do you say I like sweets in Spanish."
        reprompt_text = "Please try again giving a proper command like, " \
                        "Alexa ask Smart Apertium how do you say I like sweets in Spanish."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def translate_doc(intent, session):
    card_title = "Document Translate"
    session_attributes = {}
    should_end_session = True
    reprompt_text = None

    if 'document' in intent['slots']:
        document = intent['slots']['document']['value']
        speech_output = "Thank you for trying out this feature. " \
                        "We are working on it right now."
    else:
        speech_output = "I'm not sure what your document is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def identify_lang(intent, session):
    card_title = "Identify Language"
    session_attributes = {}
    should_end_session = False
    reprompt_text = None

    if 'sentence' in intent['slots']:
        sentence = intent['slots']['sentence']['value']
        sentence = sentence.strip('.').strip('?')
        lang_iso = language_detect(sentence)
        language = [code['language'] for code in language_codes if code['iso'] == lang_iso]
        if language == []:
            speech_output = "Sorry but Apertium cannot identify the language. " \
                            "Please rephrase your sentence."
            reprompt_text = "Please rephrase your sentence again."
        else:
            language = language[0]
            speech_output = "The phrase spoken is in " + language + " language."
            should_end_session = True
    else:
        speech_output = "I'm sorry but can't figure out what your phrase is. " \
                        "Please try again."
        reprompt_text = "Still can't figure out what your phrase is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def list_pair(intent, session):
    card_title = "List Language Pairs"
    session_attributes = {}
    should_end_session = False
    reprompt_text = None

    if 'language' in intent['slots']:
        language = intent['slots']['language']['value']
        lang_process = language.split()
        if lang_process[-1] == 'language' or lang_process[-1] == 'Language':
            lang_process.pop()
            language = ' '.join(lang_process)
        language_iso = [code['iso'] for code in language_codes if code['language'].lower() == language.lower()]
        if language_iso == []:
            speech_output = "Sorry but Apertium currently does not supports " + \
                            language + " language. Please try with some other language for now."
            reprompt_text = "Please try some other languages for now."
        else:
            language_iso = language_iso[0]
            list_pairs = url('/listPairs')['responseData']
            source_lang = []
            target_lang = []
            for pair in list_pairs:
                if pair['targetLanguage'] == language_iso:
                    lang = [code['language'] for code in language_codes if code['iso'] == pair['sourceLanguage']]
                    lang = lang[0] if len(lang) > 0 else pair['sourceLanguage']
                    source_lang.append(lang)
                elif pair['sourceLanguage'] == language_iso:
                    lang = [code['language'] for code in language_codes if code['iso'] == pair['targetLanguage']]
                    lang = lang[0] if len(lang) > 0 else pair['targetLanguage']
                    target_lang.append(lang)
            speech_output = language + " language can be"
            if len(source_lang):
                speech_output += " translated from "
                speech_output += ", ".join(source_lang)
                if len(target_lang):
                    speech_output += " languages and"
                else:
                    speech_output += " languages."
            if len(target_lang):
                speech_output += " translated to "
                speech_output += ", ".join(target_lang)
                speech_output += " languages."
            should_end_session = True

    else:
        speech_output = "I'm sorry but can't figure out what the language is. " \
                        "Please try again."
        reprompt_text = "Still can't figure out what the language is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "TranslateVoiceIntent":
        return translate_voice(intent, session)
    elif intent_name == "TranslateDocIntent":
        return translate_doc(intent, session)
    if intent_name == "IdentifyLangIntent":
        return identify_lang(intent, session)
    elif intent_name == "ListPairIntent":
        return list_pair(intent, session)
    elif intent_name == "AMAZON.HelpIntent" or intent_name == "HelloIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
        "amzn1.ask.skill.fc2d4f2d-52cf-4144-ab8c-0371761dc526"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
