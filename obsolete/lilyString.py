#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         lilyString.py
# Purpose:      Processing of lilypond strings for output
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Obsolete module that creates a lilypond document by overwriting String class.  Bad idea...

Kept in lily until all references to it can be removed; then will be in obsolete.  Do not use.
'''

import os
import sys
import tempfile
import re
import time
# import threading
import unittest, doctest



import music21
from music21 import environment
_MOD = 'lily.lilyString.py'
environLocal = environment.Environment(_MOD)


try: 
    # optional imports for PIL 
    from PIL import Image
    from PIL import ImageOps
    noPIL = False
except ImportError:
    noPIL = True



#-------------------------------------------------------------------------------

TRANSPARENCY_START = r'''
 \override Rest #'transparent  = ##t
 \override Dots #'transparent  = ##t
 '''
TRANSPARENCY_STOP = r'''
 \revert Rest #'transparent
 \revert Dots #'transparent
 '''



#-------------------------------------------------------------------------------
class LilyString(object):
    '''Class for representing complete processing of a lily pond string.
    '''
    if os.path.exists(environLocal['lilypondPath']):
        LILYEXEC = environLocal['lilypondPath']
    else:
        if sys.platform == "darwin":
            LILYEXEC = '/Applications/Lilypond.app/Contents/Resources/bin/lilypond'
        elif sys.platform == 'win32' and os.path.exists('c:/Program Files (x86)'):
            LILYEXEC = 'c:/Program\ Files\ (x86)/lilypond/usr/bin/lilypond'
        elif sys.platform == 'win32':
            LILYEXEC = 'c:/Program\ Files/lilypond/usr/bin/lilypond'
        else:
            LILYEXEC = 'lilypond'
    format   = 'pdf'
    version  = '2.11' # this should be obtained from user and/or user's system
    backend  = 'ps'
    backendString = '--backend='
    midiWrapped = False
    
    if version.count("2.11") > 0:  # new version of backend as of 2.11
        backendString = '-dbackend='
    elif sys.platform == "win32": 
        backendString = '-dbackend='
    elif sys.platform == "linux2":
        backendString = '-dbackend='
        
    if version.startswith("2.12"):
        # note: version 2.12 of lilypond needs a -formats flag, not --backend
        backendString = '--formats='
        

    snippet  = r'''
\paper {
#(define dump-extents #t)

indent = 0\mm
force-assignment = #""
oddFooterMarkup=##f
oddHeaderMarkup=##f
bookTitleMarkup=##f

}

'''
    noHeader = r'''
scoreTitleMarkup=##f
'''
    
    layout = r'''
\layout {

}
'''

    midi = r'''
\midi {

}
'''
    
    fictaDef = \
    """ficta = #(define-music-function (parser location) () #{ \\once \\set suggestAccidentals = ##t #})
    color = #(define-music-function (parser location color) (string?) #{ 
    \\once \\override NoteHead #'color = #(x11-color $color) 
    \\once \\override Stem #'color = #(x11-color $color)
    \\once \\override Rest #'color = #(x11-color $color)
    \\once \\override Beam #'color = #(x11-color $color)
     #})
     
     """

    headerInformation = "\\version \"" + version + "\"" + layout + fictaDef
    savePNG = False ## PNGs are deleted immediately.
    
    def __init__(self, value = u""):
        if hasattr(value, "value"):
            self.value = value.value
        else:
            self.value = unicode(value)
    
    def __add__(self, addStr):
        if hasattr(addStr, "value"):
            self.value = self.value + addStr.value
        else:
            self.value = self.value + addStr
        return self
    
    def __mul__(self, value):
        self.value = self.value * value
        return self
        
    def __del__(self):
        if hasattr(self, "tempName") and self.tempName:
            try:
                os.remove(self.tempName)
            except:
                pass
    
    def __str__(self):
        return self.value
    
    def __unicode__(self):
        return self.value
    
    def __repr__(self):
        return self.value
    
    def wrapForMidi(self):
        self.value = "\\score { { " + self.value + "} \\layout { } \\midi { \\context { \\Score tempoWholesPerMinute = #(ly:make-moment 100 2) } }  }"
        self.midiWrapped = True
    
    def _getWrappedValue(self):
        '''
        returns a value that is wrapped with { } if it doesn't contain a score element
        so that it can run through lilypond
        '''
        if self.midiWrapped is True:
            return self.value
        elif r'\score' in self.value:
            return self.value
        elif self.value.lstrip().startswith('{'):
            return self.value
        else:
            return unicode('{' + self.value + '}')
    
    wrappedValue = property(_getWrappedValue)
    

    def renderTemplate(self):
        '''Return configured string data. 
        '''
        data = []
        data.append(self.snippet)
        data.append(self.headerInformation)
        data.append(self.wrappedValue.encode('utf-8'))
        return "\n".join(data)

    def writeTemp(self, ext='', fp=None):
        if fp == None:
            fp = environLocal.getTempFile(ext)
        
        #(fd, tempName) = tempfile.mkstemp()
        self.tempName = fp

        data = []
        data.append(self.snippet)
        data.append(self.headerInformation)
        data.append(self.wrappedValue.encode('utf-8'))

        f = open(self.tempName, 'w')
        f.write(''.join(data))
        f.close()
        return self.tempName
    


    def runThroughLily(self):
        filename = self.tempName
        format   = self.format
        backend  = self.backend
        lilyCommand = '"' + self.LILYEXEC + '"' + " -f " + format + " " + \
                    self.backendString + backend + " -o " + filename + " " + filename
        
        try:
            os.system(lilyCommand)    
        except:
            raise
        
        try:
            os.remove(filename + ".eps")
        except:
            pass
        fileform = filename + '.' + format
        if not os.path.exists(fileform):
            fileend = os.path.basename(fileform)
            if not os.path.exists(fileend):
                raise Exception("cannot find " + fileend)
            else:
                fileform = fileend
        return fileform

    def createPDF(self, filename=None):
        self.writeTemp(fp=filename) # do not need extension here
        lilyFile = self.runThroughLily()
        return lilyFile

    def showPDF(self):
        lF = self.createPDF()
        if not os.path.exists(lF):
            raise Exception('Something went wrong with PDF Creation')
        else:
            if os.name == 'nt':
                command = 'start /wait %s && del /f %s' % (lF, lF)
            elif sys.platform == 'darwin':
                command = 'open %s' % lF
            else:
                command = ''
            os.system(command)
    
    def createPNG(self, filename=None):
        self.format = 'png'
        self.backend = 'eps'
        self.writeTemp(fp=filename) # do not need extension here
        lilyFile = self.runThroughLily()
        if noPIL is False:
            try:
                lilyImage = Image.open(lilyFile)
                lilyImage2 = ImageOps.expand(lilyImage, 10, 'white')
                if os.name == 'nt':
                    format = 'png'
                # why are we changing format for darwin? -- did not work before
                elif sys.platform == 'darwin':
                    format = 'jpeg'
                else: # default for all other platforms
                    format = 'png'
                
                if lilyImage2.mode == "I;16":
                # @PIL88 @PIL101
                # "I;16" isn't an 'official' mode, but we still want to
                # provide a simple way to show 16-bit images.
                    base = "L"
                else:
                    base = Image.getmodebase(lilyImage2.mode)
                if base != lilyImage2.mode and lilyImage2.mode != "1":
                    file = lilyImage2.convert(base)._dump(format=format)
                else:
                    file = lilyImage2._dump(format=format)
                return file
            except:
                raise
                
        return lilyFile
        
    def showPNG(self):
        '''Take the LilyString, run it through LilyPond, and then show it as a PNG file.
        On Windows, the PNG file will not be deleted, so you  will need to clean out
        TEMP every once in a while
        '''
        lilyFile = self.createPNG()
        environLocal.launch(self.format, lilyFile)
        #self.showImageDirect(lilyFile)
        
        return lilyFile
        
    def createSVG(self, filename=None):
        self.format = 'svg'
        self.backend = 'svg'
        self.writeTemp(fp=filename)
        lilyFile = self.runThroughLily()
        return lilyFile

    def showSVG(self, filename=None):
        lilyFile = self.createSVG(filename)
        environLocal.launch(self.format, lilyFile)
        return lilyFile
        
    def showPNGandPlayMIDI(self):
        if self.midiWrapped is False:
            self.wrapForMidi()
        lilyFile = self.showPNG()
        midiFile = re.sub("\.png",".midi",lilyFile)
        self.playMIDIfile(midiFile)

    def checkForMidiAndAdd(self):
        if self.checkForMidi():
            pass
        else:
            self.addMidi()
            
    def addMidi(self):
        '''override this in subclasses, such as LilyScore'''
        a = self.midi
        self.value += self.midi
    
    def checkForMidi(self):
        if self.value.count('\\midi') > 1:
            return True
        else:
            return False
        
    def playMIDIfile(self, file):
        # TODO: this should not be called play, is it does not play the file
        # but simply opens it. 
        if not os.path.exists(file):
            f2 = re.sub("\.midi",".mid", file)
            if os.path.exists(f2):
                file = f2
            elif os.path.exists("/tmp/" + file):
                file = "/tmp/" + file
            else:
                raise Exception("Cannot play midi file %s: file does not exist", file)
        if os.name == "nt":
            command = "start %s" % (file)
        else:
            command = "open %s" % (file)
        self.midiFilename = file
        os.system(command)
        
    def quickHeader(self, string):
        '''Returns a quick and dirty lilyPond header for the stream
        '''
        headOut = " \\header { \n piece = \"" 
        headOut += string
        headOut += " \" \n}\n";
        return headOut


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    pass
    

    

class TestExternal(unittest.TestCase):
    
    def testPNG(self):
        a = LilyString("c'4")
#        a.showPNG()    

    def testPNGandPlayMIDI(self):
        a = LilyString("c'4")
#        a.showPNGandPlayMIDI()
        
    def testAdd(self):
        a = LilyString("c'4 ")
        a += "d'4 "
        b = LilyString("b4 ") + a
        self.assertEqual(b.value, u"b4 c'4 d'4 ")
        b.showPNG()    
        
    def testVoices():
        myString = '''VoiceIV = \\context Voice = VoiceIV {
        \\set Staff.midiInstrument = "acoustic grand"
        \\time 3/2
        \\key c \\major
        \\clef bass c2 f \\color "DeepPink" g4 f |
        e1 f2 |
        c \\ficta des4 \\ficta des \\ficta ees ees, |
        \\ficta a,2 des1 |
    %5
        aes,1. \\bar "|."
    }
    \\score {
        <<
    
            
            \\VoiceIV
        >>
        \\layout {
        }
    
    }'''
        myString2 = '''
    { \\tempo "Fast"
    c'4 c' c' c'
    c'4 c' c' c'
    \\tempo "Andante" 4 = 120
    c'4 c' c' c'
    c'4 c' c' c'
    \\tempo 4 = 100
    c'4 c' c' c'
    c'4 c' c' c'
    \\tempo "" 4 = 30
    c'4 c' c' c'
    c'4 c' c' c'
    }
    '''
    
        LilyString(myString).showPNG()
        LilyString(myString2).showPNGandPlayMIDI()
    
    
    def testBraces():
        '''
        can we put braces around anything in lily?
        Apparently So
        '''
        lString = LilyString('{ \\time 6/4 {c\'4~} {c\'4} {d\'4} {ees\'4} r2 }')
        lString.showPNG()


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    #music21.mainTest(Test)
    music21.mainTest(Test, TestExternal)






#------------------------------------------------------------------------------
# eof

