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
# wxversion.select('2.8')

import os, time, sys, psutil, codecs
from random import shuffle

import wx
import wx.lib.buttons as bt
from pymouse import PyMouse
import numpy as np

import subprocess as sp
import shlex
from pygame import mixer

import check

#=============================================================================
class cwiczenia(wx.Frame):
	def __init__(self, parent, id):

		self.winWidth, self.winHeight = wx.DisplaySize( )
		
		wx.Frame.__init__( self , parent , id , 'EMatch' )
                style = self.GetWindowStyle( )
		self.SetWindowStyle( style | wx.STAY_ON_TOP )
		self.parent = parent

		self.Maximize( True )
		self.Center( True )
		self.MakeModal( True )

		self.initializeParameters( )
		self.createGui( )
		self.createBindings( )

		self.initializeTimer( )

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

		self.flaga = 0
		self.checkFlag = False
		self.flag = 'row'
		self.columnIteration = 0
		self.rowIteration = 0
		self.maxRowIteration = 2 * 5
		self.maxColumnIteration = 2 * 4
		self.countRow = 0
		self.countColumn = 0

		self.pressFlag = True
		self.PicNr = 0
		self.result = 0

		self.labels = [ 'speak', 'literuj', 'undo', 'exit' ]
		
		self.WordsList = os.listdir( self.pathToAP + 'multimedia/ewriting/pictures' )
		shuffle( self.WordsList )
                self.poczatek = True
		self.czyBack = False
		self.numberOfExtraWords = 3

		self.numberOfPresses = 1

		if self.control != 'tracker':
			self.mouseCursor = PyMouse( )
			self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
			self.mouseCursor.move( *self.mousePosition )			

		if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
			mixer.init( )
                        self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
                        self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )

                        self.powrotSound = mixer.Sound( self.pathToAP + '/sounds/powrot.ogg' )
		
	#-------------------------------------------------------------------------
	def initializeTimer(self):

                id1=wx.NewId( )
                wx.RegisterId( id1 )
		self.stoper = wx.Timer( self, id1 )
		self.Bind( wx.EVT_TIMER, self.timerUpdate, self.stoper, id1 )

                self.id3=wx.NewId( )
                wx.RegisterId( self.id3 )
                self.stoper3 = wx.Timer( self, self.id3 )

                self.id4=wx.NewId( )
                wx.RegisterId( self.id4 )
                self.stoper4=wx.Timer( self, self.id4 )
                self.Bind( wx.EVT_TIMER, self.pomocniczyStoper, self.stoper4, self.id4 )
                
		self.stoper.Start( self.timeGap )

	#-------------------------------------------------------------------------
	def timerUpdate(self, event):
		
		if self.control == 'tracker':
			
			if not self.poczatek: 
				try:
					self.button.SetBackgroundColour( self.backgroundColour )	
					self.Update()
					self.stoper.Stop( )
					self.pressFlag = False

				except AttributeError:
					pass
				
			if self.poczatek:
				time.sleep( 1 )
				self.stoper.Stop( )

                                unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                voice = open(unicodePath, 'rb')
				mixer.music.load( voice )
				mixer.music.play( )

				time.sleep( 2 )
				self.stoper.Start( self.timeGap )
				self.poczatek = False
				self.pressFlag = False

		else:
			self.mouseCursor.move( *self.mousePosition )

			self.numberOfPresses = 0
			
			self.flaga = self.flaga % (self.numberOfExtraWords + 2)

			if self.poczatek:
				time.sleep( 1 )
				self.stoper.Stop( )

                                unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                voice = open(unicodePath, 'rb')
				mixer.music.load( voice )
				mixer.music.play( )

				time.sleep( 2 )
				self.stoper.Start( self.timeGap )
				self.poczatek = False

			if self.flag == 'rest':
				pass
			else:

				if self.switchSound.lower( ) != 'off' and not(self.checkFlag):
					self.switchingSound.play( )

				if self.flag == 'row':
					self.rowIteration = self.rowIteration % 5

					items = self.subSizer.GetChildren( )

					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

					items = self.wordSizer.GetChildren( )

					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

					if self.countRow == self.maxRowIteration:
						self.flag = 'rest'

					else:
						if self.rowIteration == self.numberOfExtraWords + 1:				
							items = self.subSizer.GetChildren( )

							for item in items:
								b = item.GetWindow( )
								b.SetBackgroundColour( self.scanningColour )
								b.SetFocus( )

						else:
							items = self.wordSizer.GetChildren( )

							b = items[ self.rowIteration ].GetWindow( )
							b.SetBackgroundColour( self.scanningColour )
							b.SetFocus( )

						self.countRow += 1
						self.rowIteration += 1

				elif self.flag == 'column':
					self.columnIteration = self.columnIteration % 4

					if self.countColumn == self.maxColumnIteration:
						self.countColumn = 0
						self.countRow = 0
						self.rowIteration = 0
						self.columnIteration = 0
						self.flag = 'row'
					else:
						items = self.subSizer.GetChildren( )

						for item in items:
							b = item.GetWindow( )
							b.SetBackgroundColour( self.backgroundColour )
							b.SetFocus( )

						b = items[ self.columnIteration ].GetWindow( )
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus( )

						self.columnIteration += 1
						self.countColumn += 1

	
	#-------------------------------------------------------------------------
	def createGui(self):

                if self.PicNr == len( self.WordsList ):
                        self.PicNr = 0

		if self.control != 'tracker':
			event = eval('wx.EVT_LEFT_DOWN')
		else:
			event = eval('wx.EVT_BUTTON')
                                
		self.picture = self.WordsList[ self.PicNr ]
                self.PicNr += 1
		self.path = self.pathToAP + 'multimedia/ewriting/pictures/'
                im = wx.ImageFromStream( open(self.path+self.picture, "rb"))
		x = im.GetWidth( )
		y = im.GetHeight( )

		if x > y:
			im = im.Scale( 500, 400 )
                elif x == y:
                        im = im.Scale( 500, 500 )
                else:
                        im = im.Scale( 400, 500 )

		picture = wx.BitmapFromImage( im )
		self.word = self.picture[ :self.picture.index( '.' ) ]
		
		self.WORD = self.word.upper( )

		self.extraWords = [ ] #wybiera dodatkowe slowa
		while len( self.extraWords ) < self.numberOfExtraWords:
                        slowo = self.WordsList[ np.random.randint( 0, len( self.WordsList ), 1 )[ 0 ] ] 
                        slowo = slowo[ :slowo.index( '.' ) ]
			SLOWO = slowo.upper( )
                        if SLOWO not in self.extraWords and SLOWO != self.WORD:
                                self.extraWords.append( SLOWO )
                                
		b = bt.GenBitmapButton( self, -1, bitmap = picture )

                obiekty_wyrazow = [ ]
                self.wyrazy_w_kolejnosci = [ ]
                gdzie_poprawne = np.random.randint( 0, self.numberOfExtraWords, 1 )[ 0 ]

                for i, j in enumerate( self.extraWords ):
                        be = bt.GenButton( self, -1, j )
			be.name = j
                        be.SetFont( wx.Font(self.tableFontSize, eval( self.tableFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False) )
                        be.SetBackgroundColour( self.backgroundColour )
                        be.Bind( event, self.onPress )
                        obiekty_wyrazow.append( be )
                        self.wyrazy_w_kolejnosci.append( j )

                be = bt.GenButton( self, -1, self.WORD )
                be.SetFont( wx.Font( self.tableFontSize, eval( self.tableFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False) )
		be.name = self.WORD
                be.SetBackgroundColour( self.backgroundColour )
                be.Bind( event, self.onPress )
                obiekty_wyrazow.insert( gdzie_poprawne, be )
                self.wyrazy_w_kolejnosci.insert( gdzie_poprawne, self.WORD )
                
                res = bt.GenButton( self, -1, u'TWÓJ WYNIK:   ' + str(self.result) + ' / ' + str( self.maxPoints ) )
		res.SetFont( wx.Font( int(self.tableFontSize*0.6), eval( self.tableFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False) )
		
                self.wordSizer = wx.GridSizer( self.numberOfExtraWords + 1, 1, self.xBorder, self.yBorder )
                for item in obiekty_wyrazow:
                        self.wordSizer.Add( item, proportion = 1, flag = wx.EXPAND )                                
		
		try:
			self.subSizerP.Hide( 0 )
                        self.subSizerP.Remove( 0 )
                        self.subSizerP.Add( res, 0, wx.EXPAND ) #dodanie wyniku
                        self.subSizer0.Hide( 0 )
                        self.subSizer0.Remove( 0 )
                        self.subSizer0.Hide( 0 )
                        self.subSizer0.Remove( 0 )
		        self.subSizer0.Add( self.wordSizer, 0, wx.EXPAND ) #tutaj trzeba dodac caly zagniezdzony subsizer ze slowami
                        self.subSizer0.Add( b, 0, wx.EXPAND) #dodanie zdjecia
                        items=self.subSizer.GetChildren( )
                        for item in items:
                                b=item.GetWindow( )
                                b.SetBackgroundColour( self.backgroundColour )
                                b.Update

                except AttributeError:
                        if self.czyBack:
                                self.czyBack = False
                        else:
                                self. mainSizer = wx.BoxSizer( wx.VERTICAL )

                        self.subSizerP=wx.GridSizer( 1, 1, self.xBorder, self.yBorder )
                        self.subSizer0 = wx.GridSizer( 1, 2, self.xBorder, self.yBorder )
                        self.subSizer=wx.GridSizer( 1, 4, self.xBorder, self.yBorder )
                        self.subSizerP.Add( res, 0, wx.EXPAND )
		        self.subSizer0.Add( self.wordSizer, 0, wx.EXPAND )
                        self.subSizer0.Add( b, 0, wx.EXPAND )
                        self.icons = sorted( os.listdir( self.pathToAP + 'icons/ewriting/') )[ 1: ] #bo pierwszy to 1speller a tu ma go nie byc
                        self.path = self.pathToAP + 'icons/ewriting/'

                        for idx, icon in enumerate( self.icons ):

                                if icon[ 0 ].isdigit( ):
                                        k = wx.BitmapFromImage( wx.ImageFromStream( open(self.path+icon, "rb") ) )
                                        b = bt.GenBitmapButton( self, -1, bitmap = k )
					b.name = self.labels[ idx ]
                                        b.SetBackgroundColour( self.backgroundColour )
                                        b.Bind( event, self.onPress )
					self.subSizer.Add( b, 0, wx.EXPAND )						

                        self. mainSizer.Add( self.subSizerP, 1, wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border = self.xBorder )
                        self. mainSizer.Add( self.subSizer0, 7, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, border = self.xBorder )
                        self. mainSizer.Add( self.subSizer, 2, wx.EXPAND  | wx.BOTTOM | wx.LEFT | wx.RIGHT, border = self.xBorder)

                        self.SetSizer( self.mainSizer, deleteOld = True )

                self.SetBackgroundColour( 'black' )
		self.Layout( )
		self.Refresh( )
		self.Center( )
		self.MakeModal( True )
		self.flaga = 0
		self.poczatek = True

	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE, self.OnCloseWindow )
	
	#-------------------------------------------------------------------------
	def OnCloseWindow(self, event):

		if self.control != 'tracker':
			if True in [ 'debian' in item for item in os.uname( ) ]: #POSITION OF THE DIALOG WINDOW DEPENDS ON WINDOWS MANAGER NOT ON DESKTOP ENVIROMENT. THERE IS NO REASONABLE WAY TO CHECK IN PYTHON WHICH WINDOWS MANAGER IS CURRENTLY RUNNING, BESIDE IT IS POSSIBLE TO FEW WINDOWS MANAGER RUNNING AT THE SAME TIME. I DON'T SEE SOLUTION OF THIS ISSUE, EXCEPT OF CREATING OWN SIGNAL (AVR MICROCONTROLLERS).
				if os.environ.get('KDE_FULL_SESSION'):
					self.mousePosition = self.winWidth/1.7, self.winHeight/1.7
				# elif ___: #for gnome-debian
				# 	self.mousePosition = self.winWidth/6.5, self.winHeight/6.
				else:
					self.mousePosition = self.winWidth/1.8, self.winHeight/1.7
			else:
				self.mousePosition = self.winWidth/1.9, self.winHeight/1.68
			
		self.mouseCursor.move( *self.mousePosition )
			
		dial = wx.MessageDialog(self, 'Czy napewno chcesz wyjść z programu?', 'Wyjście',
					wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP)
            
		ret = dial.ShowModal()
		
		if ret == wx.ID_YES:
			try:
				if "smplayer" in [psutil.Process(i).name() for i in psutil.pids( )]:
					os.system( 'smplayer -send-action quit' )
			except TypeError:
				if "smplayer" in [psutil.Process(i).name for i in psutil.pids( )]:
					os.system( 'smplayer -send-action quit' )

			try:
				self.parent.parent.parent.parent.Destroy()
				self.parent.parent.parent.Destroy()
				self.parent.parent.Destroy()
				self.parent.Destroy()
				self.Destroy()
				
			except AttributeError:
				try:
					self.parent.parent.parent.Destroy()
					self.parent.parent.Destroy()
					self.parent.Destroy()
					self.Destroy()

				except AttributeError:
					try:
						self.parent.parent.Destroy()
						self.parent.Destroy()
						self.Destroy()

					except AttributeError:
						try:		
							self.parent.Destroy()
							self.Destroy()

						except AttributeError:
							self.Destroy()

		else:
			event.Veto()

			if self.control != 'tracker':
				self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
				self.mouseCursor.move( *self.mousePosition )	

	#-------------------------------------------------------------------------
	def onExit(self):

		if __name__ == '__main__':
			self.stoper.Stop( )
			self.Destroy( )
		else:
			self.stoper.Stop( )
			self.MakeModal( False )
			self.parent.Show( True )
			if self.control == 'tracker':
				self.parent.stoper.Start( 0.15 * self.parent.timeGap )
			else:
				self.parent.stoper.Start( self.parent.timeGap )
				
			self.Destroy( )

	#-------------------------------------------------------------------------
	def onPress(self, event):

		if self.pressSound.lower( ) != 'off':
			self.pressingSound.play( )

		if self.control == 'tracker':
			if self.pressFlag == False:
				self.button = event.GetEventObject( )
				self.button.SetBackgroundColour( self.selectionColour )
				self.Update()
				self.pressFlag = True
				self.name = self.button.name

				if self.name == 'speak':
					self.stoper.Stop( )

                                        unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                        voice = open(unicodePath, 'rb')
                                        mixer.music.load( voice )
                                        mixer.music.play( )
					self.stoper4.Start( 2000 )

				elif self.name == 'literuj':
					self.stoper.Stop( )

                                        if (self.word + ".ogg") not in os.listdir( self.pathToAP + u"multimedia/ewriting/spelling/" ):        
                                                command = 'sox -m '+ self.pathToAP + 'sounds/phone/' + list( self.word )[ 0 ].swapcase( ) + '.ogg'
                                                ile = 0

                                                for l in list( self.word )[ 1: ]:
                                                        ile += 2
                                                        command += ' "|sox ' + self.pathToAP + "sounds/phone/" + l.swapcase() + ".ogg" + ' -p pad ' + str( ile ) + '"'

                                                command += ' ' + self.pathToAP + 'multimedia/ewriting/spelling/' + self.word + '.ogg'
                                                wykonaj = sp.Popen( shlex.split( command.encode("utf-8") ) )

                                        time.sleep( 1.5 )
                                        unicodePath = self.pathToAP + u"multimedia/ewriting/spelling/" + self.word + u".ogg"
                                        voice = open(unicodePath, 'rb')
                                        do_literowania = mixer.Sound(voice)
                                        do_literowania.play( )
                                        self.stoper4.Start( ( do_literowania.get_length( ) + 0.5 ) * 1000 )

				elif self.name == 'undo':

					self.stoper.Stop( )

					self.createGui( )			
					self.stoper.Start( self.timeGap )

				elif self.name == 'exit':
					self.onExit( )

				else:
					if self.name == self.WORD:
						self.ownWord = self.WORD

					else:
						self.ownWord = ''

					self.stoper.Stop( )
					self.check( )

		else:
			self.numberOfPresses += 1
			self.countRow = 0

			if self.numberOfPresses == 1:
				
				if self.flag == 'rest':
					self.rowIteration = 0
					self.countRows = 0
					self.flag = 'row'
				
				elif self.flag == 'row':
					if self.rowIteration < self.numberOfExtraWords + 2:
						items = self.wordSizer.GetChildren( )
						item=items[ self.rowIteration-1 ]
						b = item.GetWindow( )
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus( )
						b.Update( )
					
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/1000. )
                                                self.stoper.Start( self.timeGap )
		
                                                if self.wyrazy_w_kolejnosci[ self.rowIteration-1 ] == self.WORD:
							self.ownWord = self.WORD
						
						else:
							self.ownWord=''

						self.stoper.Stop( )
						self.check( )
					
						self.rowIteration = 0
						self.countRow = 0
					
					if self.rowIteration == self.numberOfExtraWords + 2:
						self.flag = 'column'
						items = self.subSizer.GetChildren( )
						
						for item in items:
							b = item.GetWindow( )
							b.SetBackgroundColour( self.selectionColour )
							b.SetFocus( )
							b.Update( )
							
                                                self.stoper.Stop( )
                                                time.sleep( self.selectionTime/1000. )
                                                self.stoper.Start( self.timeGap )

				elif self.flag == 'column':

					if self.columnIteration == 4:
                                                b = self.subSizer.GetChildren( )[3].GetWindow( )
                                                b.SetBackgroundColour( self.selectionColour )
                                                b.SetFocus( )
                                                b.Update( )
                                                
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.powrotSound.play( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.stoper.Start( self.timeGap )
                                                                                                        
						self.onExit( )

					elif self.columnIteration == 1:
                                                b = self.subSizer.GetChildren( )[0].GetWindow( )
                                                b.SetBackgroundColour( self.selectionColour )
                                                b.SetFocus( )
                                                b.Update( )
                                                
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime )/1000. )
                                                self.stoper.Start( self.timeGap )

						self.stoper.Stop( )
                                                unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                                voice = open(unicodePath, 'rb')
                                                mixer.music.load( voice )
						mixer.music.play( )
						self.stoper4.Start( 2000 )

					elif self.columnIteration == 2:
                                                b = self.subSizer.GetChildren( )[1].GetWindow( )
                                                b.SetBackgroundColour( self.selectionColour )
                                                b.SetFocus( )
                                                b.Update( )
                                                
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime )/1000. )
                                                self.stoper.Start( self.timeGap )

						self.stoper.Stop( )

						if (self.word + ".ogg") not in os.listdir( self.pathToAP + u"multimedia/ewriting/spelling/" ):        
							command = 'sox -m '+ self.pathToAP + 'sounds/phone/' + list( self.word )[ 0 ].swapcase( ) + '.ogg'
							ile = 0

							for l in list( self.word )[ 1: ]:
                                                                ile += 2
                                                                command += ' "|sox ' + self.pathToAP + "sounds/phone/" + l.swapcase() + ".ogg" + ' -p pad ' + str( ile ) + '"'

							command += ' ' + self.pathToAP + 'multimedia/ewriting/spelling/' + self.word + '.ogg'
							wykonaj = sp.Popen( shlex.split( command.encode("utf-8") ) )

						time.sleep( 1.5 )
                                                unicodePath = self.pathToAP + u"multimedia/ewriting/spelling/" + self.word + u".ogg"
                                                voice = open(unicodePath, 'rb')
						do_literowania = mixer.Sound(voice)
						do_literowania.play( )
						self.stoper4.Start( ( do_literowania.get_length( ) + 0.5 ) * 1000 )

					elif self.columnIteration == 3:
                                                b = self.subSizer.GetChildren( )[2].GetWindow( )
                                                b.SetBackgroundColour( self.selectionColour )
                                                b.SetFocus( )
                                                b.Update( )
                                                
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/1000. )

						self.createGui( )			
						self.stoper.Start( self.timeGap )
					
					self.rowIteration = 0
					self.columnIteration = 0
					self.countRow = 0
					self.countColumn = 0
					self.flag = 'row'
			else:
				event.Skip( )

	#-------------------------------------------------------------------------
        def pomocniczyStoper(self, event):
                self.stoper4.Stop( )
                self.stoper.Start( self.timeGap )
        
	#-------------------------------------------------------------------------
	def check(self):
		
		self.checkFlag = True
                self.mainSizer.Clear( deleteWindows = True )
		self.checkW = check.check( self )

	#-------------------------------------------------------------------------
	def back(self):
                
		self.czyBack = True
		
		del self.checkW
                self.mainSizer.Clear( deleteWindows = True )
		
		self.createGui( )
		self.stoper.Start( self.timeGap )

		
#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = cwiczenia( parent = None, id = -1 )
	frame.Show( )
	app.MainLoop( )
