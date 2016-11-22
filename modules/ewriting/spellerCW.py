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

import wxversion
# wxversion.select( '2.8' )

import glob, os, time, sys, codecs
import wx
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer
import subprocess as sp
import shlex

import numpy as np

#=============================================================================
class speller( wx.Frame ):

	def __init__(self, parent):

                self.winWidth, self.winHeight = wx.DisplaySize( )

		self.parent = parent

		self.initializeParameters( )
		self.initializeBitmaps( )
		self.createGui( )

	#-------------------------------------------------------------------------
	def initializeParameters(self):

                textFile = codecs.open("./.pathToAP", mode="r", encoding="utf-8")
                self.pathToAP = textFile.readline()
                textFile.close()

		sys.path.append( self.pathToAP )
		from reader import reader
		
		reader = reader()
		reader.readParameters()
		parameters = reader.getParameters()

		for item in parameters:
			try:
				setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
			except ValueError:
				setattr(self, item[:item.find('=')], item[item.find('=')+1:])

		sys.path.append( self.pathToAP + 'modules/others' )
		from speller import speller
		sp = speller( parent = None, id = -1, con = 0 )
		label = sp.getLabels( )
		sp.onExit( ) 

		label1 = label[ 0 ]
		label2 = label[ 1 ]
		self.partLabel1, self.partLabel2 = [ ], [ ]
		
		for item in label1:
			if len(item) == 1 or len(item) == 2 :
				self.partLabel1.append( item )
			else:
				continue
		for item in label2:
			if len(item) == 1 or len(item) == 2:
				self.partLabel2.append( item )
			else:
				continue
                
		if len( self.partLabel1 ) == 23:
			self.labels = [ self.partLabel1 + 'SPECIAL_CHARACTERS DELETE TRASH CHECK ORISPEAK SPEAK EXIT'.split( ), self.partLabel2 + 'DELETE TRASH CHECK ORISPEAK SPEAK EXIT'.split( ) ]

			self.numberOfRows = [ 4, 5 ]
			self.specialButtonsMarker = -3
			self.startIndex = -7
			self.spaceButton = 3
	
		elif len( self.partLabel1 ) == 32:
			self.labels = [ self.partLabel1 + 'DELETE TRASH CHECK ORISPEAK SPEAK EXIT'.split( ), self.partLabel2 + 'DELETE TRASH CHECK ORISPEAK SPEAK EXIT'.split( ) ]
			self.numberOfRows = [ 5, 5 ]
			self.specialButtonsMarker = -4
			self.startIndex = -6
			self.spaceButton = 2
		else:
			print 'Blad w definiowaniu tablicy'
			exit( )

		self.colouredLabels = [ 'A','E','I','O','U','Y']
		self.colouredLabels2 = [ 'Ą', 'Ć', 'Ę', 'Ł', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż' ]

		self.numberOfColumns = [ 8, 9 ]
			
		mixer.init( )	
		if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
                        self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
                        self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )
		
		if self.voice == 'True':
			self.phones = glob.glob( self.pathToAP + 'sounds/phone/*' )
			self.phoneLabels = [ item[ item.rfind( '/' )+1 : item.rfind( '.' ) ] for item in self.phones ]
			self.sounds = [ mixer.Sound( self.sound ) for self.sound in self.phones ]

			self.rows = glob.glob( self.pathToAP + 'sounds/rows/*' )
			self.rowLabels = [ item[ item.rfind( '/' )+1 : item.rfind( '.' ) ] for item in self.rows ]
			self.rowSounds = [ mixer.Sound( self.sound ) for self.sound in self.rows ]

		self.SLOWO = self.parent.WORD
                self.slowo = self.parent.word

		if self.ileLuk >= len( self.SLOWO ):
                        self.ileLuk = len( self.SLOWO ) - 1

                self.flag = 'row'						
		self.pressFlag = False
                self.rowIteration = 0						
                self.columnIteration = 0							
                self.countRows = 0
                self.countColumns = 0										
		
		self.maxNumberOfRows = 2
                self.maxNumberOfColumns = 2
	    
                self.numberOfPresses = 1
                self.subSizerNumber = 0

                self.mouseCursor = PyMouse( )
		self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
		self.mouseCursor.move( *self.mousePosition )			

                self.typewriterKeySound = mixer.Sound( self.pathToAP + 'sounds/typewriter_key.ogg' )
                self.typewriterForwardSound = mixer.Sound( self.pathToAP + 'sounds/typewriter_forward.ogg' )
                self.typewriterSpaceSound = mixer.Sound( self.pathToAP + 'sounds/typewriter_space.ogg' )
                	    
                self.parent.SetBackgroundColour( 'black' )
		
	#-------------------------------------------------------------------------
        def initializeBitmaps(self):

            self.path=self.pathToAP+'icons/ewriting/'

            self.labelBitmaps = { }

	    if self.specialButtonsMarker == -3:
		    labelFiles = [ file for file in [ self.path+'speller/special_characters.png', self.path+'speller/DELETE.png', self.path+'speller/TRASH.png',   self.path+'speller/CHECK.png',self.path+'speller/ORISPEAK.png', self.path+'speller/SPEAK.png', self.path+'speller/exit.png', ] ]

		    labelBitmapIndex = [ self.labels[ 0 ].index( self.labels[ 0 ][ -7 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -6 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -5 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -4 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -3 ] ),self.labels[ 0 ].index( self.labels[ 0 ][ -2 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -1 ] ) ]

	    elif self.specialButtonsMarker == -4:
		    labelFiles = [ file for file in [ self.path+'speller/DELETE.png', self.path+'speller/TRASH.png',   self.path+'speller/CHECK.png',self.path+'speller/ORISPEAK.png', self.path+'speller/SPEAK.png', self.path+'speller/exit.png', ] ]

		    labelBitmapIndex = [ self.labels[ 0 ].index( self.labels[ 0 ][ -6 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -5 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -4 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -3 ] ),self.labels[ 0 ].index( self.labels[ 0 ][ -2 ] ), self.labels[ 0 ].index( self.labels[ 0 ][ -1 ] ) ]
	    
	    labelFiles44 = [ file for file in [ self.path+'speller/special_characters.png', self.path+'speller/DELETE.png', self.path+'speller/TRASH.png',   self.path+'speller/CHECK.png',self.path+'speller/ORISPEAK.png', self.path+'speller/SPEAK.png', self.path+'speller/exit.png', ] ]

            for labelFilesIndex, labelIndex in enumerate( labelBitmapIndex ):
		    self.labelBitmaps[ self.labels[ 0 ][ labelIndex ] ] = wx.BitmapFromImage( wx.ImageFromStream( open( labelFiles[ labelFilesIndex ], 'rb' )) )      

            self.labelBitmaps2 = { }
	    
	    labelBitmapIndex2 = [ self.labels[ 1 ].index( self.labels[ 1 ][ -6 ] ), self.labels[ 1 ].index( self.labels[ 1 ][ -5 ] ), self.labels[ 1 ].index( self.labels[ 1 ][ -4 ] ), self.labels[ 1 ].index( self.labels[ 1 ][ -3 ] ),self.labels[ 1 ].index( self.labels[ 1 ][ -2 ] ), self.labels[ 1 ].index( self.labels[ 1 ][ -1 ] ) ]

            for labelFilesIndex2, labelIndex2 in enumerate( labelBitmapIndex2 ):
		    self.labelBitmaps2[ self.labels[ 1 ][ labelIndex2 ] ] = wx.BitmapFromImage( wx.ImageFromStream( open( labelFiles44[ 1: ][ labelFilesIndex2 ], 'rb' )) )

	#-------------------------------------------------------------------------	
	def createGui(self):

		self.thicknessOfExternalBorder = self.yBorder # factor related to the border of the entire board
		self.thicknessOfInternalBorder = self.xBorder # factor related to the border of every button 

		self.textFieldWidth = self.winWidth
		self.textFieldHeight = 0.2 * ( self.winHeight - 20 ) # -20 because of the Unity upper bar

		self.buttonsBoardWidth  = self.winWidth - self.thicknessOfExternalBorder * 2 - self.thicknessOfInternalBorder * ( self.numberOfColumns[ 0 ] - 1 )
		self.buttonsBoardHeight = ( self.winHeight - 20 ) - self.textFieldHeight - self.thicknessOfExternalBorder * 3 - self.thicknessOfInternalBorder * ( self.numberOfRows[ 0 ] - 1 ) # -20 because of the Unity upper bar
		
		self.textField = wx.TextCtrl( self.parent, style = wx.TE_CENTRE | wx.TE_RICH2, size = ( self.textFieldWidth, self.textFieldHeight ) )
		self.textField.SetFont( wx.Font(  self.textFontSize, eval( self.textFont ), wx.NORMAL, wx.NORMAL ) )
		self.parent.mainSizer.Add( self.textField, flag = wx.EXPAND | wx.TOP | wx.BOTTOM, border = self.xBorder )
		
		self.subSizers = [ ]
		
		subSizer = wx.GridBagSizer( self.xBorder, self.yBorder )

		if self.control != 'tracker':
			event = eval('wx.EVT_LEFT_DOWN')
		else:
			event = eval('wx.EVT_BUTTON')

		for index_1, item in enumerate( self.labels[ 0 ][ :self.startIndex ] ):
			b = bt.GenButton( self.parent, -1, item, name = item, size = ( self.buttonsBoardWidth / float( self.numberOfColumns[ 0 ] ), self.buttonsBoardHeight / float( self.numberOfRows[ 0 ] ) ) )
			b.SetFont( wx.Font( self.tableFontSize, eval( self.tableFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
			b.SetBezelWidth( 3 )
			b.SetBackgroundColour( self.backgroundColour )

			if item in self.colouredLabels and self.vowelColour != 'False':
				b.SetForegroundColour( self.vowelColour )
			else:
				b.SetForegroundColour( self.textColour )

			b.Bind( event, self.onPress )
			subSizer.Add( b, ( index_1 / self.numberOfColumns[ 0 ], index_1 % self.numberOfColumns[ 0 ] ), wx.DefaultSpan, wx.EXPAND )

		for index_2, item in enumerate( self.labels[ 0 ][ self.startIndex : ] ):
                        if index_2 == self.spaceButton:
				b = bt.GenBitmapButton( self.parent, -1, name = item, bitmap = self.labelBitmaps[ item ], size = ( 3 * (self.buttonsBoardWidth / float( self.numberOfColumns[ 0 ] )), self.buttonsBoardHeight / float( self.numberOfRows[ 0 ] ) ) )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )
				
				subSizer.Add( b, ( ( index_1 + index_2 +1) / self.numberOfColumns[ 0 ], ( index_1 + index_2+1 ) % self.numberOfColumns[ 0 ] ), (1,3), wx.EXPAND )
                        elif index_2 > self.spaceButton:
				b = bt.GenBitmapButton( self.parent, -1, name = item, bitmap = self.labelBitmaps[ item ], size = ( self.buttonsBoardWidth / float( self.numberOfColumns[ 0 ] ), self.buttonsBoardHeight / float( self.numberOfRows[ 0 ] ) ) )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )
                        
				subSizer.Add( b, ( ( index_1 + index_2 +3) / self.numberOfColumns[ 0 ], ( index_1 + index_2 +3) % self.numberOfColumns[ 0 ] ), wx.DefaultSpan, wx.EXPAND )
                        else:
				b = bt.GenBitmapButton( self.parent, -1, name = item, bitmap = self.labelBitmaps[ item ], size = ( self.buttonsBoardWidth / float( self.numberOfColumns[ 0 ] ), self.buttonsBoardHeight / float( self.numberOfRows[ 0 ] ) ) )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )

                                subSizer.Add( b, ( ( index_1 + index_2+1 ) / self.numberOfColumns[ 0 ], ( index_1 + index_2 +1) % self.numberOfColumns[ 0 ] ), wx.DefaultSpan, wx.EXPAND )
                        
		self.subSizers.append( subSizer )		    
		self.parent.mainSizer.Add( self.subSizers[ 0 ], proportion = 1, flag = wx.EXPAND | wx.LEFT, border = self.yBorder )
		self.parent.SetSizer( self.parent.mainSizer )
		
		subSizer2 = wx.GridBagSizer( self.xBorder, self.yBorder )

		self.buttonsBoardWidth2  = self.winWidth - self.thicknessOfExternalBorder * 2 - self.thicknessOfInternalBorder * ( self.numberOfColumns[ 1 ] - 1 )
		self.buttonsBoardHeight2 = ( self.winHeight - 20 ) - self.textFieldHeight - self.thicknessOfExternalBorder * 3 - self.thicknessOfInternalBorder * ( self.numberOfRows[ 1 ] - 1 ) # -20 because of the Unity upper bar

		for index_1, item in enumerate( self.labels[ 1 ][ :-6 ] ):
			b = bt.GenButton( self.parent, -1, item, name = item, size = ( self.buttonsBoardWidth2 / float( self.numberOfColumns[ 1 ] ), self.buttonsBoardHeight2 / float( self.numberOfRows[ 1 ] ) ) )
			b.SetFont( wx.Font( self.tableFontSize, eval( self.tableFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
			b.SetBezelWidth( 3 )
			b.SetBackgroundColour( self.backgroundColour )
			b.SetForegroundColour( self.textColour )
			b.Bind( event, self.onPress )
			subSizer2.Add( b, ( index_1 / self.numberOfColumns[ 1 ], index_1 % self.numberOfColumns[ 1 ] ), wx.DefaultSpan, wx.EXPAND )

		for index_2, item in enumerate( self.labels[ 1 ][ -6 :  ] ):
			if index_2 == 2:
				b = bt.GenBitmapButton( self.parent, -1, name = item, bitmap = self.labelBitmaps2[ item ], size = ( 3 * (self.buttonsBoardWidth2 / float( self.numberOfColumns[ 1 ] )), self.buttonsBoardHeight2 / float( self.numberOfRows[ 1 ] ) ) )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )

                                subSizer2.Add( b, ( ( index_1 + index_2 +1) / self.numberOfColumns[ 1 ], ( index_1 + index_2 +1) % self.numberOfColumns[ 1 ] ), (1,4), wx.EXPAND )

                        elif index_2 > 2:
				b = bt.GenBitmapButton( self.parent, -1, name = item, bitmap = self.labelBitmaps2[ item ], size = ( self.buttonsBoardWidth2 / float( self.numberOfColumns[ 1 ] ), self.buttonsBoardHeight2 / float( self.numberOfRows[ 1 ] ) ) )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )

                                subSizer2.Add( b, ( ( index_1 + index_2 +4) / self.numberOfColumns[ 1], ( index_1 + index_2+4 ) % self.numberOfColumns[ 1 ] ), wx.DefaultSpan, wx.EXPAND )
                        else:
				b = bt.GenBitmapButton( self.parent, -1, name = item, bitmap = self.labelBitmaps2[ item ], size = ( self.buttonsBoardWidth2 / float( self.numberOfColumns[ 1 ] ), self.buttonsBoardHeight2 / float( self.numberOfRows[ 1 ] ) ) )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )

                                subSizer2.Add( b, ( ( index_1 + index_2+1 ) / self.numberOfColumns[ 1 ], ( index_1 + index_2 +1) % self.numberOfColumns[ 1 ] ), wx.DefaultSpan, wx.EXPAND )
                        
		self.subSizers.append( subSizer2 )		   
		self.parent.mainSizer.Add( self.subSizers[ 1 ], proportion = 1, flag = wx.EXPAND | wx.LEFT, border = self.yBorder )
		self.parent.mainSizer.Show( item = self.subSizers[ 1 ], show = False, recursive = True )
		self.parent.SetSizer( self.parent.mainSizer )
		
		ktore = [ ] #ktore litery wykropkowac

		if len( self.SLOWO ) == 2:
                        ktore = [ 1 ]
                else:
                        while len( ktore ) < self.ileLuk:
                                ktore.append( np.random.randint( 0, len( self.SLOWO ), 1 )[ 0 ] )
                                ktore = list( set( ktore ) )

		SLOWO = list( self.SLOWO )
		ktore = sorted( ktore )
		self.samogloski = [ ]

		for i in ktore:
                        SLOWO[ i ] = '_'       

                self.ktore = ktore
		self.textField.WriteText( ''.join( SLOWO ) )
		self.ilejuz = 0
		self.czyjuz = False
		self.parent.Layout( )

	#----------------------------------------------------------------------------
	def onExit(self):

                self.parent.PicNr -= 1
		self.parent.stoper2.Stop( )
		self.parent.back( )
		
	#----------------------------------------------------------------------------
        def czytajLitere(self, litera):

                soundIndex = self.phoneLabels.index( [ item for item in self.phoneLabels if litera in item ][ 0 ] )
		sound = self.sounds[ soundIndex ]
		sound.play( )
                self.parent.SetFocus( )
                time.sleep( 1 )

	#----------------------------------------------------------------------------
	def onPress(self, event):

		if self.pressSound.lower( ) != 'off':
			self.pressingSound.play( )

		if self.control == 'tracker':
			if self.pressFlag == False:
				self.button = event.GetEventObject( )
				self.button.SetBackgroundColour( self.selectionColour )
				self.pressFlag = True
				self.label = event.GetEventObject().GetName().encode( 'utf-8' )
				self.parent.stoper2.Start( 0.15 * self.timeGap )

				if self.label == 'SPECIAL_CHARACTERS':								

					self.subSizerNumber = 1

					self.parent.mainSizer.Show( item = self.subSizers[ 1 ], show = True, recursive = True )
					self.parent.mainSizer.Show( item = self.subSizers[ 0 ], show = False, recursive = True )					
					self.parent.SetSizer( self.parent.mainSizer )
					self.parent.Layout( )
					if self.voice:
						item = self.button
						b = item.GetWindow( )
						b.SetBackgroundColour( 'indian red' )
						b.SetFocus( )
						b.Update( )
					else:
						item = self.button
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )
						b.Update( )

				elif self.label == 'DELETE':
					if self.ilejuz > 0 and self.czyjuz: 
						self.typewriterForwardSound.play( )
						self.textField.Replace( self.textField.GetInsertionPoint( ) - 1, self.textField.GetInsertionPoint( ), '_' )
						self.ilejuz -= 1
						self.czyjuz = False

				elif self.label == 'SPEAK':
					if not self.voice:
						self.voice = True
						b = self.button
						b.SetBackgroundColour( 'indian red' )
						b.SetFocus( )
						b.Update( )
					else:
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )
						b.Update( )
						self.voice = False

				elif self.label == 'ORISPEAK':
					self.parent.stoper2.Stop( )

                                        if (self.slowo + ".ogg") not in os.listdir( self.pathToAP + u"multimedia/ewriting/spelling/" ):        
                                                command = 'sox -m '+ self.pathToAP + 'sounds/phone/' + list( self.slowo )[ 0 ].swapcase( ) + '.ogg'
                                                ile = 0

                                                for l in list( self.slowo )[ 1: ]:
                                                        ile += 2
                                                        command += ' "|sox ' + self.pathToAP + "sounds/phone/" + l.swapcase() + ".ogg" + ' -p pad ' + str( ile ) + '"'

                                                command += ' ' + self.pathToAP + 'multimedia/ewriting/spelling/' + self.slowo + '.ogg'
                                                wykonaj = sp.Popen( shlex.split( command.encode("utf-8") ) )

						time.sleep( 1.5 )
                                                unicodePath = self.pathToAP + u"multimedia/ewriting/spelling/" + self.slowo + u".ogg"
                                                voice = open(unicodePath, 'rb')
						do_literowania = mixer.Sound(voice)
						do_literowania.play( )
						self.parent.stoper4.Start( ( do_literowania.get_length( ) + 0.5 ) * 1000 )

				elif self.label == 'TRASH':
					text = self.textField.GetValue( )

					if text.count( '_' ) < self.ileLuk:
						self.typewriterForwardSound.play( )
						for i in self.ktore:
							self.textField.Replace( i, i + 1, '_' )
							self.ilejuz = 0

				elif self.label == 'EXIT':

					if self.subSizerNumber == 0:
						self.onExit( )

					else:	
						self.parent.mainSizer.Show( item = self.subSizers[ self.subSizerNumber ], show = False, recursive = True )

						self.subSizerNumber = 0
						self.parent.mainSizer.Show( item = self.subSizers[ self.subSizerNumber ], show = True, recursive = True )

						self.parent.SetSizer( self.parent.mainSizer )
						self.parent.Layout( )

						if self.voice:
							b = self.button
							b.SetBackgroundColour( 'indian red' )
							b.SetFocus( )
							b.Update( )
						else:
							b = self.button
							b.SetBackgroundColour( self.backgroundColour )
							b.SetFocus( )
							b.Update( )

				elif self.label == 'CHECK':
					self.parent.stoper2.Stop( )
					self.parent.ownWord = self.textField.GetValue( )
					self.parent.check( )

				else:
					if self.ilejuz < self.ileLuk:
						self.typewriterKeySound.play( )
						self.textField.SetInsertionPoint( self.ktore[ self.ilejuz ] )
						self.textField.Remove( self.textField.GetInsertionPoint( ), self.textField.GetInsertionPoint( ) + 1 )
						self.textField.WriteText( self.label )
						self.ilejuz += 1
						self.czyjuz = True

		else:
			self.numberOfPresses += 1

			if self.numberOfPresses == 1:

				if self.flag == 'rest':
					self.flag = 'row'
					self.rowIteration = 0
					self.countRows = 0

				elif self.flag == 'row':

					if self.rowIteration != self.numberOfRows[ self.subSizerNumber ]:
						buttonsToHighlight = range( ( self.rowIteration - 1 ) * self.numberOfColumns[ self.subSizerNumber ], ( self.rowIteration - 1 ) * self.numberOfColumns[ self.subSizerNumber ] + self.numberOfColumns[ self.subSizerNumber ] )
					else:
						buttonsToHighlight = range( ( self.rowIteration - 1 ) * self.numberOfColumns[ self.subSizerNumber ], ( self.rowIteration - 1 ) * self.numberOfColumns[ self.subSizerNumber ] + 6 )

					for i, button in enumerate( buttonsToHighlight ):
						# if self.rowIteration - 1 == self.numberOfRows[ self.subSizerNumber ] - 1 and i == len( buttonsToHighlight ) - 2 and self.voice:
						# 	pass
						# else:
						item = self.subSizers[ self.subSizerNumber ].GetItem( button )
						b = item.GetWindow( )
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus( )
						b.Update( )

                                        self.parent.stoper2.Stop( )
                                        time.sleep( self.selectionTime/1000. )
                                        self.parent.stoper2.Start( self.timeGap )

					self.flag = 'columns' 
					self.rowIteration -= 1
					self.columnIteration = 0

				elif self.flag == 'columns' and self.rowIteration != self.numberOfRows[ self.subSizerNumber ] - 1:

					item = self.subSizers[ self.subSizerNumber ].GetItem( ( self.rowIteration ) * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration - 1 )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.selectionColour )
					b.SetFocus( )
					b.Update( )

                                        self.parent.stoper2.Stop( )
                                        time.sleep( self.selectionTime/1000. )
                                        self.parent.stoper2.Start( self.timeGap )

					label = self.labels[ self.subSizerNumber ][ self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration - 1 ]

					if label == 'SPECIAL_CHARACTERS':								

						self.subSizerNumber = 1

						self.parent.mainSizer.Show( item = self.subSizers[ 1 ], show = True, recursive = True )
						self.parent.mainSizer.Show( item = self.subSizers[ 0 ], show = False, recursive = True )					
						self.parent.SetSizer( self.parent.mainSizer )
						self.parent.Layout( )
						if self.voice:
							item = self.subSizers[ self.subSizerNumber ].GetItem( self.numberOfRows[self.subSizerNumber ] * self.numberOfColumns[ self.subSizerNumber ] - 5 )
							b = item.GetWindow( )
							b.SetBackgroundColour( 'indian red' )
							b.SetFocus( )
							b.Update( )
						else:
							item = self.subSizers[ self.subSizerNumber ].GetItem( self.numberOfRows[self.subSizerNumber ] * self.numberOfColumns[ self.subSizerNumber ] - 5 )
							b = item.GetWindow( )
							b.SetBackgroundColour( self.backgroundColour )
							b.SetFocus( )
							b.Update( )

					else:
						if self.ilejuz < self.ileLuk:
							self.typewriterKeySound.play( )
							self.textField.SetInsertionPoint( self.ktore[ self.ilejuz ] )
							self.textField.Remove( self.textField.GetInsertionPoint( ), self.textField.GetInsertionPoint( ) + 1 )
							self.textField.WriteText( label )
							self.ilejuz += 1
							self.czyjuz = True

					self.flag = 'row'
					self.rowIteration = 0
					self.columnIteration = 0
					self.countColumns = 0

				elif self.flag == 'columns' and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1:

					item = self.subSizers[ self.subSizerNumber ].GetItem( ( self.rowIteration ) * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration-1 )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.selectionColour )
					b.SetFocus( )
					b.Update( )

                                        self.parent.stoper2.Stop( )
                                        time.sleep( self.selectionTime/1000. )
                                        self.parent.stoper2.Start( self.timeGap )

					label = self.labels[ self.subSizerNumber ][ self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration-1 ]

					if label == 'DELETE':
						if self.ilejuz > 0 and self.czyjuz: 
							self.typewriterForwardSound.play( )
							self.textField.Replace( self.textField.GetInsertionPoint( ) - 1, self.textField.GetInsertionPoint( ), '_' )
							self.ilejuz -= 1
							self.czyjuz = False

					elif label == 'SPEAK':
						b.SetBackgroundColour( 'red' )
						b.SetFocus( )
						b.Update( )

					elif label == 'ORISPEAK':
						self.parent.stoper2.Stop( )

						if (self.slowo + ".ogg") not in os.listdir( self.pathToAP + u"multimedia/ewriting/spelling/" ):        
							command = 'sox -m '+ self.pathToAP + 'sounds/phone/' + list( self.slowo )[ 0 ].swapcase( ) + '.ogg'
							ile = 0

							for l in list( self.slowo )[ 1: ]:
                                                                ile += 2
                                                                command += ' "|sox ' + self.pathToAP + "sounds/phone/" + l.swapcase() + ".ogg" + ' -p pad ' + str( ile ) + '"'

							command += ' ' + self.pathToAP + 'multimedia/ewriting/spelling/' + self.slowo + '.ogg'
							wykonaj = sp.Popen( shlex.split( command.encode("utf-8") ) )

						time.sleep( 1.5 )
                                                unicodePath = self.pathToAP + u"multimedia/ewriting/spelling/" + self.slowo + u".ogg"
                                                voice = open(unicodePath, 'rb')
						do_literowania = mixer.Sound(voice)
						do_literowania.play( )
						self.parent.stoper4.Start( ( do_literowania.get_length( ) + 0.5 ) * 1000 )

					elif label == 'TRASH':
						text = self.textField.GetValue( )

						if text.count( '_' ) < self.ileLuk:
							self.typewriterForwardSound.play( )
							for i in self.ktore:
								self.textField.Replace( i, i + 1, '_' )
								self.ilejuz = 0

					elif label == 'EXIT':

						if self.subSizerNumber == 0:
                                                        self.parent.stoper2.Stop( )
                                                        time.sleep( self.timeGap/1000. )
                                                        self.parent.stoper2.Start( self.timeGap )

							self.onExit( )

						else:	
                                                        self.parent.stoper2.Stop( )
                                                        time.sleep( self.timeGap/1000. )
                                                        self.parent.stoper2.Start( self.timeGap )

							self.parent.mainSizer.Show( item = self.subSizers[ self.subSizerNumber ], show = False, recursive = True )

							self.subSizerNumber = 0
							self.parent.mainSizer.Show( item = self.subSizers[ self.subSizerNumber ], show = True, recursive = True )

							self.parent.SetSizer( self.parent.mainSizer )
							self.parent.Layout( )

							if self.voice:
								item = self.subSizers[ 0 ].GetItem( self.numberOfRows[ self.subSizerNumber ] * self.numberOfColumns[ self.subSizerNumber ] -4 )
								b = item.GetWindow( )
								b.SetBackgroundColour( 'indian red' )
								b.SetFocus( )
								b.Update( )
							else:
								item = self.subSizers[ 0 ].GetItem( self.numberOfRows[ self.subSizerNumber ] * self.numberOfColumns[ self.subSizerNumber ] - 4 )
								b = item.GetWindow( )
								b.SetBackgroundColour( self.backgroundColour )
								b.SetFocus( )
								b.Update( )

					else:
                                                self.parent.stoper2.Stop( )
                                                time.sleep( self.timeGap/1000. )
                                                self.parent.stoper2.Start( self.timeGap )

						self.parent.stoper2.Stop( )
						self.parent.ownWord = self.textField.GetValue( )
						self.parent.check( )

					self.flag = 'row'
					self.rowIteration = 0
					self.columnIteration = 0
					self.countRows = 0
					self.countColumns = 0

			else:
				event.Skip( )		
	
	#-------------------------------------------------------------------------
	def timerUpdate(self, event):

		if self.control == 'tracker':

			if self.button.GetBackgroundColour( ) == self.backgroundColour:
				self.button.SetBackgroundColour( self.selectionColour )
				
			else:
				self.button.SetBackgroundColour( self.backgroundColour )	

			# self.parent.stoper2.Stop( )
			self.stoper.Stop( )
			self.pressFlag = False

		else:
			self.mouseCursor.move( *self.mousePosition )
			self.numberOfPresses = 0
			# self.numberOfIteration += 1

			if self.flag == 'rest':
				pass
			
			elif self.flag == 'row':

				if self.countRows == self.maxNumberOfRows:
					self.flag = 'rest'
					self.countRows = 0

					items = self.subSizers[ self.subSizerNumber ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

				else:
					if self.switchSound.lower( ) != 'off' and self.voice == 'False':
						self.switchingSound.play( )

					self.rowIteration = self.rowIteration % self.numberOfRows[ self.subSizerNumber ]

					items = self.subSizers[ self.subSizerNumber ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

					if self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1:
						self.countRows += 1
						buttonsToHighlight = range( self.rowIteration * self.numberOfColumns[ self.subSizerNumber ], self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + 6 )

					else:
						buttonsToHighlight = range( self.rowIteration * self.numberOfColumns[ self.subSizerNumber ], self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + self.numberOfColumns[ self.subSizerNumber ] )

					for button in buttonsToHighlight:
						item = self.subSizers[ self.subSizerNumber ].GetItem( button )
						b = item.GetWindow( )
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus( )

					self.rowIteration += 1

					if self.voice == 'True':
						for idx, item in enumerate( self.rowLabels ):
							if int(item) == self.rowIteration:
								self.rowSounds[ idx ].play( )
								break

			elif self.flag == 'columns':

				if self.countColumns == self.maxNumberOfColumns:
					self.flag = 'row'

					item = self.subSizers[ self.subSizerNumber ].GetItem( self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration - 1 )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )

					self.rowIteration = 0
					self.countRows = 0
					self.columnIteration = 0
					self.countColumns = 0

				else:
					if (self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 1 and self.rowIteration != self.numberOfRows[ self.subSizerNumber] - 1) or (self.subSizerNumber == 0 and self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 3 and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1 and self.specialButtonsMarker == -3) or ( self.subSizerNumber == 1 and self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 4 and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1 ) or (self.subSizerNumber == 0 and self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 3 and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1 and self.specialButtonsMarker == -4):
						self.countColumns += 1

					if self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] or ( self.subSizerNumber == 0 and self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 2 and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1 and self.specialButtonsMarker == -3) or ( self.subSizerNumber == 1 and self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 3 and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1 ) or ( self.subSizerNumber == 0 and self.columnIteration == self.numberOfColumns[ self.subSizerNumber ] - 2 and self.rowIteration == self.numberOfRows[ self.subSizerNumber ] - 1 and self.specialButtonsMarker == -4):
						self.columnIteration = 0

					items = self.subSizers[ self.subSizerNumber ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

					item = self.subSizers[ self.subSizerNumber ].GetItem( self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.scanningColour )
					b.SetFocus( )
										
					if self.voice == 'True':
						label = self.labels[ self.subSizerNumber ][ self.rowIteration * self.numberOfColumns[ self.subSizerNumber ] + self.columnIteration ]

						try:
							soundIndex = self.phoneLabels.index( [ item for item in self.phoneLabels if item == label ][ 0 ] )
							sound = self.sounds[ soundIndex ]
							sound.play( )

						except IndexError:
							pass


					if self.switchSound.lower( ) != 'off' and self.voice == 'False':
						self.switchingSound.play( )

					self.columnIteration += 1
					
			else:
				pass

