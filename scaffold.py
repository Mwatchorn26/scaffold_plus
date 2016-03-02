#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import re
import sys
from datetime import date

import jinja2
from pprint import pprint

from . import Command

from openerp.modules.module import (get_module_root, MANIFEST, load_information_from_description_file as load_manifest)


class Scaffold(Command):
    """ Generates an Odoo module skeleton. """

    def run(self, cmdargs):
        # TODO: bash completion file
        parser = argparse.ArgumentParser(
            prog="%s scaffold" % sys.argv[0].split(os.path.sep)[-1],
            description=self.__doc__,
            epilog=self.epilog(),
        )


        parser.add_argument('name', help="Name of the module to create")
        parser.add_argument(
            'dest', default='.', nargs='?',
            help="Directory to create the module in (default: %(default)s)")

        #group = parser.add_mutually_exclusive_group()
        parser.add_argument(
            '-t', '--template', type=template, default=template('default'),
            help=''''Use a custom module template, can be a template name or the
                 path to a module template (default: %(default)s)''')
        parser.add_argument('-i','--interrogative', action='store_true',
            help='''Build scaffold using an interrogative method.
                    The system will interrogate the developer to generate the 
                    required parameters to complete the scaffold.''')
                    #type=template, default=template('interrogative'),                   

        if not cmdargs:
            sys.exit(parser.print_help())
        args = parser.parse_args(args=cmdargs)

        if args.interrogative:
            print "Starting Interactive Build Mode..."
            args.template.render_to(
                snake(args.name),
                directory(args.dest, create=True),
                interrogation(args.name))
        else:
            args.template.render_to(
                snake(args.name),
                directory(args.dest, create=True),
                {'name':args.name})

    def epilog(self):
        return "Built-in templates available are: %s" % ', '.join(
            d for d in os.listdir(builtins())
            if d != 'base'
        )

builtins = lambda *args: os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'templates',
    *args)

def snake(s):
    """ snake cases ``s``
    :param str s:
    :return: str
    """
    # insert a space before each uppercase character preceded by a
    # non-uppercase letter
    s = re.sub(r'(?<=[^A-Z])\B([A-Z])', r' \1', s)
    # lowercase everything, split on whitespace and join
    return '_'.join(s.lower().split())

def pascal(s):
    return ''.join(
        ss.capitalize()
        for ss in re.sub('[_\s]+', ' ', s).split()
    )

def reverseSnake(s):
    s = s.replace('_',' ').title()
    return s

def reversePascal(s):
    ''' 
    Example of Pascal: 'IsThis'
    What reversePascal returns: 'Is This'
    '''
    s = re.sub(r'(?<=[^A-Z])\B([A-Z])', r' \1', s)
    return s

def nextItem(currentItem, itemList):
    #print 'currentItem: ' + currentItem
    #print 'itemList: ' + itemList
    nextIndex = (itemList.index(currentItem)+1) % len(itemList)
    return str(itemList[nextIndex])

def currentyear():
    return date.year

def directory(p, create=False):
    expanded = os.path.abspath(
        os.path.expanduser(
            os.path.expandvars(p)))
    if create and not os.path.exists(expanded):
        os.makedirs(expanded)
    if not os.path.isdir(expanded):
        die("%s is not a directory" % p)
    return expanded

env = jinja2.Environment()
env.filters['snake'] = snake
env.filters['pascal'] = pascal
env.filters['nextItem'] = nextItem
env.filters['year'] = currentyear
class template(object):
    def __init__(self, identifier):
        # TODO: archives (zipfile, tarfile)
        self.id = identifier
        # is identifier a builtin?
        self.path = builtins(identifier)
        if os.path.isdir(self.path):
            return
        # is identifier a directory?
        self.path = identifier
        if os.path.isdir(self.path):
            return
        die("{} is not a valid module template".format(identifier))

    def __str__(self):
        return self.id

    def files(self):
        """ Lists the (local) path and content of all files in the template
        """
        for root, _, files in os.walk(self.path):
            for f in files:
                path = os.path.join(root, f)
                yield path, open(path, 'rb').read()

    def render_to(self, modname, directory, params=None):
        """ Render this module template to ``dest`` with the provided
         rendering parameters
        """
        # overwrite with local
        for path, content in self.files():
            local = os.path.relpath(path, self.path)
            # strip .template extension
            root, ext = os.path.splitext(local)
            if ext == '.template':
                local = root
            dest = os.path.join(directory, modname, local)
            destdir = os.path.dirname(dest)
            if not os.path.exists(destdir):
                os.makedirs(destdir)

            with open(dest, 'wb') as f:
                if ext not in ('.py', '.xml', '.csv', '.js', '.rst', '.html', '.template'):
                    f.write(content)
                else:
                    env.from_string(content)\
                       .stream(params or {})\
                       .dump(f, encoding='utf-8')

#                     env.from_string(content.decode('utf-8'))\
#                        .stream(params or {})\
#                        .dump(f, encoding='utf-8')


def die(message, code=1):
    print >>sys.stderr, message
    sys.exit(code)

def warn(message):
    # ASK: shall we use logger ?
    print "WARNING: " + message

def interrogation(ModuleName):
    '''
    This function interacts with the developer asking questions about what 
    should be in the new module. It stores the responses various dictionaries 
    and lists, to be used by the jinja2 templates.
    '''
    # Included in the original call: #ModuleName = UserInput("Module Name:")   #raw_input("Module Name:")

    models=[]

    sys.stderr.write("\x1b[2J\x1b[H")
    while (True):
        thismodel={}
        modelname=UserInput('\n\n\nEnter the Model Name (aka class name)\n(Enter "" when complete):')
        if modelname=='':       #If the user entered nothing as a modelname
            break               #Stop looping through the models
        thismodel['ModelName']=modelname
        thismodel['ModelDescription']=UserInputRaw('Description of the model (eg: "My Menu"):')
        thismodel["IsWizard"]=str2bool(UserInput('Is ' + modelname +' a wizard?(y/n)'))
        thismodel['ModelHasMenu']=str2bool(UserInput('Should ' + modelname +' appear as a menu item? (y/n):'))
        if thismodel['ModelHasMenu']==True:
            thismodel['MenuName']=UserInput('Menu title for ' + modelname + ' (eg: "My Menu"):').capitalize()
            thismodel['ParentMenu']=UserInputRaw(''''Parent Menu Id: \n
Typical parent menus include [TODO: FILL IN THE MAIN MENUS HERE]''')
        thismodel['ModelInherits']=str2bool(UserInput('Does ' + modelname + ' inherit from another model? (y/n):'))
        if thismodel['ModelInherits']==True:
            thismodel['InheritFromModel']=UserInput('Which model does ' + modelname + ' inherit from?')
        thismodel['HasStates']=str2bool(UserInput("Does " + modelname + ''' use 'States' (y/n):'''))
        if thismodel["HasStates"]==True:
            states=["Default","Cancel"]
            while(True):
                statename=UserInput('''_ State Name _
(eg: Default,Open,Done,Cancel) 
Current States: [Default,Cancel]: 
(Enter "" when complete)''')
                if statename=="":
                    break
                ##states.append(statename.capitalize)
                states.insert(-1,statename.capitalize())
                pprint(states)
            ##states = [x.capitalize for x in states if x.capitalize != "Cancel"]
            ##states.append("Cancel")
            thismodel['states']=states

        thismodel['HasSequence']=str2bool(UserInput('Does ' + modelname +  ''' require a sequence?
similar to Purchase Orders: PO1234 or or Manufacturing Orders:MO6543 (y/n):'''))
        if thismodel["HasSequence"]==True:
            thismodel['SequenceName']=UserInput("What is the name of the sequence (Suggested is " + modelname.title() + " Sequence):").title()
            thismodel['SequencePrefix']=UserInput('''
What prefix do you want to use for your sequence?
Common prefixes include 2 characters: "XY" 
Or 2 characters and the date code:    "XY%(year)s/"
Or Month and Day:                     "Cr. %(month)s/%(day)s/"
Complete List of Built-In Options:            
Current Year with Century:            "%(year)s"
Current Year without Century:         "%(y)s"
Month:                                "%(month)s"
Day:                                  "%(day)s"
Day of the Year:                      "%(doy)s"
Week of the Year:                     "%(woy)s"
Day of the Week (0:Monday):           "%(weekday)s"
Hour 00->24:                          "%(h24)s"
Hour 00->12:                          "%(h12)s"
Minute:                               "%(min)s"
Second:                               "%(sec)s"
Please provide your prefix ("" for none)''')

        modelfields=[]                                  #Create the list to hold the fields
        listOfPages=[]                                  #Create a list to hold the various pages in the notebook
        thismodel["NotebookPages"]=listOfPages          #Assign the pages list to the NotebookPages key in the model dictionary.

        #Capture the Field(s) information now. We loop on this because we likely want to add many fields.
        while(True):
            thisfield={}
            sys.stderr.write("\x1b[2J\x1b[H")
            fieldname=UserInput('Enter field Name (Enter "" when complete):')
            if fieldname=='':
                break
            thisfield["FieldName"]=snake(fieldname)
            fieldtype=UserInput('''_ Field Type _ 
               Options: [Char, Boolean, Selection, Integer, Float, Text, Many2many, Many2one, One2Many]
               Example "Char" ("." if complete):''').capitalize()
            thisfield["FieldType"] = fieldtype
            #pprint(thisfield["FieldType"])
            #print fieldtype
            if fieldtype=="Selection":
                selections=[]
                print '''_ Selection Options _ \n
Typical: [Child, Adult, Senior]'''
                while(True):
                    selectionName=UserInput('''_ State Name _ \n
                                               Typical: [Child, Adult, Senior]\n
                                               (Enter "" when complete):''').title()
                    if selectionName=="":
                        break
                    selections.append(selectionName)
                thisfield['fieldSelections']=selections

            #Ensure the relations are identified by "id" or "ids"
            if fieldtype=="Many2many":
                if fieldname.find("_ids")==0:
                    fieldname.__add__("_ids")
            if fieldtype=="Many2one":
                if fieldname.find("_id")==0:
                    fieldname.__add__("_id")
            if fieldtype=="One2many":
                if fieldname.find("_ids")==0:
                    fieldname.__add__("_ids")
            if (fieldtype=="One2many") or (fieldtype=="Many2one") or (fieldtype=="Many2many"):
                thisfield["FieldCoModel"]=UserInput("What is the co-model (related model) for the " + thisfield["FieldName"].capitalize() + " field?")

            thisfield["FieldHelp"]=UserInputRaw('"' + fieldname + '" field help text:')
            thisfield["FieldString"]=UserInput('"' + fieldname + '" field String name (Press ENTER to accept "' + reverseSnake(thisfield["FieldName"]) + '") :')
            if thisfield["FieldString"]=="":
                thisfield["FieldString"]=reverseSnake(thisfield["FieldName"])

            thisfield["FieldOnForm"]=True # What was I thinking, it has to be here.    #str2bool(UserInput('Should the ' + fieldname + ' field show on the form?:'))
            if thisfield["FieldOnForm"]==True:
                thisfield["FieldInNotebook"]=str2bool(UserInput('Should the "' + fieldname + '" field show in the notebook? (y/n):'))
                if thisfield["FieldInNotebook"]==True:
                    notebookpage = UserInput('Name of page this ' + fieldname + ' field appears on in the notebook:').title()
                    thisfield["FieldNotebookPage"] = notebookpage
                    listOfPages.append(notebookpage)
            thisfield["FieldInTree"]=str2bool(UserInput('Should the ' + fieldname + ' field exist in the tree? (y/n):'))
            if thisfield["FieldInTree"]==True:
                thisfield["FieldTreeVisible"]=str2bool(UserInput('Should the ' + fieldname + ' field is visible in the tree? (y/n):'))
            modelfields.append(thisfield)

        thismodel["fields"]=modelfields

        sys.stderr.write("\x1b[2J\x1b[H")
        print "\n\nGetting back to the " + modelname + " class..."
        listOfPages = list(set(listOfPages).intersection(listOfPages))                  # Remove duplicates
        thismodel["HasWizard"]=str2bool(UserInput('Is ' + modelname +' associated with a wizard? (y/n):'))
        if thismodel["HasWizard"]==True:
            thismodel["WizardModelName"]=UserInput('Name of the button that calls the wizard ("myWiz"):')
        thismodel["ModelSecurity"]=str2bool(UserInput('New Security required for this model? (y/n)'))

        thismodel["HasButtons"]=str2bool(UserInput('Would you like to add some buttons to the form? (y/n)'))
        if thismodel["HasButtons"]:
            buttons=[]
            while(True):
                thisbutton={}
                buttonname=UserInput('Button Name (Enter "" when complete):')
                if buttonname=='':
                    break
                thisbutton["ButtonName"]=buttonname
                thisbutton["ButtonFunction"]=UserInputSnake('What is the name of the function to be called when the ' + thisbutton["ButtonName"] + ' button is pressed?')
                buttons.append(thisbutton)
            thismodel["buttons"]=buttons

        models.append(thismodel)
    params = {'models':models}
    pprint(params)

#     params={'models':[{'ModelName': 'classAbc',\
#   'ModelDescription': 'description 1',\
#   'HasSequence': True,\
#   'SequenceName': 'Class1 Seq',\
#   'SequencePrefix': 'CS'},\
#  {'ModelName': 'classDef',\
#   'ModelDescription': 'My super long class 2 description',\
#   'HasSequence': False}]}


#     params={'ModuleName':ModuleName,
#             'models': [{'HasSequence': False,
#              'HasStates': True,
#              'ModelDescription': 'Parent Object',
#              'ModelHasMenu': False,
#              'ModelHasWizard': False,
#              'ModelInherits': False,
#              'ModelName': 'ClassOne',
#              'ModelSecurity': False,
#              'NotebookPages': [],
#              'fields': [{'FieldHelp': "Help I've fallen and I can't get up.",
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'name',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Char'},
#                         {'FieldHelp': "Man it's late",
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'age',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Integer'}],
#              'states': ['Default', 'Open', 'Closed', 'Cancel']},
#             {'buttons':[{'ButtonFunction': "jumpoffacliff",
#                          'ButtonName': "Jump Off A Cliff"},
#                         {'ButtonFunction': "lemming",
#                          'ButtonName': "Lemming"}],
#              'HasSequence': False,
#              'HasStates': False,
#              'IsWizard': True,
#              'ModelDescription': 'The terrible twos',
#              'ModelHasMenu': False,
#              'ModelHasWizard': False,
#              'ModelInherits': False,
#              'ModelName': 'ClassTwo',
#              'ModelSecurity': False,
#              'NotebookPages': ['Children'],
#              'fields': [{'FieldHelp': 'An encyclopedia of help',
#                          'FieldInNotebook': True,
#                          'FieldInTree': False,
#                          'FieldName': 'name',
#                          'FieldNotebookPage':'Children',
#                          'FieldOnForm': True,
#                          'FieldType': 'Char'}],
#              'WizardSrcModel':'ClassOne'}]}

# 
# {'models': [{'HasButtons': False,
#              'HasSequence': False,
#              'HasStates': False,
#              'HasWizard': False,
#              'IsWizard': False,
#              'ModelDescription': 'EventType',
#              'ModelHasMenu': False,
#              'ModelInherits': False,
#              'ModelName': 'Type',
#              'ModelSecurity': False,
#              'NotebookPages': [],
#              'fields': [{'FieldHelp': '',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'Name',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Char'},
#                         {'FieldHelp': "TheEmailAddressOfTheOrganizerWhichIsPutInThe'reply-to'OfAllEmails",
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'DefaultReplyTo',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Char'},
#                         {'FieldHelp': 'ItWillSelectThisDefaultConfirmationEventMailValueWhenYouChooseThisEvent.',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'DefaultEmailEvent',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Many2One'},
#                         {'FieldHelp': 'ItWillSelectThisDefaultConfirmationRegistrationMailValueWhenYouChooseThisEvent.',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'DefaultEmailRegistration',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Many2One'},
#                         {'FieldHelp': 'MinimumNumberOfGuestsForThisEvent.',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'DefaultRegistrationMin',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Integer'},
#                         {'FieldHelp': 'MaximumNumberOfGuestsForThisEvent.',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'DefaultRegistrationMax',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Integer'}]},
#             {'HasButtons': True,
#              'HasSequence': False,
#              'HasStates': True,
#              'HasWizard': False,
#              'InheritFromModel': "['mail.thread','ir.needaction.mixin']",
#              'IsWizard': False,
#              'MenuName': 'Event',
#              'ModelDescription': 'Event',
#              'ModelHasMenu': True,
#              'ModelInherits': True,
#              'ModelName': 'Event',
#              'ModelSecurity': False,
#              'NotebookPages': ['Registrations'],
#              'ParentMenu': '',
#              'buttons': [{'ButtonFunction': 'ButtonConfirm',
#                           'ButtonName': 'ButtonConfirm'},
#                          {'ButtonFunction': 'ButtonDone',
#                           'ButtonName': 'FinishEvent'},
#                          {'ButtonFunction': 'ButtonDraft',
#                           'ButtonName': 'SetToDraft'},
#                          {'ButtonFunction': 'ButtonCancel',
#                           'ButtonName': 'CancelEvent'}],
#              'fields': [{'FieldHelp': 'EventName',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'Name',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Char'},
#                         {'FieldHelp': 'ResponsibleUser',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'UserId',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Many2One'},
#                         {'FieldHelp': '',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'Type',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Many2One'},
#                         {'FieldHelp': 'YouCanForEachEvenDefineAMaximumRegistrationLevel.IfYouHaveTooMuchRegistrationsYouAreNotAbleToConfirmYourEvent.(put0InToIgnoreThisRule)',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'SeatsMax',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': False,
#                          'FieldType': 'Integer'},
#                         {'FieldHelp': 'YouCanForEachEvenDefineAMinimumRegistrationLevel.IfYouHaveNotEnoughRegistrationsYouAreNotAbleToConfirmYourEvent.(put0ToIgnoreThisRule)',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'SeatsMin',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Integer'},
#                         {'FieldHelp': '',
#                          'FieldInNotebook': True,
#                          'FieldInTree': False,
#                          'FieldName': 'RegistrationIds',
#                          'FieldNotebookPage': 'Registrations',
#                          'FieldOnForm': True,
#                          'FieldType': 'One2Many'},
#                         {'FieldHelp': 'StartDate',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'DateBegin',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Datetime'}],
#              'states': ['Default', 'Confirm', 'Done', 'Cancel']},
#             {'HasButtons': True,
#              'HasSequence': False,
#              'HasStates': True,
#              'HasWizard': False,
#              'InheritFromModel': 'Mail.thread',
#              'IsWizard': False,
#              'ModelDescription': 'EventRegistration',
#              'ModelHasMenu': False,
#              'ModelInherits': True,
#              'ModelName': 'Registration',
#              'ModelSecurity': False,
#              'NotebookPages': [],
#              'buttons': [{'ButtonFunction': 'RegistrationOpen',
#                           'ButtonName': 'Confirm'},
#                          {'ButtonFunction': 'ButtonRegClose',
#                           'ButtonName': 'Attended'},
#                          {'ButtonFunction': 'DoDraft',
#                           'ButtonName': 'SetToUnconfirmed'},
#                          {'ButtonFunction': 'ButtonRegCancel',
#                           'ButtonName': 'CancelRegistration'}],
#              'fields': [{'FieldHelp': '',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'Name',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Char'},
#                         {'FieldHelp': 'ReferenceOfTheSalesOrderThatCreatedTheRegistration',
#                          'FieldInNotebook': False,
#                          'FieldInTree': True,
#                          'FieldName': 'Origin',
#                          'FieldOnForm': True,
#                          'FieldTreeVisible': True,
#                          'FieldType': 'Char'}],
#              'states': ['Default', 'Open', 'Done', 'Cancel']}]}



    return params

def str2bool(v):
    '''
    This function converts an assortment of TRUE responses to a boolean True value.
    '''
    return v.lower().replace('"','') in ("y","yes", "true", "t", "1","affirmative","oui","yea")

def UserInput(promptMsg):
    '''
    This function sanitizes the user input a little.
    '''
    try:
        result=''
        result = raw_input(promptMsg) #make
    except KeyboardInterrupt:
        result =  ''
    return result.replace('"','')

def UserInputRaw(promptMsg):
    '''
    This function sanitizes the user input a little.
    '''
    try:
        result=''
        result = raw_input(promptMsg)
    except KeyboardInterrupt:
        result =  ''
    return result

def UserInputSnake(promptMsg):
    '''
    This function sanitizes the user input a little.
    '''
    try:
        result=''
        result = snake(raw_input(promptMsg)) #make
    except KeyboardInterrupt:
        result =  ''
    return result.replace('"','')

def UserInputPascal(promptMsg):
    '''
    This function sanitizes the user input a little.
    '''
    try:
        result=''
        result = pascal(raw_input(promptMsg)) #make
    except KeyboardInterrupt:
        result =  ''
    return result.replace('"','')
