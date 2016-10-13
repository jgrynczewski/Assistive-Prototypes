#-*- coding: utf-8 -*-
import os 

path = '/home/radoslaw/AP/multimedia/ewriting/pictures'
path2 = '/home/radoslaw/AP/multimedia/ewriting/voices'
files = os.listdir( path )
files.sort( key=lambda f: os.path.getmtime( os.path.join(path, f) ) )

files2 = os.listdir( path2 )
files2.sort( key=lambda f: os.path.getmtime( os.path.join(path2, f) ) )

""" Nazwy obrazków, których nie ma w plikach dźwiękowych   """
idx = 1
for i in files:
    if i[:i.rfind('.')]+'.ogg' in files2:
        pass
    else:
        if idx == 1:
            print "Obrazki, których nie ma w plikach dźwiękowych: "
        print idx, ". ", i
        idx += 1

""" Nazwy dźwięków, których nie ma w plikach graficznych """        
jdx = 1
for i in files2:
    if i[:i.rfind('.')]+'.jpeg' in files or i[:i.rfind('.')]+'.jpg' in files or i[:i.rfind('.')]+'.JPG' in files or i[:i.rfind('.')]+'.JPEG' in files or i[:i.rfind('.')]+'.png' in files or i[:i.rfind('.')]+'.PNG' in files :
        pass
    else:
        if jdx == 1:
            print "Dźwięki, których nie ma w obrazkach: "
        print jdx, ". ", i
        jdx += 1

""" Jeżeli w plikach graficznych powtarzają się nazwy (ale mają różne rozszerzenia) """
for i in files:
    for j in files:
        if (i[:i.rfind('.')].upper() == j[:j.rfind('.')].upper()) and (i[i.rfind('.'):] != j[j.rfind('.'):]):
            print i
        else:
            pass

""" Jeżeli w plikach graficznych powtarzają się nazwy (drukowane i pisane) """
for i in files:
    for j in files:
        if (i[:i.rfind('.')] != j[:j.rfind('.')]) and (i[:i.rfind('.')].upper() == j[:j.rfind('.')].upper()):
            print i, j
        else:
            pass

""" Jeżeli w plikach dźwiękowych powtarzają się nazwy (drukowane i pisane) """
for i in files2:
    for j in files2:
        if (i[:i.rfind('.')] != j[:j.rfind('.')]) and (i[:i.rfind('.')].upper() == j[:j.rfind('.')].upper())                                    :
            print i, j
        else:
            pass

""" Jeżeli w plikach graficznych powtarzają się nazwy (drukowane, pisane i różne rozszerzenia) """
for i in files:
    for j in files:
        if (i[:i.rfind('.')] != j[:j.rfind('.')]) and  (i[:i.rfind('.')].upper() == j[:j.rfind('.')].upper()) and (i[:i.rfind('.')].upper() != j[:j.rfind('.')].upper()):
            print i, j
        else:
            pass

""" Szukanie nieprzewidzianych formatów w plikach graficznych """
for j in files:
    if j[j.rfind('.'):] not in  ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG']:
        print j

""" Szukanie nieprzewidzianych formatów w plikach dźwiękowych """
for i in files2:
    if i[i.rfind('.'):] != '.ogg':
        print i

print "Liczba obrazków: ", len(files) 
print "Liczba dźwięków: ", len(files2)
