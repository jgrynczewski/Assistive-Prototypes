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

import wx, glob, os, sys, time, psutil, alsaaudio, urllib2, zmq
import wx.lib.buttons as bt
import subprocess as sp
from subprocess import Popen, PIPE, STDOUT

from pymouse import PyMouse
from pygame import mixer

from modules import radio, music, audiobook, nowe
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
                self.panel = wx.Panel(self) 
                self.Bind(wx.EVT_LEFT_DOWN, self.onKey)

                style = self.GetWindowStyle( )
                self.SetWindowStyle( style | wx.STAY_ON_TOP )

                self.Maximize( True )
                self.Centre( True )
                self.MakeModal( True )                
                self.ShowFullScreen(True)

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
                self.configurationPath = self.home+"Assistive-Prototypes/"
                
                files = [ '.pathToAP', './modules/.pathToAP', './modules/pilots/.pathToAP', './modules/others/.pathToAP', 'modules/ewriting/.pathToAP', 'modules/games/atmemory/.pathToAP', 'modules/games/atsweeper/.pathToAP' ]

                for item in files:
                        with open(item, 'w') as textFile:
                                textFile.write( self.path ) 

                                sys.path.append( self.path )

                from reader import reader
                
		self.reader = reader()
		self.reader.readParameters()
		parameters = self.reader.getParameters()
                
                self.unpackParameters(parameters)
                
                self.labels = 'PISAK EXERCISES RADIO MUSIC AUDIOBOOK NOWE AKTUALIZACJE PUSTE PUSTE'.split( )
                
                self.flag = 'row'
                self.pressFlag = False
                
                self.numberOfRows = [ 3 ]
                self.numberOfColumns = [ 3 ]
                self.maxRows = [ 3 * item for item in self.numberOfRows ]
                self.maxColumns = [ 2 * item for item in self.numberOfColumns ]
                
                self.rowIteration = 0
                self.colIteration = 0
                self.countRows = 0
                self.countColumns = 0
                
                if self.volumeLevel == 0:
                    self.volumeLevel = 100

                    os.system("pactl set-sink-volume alsa_output.pci-0000_00_1b.0.analog-stereo %d%%" % self.volumeLevel)
                    self.reader.saveVolume(self.volumeLevel)
                    
                else:
                    self.volumeLevels = [0, 20, 40, 60, 80, 100, 120, 140, 160]
                    
                    if self.volumeLevel not in self.volumeLevels:
                        raise("Wrong value of volumeLevel. Accepted values: 0, 20, 40, 60, 80, 100, 120, 140, 160")
                    os.system("pactl set-sink-volume alsa_output.pci-0000_00_1b.0.analog-stereo %d%%" % self.volumeLevel)

                self.numberOfPresses = 1
                self.mouseCursor = PyMouse( )
                
                if self.control != 'tracker':
                        self.mouseCursor = PyMouse( )
                        self.mousePosition = self.winWidth - 4 - self.xBorder, self.winHeight - 4 - self.yBorder
                        self.mouseCursor.move( *self.mousePosition )
                                                        
                # if self.switchSound.lower( ) != 'off' or self.pressSound.lower( ) != 'off':
                mixer.init( )
                self.usypiamSound = mixer.Sound(self.path + '/sounds/usypiam.ogg')
                self.clickSound = mixer.Sound("click.wav")
                
                # if self.switchSound.lower( ) == 'on':
                self.switchingSound = mixer.Sound( self.path + '/sounds/switchSound.ogg' )
                #if self.pressSound.lower( ) == 'on':
                self.pressingSound = mixer.Sound( self.path + '/sounds/pressSound.ogg' )
                
                if self.switchSound.lower( ) == 'voice' or self.pressSound.lower( ) == 'voice':
                    self.oneSound = mixer.Sound(self.path + '/sounds/rows/1.ogg')
                    self.twoSound = mixer.Sound(self.path + '/sounds/rows/2.ogg')
                    self.threeSound = mixer.Sound(self.path + '/sounds/rows/3.ogg')
                    
                    self.noweSound = mixer.Sound(self.path + '/sounds/nowe.ogg')
                    self.zadanieSound = mixer.Sound( self.path + '/sounds/zadanie.ogg' )
                    self.muzykaSound = mixer.Sound( self.path + '/sounds/muzyka.ogg' )
                    self.filmSound = mixer.Sound( self.path + '/sounds/film.ogg' )
                    self.radioSound = mixer.Sound( self.path + '/sounds/radio.ogg' )
                    self.aktualizujSound = mixer.Sound( self.path + '/sounds/aktualizuj.ogg' )
                    self.pisakSound = mixer.Sound( self.path + '/sounds/pisak.ogg' )
                    self.pusteSound = mixer.Sound( self.path + '/sounds/puste.ogg' )
                    self.audiobookSound = mixer.Sound( self.path + '/sounds/książki_czytane.ogg')

                self.SetBackgroundColour( 'black' )

	        #-------------------------------------------------------------------------	
        def unpackParameters(self, parameters):
		for item in parameters:
			try:
				setattr(self, item[:item.find('=')], int(item[item.find('=')+1:]))
			except ValueError:
				setattr(self, item[:item.find('=')], item[item.find('=')+1:])			

        #-------------------------------------------------------------------------        
        def initializeBitmaps(self):
            
            labelFiles = [ self.path + item for item in [ 'icons/modules/pisak.png', 'icons/modules/exercises.png', 'icons/modules/radio.png', 'icons/modules/music.png', 'icons/modules/audiobook.png', 'icons/modules/nowe.png', 'icons/modules/aktualizacja.png', 'icons/modules/puste.png', 'icons/modules/puste.png'] ]

            self.labelbitmaps = { }
            for index in xrange( len(self.labels) ):
                    self.labelbitmaps[ self.labels[index] ] = wx.BitmapFromImage( wx.ImageFromStream( open(labelFiles[index], "rb") ) )

        #-------------------------------------------------------------------------
        def createGui(self):

                cmd = "cd " + self.home + "Assistive-Prototypes && git pull --dry-run | grep -q -v 'Already up-to-date.' && changed=1"
                p = Popen( cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True )
                self.output = p.stdout.read( )

                # b = bt.GenBitmapButton( self , -1, bitmap = self.labelbitmaps[ self.labels[0] ], name = self.labels[0] )#przycisk stworzony tylko po to, żeby 4 linijki niżej wyciagnąć domyslny kolor przycisku 
                if self.output[:5]!="fatal" and len(self.output)!=0:
                        self.color = "green"
                else:
                        self.color = wx.NullColour
                        
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
                        b.mode = 'pointing'
                        b.Bind( event, self.onKey )
                        # b.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
                        b.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)
                        b.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)

			self.sizer.Add( b, 0, wx.EXPAND )

                self.colour = b.GetBackgroundColour()
		self.vbox.Add( self.sizer, proportion=2, flag=wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=self.xBorder )
		self.SetSizer( self.vbox )

        #-------------------------------------------------------------------------
	def initializeTimer(self):
		self.stoper = wx.Timer( self )
		self.Bind( wx.EVT_TIMER , self.timerUpdate , self.stoper )

		# if self.control != 'tracker':
		self.stoper.Start( 50 )
                        
	#-------------------------------------------------------------------------
	def createBindings(self):
		self.Bind( wx.EVT_CLOSE , self.OnCloseWindow )

	#-------------------------------------------------------------------------
        def onKey(self, event):
            """
            Check for left mouse click. If so, press active button of the parent frame.
            """

            # key_code = event.GetKeyCode()
            # if key_code == wx.EVT_LEFT_DOWN:
            items = self.sizer.GetChildren( )

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
                            b2.Refresh()
                    time.sleep(2)

                    if self.pressFlag == False:
                            self.button = event.GetEventObject( )
                            # self.button.SetBackgroundColour( self.selectionColour )
                            self.pressFlag = True
                            # self.Update()
                            
                            self.label = b_active.GetName( ).encode( 'utf-8' )
                            # self.stoper.Start( 0.15 * self.timeGap )

                    if self.label == 'PISAK':
                            if self.pressSound.lower() == 'voice':
                                self.pisakSound.play()
                            # self.stoper.Stop( )
                            # time.sleep( 1 )
                            self.Hide( )
                            self.Update( )
                            
                            # self.mousePosition = self.winWidth - self.xBorder/2., self.winHeight - self.yBorder/2.
                            # self.mouseCursor.move( *self.mousePosition )        
                            
                            os.system("pisak")
                                            
                            self.mousePosition = self.winWidth - 100 - self.xBorder, self.winHeight - 100 - self.yBorder
                            self.mouseCursor.move( *self.mousePosition )        

                            self.Show()
                            self.SetFocus()
                            
                            self.stoper.Start( 50 )
 
                    elif self.label == 'EXERCISES':
                            if self.pressSound.lower() == 'voice':
                                self.zadanieSound.play()
                            exercise.exercise( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'AKTUALIZACJE':
                            if self.pressSound.lower() == 'voice':
                                self.aktualizujSound.play()

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

                            if self.pressSound.lower() == 'voice':
                                self.muzykaSound.play()

                            music.music( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'AUDIOBOOK':
                            if self.pressSound.lower() == 'voice':
                                self.audiobookSound.play()
                            audiobook.audiobook( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'MOVIES':
                            if self.pressSound.lower() == 'voice':
                                self.filmSound.play()
                            movie.movie( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'RADIO':
                            if self.pressSound.lower() == 'voice':
                                self.radioSound.play()

                            if self.internet_on():
                                    radio.radio( parent = self, id = -1 ).Show( True )
                                    self.Hide( )
                            else:
                                    os.system("milena_say Brak połączenia z internetem. Proszę podłączyć komputer do sieci.")
                            

                    elif (self.label == 'NOWE'):
                        if self.pressSound.lower() == 'voice':
                            self.noweSound.play()

                        nowe.nowe( parent = self, id = -1).Show( True )
                        self.Hide( )

                    elif (self.label == 'PUSTE'):
                        if self.pressSound.lower() == 'voice':
                            self.pusteSound.play()

                        # pass

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
        def onPress( self, event ):
                
                if self.pressSound.lower( ) != 'off':
                        self.pressingSound.play( )
                # if self.pressSound.lower( ) == 'voice':
                #         os.system("milena_say Wybrałeś")
                # self.pressingSound.play( )
                
                if self.control == 'tracker':
                    if self.pressFlag == False:
                            self.button = event.GetEventObject( )
                            self.button.SetBackgroundColour( self.selectionColour )
                            self.pressFlag = True
                            self.Update()
                            self.label = event.GetEventObject( ).GetName( ).encode( 'utf-8' )
                            self.stoper.Start( 0.15 * self.timeGap )

                    if self.label == 'PISAK':
                            if self.pressSound.lower() == 'voice':
                                self.pisakSound.play()
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
                            if self.pressSound.lower() == 'voice':
                                self.zadanieSound.play()
                            exercise.exercise( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'AKTUALIZACJE':
                            if self.pressSound.lower() == 'voice':
                                self.aktualizujSound.play()

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

                            if self.pressSound.lower() == 'voice':
                                self.muzykaSound.play()

                            music.music( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'AUDIOBOOK':
                            if self.pressSound.lower() == 'voice':
                                self.audiobookSound.play()
                            audiobook.audiobook( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'MOVIES':
                            if self.pressSound.lower() == 'voice':
                                self.filmSound.play()
                            movie.movie( self, id = -1 ).Show( True )
                            self.Hide( )

                    elif self.label == 'RADIO':
                            if self.pressSound.lower() == 'voice':
                                self.radioSound.play()

                            if self.internet_on():
                                    radio.radio( parent = self, id = -1 ).Show( True )
                                    self.Hide( )
                            else:
                                    os.system("milena_say Brak połączenia z internetem. Proszę podłączyć komputer do sieci.")
                            

                    elif (self.label == 'NOWE'):
                        if self.pressSound.lower() == 'voice':
                            self.noweSound.play()

                        nowe.nowe( parent = self, id = -1).Show( True )
                        self.Hide( )

                    elif (self.label == 'PUSTE'):
                        if self.pressSound.lower() == 'voice':
                            self.pusteSound.play()
                    
        #-------------------------------------------------------------------------
        def timerUpdate(self , event):

                if self.control == 'tracker':
                            items = self.sizer.GetChildren( )
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
