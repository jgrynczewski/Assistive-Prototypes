#! /bin/bash

#    This file is part of AP - Assistive Prototypes.
#
#    AP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    AP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with AP.  If not, see <http://www.gnu.org/licenses/>.

echo -e "\nThe Milena PPA repository will be add to your system and the following packages will be installed:\npython2.7 python-wxgtk2.8 python-alsaaudio python-pygame python-psutil python-xlib python-pip pyuserinput calibre smplayer milena xdotool wmctrl\n"

read -p "Do you want to continue? [Y/n]"

if [ "$REPLY" == Y ] || [ "$REPLY" == y ]; then


   sudo apt-get install python2.7 python-wxgtk2.8 python-alsaaudio python-pygame python-psutil python-xlib python-pip calibre smplayer milena xdotool wmctrl

   sudo pip install pyuserinput

    echo "Done."

    else

    echo -e "Abort on request."
fi
