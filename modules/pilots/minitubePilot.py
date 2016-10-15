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

import glob, os, time, sys, psutil
import wx, alsaaudio
import wx.lib.buttons as bt

import subprocess as sp
from pymouse import PyMouse
from string import maketrans
from pygame import mixer

import suspend
#=============================================================================
class pilot(wx.Frame):
	def __init__(self, parent, id):
	
	    self.winWidth, self.winHeight = wx.DisplaySize( )
	    
	    self.dw, self.dh = wx.DisplaySize()
	    
            self.initializeParameters()				
            wx.Frame.__init__(self , parent , id, 'Pilot', size = (220, 400), pos = (self.dw - 230, self.dh - 435) )
            self.SetBackgroundColour( 'black' )
	    
            style = self.GetWindowStyle()
            self.SetWindowStyle( style | wx.STAY_ON_TOP )
            self.parent = parent
	    
            self.MakeModal( True )		
		
            self.initializeBitmaps()
            self.createGui()								
            self.createBindings()						

            self.initializeTimer()					

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
                        
            self.flag = 'row'
	    self.pressFlag = False
            self.pressedStopFlag = False
	    
            self.rowIteration = 0						
            self.colIteration = 0

            self.rowIteration = 0						
            self.colIteration = 0

            self.numberOfColumns = 2,
            self.numberOfRows = 5,

            self.numberOfSymbol = 0
            
	    self.numberOfEmptyIteration = 0
            self.countRows = 0
            self.countColumns = 0
            self.button = 1
            self.countMaxRows = 2									
            self.countMaxColumns = 2									
            self.numberOfPresses = 0

            ### if download option was available
	    # self.youtubeFiles = sorted( glob.glob('./youtube playlist/*') )
	    # if bool( self.youtubeFiles ) == False:
	    #         self.lastYoutubeFile = 1
	    # else:
	    #         self.lastYoutubeFile = self.youtubeFiles[-1]

	    if self.control != 'tracker':	    
		    self.mouseCursor = PyMouse( )
		    # self.mousePosition = self.winWidth - 8 - self.xBorder, self.winHeight - 16 - self.yBorder
		    # self.mouseCursor.move( *self.mousePosition )	
                    self.mouseCursor.move( self.dw - 225, self.dh - 265 )	

	    if self.switchSound.lower( ) == 'on' or self.pressSound.lower( ) == 'on':
		    mixer.init( )
		    if self.switchSound.lower( ) == 'on':
			    self.switchingSound = mixer.Sound( self.pathToAP + '/sounds/switchSound.ogg' )
		    if self.pressSound.lower( ) == 'on':
			    self.pressingSound = mixer.Sound( self.pathToAP + '/sounds/pressSound.ogg' )
            	    
	    self.width = self.numberOfColumns[0] * 120
	    self.height = self.numberOfRows[0] * 100

            self.card_index = 0
            try:
                    alsaaudio.Mixer( control = 'Master', cardindex=self.card_index ).setvolume( self.musicVolumeLevel, 0 )
            except alsaaudio.ALSAAudioError:
                    self.card_index = 1
                    
	#-------------------------------------------------------------------------	
        def initializeBitmaps(self):

            radioLogoPaths = glob.glob(self.pathToAP + 'icons/pilots/minitubePilot/*') #labelFiles
            
            self.radios = {}

            for radioLogoPath in radioLogoPaths:

                radioLogoBitmap = wx.BitmapFromImage( wx.ImageFromStream( open(radioLogoPath, "rb") ))

                radioLabel = radioLogoPath[ radioLogoPath.rfind( '/' )+1 : radioLogoPath.rfind('.') ]
                try:
                    radioPosition = int( radioLabel.split('_')[0] )
                    radioName = radioLabel[ radioLabel.find('_')+1: ]
                    self.radios[radioPosition] = [radioName, radioLogoBitmap]
                    

                except ValueError:
                    print 'Symbol %s w folderze %s ma nieprawidłową nazwę.' % (symbolName.split('_')[0], page[page.rfind('/')+1:])
                    pass

	#-------------------------------------------------------------------------
	def createGui(self):

		self.mainSizer = wx.BoxSizer( wx.VERTICAL )

		self.subSizer = wx.GridBagSizer( 4, 4 )
		
		print self.radios.keys()[-5:]

		for key, value in self.radios.items():
			if key == 1 or key == 2 or key == 3 or key == 4:
				b = bt.GenBitmapButton( self, -1, name = value[0], bitmap = value[1] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
				
				self.subSizer.Add(b, ( (key-1) / self.numberOfColumns[0], (key-1) % self.numberOfColumns[0] ), wx.DefaultSpan, wx.EXPAND)

			elif key == 5:
				b = bt.GenBitmapButton( self, -1, name = value[0], bitmap = value[1] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
				
				self.subSizer.Add(b, ( (key-1) / self.numberOfColumns[0], (key-1) % self.numberOfColumns[0] ), (1, 2), wx.EXPAND)
			
			elif key == 6:
				b = bt.GenBitmapButton( self, -1, name = value[0], bitmap = value[1] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
				
				self.subSizer.Add(b, ( (key) / self.numberOfColumns[0], (key) % self.numberOfColumns[0] ), (1, 2), wx.EXPAND)
			
			# elif key == 7 or key == 8:
			# 	b = bt.GenBitmapButton( self, -1, name = value[0], bitmap = value[1] )
			# 	b.SetBackgroundColour( self.backgroundColour )
			# 	b.SetBezelWidth( 3 )
			# 	b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
				
			# 	self.subSizer.Add(b, ( (key+1) / self.numberOfColumns[0], (key+1) % self.numberOfColumns[0] ), wx.DefaultSpan, wx.EXPAND)
			
			elif key == 9:
				b = bt.GenBitmapButton( self, -1, name = value[0], bitmap = value[1] )
				b.SetBackgroundColour( self.backgroundColour )
				b.SetBezelWidth( 3 )
				b.Bind( wx.EVT_LEFT_DOWN, self.onPress )
				
				self.subSizer.Add(b, ( (key-1) / self.numberOfColumns[0], (key-1) % self.numberOfColumns[0] ), (1, 2), wx.EXPAND)
			
                for number in range(self.numberOfRows[0]):
                    self.subSizer.AddGrowableRow( number )
                for number in range(self.numberOfColumns[0]):
                    self.subSizer.AddGrowableCol( number )
		
		self. mainSizer.Add( self.subSizer, proportion=1, flag=wx.EXPAND )
		self.SetSizer( self. mainSizer )
                    
	#-------------------------------------------------------------------------
	def initializeTimer(self):
		self.stoper = wx.Timer(self)
		self.Bind( wx.EVT_TIMER , self.timerUpdate , self.stoper )
		self.stoper.Start( self.timeGap )
	
	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE , self.OnCloseWindow )

	#-------------------------------------------------------------------------
	def OnCloseWindow(self , event):
		self.stoper.Stop()
		self.Destroy()

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
	def setP(self, message):
		self.radioID = message.data

	#-------------------------------------------------------------------------
        def onPress(self, event):

		if self.pressSound.lower( ) == 'on':
			self.pressingSound.play( )
		
		self.numberOfEmptyIteration = 0

                # print(self.rowIteration)
                if self.numberOfPresses == 0:
                         
			if self.flag == 'row':

                                self.rowIteration -= 1

				if self.rowIteration == 0 or self.rowIteration == 1:
					buttonsToHighlight = range(self.rowIteration*self.numberOfColumns[0], self.rowIteration*self.numberOfColumns[0] + self.numberOfColumns[0])
					for button in buttonsToHighlight:
						item = self.subSizer.GetItem( button )
						b = item.GetWindow()
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus()
					self.flag = 'columns'
					self.colIteration = 0                                

					#self.stoper.Start( self.timeGap )
									
				elif self.rowIteration == 2:
					buttonsToHighlight = self.rowIteration*self.numberOfColumns[0],
					for button in buttonsToHighlight:
						item = self.subSizer.GetItem( button )
						b = item.GetWindow()
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus()

					self.rowIteration = 0
					os.system("wid=`wmctrl -l | awk '/Minitube/ {print $1}'` && xdotool windowfocus $wid && xdotool key --window $wid F11 && wid=`wmctrl -l | awk '/Pilot/ {print $1}'` && xdotool windowactivate $wid' #&& xdotool keydown alt key Tab; sleep 1; xdotool keyup alt'  #&& wid2=`wmctrl -l | awk '/Pilot/ {print $1}'` && xdotool windowraise $wid2")
					
				elif self.rowIteration == 3:
					buttonsToHighlight = self.rowIteration*self.numberOfColumns[0] - 1,
					for button in buttonsToHighlight:
						item = self.subSizer.GetItem( button )
						b = item.GetWindow()
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus()                                
					
					self.rowIteration = 0
					os.system("wid=`wmctrl -l | awk '/Minitube/ {print $1}'` && xdotool windowfocus $wid && xdotool key --window $wid space")
					# self.mouseCursor.click( self.playButtonPosition[self.radioID][0], self.playButtonPosition[self.radioID][1], 1 )
					# time.sleep(0.2)
					# self.mouseCursor.click( self.playButtonPosition[self.radioID][0], self.playButtonPosition[self.radioID][1], 1 )
                                ### if download option were available
				# elif self.rowIteration == 4:
				# 	buttonsToHighlight = range(self.rowIteration*self.numberOfColumns[0] - 2, self.rowIteration*self.numberOfColumns[0] + self.numberOfColumns[0] - 2)
				# 	for button in buttonsToHighlight:
				# 		item = self.subSizer.GetItem( button )
				# 		b = item.GetWindow()
				# 		b.SetBackgroundColour( self.selectionColour )
				# 		b.SetFocus()
				# 	self.flag = 'columns'
				# 	self.colIteration = 0                                

				elif self.rowIteration == 4:
					
					buttonsToHighlight = self.rowIteration*self.numberOfColumns[0] - 2,
					for button in buttonsToHighlight:
						item = self.subSizer.GetItem( button )
						b = item.GetWindow()
						b.SetBackgroundColour( self.selectionColour )
						b.SetFocus()
						
					os.system('wmctrl -c Minitube')

                                        ### if download option exists
					# time.sleep(0.5)
					# cmd = 'wmctrl -l'
					# p = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT, close_fds=True)
					# output = p.stdout.read()

					# if 'minitube' in output:
						# for button in buttonsToHighlight:
						# 	item = self.subSizer.GetItem( button )
						# 	b = item.GetWindow()
						# 	b.SetBackgroundColour( 'red' )
						# 	b.SetFocus()
						# self.Update()

						# os.system('wid=`xdotool search --onlyvisible --name minitube|head -1` && xdotool windowfocus $wid && xdotool windowactivate $wid && sleep 0.2 && xdotool key Escape && xdotool key Escape')
                                                
						# os.system('milena_say Nie ukończono pobierania materiału. Po ponownym włączeniu proszę rozpocząć pobieranie od początku')
						# path = '/home/jgrynczewski/Desktop/changes/youtube playlist'
						# files = os.listdir(path)
						# files.sort(key=lambda f: os.path.getmtime(os.path.join(path, f)))
						# os.system( 'rm ./youtube\ playlist/%s' % files[-1].replace(' ', '\ ') )

					self.onExit()
					
			elif self.flag == 'columns':
                            
                                self.colIteration -= 1
				
				if self.rowIteration == 0 or self.rowIteration == 1:
					self.position = self.rowIteration*self.numberOfColumns[ 0 ] + self.colIteration + 1
					
                                ### if download option were available BEG#####
				# elif self.rowIteration == 4:
				# 	self.position = self.rowIteration*self.numberOfColumns[ 0 ] + self.colIteration - 1
					
				item = self.subSizer.GetItem( self.position - 1 )
				selectedButton = item.GetWindow()
				selectedButton.SetBackgroundColour( self.selectionColour )
				selectedButton.SetFocus()
                                
                                self.Update()

                                ### if download option were available END####
###                                
				# if self.radios[self.position][0] == 'volume down':
				# 	try:
				# 		recentVolume = alsaaudio.Mixer( control = 'Master' ).getvolume()[0] 
				# 		alsaaudio.Mixer( control = 'Master' ).setvolume( recentVolume - 15, 0 )
				# 		time.sleep(1.5)

				# 	except alsaaudio.ALSAAudioError:
				# 		selectedButton.SetBackgroundColour( 'red' )
				# 		selectedButton.SetFocus()
                                
				# 		self.Update()
				# 		time.sleep( 1.5 )
					
				# elif self.radios[self.position][0] == 'volume up':
				# 	try:
				# 		recentVolume = alsaaudio.Mixer( control = 'Master' ).getvolume()[0] 
				# 		alsaaudio.Mixer( control = 'Master' ).setvolume( recentVolume + 15, 0 )
				# 		time.sleep(1.5)
					
				# 	except alsaaudio.ALSAAudioError:
				# 		selectedButton.SetBackgroundColour( 'red' )
				# 		selectedButton.SetFocus()
                                
				# 		self.Update()
				# 		time.sleep( 1.5 )

########################
				# elif self.radios[self.position][0] == 'undo':
				# 	# os.system('wmctrl -c "ATPlatform radio"')
				# 	os.system('wmctrl -c Mozilla')
					
				# 	cmd = 'wmctrl -l'
				# 	p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
				# 	output = p.stdout.read()
				# 	print output
				# 	if 'minitube' in output:
						
					# 	os.system('wid=`xdotool search --onlyvisible --name minitube|head -1` && xdotool windowfocus $wid && xdotool windowactivate $wid && sleep 0.2 && xdotool key Escape && xdotool key Escape')

					# self.stoper.Stop()
					# self.menu = radios(self, id=-1 )
					# self.Hide()
					# self.menu.Show()
					
				# elif self.radios[self.position][0] == 'expand':
				# 	os.system('wid=`xdotool search --onlyvisible --name Minitube` && xdotool windowfocus $wid && xdotool key --window $wid F11 && wid=`xdotool search --onlyvisible --name Pilot` && xdotool windowactivate $wid') #&& xdotool keydown alt key Tab; sleep 1; xdotool keyup alt')  #&& wid2=`xdotool search --onlyvisible --name Pilot` && xdotool windowraise $wid2')
						
				if self.radios[self.position][0] == 'previous':
					os.system("wid=`wmctrl -l | awk '/Minitube/ {print $1}'` && xdotool windowfocus $wid && xdotool key --window $wid ctrl+Left")					
			
				elif self.radios[self.position][0] == 'next':
					os.system("wid=`wmctrl -l | awk '/Minitube/ {print $1}'` && xdotool windowfocus $wid && xdotool key --window $wid ctrl+Right")					
					
                                ### if download were available
				# elif self.radios[self.position][0] == 'download':
				# 	os.system("wid=`wmctrl -l | awk '/Minitube/ {print $1}'` && xdotool windowfocus $wid && xdotool key --window $wid ctrl+s")
					
				# elif self.radios[self.position][0] == 'tab switch':
				# 	os.system("wid=`wmctrl -l | awk '/Minitube/ {print $1}'` && xdotool windowfocus $wid && xdotool key --window $wid ctrl+j")
				
				# elif self.radios[self.position][0] == 'undo':
					# self.stoper.Stop()
					# self.menu = radios(self, id=-1 )
					
					#self.message = self.radioID
					#Publisher().sendMessage( ( 'radioID' ), self.message ) #call the Publisher object’s sendMessage method and pass it the topic string and the message in order to send the message
					
					#self.message = 'ON'
					#Publisher().sendMessage( ( 'radioFlag' ), self.message ) #call the Publisher object’s sendMessage method and pass it the topic string and the message in order to send the message

					# self.Hide()
					# self.menu.Show()

                                selectedButton.SetBackgroundColour( self.backgroundColour )
				self.flag = 'row'
                                self.panelIteration = 0
				self.rowIteration = 0
				self.colIteration = 0
				self.count = 0
                                #self.stoper.Start( self.timeGap )
                        
                        self.numberOfPresses += 1

	#-------------------------------------------------------------------------
	def timerUpdate(self , event):
            
                # print("####################")
                # print "flag = ", self.flag
                # print "rowIter = ", self.rowIteration
                # print "colIter = ", self.colIteration
                # print("####################")
                
               	self.mouseCursor.move( self.dw - 225, self.dh - 265 )	
            
                self.numberOfPresses = 0

                if self.numberOfEmptyIteration < 3:

                        if self.switchSound.lower( ) == 'on':
                                self.switchingSound.play( )

			if self.flag == 'row': #flag == row ie. switching between rows

					self.numberOfEmptyIteration += 1./self.numberOfRows[0]        

					if self.rowIteration == self.numberOfRows[0]:
						self.rowIteration = 0

					items = self.subSizer.GetChildren()
					for item in items:
						b = item.GetWindow()
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus()

					if self.rowIteration == 0 or self.rowIteration == 1:
						zakres = range(self.rowIteration*self.numberOfColumns[0], self.rowIteration*self.numberOfColumns[0] + self.numberOfColumns[0])

					elif self.rowIteration == 2:
						zakres = self.rowIteration*self.numberOfColumns[0], 
						
					elif self.rowIteration == 3:
						zakres = self.rowIteration*self.numberOfColumns[0] - 1, 

                                        ### if download version were available
					# elif self.rowIteration == 4:
					# 	zakres = range(self.rowIteration*self.numberOfColumns[0] - 2, self.rowIteration*self.numberOfColumns[0] + self.numberOfColumns[0] - 2)
					elif self.rowIteration == 4:
						zakres = self.rowIteration*self.numberOfColumns[0] - 2, 

					for i in zakres:
						item = self.subSizer.GetItem( i )
						b = item.GetWindow()
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus()
					self.rowIteration += 1

			elif self.flag == 'columns': #flag = columns ie. switching between cells in the particular row

				if self.countColumns == self.countMaxColumns:
					self.flag = 'row'
					self.rowIteration = 0
					self.colIteration = 0
					self.countColumns = 0
					self.countRows = 0

					items = self.subSizer.GetChildren()
					for item in items:
						b = item.GetWindow()
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus()

				else:
					if self.colIteration == self.numberOfColumns[0]:
						self.colIteration = 0

					if self.colIteration == self.numberOfColumns[0]-1:
						self.countColumns += 1

					items = self.subSizer.GetChildren()
					for item in items:
						b = item.GetWindow()
						b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus()

					if self.rowIteration == 0:
						item = self.subSizer.GetItem( self.rowIteration*self.numberOfColumns[ 0 ] + self.colIteration )
					
					elif self.rowIteration == 1:
						item = self.subSizer.GetItem( self.rowIteration*self.numberOfColumns[ 0 ] + self.colIteration )

                                        # if download option was available
					# elif self.rowIteration == 4:
					# 	item = self.subSizer.GetItem( self.rowIteration*self.numberOfColumns[ 0 ] + self.colIteration - 2 )				
					b = item.GetWindow()
					b.SetBackgroundColour( self.scanningColour )
					b.SetFocus()

					self.colIteration += 1

		else:
                    self.stoper.Stop( )
                    suspend.suspend( self, id = 2 ).Show( True )
                    self.Hide( )
                    self.numberOfEmptyIteration = 0

                    #self.message = self.radioID
                    #Publisher().sendMessage( ( 'radioID' ), self.message ) #call the Publisher object’s sendMessage method and pass it the topic string and the message in order to send the message
                    # self.menu.Show()

                    # self.flag = 'rest'

#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = pilot( parent = None, id = -1 )
        frame.Show( True )
	app.MainLoop( )
