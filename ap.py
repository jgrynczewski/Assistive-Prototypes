#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# AP - Assistive Prototypes is a set of interactive prototypes for people with severe expressive, communication disorders.

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

import wx, glob, os, sys, time, alsaaudio, psutil, urllib2, zmq
import wx.lib.buttons as bt
import subprocess as sp
from subprocess import Popen, PIPE, STDOUT

from pymouse import PyMouse
from pygame import mixer

from modules import radio, music, audiobook
from modules import exercise

if (psutil.__version__ < 2):
    print("\nFor properly close PISAK you need newer version of psutil. \nType: sudo pip2 install 'psutil==2.2.1' --upgrade\n")
#=============================================================================
class main_menu( wx.Frame ):
	def __init__(self, parent, id):

                # context = zmq.Context()
                # self.socket = context.socket(zmq.REQ)
                # self.socket.connect("tcp://localhost:5556")
                
		self.winWidth, self.winHeight = wx.DisplaySize( )

		wx.Frame.__init__( self , parent , id, 'AP MainMenu' )
		style = self.GetWindowStyle( )
		self.SetWindowStyle( style | wx.STAY_ON_TOP )

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

		cmd = 'pwd'
		p = sp.Popen( cmd, shell = True, stdin = sp.PIPE, stdout = sp.PIPE, stderr = sp.STDOUT, close_fds = True )
		self.path = p.stdout.read( )[ :-1 ] + '/'
                self.home = self.path[:self.path[:-1].rfind("/")] + '/' 
                self.configurationPath = self.home+".pisak/"
                
		files = [ '.pathToAP', './modules/.pathToAP', './modules/pilots/.pathToAP', './modules/others/.pathToAP', 'modules/ewriting/.pathToAP', 'modules/games/atmemory/.pathToAP', 'modules/games/atsweeper/.pathToAP' ]

		for item in files:
			with open(item, 'w') as textFile:
				textFile.write( self.path ) 

				sys.path.append( self.path )

		from reader import reader
		
		reader = reader()
		reader.readParameters()
		parameters = reader.getParameters()

		for item in parameters:
			try:
				setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
			except ValueError:
				setattr(self, item[:item.find('=')], item[item.find('=')+1:])

		self.labels = 'PISAK EXERCISES RADIO MUSIC AUDIOBOOK AKTUALIZACJE'.split( )

		self.flag = 'row'
		self.pressFlag = False

		self.numberOfRows = [ 2 ]
		self.numberOfColumns = [ 3 ]
		self.maxRows = [ 3 * item for item in self.numberOfRows ]
		self.maxColumns = [ 2 * item for item in self.numberOfColumns ]

		self.rowIteration = 0
		self.colIteration = 0
		self.countRows = 0
		self.countColumns = 0

		self.numberOfPresses = 1
		self.mouseCursor = PyMouse( )
		
		if self.control != 'tracker':
			self.mouseCursor = PyMouse( )
			self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
			self.mouseCursor.move( *self.mousePosition )
							
		if self.switchSound.lower( ) == 'on' or self.pressSound.lower( ) == 'on':
			mixer.init( )
			if self.switchSound.lower( ) == 'on':
				self.switchingSound = mixer.Sound( self.path + '/sounds/switchSound.ogg' )
			if self.pressSound.lower( ) == 'on':
				self.pressingSound = mixer.Sound( self.path + '/sounds/pressSound.ogg' )

                self.zadanieSound = mixer.Sound( self.path + '/sounds/zadanie.ogg' )
                self.blogSound = mixer.Sound( self.path + '/sounds/blog.ogg' )
                self.muzykaSound = mixer.Sound( self.path + '/sounds/muzyka.ogg' )
                self.filmSound = mixer.Sound( self.path + '/sounds/film.ogg' )
                self.radioSound = mixer.Sound( self.path + '/sounds/radio.ogg' )
                self.pisakSound = mixer.Sound( self.path + '/sounds/pisak.ogg' )

		self.SetBackgroundColour( 'black' )

		#alsaaudio.Mixex( control = 'Master', cardindex = card_index ).setvolume( self.musicVolumeLevel, 0 )

	#-------------------------------------------------------------------------	
        def initializeBitmaps(self):
            
	    labelFiles = [ self.path + item for item in [ 'icons/modules/pisak.png', 'icons/modules/exercises.png', 'icons/modules/radio.png', 'icons/modules/music.png', 'icons/modules/audiobook.png', 'icons/modules/aktualizacja.png', ] ]

            self.labelbitmaps = { }
	    for index in xrange( len(self.labels) ):
		    self.labelbitmaps[ self.labels[index] ] = wx.BitmapFromImage( wx.ImageFromStream( open(labelFiles[index], "rb") ) )

	#-------------------------------------------------------------------------
	def createGui(self):

                cmd = "cd " + self.home + ".pisak && git pull --dry-run | grep -q -v 'Already up-to-date.' && changed=1"
                p = Popen( cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
                self.output = p.stdout.read( )

                if self.output[:5]!="fatal" and len(self.output)!=0:
                        self.color = "green"
                else:
                        self.color = self.backgroundColour
                        
                self.vbox = wx.BoxSizer( wx.VERTICAL )
                self.sizer = wx.GridSizer( self.numberOfRows[ 0 ], self.numberOfColumns[ 0 ], self.xBorder, self.yBorder )

		if self.control != 'tracker':
			event = eval('wx.EVT_LEFT_DOWN')
		else:
			event = eval('wx.EVT_BUTTON')
			
		for i in self.labels:
			b = bt.GenBitmapButton( self , -1, bitmap = self.labelbitmaps[ i ], name = i )
                        if i=="AKTUALIZACJE":
           		        b.SetBackgroundColour( self.color )
			b.Bind( event, self.onPress )
                        b.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
                        
			self.sizer.Add( b, 0, wx.EXPAND )
		self.vbox.Add( self.sizer, proportion=2, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=self.xBorder )
		self.SetSizer( self.vbox )

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
	def OnCloseWindow(self , event):
		
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
					wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION | wx.STAY_ON_TOP )

		ret = dial.ShowModal( )
		
		if ret == wx.ID_YES:
			try:
				if "smplayer" in [psutil.Process( i ).name() for i in psutil.pids( )]:
					os.system( 'smplayer -send-action quit' )
			except TypeError:
				if "smplayer" in [psutil.Process( i ).name for i in psutil.pids( )]:
					os.system( 'smplayer -send-action quit' )
					
			self.Destroy( )
		else:
			event.Veto( )

			if self.control != 'tracker':
					self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
					self.mouseCursor.move( *self.mousePosition )	

	#-------------------------------------------------------------------------
	def onKeyPress( self, event ):
                keycode = event.GetKeyCode()

                # print keycode

                if keycode == wx.WXK_SPACE:

                        # self.socket.send("Error")
                        os.system("milena_say Zbieranie sygnału")
 
                event.Skip()

	#-------------------------------------------------------------------------
	def onPress( self, event ):
		
		if self.pressSound.lower( ) == 'on':
			self.pressingSound.play( )
                
		if self.control == 'tracker':
                    if self.pressFlag == False:
			    self.button = event.GetEventObject( )
			    self.button.SetBackgroundColour( self.selectionColour )
			    self.pressFlag = True
                            self.Update()
			    self.label = event.GetEventObject( ).GetName( ).encode( 'utf-8' )
			    self.stoper.Start( 0.15 * self.timeGap )
			    
		    if self.label == 'PISAK':
                            self.stoper.Stop( )
                            time.sleep( 1 )
                            self.Hide( )
                            self.Update( )
                            
                            self.mousePosition = self.winWidth - self.xBorder/2., self.winHeight - self.yBorder/2.
                            self.mouseCursor.move( *self.mousePosition )	
                            
                            os.system("pisak")
                                            
                            self.mousePosition = self.winWidth - 100 - self.xBorder, self.winHeight - 100 - self.yBorder
                            self.mouseCursor.move( *self.mousePosition )	

                            self.Show()
                            self.SetFocus()
                            
 			    self.stoper.Start( 0.15 * self.timeGap )
 
		    elif self.label == 'EXERCISES':
			    exercise.exercise( self, id = -1 ).Show( True )
			    self.Hide( )

		    elif self.label == 'AKTUALIZACJE':

                            # cmd = "cd " + self.home + ".pisak && git pull --dry-run | grep -q -v 'Already up-to-date.' && changed=1"
                            # p = Popen( cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
                            # output = p.stdout.read( )
                            
                            # if output[:5] == "fatal":
                            #         os.system("milena_say Brak połączenia z repozytorium zewnętrznym")
                            # elif len(output) == 0:
                            #         os.system("milena_say Brak aktualizacji")
                            # else:
                            #         os.system("cd " + self.home + ".pisak && git pull")
                            #         os.system("milena_say Zaktualizowano pisaka")

                            #         with open( self.home + ".pisak/message", 'r' ) as f:
                            #                 for line in f:
                            #                         if line.strip():
                            #                                 os.system( "milena_say %s " % line )

                               # # blog.blog( parent = self, id = -1 ).Show( True )
                               # # self.Hide( )
                            
                            os.system("milena_say Do poprawienia")
                            pass

		    elif self.label == 'MUSIC':
			    music.music( self, id = -1 ).Show( True )
			    self.Hide( )

		    elif self.label == 'AUDIOBOOK':
			    audiobook.audiobook( self, id = -1 ).Show( True )
			    self.Hide( )

		    elif self.label == 'MOVIES':
			    movie.movie( self, id = -1 ).Show( True )
			    self.Hide( )

		    elif self.label == 'RADIO':
                            if self.internet_on():
                                    radio.radio( parent = self, id = -1 ).Show( True )
                                    self.Hide( )
                            else:
                                    os.system("milena_say Brak połączenia z internetem. Proszę podłączyć komputer do sieci.")
			    
		else:	
			self.numberOfPresses += 1
			self.countRows = 0

			if self.numberOfPresses == 1:

			    if self.flag == 'rest':
				    self.flag = 'row'
				    self.rowIteration = 0
				    self.colIteration = 0 
				    self.countRows = 0

			    elif self.flag == 'row':

				    buttonsToHighlight = range( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ], ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] )
				    for button in buttonsToHighlight:
					    item = self.sizer.GetItem( button )
					    b = item.GetWindow( )
					    b.SetBackgroundColour( self.selectionColour )
					    b.SetFocus( )

                                    self.Update()

                                    self.stoper.Stop( )
                                    time.sleep( self.selectionTime/1000. )
                                    self.stoper.Start( self.timeGap )

                                    self.flag = 'columns'
				    self.colIteration = 0

			    elif self.flag == 'columns':

				    self.position = ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.colIteration - 1

				    item = self.sizer.GetItem( self.position )
				    selectedButton = item.GetWindow( )
				    selectedButton.SetBackgroundColour( self.selectionColour )
				    selectedButton.SetFocus( )
				    self.Update( )
                                    
				    label = self.labels[ self.position ]			    
				    
                                    if label == 'PISAK':
                                            self.stoper.Stop( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.pisakSound.play( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.stoper.Start( self.timeGap )
                                            
                                            self.stoper.Stop()
                                            self.Hide()
                                            self.Update()

                                            self.mousePosition = self.winWidth - self.xBorder/2., self.winHeight - self.yBorder/2.
                                            self.mouseCursor.move( *self.mousePosition )	

                                            os.system("pisak")
                        
                                            self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 30 - self.yBorder
                                            self.mouseCursor.move( *self.mousePosition )	

                                            self.Show()
                                            self.SetFocus()
                                            self.stoper.Start( self.timeGap )
                                            
				    elif label == 'EXERCISES':
                                            self.stoper.Stop( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.zadanieSound.play( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.stoper.Start( self.timeGap )

					    self.stoper.Stop( )
					    exercise.exercise( self, id = -1 ).Show( True )
					    self.Hide( )

				    elif label == 'AKTUALIZACJE':

                                            if self.output[:5] == "fatal":
                                                    os.system("milena_say Brak połączenia z repozytorium zewnętrznym. Prawdopodbnie nie jesteś połączony z internetem.")
                                            elif len(self.output) == 0:
                                                    os.system("milena_say Brak aktualizacji")
                                            else:
                                                    os.system("cd " + self.home + ".pisak && git pull")
                                                    os.system("milena_say Zaktualizowano pisaka")
                                                    
                                                    with open(self.path + "read", 'a+') as f:
                                                            readMessages = f.read()
                                                            readMessages = readMessages.replace("\n", " ")

                                                    messages = []
                                                    for item in os.listdir( self.configurationPath+"messages/"):
                                                        if ("message" in item) and (item not in readMessages):
                                                                with open(self.configurationPath+"messages/"+item, 'r') as f:
                                                                        messages.append( f.read().replace("\n", " ") )
                                                                with open(self.path + "read", 'a+') as f:
                                                                        f.write(item+'\n')

                                                    lenght = len(messages)
                                                    
                                                    if lenght == 1:
                                                            os.system("milena_say Masz jedną aktualizację.")
                                                            os. system("milena_say %s" % messages[0])
                                                    else:
                                                            if lenght == 2:
                                                                    os.system("milena_say Masz dwie aktualizację")
                                                            elif (lenght%10 in [2,3,4]):
                                                                    os.system("milena_say Masz %i aktualizację" % lenght)
                                                            else:
                                                                    os.system("milena_say Masz %i aktualizacji" % lenght)
                                                                    
                                                            for (i, j) in enumerate(messages, start=1):
                                                                    os.system("milena_say Aktualizacja numer %i." % i)
                                                                    os.system("milena_say %s" % j)
                                                                    
                                                    cmd = "cd " + self.home + ".pisak && git pull --dry-run | grep -q -v 'Already up-to-date.' && changed=1"
                                                    p = Popen( cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
                                                    self.output = p.stdout.read( )

           		                            self.color = self.backgroundColour
                                                    self.Update( )
                                                    
                                            # self.stoper.Stop( )
                                            # time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            # self.blogSound.play( )
                                            # time.sleep( ( self.selectionTime + self.timeGap )/(1000*2) )
                                            # self.stoper.Start( self.timeGap )
                                            
					    # self.stoper.Stop( )
					    # blog.blog( parent = self, id = -1 ).Show( True )
					    # self.Hide( )

				    elif label == 'MUSIC':
                                            self.stoper.Stop( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.muzykaSound.play( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.stoper.Start( self.timeGap )

					    self.stoper.Stop( )
					    music.music( self, id = -1 ).Show( True )
					    self.Hide( )

				    elif label == 'AUDIOBOOK':
                                            self.stoper.Stop( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.stoper.Start( self.timeGap )

					    self.stoper.Stop( )
					    audiobook.audiobook( self, id = -1 ).Show( True )
					    self.Hide( )

				    elif label == 'MOVIES':
                                            self.stoper.Stop( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.filmSound.play( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.stoper.Start( self.timeGap )

					    self.stoper.Stop( )
					    movie.movie( self, id = -1 ).Show( True )
					    self.Hide( )

				    elif label == 'RADIO':
                                            self.stoper.Stop( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.radioSound.play( )
                                            time.sleep( ( self.selectionTime + self.timeGap )/(1000.*2) )
                                            self.stoper.Start( self.timeGap )

                                            if self.internet_on():
                                                    self.stoper.Stop( )
                                                    radio.radio( parent = self, id = -1 ).Show( True )
                                                    self.Hide( )
                                            else:
                                                    os.system("milena_say Brak połączenia z internetem. Proszę podłączyć komputer do sieci.")

				    self.flag = 'row'
				    self.rowIteration = 0
				    self.colIteration = 0
				    self.countColumns = 0
				    self.countRows = 0

			else:
				pass

	#-------------------------------------------------------------------------
	def timerUpdate(self , event):

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

			if self.flag == 'rest':
				pass

			elif self.countRows < self.maxRows[ 0 ]:

				if self.flag == 'row':

					self.rowIteration = self.rowIteration % self.numberOfRows[ 0 ]

					items = self.sizer.GetChildren( )
					for item in items:
						b = item.GetWindow( )
                                                if b.Name == "AKTUALIZACJE":
						        b.SetBackgroundColour( self.color )
                                                else:
						        b.SetBackgroundColour( self.backgroundColour )
						b.SetFocus( )

					buttonsToHighlight = range( self.rowIteration * self.numberOfColumns[ 0 ], self.rowIteration * self.numberOfColumns[ 0 ] + self.numberOfColumns[ 0 ] )
					for button in buttonsToHighlight:
						item = self.sizer.GetItem( button )
						b = item.GetWindow( )
                                                b.SetBackgroundColour( self.scanningColour )
                                                        
						b.SetFocus( )

					self.rowIteration += 1
					self.countRows += 1

				elif self.flag == 'columns':
					if self.countColumns == self.maxColumns[ 0 ]:
						self.flag = 'row'
						self.rowIteration = 0
						self.colIteration = 0
						self.countColumns = 0
						self.countRows = 0
					else:

						self.colIteration = self.colIteration % self.numberOfColumns[ 0 ]

						items = self.sizer.GetChildren( )
						for item in items:
							b = item.GetWindow( )
                                                        if b.Name == "AKTUALIZACJE":
						                b.SetBackgroundColour( self.color )
                                                        else:
						                b.SetBackgroundColour( self.backgroundColour )

							b.SetFocus( )

						item = self.sizer.GetItem( ( self.rowIteration - 1 ) * self.numberOfColumns[ 0 ] + self.colIteration )
						b = item.GetWindow( )
						b.SetBackgroundColour( self.scanningColour )
						b.SetFocus( )

                                                self.Update( )

						self.colIteration += 1
						self.countColumns += 1
				
				if self.switchSound.lower( ) == 'on':
					self.switchingSound.play( )

			elif self.countRows == self.maxRows[ 0 ]:
				self.flag = 'rest'
				self.countRows += 1

				items = self.sizer.GetChildren( )

				for item in items:
					b = item.GetWindow( )
                                        if b.Name == "AKTUALIZACJE":
						b.SetBackgroundColour( self.color )
                                        else:
						b.SetBackgroundColour( self.backgroundColour )
                                        
					b.SetFocus( )

			else:
				pass

			# print self.rowIteration, self.colIteration

	#-------------------------------------------------------------------------
        def internet_on( self ):
                try:
                        response = urllib2.urlopen('http://216.58.209.67',timeout=1)
                        return True
                except urllib2.URLError as err:
                        return False

#=============================================================================
if __name__ == '__main__':

	app = wx.App(False)
	frame = main_menu( parent = None, id = -1 )
	frame.Show( True )
	app.MainLoop( )
