#!/bin/env python2.7
# -*- coding: utf-8 -*-
import os
from string import maketrans
import time

text='0'

# inputTable = '~!#$&( )[]{}<>;:"\|'
# outputTable = ' ' * len( inputTable )
# translateTable = maketrans( inputTable, outputTable )
# textToSpeech = text.translate( 

replacements = { '-' : ' minus ', 
                 '+' : ' plus ', 
                 '*' : ' razy ', 
                 '/' : ' podzielić na ', 
                 '=' : ' równa się ', 
                 '%' : ' procent ', 
                 '$' : ' dolar', 
                 '~' : 'tylda', 
                 '!' : 'wykrzyknik', 
                 '#' : 'hasz', 
                 '&' : 'ampersand', 
                 '(' : 'nawias okrągły', 
                 ')' : 'nawias okrągły', 
                 '[' : 'nawias kwadratowy', 
                 ']' : 'nawias kwadratowy', 
                 '{' : 'nawias klamrowy', 
                 '}' : 'nawias klamrowy', 
                 '<' : 'nawias ostrokątny', 
                 '>' : 'nawias ostrokątny', 
                 ';' : 'średnik', 
                 ':' : 'dwukropek', 
                 '\\' : 'ukośnik', 
                 '"' : 'cudzysłów', 
                 '\'': 'apostrof' 
}

textToSpeech = reduce( lambda text, replacer: text.replace( *replacer ), replacements.iteritems( ), text )
print textToSpeech
os.system( 'milena_say %s' %textToSpeech )
