import json
import logging
import datetime
import boto3
import random


# LOGS PART #

DEBUG = True
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def log_smth(intent_name, msg):
    global DEBUG
    log_in_db(intent_name + " " + msg)
    if DEBUG:
        logger.debug("{} - {}: {}".format(datetime.datetime.now(), intent_name, msg))


# DB PART #

dynamodb = boto3.client('dynamodb')

def log_in_db(request):
    init_db()
    resultLog = {
        'date': {"S": str(datetime.datetime.now())},
        'request': {"S": request}
    }

    dynamodb.put_item(TableName='Log', Item=resultLog)


def contact_in_db(firstname, lastname, email, situation, type):
    init_db()
    resultContact = {
        'firstname': {"S": firstname},
        'lastname': {"S": lastname},
        'email': {"S": email}, 
        'situation': {"S": situation},
        'type': {"S": type}
    }

    dynamodb.put_item(TableName='Contact', Item=resultContact)


def init_db():
    exist = dynamodb.list_tables()['TableNames']
    if 'Log' not in exist:
        tableLog = dynamodb.create_table(
            TableName='Log',
            KeySchema=[
                {
                    'AttributeName': 'date',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'request',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'date',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'request',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
    if 'Contact' not in exist:
        tableContact = dynamodb.create_table(
            TableName='Contact',
            KeySchema=[
                {
                    'AttributeName': 'lastname',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'lastname',
                    'AttributeType': 'S'
                }
    
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )


# RETURN FUNCTIONS #

def require_smth(intent_request, slots, msg, slot_name):
    log_smth(intent_request['sessionState']['intent']['name'], "Require another information: {}".format(slot_name))
    intent_request['sessionState']['intent']['state'] = None
    return {
        'sessionState': {
            'sessionAttributes': intent_request['sessionState']['sessionAttributes'],
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_name
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': msg
        }],
        'slots': slots,
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }
    
    
def delegate(intent_request, slots):
    log_smth(intent_request['sessionState']['intent']['name'], "Delegate")
    return {
        'sessionState': {
            'sessionAttributes': intent_request['sessionState']['sessionAttributes'],
            'dialogAction': {
                'type': 'Delegate'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'slots': slots,
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


def change_intent(intent_request, slots, new_intent):
    log_smth(intent_request['sessionState']['intent']['name'], "Change intent to: {}".format(new_intent))
    intent_request['sessionState']['intent']['name'] = new_intent
    intent_request['sessionState']['intent']['state'] = None
    return {
        'sessionState': {
            'sessionAttributes': intent_request['sessionState']['sessionAttributes'],
            'dialogAction': {
                'type': 'ConfirmIntent'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'slots': slots,
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


def validate(intent_request, msg):
    log_smth(intent_request['sessionState']['intent']['name'], "Validate: " + msg)
    intent_request['sessionState']['intent']['state'] = 'Fulfilled'
    return {
        'sessionState': {
            'sessionAttributes': intent_request['sessionState']['sessionAttributes'],
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': msg
        }],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }
    
    
def decline(intent_request, msg):
    log_smth(intent_request['sessionState']['intent']['name'], "Decline: " + msg)
    intent_request['sessionState']['intent']['state'] = 'Failed'
    return {
        'sessionState': {
            'sessionAttributes': intent_request['sessionState']['sessionAttributes'],
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': msg
        }],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


# LIB #

def search_string_tab(sentence, tab):
    for elm in tab:
        if sentence.lower() == elm.lower():
            return True
    return False


def get_firstname(event):
    firstname = None
    log_smth('getFirstName obj', event['sessionState'])
    if 'sessionAttributes' in event['sessionState']:
        if 'firstname' in event['sessionState']['sessionAttributes']:
            firstname = event['sessionState']['sessionAttributes']['firstname']
    if not firstname and 'slots' in event['sessionState']['intent']:
        if event['sessionState']['intent']['slots'] is not None and 'firstname' in event['sessionState']['intent']['slots']:
            if event['sessionState']['intent']['slots']['firstname'] is not None:
                firstname = event['sessionState']['intent']['slots']['firstname']['value']['interpretedValue']
                event['sessionState']['sessionAttributes']['firstname'] = firstname
    log_smth('getFirstName', firstname)
    return firstname
    
    
# LAMBDA FUNCTIONS #

PEOPLE_LIST = ['Jean', 'Eleonore', 'John', 'Baptiste', 'Axelle', 'Roger', 'Claire']
ADDR_LIST = ['epitech', 'epitechbarcelona']

def parse_address(event):
    global ADDR_LIST
    dest = event['sessionState']['intent']['slots']['dest']['value']['interpretedValue'] if 'dest' in event['sessionState']['intent']['slots'] else None

    slots = {'dest': dest}
    if dest is None:
        return require_smth(event, slots, "Where the package is meant to be delivered ?", 'dest')
            
    if search_string_tab(dest, ADDR_LIST):
        return validate(event, "Yes, you are at the right place ! Just knock at the third door.")
        
    return decline(event, "No, you are not in the right place I'm afraid ...")


def manage_mail(event):
    global ADDR_LIST
    dest = event['sessionState']['intent']['slots']['dest']['value']['interpretedValue'] if 'dest' in event['sessionState']['intent']['slots'] else None

    slots = {'dest': dest}
    if dest is None:
        return require_smth(event, slots, "Where the letter is meant to be delivered ?", 'dest')
            
    if search_string_tab(dest, ADDR_LIST):
        return validate(event, "Yes, you are at the right place ! Just put it in the letterbox at the right of the corridor entrance.")
        
    return decline(event, "No, you are not in the right place, here we are at Epitech Barcelona campus !")
  
    
def manage_jpo(event):
    global PEOPLE_LIST
    firstname = get_firstname(event)
    slots = {'firstname': firstname}
    
    if datetime.datetime.today().weekday() == 5:
        if firstname is None:
            return require_smth(event, slots, "What is your first name ?", 'firstname')
        elif firstname.capitalize() not in PEOPLE_LIST:
            return validate(event, "Yes there is a JPO today ! I register you on the list !")
        return validate(event, "Yes there is a JPO today ! Just turn left and go to the end of the corridor, some people are here to welcome you and present the school")
        
    return decline(event, "No there is no JPO today ! But I can give you some information about the next one if you want")


def manage_coding_club(event):
    global PEOPLE_LIST
    firstname = get_firstname(event)
    slots = {'firstname': firstname}
    
    if datetime.datetime.today().weekday() == 5:
        if firstname is None:
            return require_smth(event, slots, "What is your first name ? Just to check if you are registered", 'firstname')
        elif firstname.capitalize() not in PEOPLE_LIST:
            return validate(event, "There is a coding club in the SciFi room, but are you sure you are registered ? I don't see your name in the list ...")
        return validate(event, "Yes there is a coding club in the SciFi room ! Just turn left and go to the end of the corridor")
        
    return decline(event, "No there is no coding club today ! But I can give you some information about the next one if you want")


INF_TYPE_LIST = [
    'openinghours',
    'price',
    'diploma',
    'duration',
    'methodology'
]

def information_parser(event):
    global INF_TYPE_LIST
    inf_type = event['sessionState']['intent']['slots']['BasicInformation']['value']['interpretedValue'] if 'BasicInformation' in event['sessionState']['intent']['slots'] else None

    if inf_type == INF_TYPE_LIST[0]:
        return validate(event, "The school is open from monday to Friday, and from 8am to 20pm !\n\
                                It is also open exceptionally later in the night or on weekends for special events !")
    elif inf_type == INF_TYPE_LIST[1]:
        return validate(event, "The studies are REALLY expensive. You can expect to pay more than 7k per year...\n\
                                But you can pretend to scholarship or borrow money at the bank with student loans.")
    elif inf_type == INF_TYPE_LIST[2]:
        return validate(event, "The diploma is based on an equivalent of engineer studies with an 'information system expert' title. It is recognized by officials.")
    elif inf_type == INF_TYPE_LIST[3]:
        return validate(event, "The studies takes 5 years to complete, with two available cycles: Innovation with abroad experience, or Technical with network or security expertise.")
    elif inf_type == INF_TYPE_LIST[4]:
        return validate(event, "The school does not use a traditional mean of teaching. All the work is done by projects, that are all evaluates and there is no real courses with teachers.\n\
                                It helps students to comform to companies methodology with a lot of internships but require a great autonomy.")
    
    if random.choice([0, 1]) == 0:
        return decline(event, "Sorry, I think I can't help you on this request ... I'm a bit limited sorry ! Maybe try to reformulate ?")
    else:
        return decline(event, "Sorry I don't understand ... I think I'm stupid ;)")


def manage_information(event):
    global INF_TYPE_LIST
    inf_type = event['sessionState']['intent']['slots']['BasicInformation']['value']['interpretedValue'] if 'BasicInformation' in event['sessionState']['intent']['slots'] else None
    
    slots = {'BasicInformation': inf_type}
    
    if inf_type is None:
        return require_smth(event, slots, "What kind of information do you want ? I can tell you about the opening hours, the price of the school, the diploma, the studies duration or the methodology. (choose one)", 'informationtype')
    elif inf_type not in INF_TYPE_LIST:
        return require_smth(event, slots, "Sorry, I don't understand, what do you want to know ? I can tell you about the opening hours, the price of the school, the diploma, the studies duration or the methodology. (choose one)", 'informationtype')
    
    if inf_type in INF_TYPE_LIST:
        return information_parser(event)
        
    return decline(event, "Sorry I don't understand what you want, maybe try to rephrase ...")
    

def manage_diploma(event):
    global PEOPLE_LIST
    year = int(event['sessionState']['intent']['slots']['year']['value']['interpretedValue']) if 'year' in event['sessionState']['intent']['slots'] else None
    firstname = get_firstname(event)
    slots = {'year': year}

    if year is None:
        return require_smth(event, slots, "Can you tell me in which year you are please ?", 'year')
    elif year < 3 or year > 5:
        return decline(event, 'The specified information cannot allow you to have any diploma to pick up. Any other questions ?')
    elif firstname is None:
        return require_smth(event, slots, "Can I get your name please ?", 'firstname')
    elif firstname.capitalize() not in PEOPLE_LIST:
        return decline(event, 'You are not registered on my list, are you sure that you are part of Epitech Barcelona ? Or maybe you misspelled your name ? Mind retrying')
        
    return validate(event, "You can go to the left corridor you will see a room with the administration.")


def manage_student_card(event):
    global PEOPLE_LIST
    firstname = get_firstname(event)
    slots = {'firstname': firstname}

    if firstname is None:
        return require_smth(event, slots, "Can I get your name please ?", 'firstname')
    elif firstname.capitalize() not in PEOPLE_LIST:
        return decline(event, 'You are not a student of Epitech, any other questions ?')
        
    return validate(event, "You can pick up your student card in the left corridor you will see a room with the administration.")


def manage_event_type(inf_type, eventType):
    for elm in eventType:
        if inf_type == elm['type']:
            return True
    return False


def manage_event(event):
    #nom date type desc
    inf_type = event['sessionState']['intent']['slots']['EventType']['value']['interpretedValue'] if 'EventType' in event['sessionState']['intent']['slots'] else None

    eventsType = [
        {
            "type": "Gamejam",
            "desc": "this is an event where you can try to create a video game in less than 48 hours."
        },
        {
            "type": "Open house day",
            "desc": "this is a day where you can visit the epitech premises"
        },
        {
            "type": "Coding club",
            "desc": "this is a day where you can come to a lesson with student to learn basics in code"
        },
        {
            "type": "Hubtalk",
            "desc": "This is an event where you can talk about new technologies news with the other epitech's student"
        },
        {
            "type": "Hubnight",
            "desc": "This is an event where you can challenge yourself against the other student on an innovative subject"
        }
    ]

    events = [
        {
            "event": eventsType[0],
            "date": datetime.date(year=2022, month=1, day=28)
        },
        {
            "event": eventsType[1],
            "date": datetime.date(year=2022, month=2, day=5)
        },
        {
            "event": eventsType[2],
            "date": datetime.date(year=2022, month=2, day=19)
        }
    ]

    slots = {'EventType': inf_type}

    if inf_type is None:
        return require_smth(event, slots, "What kind of event is interesting you ? I can tell you about the Gamejam or about an Open house day or about a Coding club.(choose one)", 'EventType')
    elif not manage_event_type(inf_type, eventsType):
        return decline(event, "Sorry but I don't understand which type you are talking. Can you repeat or rephrase ?")
    
    i = 0
    for evt in events:
        if evt['event']['type'] == inf_type:
            break
        i += 1
    
    return validate(event, "The next {} is on the {}, {}. ".format(events[i]['event']['type'], events[i]['date'], events[i]['event']['desc']))

INF_TYPE_STUDENT = [
    "administration",
    "pedagogy"
]

def manage_student(event):
    global INF_TYPE_STUDENT
    inf_type = event['sessionState']['intent']['slots']['StudentInfo']['value']['interpretedValue'] if 'StudentInfo' in event['sessionState']['intent']['slots'] else None
    
    slots = {'StudentInfo': inf_type}
    
    if inf_type is None:
        return require_smth(event, slots, "What kind of information do you want ? I can tell you about the administration team or about the pedagogy team. (choose one)", 'StudentInfo')
    elif inf_type not in INF_TYPE_STUDENT:
        return require_smth(event, slots, "Sorry, I don't understand, what do you want to know ? I can tell you about  the administration team or about the pedagogy team. (choose one)", 'StudentInfo')
    
    if inf_type in INF_TYPE_STUDENT:
        return student_information_parser(event)
        
    return decline(event, "Sorry I don't understand what you want, maybe try to rephrase ...")
    

def student_information_parser(event) :
    global INF_TYPE_STUDENT
    inf_type = event['sessionState']['intent']['slots']['StudentInfo']['value']['interpretedValue'] if 'StudentInfo' in event['sessionState']['intent']['slots'] else None

    if INF_TYPE_STUDENT[0] == inf_type:
        return validate(event, "If you want to take an appointment with the administration you can go in the office of MS. RABACCA")
    elif INF_TYPE_STUDENT[1] == inf_type:
        return validate(event, "If you want to take an appointment with the pedagogy you can go in the office of MR. GOBY")

    if random.choice([0, 1]) == 0:
        return decline(event, "Sorry, I think I can't help you on this request ... I'm a bit limited sorry ! Maybe try to reformulate ?")
    else:
        return decline(event, "Sorry I don't understand ... I think I'm stupid ;)")



def get_contact(event):
    firstname = event['sessionState']['intent']['slots']['firstname']['value']['interpretedValue']
    lastname = event['sessionState']['intent']['slots']['LastName']['value']['interpretedValue']
    email = event['sessionState']['intent']['slots']['email']['value']['interpretedValue']
    situation = event['sessionState']['intent']['slots']['Situation']['value']['interpretedValue']
    informationType = event['sessionState']['intent']['slots']['informationType']['value']['interpretedValue']

    contact_in_db(firstname, lastname, email, situation, informationType)
    return validate(event, "Thank you ! I am keeping you in a corner of my adress list ! I will ensure that you will get informed as soon as I have new informations !")


# HANDLER #

def lambda_handler(event, context):
    intent_name = event['sessionState']['intent']['name']
    init_db()

    if 'slots' not in event['sessionState']['intent']:
        event['sessionState']['intent']['slots'] = {}
    if 'sessionAttributes' not in event['sessionState']:
        event['sessionState']['sessionAttributes'] = {}

    if intent_name == 'Package':
        return parse_address(event)
    elif intent_name == 'Mail':
        return manage_mail(event)
    elif intent_name == 'JPO':
        return manage_jpo(event)
    elif intent_name == 'CodingClub':
        return manage_coding_club(event)
    elif intent_name == 'Information':
        return manage_information(event)
    elif intent_name == 'InformationParser':
        return information_parser(event)
    elif intent_name == 'InformationStudentParser':
        return student_information_parser(event)
    elif intent_name == 'Student':
        return manage_student(event)
    elif intent_name == 'Diploma':
        return manage_diploma(event)
    elif intent_name == 'StudentCard':
        return manage_student_card(event)
    elif intent_name == 'Event':
        return manage_event(event)
    elif intent_name == 'getContact':
        return get_contact(event)

    raise Exception('Intent with name ' + intent_name + ' not supported')

