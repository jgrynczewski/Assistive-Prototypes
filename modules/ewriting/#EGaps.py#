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

import subprocess as sp
import shlex
from pygame import mixer

import check, spellerCW

#=============================================================================
class cwiczenia(wx.Frame):
	def __init__(self, parent, id):

		self.winWidth, self.winHeight = wx.DisplaySize( )
		
		wx.Frame.__init__( self , parent , id , 'EGaps' )
                style = self.GetWindowStyle( )
		self.SetWindowStyle( style | wx.STAY_ON_TOP ) 
		self.parent = parent

		self.Maximize( True )
		self.Centre( True )
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

		# with open( './.pathToAP' ,'r' ) as textFile:
		# 	self.pathToAP = textFile.readline( )

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

		self.ownWord = ''
		self.flaga = 0
		self.checkFlag = False
		self.PicNr = 0
		self.result = 0

		self.WordsList = os.listdir( unicode(self.pathToAP) + u"multimedia/ewriting/pictures" )
		shuffle( self.WordsList )

                self.poczatek = True
		self.czyBack = False

		self.numberOfPresses = 1
		self.pressFlag = False
		
		self.numberOfIteration = 0
		self.maxNumberOfIteration = 2 * 5
		
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

                id1 = wx.NewId( )
                wx.RegisterId( id1 )
		self.stoper = wx.Timer( self, id1 )
		self.Bind( wx.EVT_TIMER, self.timerUpdate, self.stoper,id1 )
		
		self.id2 = wx.NewId( )
                wx.RegisterId( self.id2 )
                self.stoper2 = wx.Timer( self, self.id2 )

                self.id3 = wx.NewId( )
                wx.RegisterId( self.id3 )
                self.stoper3 = wx.Timer( self, self.id3 )

                self.id4 = wx.NewId( )
                wx.RegisterId( self.id4 )
                self.stoper4=wx.Timer( self, self.id4 )
                self.Bind( wx.EVT_TIMER, self.pomocniczyStoper, self.stoper4, self.id4 )
                
		# if self.control != 'tracker':
		self.stoper.Start( self.timeGap * 0.15 )

	#-------------------------------------------------------------------------		
	def createGui( self ):

		self.pressFlag = False

                if self.PicNr == len( self.WordsList ):
                        self.PicNr = 0

		self.picture = self.WordsList[ self.PicNr ]
                self.PicNr += 1

		self.path = self.pathToAP + 'multimedia/ewriting/pictures/'

		if self.control != 'tracker':
			event = eval('wx.EVT_LEFT_DOWN')
		else:
			event = eval('wx.EVT_BUTTON')

                im = wx.ImageFromStream( open( self.path + self.picture, "rb" ) )

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

		b = bt.GenBitmapButton( self, -1, bitmap=picture )
		# b.SetBackgroundColour( self.backgroundColour )
		b.Bind( event, self.onPress )

                be = bt.GenButton( self, -1, self.WORD )
		be.SetFont( wx.Font( self.textFontSize, eval( self.textFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
		# be.SetBackgroundColour( self.backgroundColour )
		be.Bind( event, self.onPress )

                res = bt.GenButton( self, -1, u'TWÓJ WYNIK:   ' + str( self.result ) + ' / ' + str( self.maxPoints ) )
		res.SetFont( wx.Font( int( self.tableFontSize*0.6 ), eval( self.tableFont ), wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False) )
		# res.SetBackgroundColour( self.backgroundColour )
		res.Bind( event, self.onPress )
		
		try:
                        self.subSizerP.Hide( 0 )
                        self.subSizerP.Remove( 0 )
                        self.subSizerP.Add( res, 0, wx.EXPAND )
                        self.subSizer0.Hide( 0 )
                        self.subSizer0.Remove( 0 )
                        self.subSizer0.Hide( 0 )
                        self.subSizer0.Remove( 0 )
                        self.subSizer0.Add( b, 0, wx.EXPAND )
		        self.subSizer0.Add( be, 0, wx.EXPAND )

		        items = self.subSizer.GetChildren( )

                        for i in items:
                                b=i.GetWindow( )
                                b.SetBackgroundColour( self.backgroundColour )
                                b.Update
                                
                except AttributeError:
                        if self.czyBack:
                                self.czyBack = False
                        else:
                                self. mainSizer = wx.BoxSizer( wx.VERTICAL )

                        self.subSizerP = wx.GridSizer( 1, 1, self.xBorder, self.yBorder )
                        self.subSizer0 = wx.GridSizer( 1, 2, self.xBorder, self.yBorder )
                        self.subSizer=wx.GridSizer( 1, 5, self.xBorder, self.yBorder )
                        self.subSizerP.Add( res, 0, wx.EXPAND )
                        self.subSizer0.Add( b, 0, wx.EXPAND )
		        self.subSizer0.Add( be, 0, wx.EXPAND )

                        self.icons = sorted( os.listdir( self.pathToAP + 'icons/ewriting/' ) )
                        self.path = self.pathToAP + 'icons/ewriting/'

                        for idx, icon in enumerate( self.icons ):
                                if icon[ 0 ].isdigit( ):
                                        i = wx.BitmapFromImage( wx.ImageFromStream( open(self.path+icon, "rb") ) )
                                        b = bt.GenBitmapButton( self, -1, bitmap = i )
                                        b.SetBackgroundColour( self.backgroundColour )
					b.name = idx
                                        b.Bind( event, self.onPress )
                                        self.subSizer.Add( b, 0, wx.EXPAND )

                        self. mainSizer.Add( self.subSizerP, proportion = 1, flag = wx.EXPAND | wx.TOP | wx.RIGHT | wx.LEFT, border = self.xBorder)
                        self. mainSizer.Add( self.subSizer0, proportion = 7, flag = wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, border = self.xBorder )
                        self. mainSizer.Add( self.subSizer, proportion = 2, flag = wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, border = self.xBorder )
                        self.SetSizer( self. mainSizer, deleteOld = True )

                self.SetBackgroundColour( 'black' )
		self.Layout( )
		self.Refresh( )
		self.Center( )
		self.MakeModal( True ) 
		self.flaga = 0
		self.poczatek = True

	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE , self.OnCloseWindow )

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
            
		ret = dial.ShowModal( )
		
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
			event.Veto( )

			if self.control != 'tracker':
				self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
				self.mouseCursor.move( *self.mousePosition )	

	#-------------------------------------------------------------------------	
	def onExit( self ):

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
	def onPress( self, event ):
		
		if self.pressSound.lower( ) != 'off':
			self.pressingSound.play( )

		if self.control == 'tracker':
			if self.pressFlag == False:
				try:
					self.button = event.GetEventObject( )
					self.name = self.button.name
					self.button.SetBackgroundColour( self.selectionColour )
					self.Update()
					self.pressFlag = True

					if self.name == 0:
						self.stoper.Stop( )
						self.mainSizer.Clear( deleteWindows = True )
						self.spellerW = spellerCW.speller( self )
						self.Bind( wx.EVT_TIMER, self.spellerW.timerUpdate, self.stoper2, self.id2 )
						self.stoper2.Start( self.spellerW.timeGap )

					if self.name == 4:
						self.onExit( )

					if self.name == 1:
						# time.sleep( 0.5 )
						# self.stoper.Stop( )
                                                unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                                voice = open(unicodePath, 'rb')
                                                mixer.music.load( voice )
						mixer.music.play( )
						self.stoper.Start( self.timeGap )

					if self.name == 2:
						self.stoper.Stop( )
                                                
						if (self.word + '.ogg') not in os.listdir( self.pathToAP + u"multimedia/ewriting/spelling/" ):        
							command = 'sox -m '+ self.pathToAP + 'sounds/phone/' + list( self.word )[ 0 ].swapcase( ) + '.ogg'
							ile = 0

							for l in list( self.word )[ 1: ]:
								ile += 2
								command += ' "|sox ' + self.pathToAP + 'sounds/phone/' + l.swapcase() + '.ogg' + ' -p pad ' + str( ile ) + '"'

							command += ' ' + self.pathToAP + 'multimedia/ewriting/spelling/' + self.word + '.ogg'
							wykonaj = sp.Popen( shlex.split( command.encode("utf-8") ) )

						# time.sleep( 1.5 )
                                                unicodePath = self.pathToAP + u'multimedia/ewriting/spelling/' + self.word + u'.ogg'
                                                voice = open(unicodePath, 'rb')
						do_literowania = mixer.Sound( voice )
						do_literowania.play( )
						self.stoper4.Start( ( do_literowania.get_length( ) + 0.5 ) * 1000 )

					if self.name == 3:
						# self.button = event.GetEventObject( )
						# self.button.SetBackgroundColour( self.selectionColour )
						self.stoper.Stop( )
						self.createGui( )
						self.stoper.Start( self.timeGap*0.15 )

				except AttributeError:
					pass
		else:
			self.numberOfPresses += 1
			self.numberOfIteration = 0

			if self.numberOfPresses == 1:
				
				if self.flaga == 'rest':
					self.flaga = 0
				else:

					item = self.subSizer.GetItem( self.flaga - 1 )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.selectionColour )
					b.SetFocus( )
					b.Update( )

					if 'speller' in self.icons[ self.flaga - 1 ]:

                                                self.stoper.Stop( )
                                                time.sleep( self.timeGap/1000. )
                                                self.stoper.Start( self.timeGap )

						self.stoper.Stop( )
						self.mainSizer.Clear( deleteWindows = True )
						self.spellerW = spellerCW.speller( self )
						self.Bind( wx.EVT_TIMER, self.spellerW.timerUpdate, self.stoper2, self.id2 )
						self.stoper2.Start( self.spellerW.timeGap )

					if 'cancel' in self.icons[ self.flaga - 1 ] or self.flaga == 0:
                                                
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.powrotSound.play( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.stoper.Start( self.timeGap )
                                                
						self.onExit( )

					if 'speak' in self.icons[ self.flaga - 1 ]:
                                                self.stoper.Stop( )
                                                time.sleep( self.selectionTime/1000. )
                                                self.stoper.Start( self.timeGap )

						time.sleep( 1 )
						self.stoper.Stop( )
                                                unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                                voice = open(unicodePath, 'rb')
                                                mixer.music.load( voice )
						mixer.music.play( )
						self.stoper4.Start( 2000 )

					if 'literuj' in  self.icons[ self.flaga - 1 ]:
                                                self.stoper.Stop( )
                                                time.sleep( self.selectionTime/1000. )
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

					if 'undo' in self.icons[ self.flaga - 1 ]:
                                                self.stoper.Stop( )
                                                time.sleep( self.selectionTime/1000. )
                                                self.stoper.Start( self.timeGap )

						self.stoper.Stop( )
						self.createGui( )		
						self.stoper.Start( self.timeGap )

			else:
				event.Skip( )

	#-------------------------------------------------------------------------	
        def pomocniczyStoper(self, event):

                self.stoper4.Stop( )

                if hasattr( self, 'spellerW' ):
                        self.stoper2.Start( self.spellerW.timeGap )
                else:
                        self.stoper.Start( self.timeGap )

	#-------------------------------------------------------------------------	        
	def check(self):
		
		self.checkFlag = True
                self.mainSizer.Clear( deleteWindows = True )
		self.checkW = check.check( self )
		# self.Bind( wx.EVT_TIMER, self.checkW.zamknij, self.stoper3, self.id3 )

	#-------------------------------------------------------------------------	
	def back(self):

                self.czyBack = True

                try:
                        del self.spellerW
                except NameError:
                        del self.checkW

                self.mainSizer.Clear( deleteWindows = True )
		self.createGui( )
		self.stoper.Start( self.timeGap )

	#-------------------------------------------------------------------------	
	def timerUpdate( self, event ):

		if self.control == 'tracker':
			try:
				self.button.SetBackgroundColour( self.backgroundColour )	
					
				self.stoper.Stop( )
				self.pressFlag = False

			except AttributeError:
				pass

			if self.poczatek:
				self.stoper.Stop( )
                                unicodePath = self.pathToAP + u"multimedia/ewriting/voices/" + self.word + u".ogg"
                                voice = open(unicodePath, 'rb')
				mixer.music.load( voice )
				mixer.music.play( )
				self.poczatek = False

		else:
			self.mouseCursor.move( *self.mousePosition )
			self.numberOfPresses = 0
			self.numberOfIteration += 1

			if self.flaga == 'rest':
				pass

			elif self.numberOfIteration > self.maxNumberOfIteration:
				for i in range( 5 ):
					item = self.subSizer.GetItem( i )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
					b.SetFocus( )

				self.flaga = 'rest'

			else:

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

				if self.switchSound.lower( ) != 'off' and not( self.checkFlag ):
					self.switchingSound.play( )

				for i in range( 5 ):
					item = self.subSizer.GetItem( i )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
					b.SetFocus( )

				if self.flaga == 5:
					item = self.subSizer.GetItem( 0 )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.scanningColour )
					b.SetFocus( )

					self.flaga = 1

				else:
					item = self.subSizer.GetItem( self.flaga )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.scanningColour )
					b.SetFocus( )

					self.flaga += 1

#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = cwiczenia( parent = None, id = -1 ) 
	frame.Show( )
	app.MainLoop( )
