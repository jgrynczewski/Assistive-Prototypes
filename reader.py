#!/bin/env python2.7
# -*- coding: utf-8 -*-

# This file is part of AP - Assistive Prototypes.
#
# AP is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# AP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AP. If not, see <http://www.gnu.org/licenses/>.

class reader():
    def __init__(self):
        self.parameters = []

        with open( './.pathToAP' ,'r' ) as textFile:
            self.pathToAP = textFile.readline( )

    #-------------------------------------------------------------------------    
    def readParameters(self):
        
        with open( self.pathToAP + 'parameters', 'r' ) as parametersFile:
            for line in parametersFile:
                self.parameters.append( "".join( line.split() ) )
    
    #-------------------------------------------------------------------------
    def getParameters(self):

        if self.parameters == []:
            self.readParameters()
            
        return self.parameters

    #-------------------------------------------------------------------------
    def setParameter(self, param, value):

        if self.parameters == []:
            self.getParameters()

        for idx, item in enumerate(self.parameters):
            if item.startswith(str(param)):
                self.parameters[idx] = "%s = %s" %(param, value)
            
        with open( self.pathToAP + 'parameters', 'w' ) as parametersFile:
                parametersFile.write( "\n".join(self.parameters) )

    #-------------------------------------------------------------------------
    def saveVolume(self, value):

        for idx, item in enumerate(self.parameters):
            if item.startswith("volumeLevel"):
                self.parameters[idx] = "volumeLevel = " + str(value)

        with open( self.pathToAP + 'parameters', 'w' ) as parametersFile:
                parametersFile.write( "\n".join(self.parameters) )
