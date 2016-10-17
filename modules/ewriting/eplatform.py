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

import os, sys, psutil, time
import wx
import wx.lib.buttons as bt
from pymouse import PyMouse

from pygame import mixer

import EGaps, EMatch

#=============================================================================
class cwiczenia(wx.Frame):
	def __init__(self, parent, id):
		
		self.winWidth, self.winHeight = wx.DisplaySize( )
		
		wx.Frame.__init__( self , parent , id , 'e-platform main menu')
                style = self.GetWindowStyle( )
		self.SetWindowStyle( style | wx.STAY_ON_TOP ) 
		self.parent = parent

		self.Maximize( True )
		self.Centre( True )
		self.MakeModal( True )
		
		self.initializeParameters( )
		self.initializeBitmaps( )
		self.createGui( )
		self.createBindings( )

		self.initializeTimer( )

	#-------------------------------------------------------------------------	
	def initializeParameters(self):

		with open( './.pathToAP' ,'r' ) as textFile:
			self.pathToAP = textFile.readline( )

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

		self.pressFlag = False

		self.numberOfRows = 3,
		self.numberOfColumns = 1,
		self.numberOfIteration = 0
		self.maxNumberOfIteration = 2 * self.numberOfRows[0]

		self.flaga = 0
		
		if self.control != 'tracker':
			self.mouseCursor = PyMouse( )
			self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 8 - self.yBorder
			self.mouseCursor.move( *self.mousePosition )			
							
		if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
			mixer.init( )
                        self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
                        self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )
                        
                        self.powrotSound = mixer.Sound( self.pathToAP + '/sounds/powrot.ogg' )
                        self.slowoSound = mixer.Sound( self.pathToAP + '/sounds/slowo.ogg' )
                        self.dziuraSound = mixer.Sound( self.pathToAP + '/sounds/dziura.ogg' )

                self.poczatek = True
		self.numberOfPresses = 1

	#-------------------------------------------------------------------------	
        def initializeBitmaps(self):
            
		self.functionButtonPath = [ wx.BitmapFromImage( wx.ImageFromStream( open(self.pathToAP + 'icons/back.png', 'rb' ) ) ) ]

		self.functionButtonName = [ 'back' ]

	#-------------------------------------------------------------------------	
	def initializeTimer(self):

                id1 = wx.NewId( )
                wx.RegisterId( id1 )
		self.stoper = wx.Timer( self, id1 )
		self.Bind( wx.EVT_TIMER, self.timerUpdate, self.stoper,id1 )

		if self.control != 'tracker':
			self.stoper.Start( self.timeGap )

	#-------------------------------------------------------------------------	
	def createGui(self):

		self.mainSizer = wx.GridBagSizer( self.xBorder, self.yBorder )

                nazwy = [ u'DZIURA',u'SŁOWO' ]
                kolory = [ 'indian red', 'yellow' ]

		b = bt.GenButton( self, -1, nazwy[ 0 ], name = nazwy[ 0 ])
		b.SetFont( wx.Font( 75, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
		b.SetBezelWidth( 3 )
		b.SetBackgroundColour( self.backgroundColour )
		b.SetForegroundColour( kolory[ 0 ] )
		b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
		self.mainSizer.Add( b, ( 0, 0 ), wx.DefaultSpan, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border = self.xBorder )

		b = bt.GenButton( self, -1, nazwy[ 1 ], name = nazwy[ 1 ])
		b.SetFont( wx.Font( 75, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,  False ) )
		b.SetBezelWidth( 3 )
		b.SetBackgroundColour( self.backgroundColour )
		b.SetForegroundColour( kolory[ 1 ] )
		b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
		self.mainSizer.Add( b, ( 1, 0 ), wx.DefaultSpan, wx.EXPAND | wx.LEFT | wx.RIGHT, border = self.xBorder )

		b = bt.GenBitmapButton( self, -1, bitmap = self.functionButtonPath[ 0 ], name = self.functionButtonName[ 0 ] )
		b.SetBackgroundColour( self.backgroundColour )
		b.SetBezelWidth( 3 )
		b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
		self.mainSizer.Add( b, ( 2, 0 ), wx.DefaultSpan, wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, border = self.xBorder)
		
		for number in range( self.numberOfRows[ 0 ] ):
			self.mainSizer.AddGrowableRow( number )
		for number in range( self.numberOfColumns[ 0 ] ):
			self.mainSizer.AddGrowableCol( number )

                self.SetSizer( self.mainSizer )
                self.SetBackgroundColour( 'black' )
		self.Layout( )
		self.Refresh( )
		self.Center( )
		self.MakeModal( True )
		self.flaga = 0

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
                if self.parent:
                        self.parent.MakeModal( True )
                        self.parent.Show( )
			if self.control == 'tracker':
				self.parent.stoper.Start( 0.15 * self.parent.timeGap )
			else:
				self.parent.stoper.Start( self.parent.timeGap )

                        self.MakeModal( False )
                        self.Destroy( )
                else:
                        self.MakeModal( False )
                        self.Destroy( )

	#-------------------------------------------------------------------------	
	def onPress(self, event):
		
		if self.pressSound.lower( ) != 'off':
			self.pressingSound.play( )

		if self.control == 'tracker':
			if self.pressFlag == False:
				self.button = event.GetEventObject()
				self.button.SetBackgroundColour( self.selectionColour )
				self.pressFlag = True
				self.label = event.GetEventObject().GetName().encode( 'utf-8' )
				self.stoper.Start( 0.15 * self.timeGap )

				if self.label == 'DZIURA':
                                        if self.pressSound.lower( ) == 'voice':
                                                self.dziuraSound.play()
					self.stoper.Stop( )
					EGaps.cwiczenia( self, id = -1 ).Show( True )
					self.MakeModal( False )
					self.Hide( )

				elif self.label == u'SŁOWO':
					self.stoper.Stop( )
                                        if self.pressSound.lower( ) == 'voice':
                                                self.slowoSound.play()
					EMatch.cwiczenia( self, id = -1 ).Show( True )
					self.MakeModal( False )
					self.Hide( )

				if self.label == 'back':
                                        self.stoper.Stop( )
                                        time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                        if self.pressSound.lower( ) == 'voice':
                                                self.powrotSound.play()
                                        time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                        self.stoper.Start( self.timeGap )

					self.onExit( )

		else:
			self.numberOfPresses += 1
			self.numberOfIteration = 0

			if self.numberOfPresses == 1:
				
				items = self.mainSizer.GetChildren( )
				
				if self.flaga == 'rest':
					self.flaga = 0				
				
				else:
					if self.flaga == 0:
						b = items[ 2 ].GetWindow( )

					elif self.flaga == 1:
					       b = items[ 0 ].GetWindow( )

					elif self.flaga == 2:
						b = items[ 1 ].GetWindow( )

					b.SetBackgroundColour( self.selectionColour )
					b.SetFocus( )
					b.Update( )
                                        
					if self.flaga == 0 :
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                if self.pressSound.lower( ) == 'voice':
                                                        self.powrotSound.play()
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.stoper.Start( self.timeGap )

						self.onExit( )

					if self.flaga == 1 :
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                if self.pressSound.lower( ) == 'voice':
                                                        self.dziuraSound.play()
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.stoper.Start( self.timeGap )

						self.stoper.Stop( )
						EGaps.cwiczenia( self, id = -1 ).Show( True )
						self.MakeModal( False )
						self.Hide( )

					if self.flaga == 2 :
                                                self.stoper.Stop( )
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                if self.pressSound.lower( ) == 'voice':
                                                        self.slowoSound.play()
                                                time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                self.stoper.Start( self.timeGap )

						self.stoper.Stop( )
						EMatch.cwiczenia( self, id = -1 ).Show( True )
						self.MakeModal( False )
						self.Hide( )

			else:
				event.Skip( )

	#-------------------------------------------------------------------------	
	def timerUpdate(self, event):

		if self.control == 'tracker':
			
			if self.button.GetBackgroundColour( ) == self.backgroundColour:
				self.button.SetBackgroundColour( self.selectionColour )
				
			else:
				self.button.SetBackgroundColour( self.backgroundColour )	
		
			self.stoper.Stop( )
			self.pressFlag = False

		else:
			self.mouseCursor.move( *self.mousePosition )
			self.numberOfPresses = 0
			
			self.numberOfIteration += 1

			if self.flaga == 'rest':
				pass

			elif self.numberOfIteration > self.maxNumberOfIteration:
				for i in range( 3 ):
					item = self.mainSizer.GetItem( i )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
					b.SetFocus( )
                                if self.switchSound == "voice":
                                        self.usypiamSound.play()
				self.flaga = 'rest'

			else:
				for i in range( 3 ):
					item = self.mainSizer.GetItem( i )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.backgroundColour )
					b.SetFocus( )

				item = self.mainSizer.GetItem( self.flaga )
				b = item.GetWindow( )
				b.SetBackgroundColour( self.scanningColour )
				b.SetFocus( )
                                logo = b.Name
                                
                                if self.switchSound.lower() == "voice":
                                        if logo == "DZIURA":
                                                self.dziuraSound.play()
                                        elif logo == u"SŁOWO":
                                                self.slowoSound.play()
                                        elif logo == "back":
                                                self.powrotSound.play()
                                
				if self.flaga == 2:
					self.flaga = 0
				else:
					self.flaga += 1			
					
				if self.switchSound.lower( ) == 'on':
					self.switchingSound.play( )

#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = cwiczenia( parent = None, id = -1 )
	frame.Show( )
	app.MainLoop( )
