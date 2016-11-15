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

import wx, glob, os, alsaaudio, psutil, time, sys
import wx.lib.buttons as bt
import subprocess as sp

from pymouse import PyMouse
from pygame import mixer

import suspend

#=============================================================================
class pilot(wx.Frame):
	def __init__(self, parent, id):

	    self.winWidth, self.winHeight = wx.DisplaySize( )
	    
            self.initializeParameters( )				
            wx.Frame.__init__( self , parent , id, 'musicPilot', size = ( self.width, self.height ), pos = ( self.winWidth - self.width - self.xBorder*(self.numberOfColumns[0]-2), self.winHeight - self.height - self.xBorder*(self.numberOfRows[0]-6) ) )
            self.SetBackgroundColour( 'black' )
	    
            style = self.GetWindowStyle( )
            self.SetWindowStyle( style | wx.STAY_ON_TOP )
	    self.parent = parent
            
	    self.MakeModal( True )		
	    
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
	    
            self.reader = reader()
            self.reader.readParameters()
            parameters = self.reader.getParameters()
            self.unpackParameters(parameters)
            
            self.flag = 'row'
	    self.pressFlag = False
            self.pressedStopFlag = False
	    
            self.rowIteration = 0						
            self.colIteration = 0

            self.numberOfColumns = 2,
            self.numberOfRows = 7,

	    self.numberOfEmptyIteration = 0
            self.countRows = 0
            self.countColumns = 0
            self.countMaxRows = 2									
            self.countMaxColumns = 2									
	    self.countMaxEmptyIteration = 3
            self.numberOfPresses = 1

            self.volumeLevels = [0, 20, 40, 60, 80, 100, 120, 140, 160]
            if self.volumeLevel not in self.volumeLevels:
                raise("Wrong value of volumeLevel. Accepted values: 0, 20, 40, 60, 80, 100, 120, 140, 160")

	    if self.control != 'tracker':	    
		    self.mouseCursor = PyMouse( )
		    self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 16 - self.yBorder
		    self.mouseCursor.move( *self.mousePosition )	

	    if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
		    mixer.init( )
                    self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
                    self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )
            	    
                    self.ciszejSound = mixer.Sound( self.pathToAP + '/sounds/ciszej.ogg' )
                    self.glosniejSound = mixer.Sound( self.pathToAP + '/sounds/glosniej.ogg' )
                    self.zatrzymajGrajSound = mixer.Sound( self.pathToAP + '/sounds/zatrzymaj_graj.ogg' )
                    self.stopSound = mixer.Sound( self.pathToAP + '/sounds/stop.ogg' )
                    self.playlistSound = mixer.Sound( self.pathToAP + '/sounds/playlist.ogg' )

                    self.przewinDoPrzoduSzybkoSound = mixer.Sound( self.pathToAP + '/sounds/przewiń_do_przodu_szybko.ogg' )
                    self.przewinDoTyluSzybkoSound = mixer.Sound( self.pathToAP + '/sounds/przewiń_do_tyłu_szybko.ogg' )
                    self.przewinDoPrzoduSound = mixer.Sound( self.pathToAP + '/sounds/przewiń_do_przodu.ogg' )
                    self.przewinDoTyluSound = mixer.Sound( self.pathToAP + '/sounds/przewiń_do_tyłu.ogg' )

                    self.powtarzajUtworSound = mixer.Sound( self.pathToAP + '/sounds/powtarzaj_ten_utwór.ogg' )
                    self.powtarzajListeSound = mixer.Sound( self.pathToAP + '/sounds/powtarzaj_ten_album.ogg' )

                    self.oneSound = mixer.Sound( self.pathToAP + '/sounds/rows/1.ogg' )
                    self.twoSound = mixer.Sound( self.pathToAP + '/sounds/rows/2.ogg' )
                    self.threeSound = mixer.Sound( self.pathToAP + '/sounds/rows/3.ogg' )
                    self.fourSound = mixer.Sound( self.pathToAP + '/sounds/rows/4.ogg' )
                    self.fiveSound = mixer.Sound( self.pathToAP + '/sounds/rows/5.ogg' )
                    self.sixSound = mixer.Sound( self.pathToAP + '/sounds/rows/6.ogg' )
                    self.sevenSound = mixer.Sound( self.pathToAP + '/sounds/rows/7.ogg' )

                    self.wyjscieSound = mixer.Sound( self.pathToAP + '/sounds/wyjście.ogg' )
                    self.powrotSound = mixer.Sound( self.pathToAP + '/sounds/powrot.ogg' )
                    self.usypiamSound = mixer.Sound( self.pathToAP + '/sounds/usypiam.ogg' )

	    self.width = self.numberOfColumns[0] * 120
	    self.height = self.numberOfRows[0] * 100

	#-------------------------------------------------------------------------	
        def unpackParameters(self, parameters):
		for item in parameters:
			try:
				setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
			except ValueError:
				setattr(self, item[:item.find('=')], item[item.find('=')+1:])			

        #-------------------------------------------------------------------------	
        def initializeBitmaps(self):

            buttonPaths = glob.glob( self.pathToAP + 'icons/pilots/musicPilot/*' ) #labelFiles
            
            self.buttons = { }

            for buttonPath in buttonPaths:

                buttonBitmap = wx.BitmapFromImage( wx.ImageFromStream( open(buttonPath, "rb") ) )

                buttonLabel = buttonPath[ buttonPath.rfind( '/' )+1 : buttonPath.rfind('.') ]
                try:
                    buttonPosition = int( buttonLabel.split( '_' )[ 0 ] )
                    buttonName = buttonLabel[ buttonLabel.find( '_' )+1: ]
                    self.buttons[ buttonPosition ] = [ buttonName, buttonBitmap ]
                    
                except ValueError:
                    print 'Symbol %s ma nieprawidłową nazwę.' % ( buttonLabel )
                    pass

	#-------------------------------------------------------------------------
	def createGui(self):

		self.mainSizer = wx.BoxSizer( wx.VERTICAL )

		self.subSizer = wx.GridBagSizer( self.xBorder, self.yBorder )

		if self.control != 'tracker':
			event = eval('wx.EVT_LEFT_DOWN')
		else:
			event = eval('wx.EVT_BUTTON')
		
		for key, value in self.buttons.items( ):
			if key == 1 or key == 2 or key == 3 or key == 4:
				b = bt.GenBitmapButton( self, -1, name = value[ 0 ], bitmap = value[ 1 ] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )
				
				self.subSizer.Add( b, ( ( key - 1 ) / self.numberOfColumns[ 0 ], ( key - 1 ) % self.numberOfColumns[ 0 ] ), wx.DefaultSpan, wx.EXPAND )

			elif key == 5:
				b = bt.GenBitmapButton( self, -1, name = value[ 0 ], bitmap = value[ 1 ] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )

				self.subSizer.Add( b, ( ( key - 1 ) / self.numberOfColumns[ 0 ], ( key - 1 ) % self.numberOfColumns[ 0 ] ), ( 1, 2 ), wx.EXPAND )
			
			else:
				b = bt.GenBitmapButton( self, -1, name = value[ 0 ], bitmap = value[ 1 ] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( event, self.onPress )
				
				self.subSizer.Add( b, ( ( key ) / self.numberOfColumns[ 0 ], ( key ) % self.numberOfColumns[ 0 ] ), wx.DefaultSpan, wx.EXPAND )
			
                for number in range( self.numberOfRows[ 0 ] ):
                    self.subSizer.AddGrowableRow( number )
                for number in range( self.numberOfColumns[ 0 ] ):
                    self.subSizer.AddGrowableCol( number )
		
		self. mainSizer.Add( self.subSizer, proportion = 1, flag = wx.EXPAND | wx.RIGHT | wx. LEFT | wx.TOP | wx.BOTTOM, border = self.xBorder )
		self.SetSizer( self. mainSizer )

	#-------------------------------------------------------------------------
	def initializeTimer(self):
		self.stoper = wx.Timer( self )
		self.Bind( wx.EVT_TIMER , self.timerUpdate , self.stoper )

		if self.control != 'tracker':
			self.stoper.Start( self.timeGap )
	
	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE , self.OnCloseWindow )

	#-------------------------------------------------------------------------
	def OnCloseWindow(self, event):

		if self.control != 'tracker':
			if True in [ 'debian' in item for item in os.uname( ) ]: #POSITION OF THE DIALOG WINDOW DEPENDS ON WINDOWS MANAGER NOT ON DESKTOP ENVIROMENT. THERE IS NO REASONABLE WAY TO CHECK IN PYTHON WHICH WINDOWS MANAGER IS CURRENTLY RUNNING, BESIDE IT IS POSSIBLE TO FEW WINDOWS MANAGER RUNNING AT THE SAME TIME. I DON'T SEE SOLUTION OF THIS ISSUE, EXCEPT OF CREATING OWN SIGNAL (AVR MICROCONTROLLERS).
				if os.environ.get('KDE_FULL_SESSION'):
					self.mousePosition = self.winWidth/1.05, self.winHeight/1.6
				# elif ___: #for gnome-debian
				# 	self.mousePosition = self.winWidth/6.5, self.winHeight/6.
				else:
					self.mousePosition = self.winWidth/1.07, self.winHeight/1.61
			else:
				self.mousePosition = self.winWidth/1.12, self.winHeight/1.6

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
				self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 16 - self.yBorder
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
				self.button = event.GetEventObject()
				self.button.SetBackgroundColour( self.selectionColour )
				self.pressFlag = True
				self.label = event.GetEventObject().GetName().encode( 'utf-8' )			
				self.stoper.Start( 0.15 * self.timeGap )

				if self.label == 'volume down':
					try:
						recentVolume = alsaaudio.Mixer( control = 'Master', cardindex = self.card_index ).getvolume( )[ 0 ] 
						alsaaudio.Mixer( control = 'Master', cardindex = self.card_index ).setvolume( recentVolume - 15, 0 )
						time.sleep( 1.5 )

					except alsaaudio.ALSAAudioError:
						self.button.SetBackgroundColour( 'red' )
						self.button.SetFocus( )

						self.Update( )
						time.sleep( 1.5 )

				elif self.label == 'volume up':
					try:
						recentVolume = alsaaudio.Mixer( control = 'Master', cardindex = self.card_index ).getvolume( )[ 0 ] 
						alsaaudio.Mixer( control = 'Master', cardindex = self.card_index ).setvolume( recentVolume + 15, 0 )
						time.sleep( 1.5 )

					except alsaaudio.ALSAAudioError:
						self.button.SetBackgroundColour( 'red' )
						self.button.SetFocus( )
							
						self.Update( )
						time.sleep( 1.5 )

				elif self.label == 'play pause':
					if self.pressedStopFlag == True:
						os.system( 'smplayer -send-action play' ) 
						self.pressedStopFlag = False
						
					else:
						os.system( 'smplayer -send-action pause' )
						
				elif self.label == 'stop':
					os.system( 'smplayer -send-action stop && smplayer -send-action stop %% smplayer -send-action fullcreen' )
					self.pressedStopFlag = True
					
				elif self.label == 'fast backward':
					os.system( 'smplayer -send-action pl_prev' )
					
				elif self.label == 'fast forward':
					os.system( 'smplayer -send-action pl_next' )
					
				elif self.label == 'backward':
					os.system( 'smplayer -send-action rewind1' )
					
				elif self.label == 'forward':
					os.system( 'smplayer -send-action forward1' )
					
				elif self.label == 'repeat':
					os.system( 'smplayer -send-action repeat' )
					
				elif self.label == 'playlist repeat':
					os.system( 'smplayer -send-action pl_repeat' )
					
				elif self.label == 'cancel':
					if "smplayer" in [psutil.Process(i).name() for i in psutil.pids( )]:
						os.system( 'smplayer -send-action quit' )
						
					self.onExit( )
					
				elif self.label == 'back':
					self.onExit( )
				
				elif self.label == 'playlist':
					os.system( 'smplayer -send-action show_playlist' )

		else:
			self.numberOfPresses += 1
			self.numberOfEmptyIteration = 0

			if self.numberOfPresses == 1:

				if self.flag == 'row':

                                        if self.pressSound == "voice":
                                                if (self.rowIteration == 1):
                                                        self.oneSound.play()
                                                if (self.rowIteration == 2):
                                                        self.twoSound.play()
                                                if (self.rowIteration == 4):
                                                        self.fourSound.play()
                                                if (self.rowIteration == 5):
                                                        self.fiveSound.play()
                                                if (self.rowIteration == 6):
                                                        self.sixSound.play()
                                                if (self.rowIteration == 7):
                                                        self.sevenSound.play()

					if self.rowIteration == 1 or self.rowIteration == 2:
						buttonsToHighlight = range( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ], ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] )
						for button in buttonsToHighlight:
							item = self.subSizer.GetItem( button )
							b = item.GetWindow( )
							b.SetBackgroundColour( self.selectionColour )
							b.SetFocus( )
						self.flag = 'columns'
						self.colIteration = 0                                

					elif self.rowIteration == 3:
                                                if self.pressSound == "voice":
                                                        self.playlistSound.play()
						buttonsToHighlight = ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ],
						for button in buttonsToHighlight:
							item = self.subSizer.GetItem( button )
							b = item.GetWindow( )
							b.SetBackgroundColour( self.selectionColour )
							b.SetFocus( )

						self.rowIteration = 0
						os.system( 'smplayer -send-action show_playlist' )

					else:
						buttonsToHighlight = range( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] - 1, ( self.rowIteration - 1) * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] - 1 )
						for button in buttonsToHighlight:
							item = self.subSizer.GetItem( button )
							b = item.GetWindow( )
							b.SetBackgroundColour( self.selectionColour )
							b.SetFocus( )
						self.flag = 'columns'
						self.colIteration = 0                                

				elif self.flag == 'columns':

					if self.rowIteration == 1 or self.rowIteration == 2:
						self.position = ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.colIteration

					else:
						self.position = ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.colIteration - 1

					item = self.subSizer.GetItem( self.position - 1 )
					selectedButton = item.GetWindow( )
					selectedButton.SetBackgroundColour( self.selectionColour )
					selectedButton.SetFocus( )

					self.Update( )

					if self.buttons[ self.position ][ 0 ] == 'volume down':
						try:
                                                        if self.pressSound == "voice":
                                                                self.ciszejSound.play()

                                                        
                                                        self.reader.readParameters()
                                                        parameters = self.reader.getParameters()
                                                        self.unpackParameters(parameters)
                                                        
                                                        if self.volumeLevel == 0: 
                                                                raise alsaaudio.ALSAAudioError
                                                        else:
                                                                for idx, item in enumerate(self.volumeLevels):
                                                                        if self.volumeLevel == item:
                                                                                self.volumeLevel = self.volumeLevels[idx-1]
                                                                                break

                                                        os.system("pactl set-sink-volume alsa_output.pci-0000_00_1b.0.analog-stereo %d%%" % self.volumeLevel)
                                                        self.reader.saveVolume(self.volumeLevel)
                                                        time.sleep( 1.5 )

						except alsaaudio.ALSAAudioError:
							selectedButton.SetBackgroundColour( 'red' )
							selectedButton.SetFocus( )

							self.Update( )
							time.sleep( 1.5 )

					elif self.buttons[ self.position ][ 0 ] == 'volume up':
						try:
                                                        if self.pressSound == "voice":
                                                                self.glosniejSound.play()

                                                        self.reader.readParameters()
                                                        parameters = self.reader.getParameters()
                                                        self.unpackParameters(parameters)
                                                        
                                                        if self.volumeLevel == 160: 
                                                                raise alsaaudio.ALSAAudioError
                                                        else:
                                                                for idx, item in enumerate(self.volumeLevels):
                                                                        if self.volumeLevel == item:
                                                                                self.volumeLevel = self.volumeLevels[idx+1]
                                                                                break
                                                                                        
                                                        os.system("pactl set-sink-volume alsa_output.pci-0000_00_1b.0.analog-stereo %d%%" % self.volumeLevel)
                                                        self.reader.saveVolume(self.volumeLevel)
                                                
                                                        time.sleep( 1.5 )
					

						except alsaaudio.ALSAAudioError:
							selectedButton.SetBackgroundColour( 'red' )
							selectedButton.SetFocus( )

							self.Update( )
							time.sleep( 1.5 )

					elif self.buttons[ self.position ][ 0 ] == 'play pause':
                                                if self.pressSound == "voice":
                                                        self.zatrzymajGrajSound.play()
						if self.pressedStopFlag == True:
							os.system( 'smplayer -send-action play' ) 
							self.pressedStopFlag = False

						else:
							os.system( 'smplayer -send-action pause' )

					elif self.buttons[ self.position ][ 0 ] == 'stop':
                                                if self.pressSound == "voice":
                                                        self.stopSound.play()
						os.system( 'smplayer -send-action stop && smplayer -send-action stop %% smplayer -send-action fullcreen' )
						self.pressedStopFlag = True

					elif self.buttons[ self.position ][ 0 ] == 'fast backward':
                                                if self.pressSound == "voice":
                                                        self.przewinDoTyluSzybkoSound.play()
						os.system( 'smplayer -send-action pl_prev' )

					elif self.buttons[ self.position ][ 0 ] == 'fast forward':
                                                if self.pressSound == "voice":
                                                        self.przewinDoPrzoduSzybkoSound.play()
						os.system( 'smplayer -send-action pl_next' )

					elif self.buttons[ self.position ][ 0 ] == 'backward':
                                                if self.pressSound == "voice":
                                                        self.przewinDoTyluSound.play()
						os.system( 'smplayer -send-action rewind1' )

					elif self.buttons[ self.position ][ 0 ] == 'forward':
                                                if self.pressSound == "voice":
                                                        self.przewinDoPrzoduSound.play()
						os.system( 'smplayer -send-action forward1' )

					elif self.buttons[ self.position ][ 0 ] == 'repeat':
                                                if self.pressSound == "voice":
                                                        self.powtarzajUtworSound.play()
						os.system( 'smplayer -send-action repeat' )

					elif self.buttons[ self.position ][ 0 ] == 'playlist repeat':
                                                if self.pressSound == "voice":
                                                        self.powtarzajListeSound.play()
						os.system( 'smplayer -send-action pl_repeat' )

					elif self.buttons[ self.position ][ 0 ] == 'cancel':
                                                if self.pressSound == "voice":
                                                        self.wyjscieSound.play()
						if "smplayer" in [psutil.Process(i).name() for i in psutil.pids( )]:
							os.system( 'smplayer -send-action quit' )

						self.onExit( )

					elif self.buttons[ self.position ][ 0 ] == 'back':
                                                if self.pressSound == 'voice':
                                                        self.powrotSound.play()
						self.onExit( )

					selectedButton.SetBackgroundColour( self.backgroundColour ) # depend on abilites comment or not
					self.flag = 'row'
					self.rowIteration = 0
					self.colIteration = 0
					self.countRows = 0
					self.countColumns = 0

			else:
				pass

			# print self.numberOfPresses

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
			if self.control != 'tracker':
				self.mouseCursor.move( *self.mousePosition )	

			self.numberOfPresses = 0

			if self.numberOfEmptyIteration < 3*0.9999999999:

				if self.switchSound.lower( ) == 'on':
					self.switchingSound.play( )

				if self.flag == 'row': #flag == row ie. switching between rows

						self.numberOfEmptyIteration += 1. / self.numberOfRows[ 0 ]

						self.rowIteration = self.rowIteration % self.numberOfRows[ 0 ]

                                                if self.switchSound == "voice":
                                                        if (self.rowIteration == 0):
                                                                self.oneSound.play()
                                                        if (self.rowIteration == 1):
                                                                self.twoSound.play()
                                                        if (self.rowIteration == 3):
                                                                self.fourSound.play()
                                                        if (self.rowIteration == 4):
                                                                self.fiveSound.play()
                                                        if (self.rowIteration == 5):
                                                                self.sixSound.play()
                                                        if (self.rowIteration == 6):
                                                                self.sevenSound.play()

						items = self.subSizer.GetChildren( )
						for item in items:
							b = item.GetWindow( )
							b.SetBackgroundColour( self.backgroundColour )
							b.SetFocus( )

						if self.rowIteration == 0 or self.rowIteration == 1:
							scope = range( self.rowIteration * self.numberOfColumns[ 0 ], self.rowIteration * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] )

						elif self.rowIteration == 2:
                                                        if self.switchSound == "voice":
                                                                self.playlistSound.play()

							scope = self.rowIteration * self.numberOfColumns[ 0 ], 

						else:
							scope = range( self.rowIteration * self.numberOfColumns[ 0 ] - 1, self.rowIteration * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] - 1 )
						for i in scope:
							item = self.subSizer.GetItem( i )
							b = item.GetWindow( )
							b.SetBackgroundColour( self.scanningColour )
							b.SetFocus( )

						self.rowIteration += 1

				elif self.flag == 'columns': #flag = columns ie. switching between cells in the particular row

					if self.countColumns == self.countMaxColumns:
						self.flag = 'row'
						self.rowIteration = 0
						self.colIteration = 0
						self.countColumns = 0
						self.countRows = 0

						items = self.subSizer.GetChildren( )
						for item in items:
							b = item.GetWindow( )
							b.SetBackgroundColour( self.backgroundColour )
							b.SetFocus( )

					else:
						self.colIteration = self.colIteration % self.numberOfColumns[ 0 ]

						if self.colIteration == self.numberOfColumns[ 0 ] - 1:
							self.countColumns += 1

						items = self.subSizer.GetChildren( )
						for item in items:
							b = item.GetWindow( )
							b.SetBackgroundColour( self.backgroundColour )
							b.SetFocus( )

						if self.rowIteration == 1 or self.rowIteration == 2:
							item = self.subSizer.GetItem( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.colIteration )

						else:
							item = self.subSizer.GetItem( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.colIteration - 1 )				
						b = item.GetWindow( )
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus( )
                                                logo = b.Name
                                                
                                                if self.switchSound == "voice":
                                                        if logo == 'volume down':
                                                                self.ciszejSound.play()
                                                        if logo == 'volume up':
                                                                self.glosniejSound.play()
                                                        if logo == 'play pause':
                                                                self.zatrzymajGrajSound.play()
                                                        if logo == 'stop':
                                                                self.stopSound.play()
                                                        if logo == 'fast backward':
                                                                self.przewinDoTyluSzybkoSound.play()
                                                        if logo == 'fast forward':
                                                                self.przewinDoPrzoduSzybkoSound.play()
                                                        if logo == 'backward':
                                                                self.przewinDoTyluSound.play()
                                                        if logo == 'forward':
                                                                self.przewinDoPrzoduSound.play()
                                                        if logo == 'repeat':
                                                                self.powtarzajUtworSound.play()
                                                        if logo == 'playlist repeat':
                                                                self.powtarzajListeSound.play()
                                                        if logo == 'cancel':
                                                                self.wyjscieSound.play()
                                                        if logo == 'back':
                                                                self.powrotSound.play()
                                                
						self.colIteration += 1

			else:
                            if self.switchSound == "voice":
                                    self.usypiamSound.play()
			    self.stoper.Stop( )
			    suspend.suspend( self, id = 2 ).Show( True )
			    self.Hide( )

			    items = self.subSizer.GetChildren( )			
			    for item in items:
				    b = item.GetWindow( )
				    b.SetBackgroundColour( self.backgroundColour )
				    b.SetFocus( )

			    self.numberOfEmptyIteration = 0
			    self.countColumns = 0
			    self.countRows = 0
			    self.colIteration = 0
			    self.rowIteration = 0
			    self.countColumns = 0
			    self.countRows = 0
			    self.numberOfPresses = 1

			# print self.rowIteration, self.colIteration

#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = pilot( parent = None, id = -1 )
        frame.Show( True )
	app.MainLoop( )
