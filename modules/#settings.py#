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

import glob, os, time, sys, psutil
import wx
import wx.lib.buttons as bt

from pymouse import PyMouse
from pygame import mixer
from ewriting import eplatform
import atgames

#=============================================================================
class settings( wx.Frame ):
	def __init__(self, parent, id):

	    self.winWidth, self.winHeight = wx.DisplaySize( )
	
            wx.Frame.__init__( self , parent , id, 'ATExercise' )
            # style = self.GetWindowStyle( )
            # self.SetWindowStyle( style | wx.STAY_ON_TOP )
            # self.Maximize( True )
            # self.Centre( True )
            # self.MakeModal( True )		

            self.ShowFullScreen( True )
            self.parent = parent
            
            self.initializeParameters( )
            self.initializeBitmaps( )
            self.createGui( )
            self.createBindings( )
            
            self.initializeTimer( )
            
	#-------------------------------------------------------------------------
	def reloadWindow(self): 
                
            self.mainSizer.DeleteWindows()
            self.initializeParameters( )
            self.createGui( )
            self.Layout()
            self.Update()
            self.createBindings( )						
            
            self.initializeTimer( )				
	#-------------------------------------------------------------------------
	def initializeParameters(self):

		with open( './.pathToAP' ,'r' ) as textFile:
			self.pathToAP = textFile.readline( )

		sys.path.append( self.pathToAP )
		from reader import reader
		
		self.reader = reader()
	        self.parameters = self.reader.getParameters()

                self.unpackParameters(self.parameters)
							
		self.pressFlag = False

		self.numberOfColumns = 2,
		self.numberOfRows = 2,
		
		self.columnIteration = 0
		self.rowIteration = 0	
		self.panelIteration = 0
		self.emptyColumnIteration = 0
		self.emptyRowIteration = 0
		self.emptyPanelIteration = 0
		self.maxEmptyColumnIteration = 2									
		self.maxEmptyRowIteration = 2									
		self.maxEmptyPanelIteration = 2
		
		self.numberOfPresses = 1

		if self.control not in ['tracker', 'eye']:
			self.mouseCursor = PyMouse( )
			self.mousePosition = self.winWidth - 8 - self.yBorder, self.winHeight - 8 - self.xBorder
			self.mouseCursor.move( *self.mousePosition )			

                mixer.init()
		if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
				self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
				self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )
                                
                                self.glowaSound = mixer.Sound( self.pathToAP + '/sounds/glowa.ogg' )
                                self.oneSound = mixer.Sound( self.pathToAP + '/sounds/rows/1.ogg' )
                                self.oczySound = mixer.Sound( self.pathToAP + '/sounds/oczy.ogg' )
                                self.powrotSound = mixer.Sound( self.pathToAP + '/sounds/powrot.ogg' )
                                self.usypiamSound = mixer.Sound( self.pathToAP + '/sounds/usypiam.ogg' )
                                self.clickSound = mixer.Sound(self.pathToAP + '/sounds/click.ogg')
		
		self.SetBackgroundColour( 'black' )

	#-------------------------------------------------------------------------	
        def unpackParameters(self, parameters):

            for item in parameters:

                name = item[:item.find('=')]
                value = item[item.find('=')+1:]

                if value.startswith('wx.'): #when using wxpython values
		    setattr( self, name, eval(value) )
                else: 
		    try:
			setattr( self, name, int(value) )
		    except ValueError:
			setattr( self, name, value )
                        
	#-------------------------------------------------------------------------	
        def initializeBitmaps(self):
		
		self.panels = { 1 : [ [], [] ] }
		self.numberOfPanels = 1
				
		self.functionButtonPath = [ wx.BitmapFromImage( wx.ImageFromStream( open(self.pathToAP + 'icons/back.png', 'rb' ) ) ), wx.BitmapFromImage( wx.ImageFromStream( open(self.pathToAP + 'icons/modules/headtracking.png', 'rb' ) ) ), wx.BitmapFromImage( wx.ImageFromStream(open(self.pathToAP + 'icons/modules/eyetracking.png', 'rb' ) ) ) ]

		self.labels = [ 'headtracking', 'eyetracking' ]
		self.functionButtonName = [ 'back' ]

		if self.numberOfPanels == 1:
			self.flag = 'row'
		else:
			self.flag = 'panel'
		
	#-------------------------------------------------------------------------
	def createGui(self):

                self.subSizers = [ ]
                self.mainSizer = wx.BoxSizer( wx.VERTICAL )
                
		self.numberOfCells = self.numberOfRows[ 0 ] * self.numberOfColumns[ 0 ]

		if self.control not in ['tracker', 'eye']:
			event = eval('wx.EVT_LEFT_DOWN')
		else:
			event = eval('wx.EVT_BUTTON')

                for panel in self.panels.keys( ):
			
			subSizer = wx.GridBagSizer( self.xBorder, self.yBorder )
                   
			self.subSizers.append( subSizer )
			
			index = 0

			for index in range( 2 ):
				b = bt.GenBitmapButton( self, -1, bitmap = self.functionButtonPath[ index+1 ], name = self.labels[ index ] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
                                b.mode = 'pointing'
                                if self.control == 'eye':
                                        b.Bind( event, self.onKey )
                                        b.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)
                                        b.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)
                                else:
                                        b.Bind( event, self.onPress )

				subSizer.Add( b, ( index / self.numberOfColumns[ 0 ], index % self.numberOfColumns[ 0 ] ), wx.DefaultSpan, wx.EXPAND )

			b = bt.GenBitmapButton( self, -1, bitmap = self.functionButtonPath[ 0 ], name = self.functionButtonName[ 0 ] )
			b.SetBackgroundColour( self.backgroundColour )
			b.SetBezelWidth( 3 )
                        b.mode = 'pointing'
                        if self.control == 'eye':
                                b.Bind( event, self.onKey )
                                b.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)
                                b.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)
                        else:
                                b.Bind( event, self.onPress )

			subSizer.Add( b, ( ( index + 1 ) / self.numberOfColumns[ 0 ], ( index + 1 ) % self.numberOfColumns[ 0 ] ), (1, 2), wx.EXPAND )
				
			for number in range( self.numberOfRows[ 0 ] ):
				subSizer.AddGrowableRow( number )
			for number in range( self.numberOfColumns[ 0 ] ):
				subSizer.AddGrowableCol( number )
		
			self.Layout( )
                        self.colour = b.GetBackgroundColour( )
			self.mainSizer.Add( subSizer, proportion = 1, flag = wx.EXPAND | wx.LEFT | wx. TOP | wx.BOTTOM | wx.RIGHT, border = self.xBorder)
			
			self.Center( True )
                        
			if panel != 1:
				self.mainSizer.Show( item = self.subSizers[ panel - 1 ], show = True, recursive = True )
                    
			self.SetSizer( self.mainSizer )
                
	#-------------------------------------------------------------------------
	def initializeTimer(self):
		self.stoper = wx.Timer( self )
		self.Bind( wx.EVT_TIMER , self.timerUpdate , self.stoper )

                if self.control == 'eye':
                    self.stoper.Start( 50 )
		elif self.control != 'tracker':
			self.stoper.Start( self.timeGap )
	
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
            
		ret = dial.ShowModal()
		
		if ret == wx.ID_YES:
			try:
				if "smplayer" in [psutil.Process(i).name() for i in psutil.pids( )]:
					os.system( 'smplayer -send-action quit' )
			except TypeError:
				if "smplayer" in [psutil.Process(i).name for i in psutil.pids( )]:
					os.system( 'smplayer -send-action quit' )

			if __name__ == '__main__':
				self.Destroy( )
			else:
				self.parent.Destroy( )
				self.Destroy( )

		else:
			event.Veto()

			if self.control != 'tracker':
				self.mousePosition = self.winWidth - 8 - self.yBorder, self.winHeight - 8 - self.xBorder
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
			if self.control != 'tracker':
				self.parent.stoper.Start( self.parent.timeGap )
				self.parent.reloadWindow()
                        
			self.Destroy( )

	#-------------------------------------------------------------------------
        def onKey(self, event):
            """
            Check for left mouse click. If so, press active button of the parent frame.
            """

            items = self.subSizers[ 0 ].GetChildren( )

            for item in items:
                b_active = item.GetWindow( )
                if b_active.mode == 'confirmation':
                    b_active.SetBackgroundColour(wx.Colour(255,0,255, b_active.GetBackgroundColour().Alpha()))
                    b_active.Refresh()
                    b_active.Update()
                    for button in items:
                        b2 = button.GetWindow( )
                        if b2!=b_active:
                            b2.SetBackgroundColour(self.colour)
                            b2.mode = 'pointing'
                            b2.Update()
                    time.sleep(2)

                    if self.pressFlag == False:
                            self.button = event.GetEventObject( )
                            self.pressFlag = True
                            
                            self.label = b_active.GetName( ).encode( 'utf-8' )
                            self.stoper.Stop()
                            
                    if self.label == 'headtracking':
                            self.reader.setParameter('control', 'switch')
                            self.parameters = self.reader.getParameters()
                            self.reloadWindow()
                            os.system("milena_say Ustawiono metodę obsługi komputera na ruchy głowy")
                            
		    elif self.label == 'eyetracking':
                            self.reader.setParameter('control', 'eye')
                            self.parameters = self.reader.getParameters()
                            self.reloadWindow()
                            os.system("milena_say Ustawiono metodę obsługi komputera na ruchy oczu i głowy")

		    elif self.label == 'back':
			    self.onExit( )

	#-------------------------------------------------------------------------
        def onMouseOver(self, event):
            # mouseover changes colour of button

            self.b = event.GetEventObject()
            if self.b.mode == 'pointing':
                self.b.SetBackgroundColour(wx.Colour(0,255,255, self.b.GetBackgroundColour().Alpha()))
            event.Skip()

        #-------------------------------------------------------------------------
        def onMouseLeave(self, event):
            # mouse not over button, back to original colour
            # self.b = event.GetEventObject()

            if self.b.mode == 'pointing':
                self.b.SetBackgroundColour(self.colour)
            event.Skip()

                        
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

			if self.label == 'headtracking':
                                self.reader.setParameter('control', 'switch')
                                self.parameters = self.reader.getParameters()
                                self.reloadWindow()
                                os.system("milena_say Ustawiono metodę obsługi komputera na ruchy głowy")

			elif self.label == 'eyetracking':
                                self.reader.setParameter('control', 'eye')
                                self.parameters = self.reader.getParameters()
                                self.reloadWindow()
                                os.system("milena_say Ustawiono metodę obsługi komputera na ruchy oczu i głowy")

			elif self.label == 'back':
				self.onExit( )

		else:
			self.numberOfPresses += 1

			if self.numberOfPresses == 1:

				if self.flag == 'rest':

					if self.numberOfPanels == 1:
						self.flag = 'row'
					else:
						self.flag = 'panel'

				elif self.flag == 'panel':
					items = self.subSizers[ self.panelIteration ].GetChildren( )			

					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus( )

                                        self.stoper.Stop( )
                                        time.sleep( self.selectionTime/1000. )
                                        self.stoper.Start( self.timeGap )

					self.flag = 'row'

				elif self.flag == 'row':

					if self.rowIteration == self.numberOfRows[ 0 ]:
						buttonsToHighlight = ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ],

					else:
						buttonsToHighlight = range( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ], ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] )

					for button in buttonsToHighlight:
						item = self.subSizers[ self.panelIteration ].GetItem( button )
						b = item.GetWindow( )
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus( )
                                                
                                        self.Update( )

					if self.rowIteration == self.numberOfRows[ 0 ]:

                                                if self.pressSound.lower() == 'voice':
                                                        self.powrotSound.play()

                                                # self.stoper.Stop( )
                                                # time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                # self.powrotSound.play( )
                                                # time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                                # self.stoper.Start( self.timeGap )

                                                self.onExit( )

                                        else:
                                                if self.pressSound.lower() == 'voice':
                                                        self.oneSound.play()

                                                self.stoper.Stop( ) ## Strange pauses in the code are delivered in order to make interaction slower and less immediate.
                                                time.sleep( self.selectionTime/1000. )
                                                self.stoper.Start( self.timeGap )

					self.flag = 'columns'

				elif self.flag == 'columns':

					self.position = ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.columnIteration - 1

					item = self.subSizers[ self.panelIteration ].GetItem( self.position )
					selectedButton = item.GetWindow( )
					selectedButton.SetBackgroundColour( self.selectionColour )
					selectedButton.SetFocus( )

					self.Update( )

			                if self.position == 0:
                                                if self.pressSound.lower() != 'off':
                                                        self.glowaSound.play()

                                                self.reader.setParameter('control', 'switch')
                                                self.reloadWindow()
                                                # self.parameters = self.reader.getParameters()
                                                os.system("milena_say Ustawiono metodę obsługi komputera na ruchy głowy")
                                                
                                
			                elif self.position == 1:
                                                if self.pressSound.lower() != 'off':
                                                        self.oczySound.play()

                                                self.reader.setParameter('control', 'eye')
                                                self.reloadWindow()
                                                # self.parameters = self.reader.getParameters()
                                                os.system("milena_say Ustawiono metodę obsługi komputera na ruchy oczu i głowy")
                                                
                                                
					if self.numberOfPanels == 1:
					    self.flag = 'row'
					    self.panelIteration = 0
					else:
					    self.flag = 'panel'
					    self.panelIteration = -1

					self.rowIteration = 0
					self.columnIteration = 0

					self.emptyPanelIteration = -1
					self.emptyRowIteration = 0
					self.emptyColumnIteration = 0

					selectedButton = item.GetWindow( )
                                        if selectedButton != None:
					        selectedButton.SetBackgroundColour( self.backgroundColour )
					        selectedButton.SetFocus( )

			else:
				pass

			# print self.numberOfPresses

	#-------------------------------------------------------------------------
	def timerUpdate(self , event):

                if self.control == 'eye':
                            print("AAAAAAAAAAAAAAAAAAAAAAAAAA")
                            items = self.subSizers[ 0 ].GetChildren( )
                            for item in items:
                                b = item.GetWindow( )
                                if b.GetBackgroundColour() != self.colour and b.mode != 'confirmation':
                                    if (b.GetBackgroundColour().Blue() < 50):
                                        self.clickSound.play( )
                                        b.SetBackgroundColour(wx.Colour(0,255,0, b.GetBackgroundColour().Alpha()))
                                        bSize = b.GetSize()
                                        b.SetSize((bSize[0]*1.05, bSize[1]*1.05))
                                        bPosition = b.GetPosition()
                                        b.SetPosition((bPosition[0]-(bSize[0]*1.05-bSize[0])/2., bPosition[1]-(bSize[1]*1.05-bSize[1])/2.))
                                        b.mode = 'confirmation'

                                        for button in items:
                                            b2 = button.GetWindow( )
                                            if b2!=b and b2.mode == 'confirmation':
                                                b2.SetBackgroundColour(self.colour)
                                                b2.mode = 'pointing'
                                                b2Size = b2.GetSize()
                                                b2.SetSize((b2Size[0]*0.95, b2Size[1]*0.95))
                                                b2Position = b2.GetPosition()
                                                b2.SetPosition((b2Position[0]-(b2Size[0]*0.95-b2Size[0])/2., b2Position[1]-(b2Size[1]*0.95-b2Size[1])/2.))

                                    else:
                                        b.SetBackgroundColour(wx.Colour(b.GetBackgroundColour().Red(),b.GetBackgroundColour().Green()-1,b.GetBackgroundColour().Blue()-6, b.GetBackgroundColour().Alpha()))

                elif self.control == 'tracker':

			if self.button.GetBackgroundColour( ) == self.backgroundColour:
				self.button.SetBackgroundColour( self.selectionColour )
				
			else:
				self.button.SetBackgroundColour( self.backgroundColour )	
		
			self.stoper.Stop( )
			self.pressFlag = False

		else:
                        print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB")
			if self.control != 'tracker':
				self.mouseCursor.move( *self.mousePosition )	

                        self.numberOfPresses = 0
            
			if self.flag == 'panel': ## flag == panel ie. switching between panels
				
				if self.emptyPanelIteration == self.maxEmptyPanelIteration:
					self.flag = 'rest'
					self.emptyPanelIteration = 0
				else:
					self.panelIteration += 1
				
					self.panelIteration = self.panelIteration % self.numberOfPanels
					
					if self.panelIteration == self.numberOfPanels - 1:
						self.emptyPanelIteration += 1

					for item in range( self.numberOfPanels ):
						if item != self.panelIteration:
							self.mainSizer.Show( item = self.subSizers[ item ], show = False, recursive = True )
							
					self.mainSizer.Show( item = self.subSizers[ self.panelIteration ], show = True, recursive = True )
					self.SetSizer( self.mainSizer )
					self.Layout( )
					
			if self.flag == 'row': #flag == row ie. switching between rows
				
				if self.emptyRowIteration == self.maxEmptyRowIteration:
					self.emptyRowIteration = 0
					self.emptyPanelIteration = 0
					
					if self.numberOfPanels == 1:
                                                if self.pressSound.lower() == 'voice':
                                                        self.usypiamSound.play()
						self.flag = 'rest'
					else:
						self.flag = 'panel'

					items = self.subSizers[ self.panelIteration ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )
#####################################################################################################################################

					if self.numberOfPanels > 1:
						if self.panelIteration == self.numberOfPanels:
							self.panelIteration = self.numberOfPanels - 1
						else:
							self.panelIteration -= 1

######################################################################################################################################			
				else:
					self.rowIteration = self.rowIteration % self.numberOfRows[ 0 ]

                                        if self.switchSound == "voice":
                                            if (self.rowIteration == 0):
                                                self.oneSound.play()
                                            if (self.rowIteration == 1):
                                                self.powrotSound.play()
                                
					items = self.subSizers[ self.panelIteration ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )
				
					if self.rowIteration == self.numberOfRows[ 0 ] - 1:
						self.emptyRowIteration += 1
				
						scope = self.rowIteration * self.numberOfColumns[ 0 ],
					else:
						scope = range( self.rowIteration * self.numberOfColumns[ 0 ], self.rowIteration * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] )
					for i in scope:
						item = self.subSizers[ self.panelIteration ].GetItem( i )
						b = item.GetWindow( )
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus( )
					self.rowIteration += 1
                        
			elif self.flag == 'columns': #flag = columns ie. switching between cells in the particular row

				if self.emptyColumnIteration == self.maxEmptyColumnIteration:
					self.flag = 'row'
					self.rowIteration = 0
					self.columnIteration = 0
					self.emptyColumnIteration = 0
					self.emptyRowIteration = 0
					
					items = self.subSizers[ self.panelIteration ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

				else:
					self.columnIteration = self.columnIteration % self.numberOfColumns[ 0 ]
					
					if self.columnIteration == self.numberOfColumns[ 0 ] - 1:
						self.emptyColumnIteration += 1

                                        if self.switchSound == "voice":
                                            if (self.columnIteration == 0):
                                                self.glowaSound.play()
                                            if (self.columnIteration == 1):
                                                self.oczySound.play()

					items = self.subSizers[ self.panelIteration ].GetChildren( )
					for item in items:
						b = item.GetWindow( )
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

					item = self.subSizers[ self.panelIteration ].GetItem( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.columnIteration )
					b = item.GetWindow( )
					b.SetBackgroundColour( self.scanningColour )
					b.SetFocus( )

					self.columnIteration += 1

			if self.flag != 'rest':
				if self.switchSound.lower( ) == 'on':
					self.switchingSound.play( )

			else:
				pass

		# print self.panelIteration, self.rowIteration, self.columnIteration


#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = settings( parent = None, id = -1 )
        frame.Show( True )
	app.MainLoop( )
