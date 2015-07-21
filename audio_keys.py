"""
Author: Peter Matev
Date: 	01/03/2011


A script to help keyframe objects' translation in response to an audio track. Useful for the generation of speakers and audio driven animations.
Only works on 8bit mono and stereo wav files due to limitations in the built in python wave modules. This script is intended for rendering purposes
more than realtime as the effect is much better with motion blur turned on.

User Manual:

1. Open a .wav file in the open file dialog
2. Choose a channel from which to take audio data. (only applies to stereo tracks)
3. Choose an axis in which to move the object.
4. Choose a level of detail as a percentage. 1 is one key per frame, 100 is the maximum density (one key for every piece of audio data)
5. Set a range between which you would like the object to move. An easy workflow would be to select the object, ensure that you have selected the desired value.
   Move the object to the minimum distance and press the left arrow button (<). Similarly, move the object to the maximum distance and hit the right arrow (>)
6. Autolock is usually left off for testing purposes. If selected it will automatically lock the object from receiving any more keyframes if the script is run a second time.
   Its most useful for distinguishing between multiple objects which have been keyed. Note: deleting keys will automatically unlock any locked object.
7. Ensure the object is selected and press Generate Keyframes to create the keys.
8. Similarly, ensure the object is selected and the desired axis is selected when pressing Delete Keyframes as it will only delete in the axis chosen.


"""

import wave, audioop
import maya.cmds as cmds
import maya.mel as mel
	
#---- initialize global variables ----#
## the wav file object loaded in the current scene
wavFile = 0
   
## the detailed parameters of the wav file in the format (nchannels, sampwidth, framerate, nframes, comptype, compname)
params = 0 

## the array of raw audio data (in ascii form)
frames = 0  

#------- default values -------#

## The density of keyframes to generate. Higher keyframe density provides more accurate results for rendering with motionblur but is slower to generate. Default value is 166 or 50%
detail = 166

## If autolock is set, the object gets locked from receiving more keyframes by default by creating a 'lock' attribute. This is useful if you have multiple objects to create keyframes for. Default value is off.
autoLock = False

## Array to hold the string attributes for Translation Axis.
axis = ['tx', 'ty', 'tz']

## Array to hold the string attributes for Rotate Pivot Axes.
rpaxes = ['rptx', 'rpty', 'rptz']

## Default value for the UI axis option box. Default is X.
chosenAxis = 1

## Default value for the UI channel option box. Default is Left.
chosenChannel = 1

## The range between which the object should move. Default is between 0 and 10.
minMax=[0,10]

def createUI():
   """
   Function to build the User Interface.
   
   If the window is already open it closes it and opens a new one.
   """
   #------- check to see if the window already exists and deletes if it does.-------#
   if(cmds.window("UI",exists=True)):
      cmds.deleteUI("UI")
   
   #create the window
   window = cmds.window("UI", title="Audio Driven Keyframes")
   
   #initialize the form layout
   form = cmds.formLayout(numberOfDivisions=100)
   
   #initialize progress bar
   progress = cmds.progressBar('progress')
      
   # create open button
   openButton = cmds.button(label="Open...", command=('openFile()'))   
   
   #new column layout
   infoCol = cmds.columnLayout()
   
   #------- if the audio has already been imported use it -------#
   if(cmds.objExists('audio')):
      
      global fileName, wavFile, params, frames
      fileName = cmds.getAttr('audio.filename')
           
      #------- set up the stream -------#
      wavFile = wave.open(fileName)   
      params = wavFile.getparams()   
      frames = wavFile.readframes(params[3])
      cmds.progressBar('progress', edit=True, maxValue = params[3])
      
      #------- text label for the current audio file loaded -------#
      currentAudioPath = cmds.text('currentAudioPath', label="Currently loaded "+fileName)
      currentParams = cmds.text('currentParams', label=str(params))
   
   #------- otherwise just place dummy text-------#   
   else:
      currentAudioPath = cmds.text('currentAudioPath', label="Please choose an audio file.")
      currentParams = cmds.text('currentParams', label="")
   
   cmds.setParent("..")
    
   # create grid layout for all the variables in the form
   numbers =  cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1,100)])
   
   #create channel option boxes
   cmds.text(label="Channel")
   cmds.radioButtonGrp('channel',
                              nrb=3, 
                              onc="changeChannel()", 
                              numberOfRadioButtons=3, 
                              labelArray3=['Left', 'Right', 'Both (Mono)'], 
                              sl=chosenChannel )
   
   #create axis option boxes
   cmds.text(label="Axis")
   cmds.radioButtonGrp('axis',
                              nrb=3, 
                              onc="changeAxis()", 
                              numberOfRadioButtons=3, 
                              labelArray3=['X', 'Y', 'Z'], 
                              sl=chosenAxis )
   
   #create detail slider
   cmds.text(label="Detail")
   detailSld = cmds.intSliderGrp('detail', field=True, cc="changeDetail()", value=50,minValue = 1, maxValue=100)
   
   #create range row
   cmds.text(label="Range")
   cmds.rowLayout(numberOfColumns=5)
   
   #min range field
   cmds.floatField('min', value=minMax[0])
   
   #assign current-to-min button
   cmds.button('assignLeft', label='<', c="assignLeft()")
   
   #initialize the current field and if the object has been selected use the objects default axis value otherwise just set it to 0
   if(cmds.ls(sl=True)):   
      selection = cmds.ls(sl=True)
      cmds.floatField('current', rfc="updateCurrentValue()", value=cmds.getAttr(selection[0]+"."+axis[chosenAxis-1]))
   else:
      cmds.floatField('current', rfc="updateCurrentValue()", value=0)
   
   #assign current-to-max button
   cmds.button('assignRight', label='>', c="assignRight()")
   
   #max range field
   cmds.floatField('max', value=minMax[1])
   cmds.setParent("..")
   
   #autolock option box
   cmds.text(label="Auto Lock")
   cmds.checkBox('autoLock', label="", cc=('lock()'), value=autoLock)
   
   cmds.setParent("..")
   
  #make the generate and delete buttons on one row
   buttonsRow = cmds.rowColumnLayout(numberOfColumns=2)
   createButton = cmds.button(label="Generate Keyframes", command=('generateKeyframes()'))
   deleteButton = cmds.button(label="Delete Keyframes", command=('deleteKeyframes()'))   
   
   
   cmds.setParent("..")   
   
   
   #------ put all these items in the form -----#
   cmds.formLayout(form, edit=True, attachForm=[(openButton, 'left', 10),
                                                (openButton, 'right', 10), 
                                                (openButton, 'top', 10),
                                                (infoCol, 'left', 10),
                                                (infoCol, 'right', 10),
                                                (numbers, 'left', 10),
                                                (numbers, 'right', 10),
                                                (buttonsRow, 'left', 10),
                                                (buttonsRow, 'right', 10),
                                                (progress, 'left', 10),
                                                (progress, 'right', 10),
                                                (progress, 'bottom', 10),],
                                    attachControl=[(infoCol, 'top',10, openButton),
                                                         (numbers, 'top', 10, infoCol),
                                                         (buttonsRow, 'bottom',0, progress)])
                                                
   cmds.showWindow()


def openFile():
   """
   Function to open a new wav file into the scene. 
   
   Creates a new Maya sound node and changes the timeslider to use the audio for playback while scrubbing.
   
   Prepares the wav file for reading audio data.
   
   Adjusts the UI to display the current audio parameters and progress bar for the new track.
   """
   global wavFile, params, frames
   
   #open file dialog
   fileNameList = cmds.fileDialog2(cap="Choose Audio File...", ff="*.wav", fm=4, ds=2, okc="Open")
   
   #convert result from dialog box to a useable string
   fileName = str(fileNameList[0])   
   
   #load the file name into the info text area in the UI
   cmds.text('currentAudioPath', edit=True, label="Currently Loaded: "+fileName)
   
   #delete any existing audio nodes
   if(cmds.objExists('audio')):
      cmds.select('audio')
      cmds.delete()
   
   #create a new sound node
   cmds.sound(f=fileName, n="audio")
   
   #set the 'audio' node to be the audio for the timeline.
   #--------- code from documentation starts here ------------#
   gPlayBackSlider = mel.eval( '$tmpVar=$gPlayBackSlider' )
   cmds.timeControl( gPlayBackSlider, edit=True, sound='audio', displaySound=True)
   #--------- code from documentation ends here -------------#
   
   #set the playback range to the range of the audio
   cmds.playbackOptions(min=0, aet=(cmds.getAttr('audio.duration')), max=(cmds.getAttr('audio.duration')))
   
   #------- set up the stream -------#
   wavFile = wave.open(fileName)   
   params = wavFile.getparams()   
   frames = wavFile.readframes(params[3])
   
   #update the info text with the audio parameters.
   cmds.text('currentParams', edit=True, label=str(params))
   
   #set the max of the progress bar to the number of audio frames in the selected track
   cmds.progressBar('progress', edit=True, maxValue = params[3])
   
   print "Result: ",fileName, "has been loaded."

def changeAxis():
   """
   Function for the user interface controls. 
   
   Sets the chosenAxis variable to that chosen in 'axis' option box and updates the value of the current value field (middle field in Range)
   """
   global chosenAxis
   chosenAxis = cmds.radioButtonGrp('axis', query=True, sl=True)
   updateCurrentValue()

def changeChannel():
   """
   Function for the user interface controls
   
   Sets the chosenChannel variable to that chosen in the 'channel' option box.
   """
   global chosenChannel
   chosenChannel = cmds.radioButtonGrp('channel', query=True, sl=True)
   
def changeDetail():
   """
   Function to get the detail value from the user interface (as a percentage) and convert it to a useable value for keyframe density 
   
   Conversion step in detail:
   
   Since a value of 100 must equal the smallest possible keyframe step (i.e. 1) and a value of 1 must equal the highest possible keyframe step (i.e. once per frame),
   we first invert the value by 101 minus value from the slider (101 because if it was set to 100, 100 - 100 = 0 so the step size would be 0 and that gives an error.)
   Then divide by 100 to give a value between 0.1 and 1.0
   Multiply by the sample rate of the track divided by the frame rate of the video (so that the video matches the audio).
   
   """
   global detail
   
   detailPerc = cmds.intSliderGrp('detail', query=True, value=True)
   detail = ((101-detailPerc)/100.0)*(8000/24.0)

def lock():
   """
   Function to get the state of the autolock option box
   """
   global autoLock
   autoLock = cmds.checkBox('autoLock', query=True, value=True)

def assignLeft():
   """
   Function to set the current value of the translation to the minimum limit.
   Updates the current value field first in case it hasnt been updated for whatever reason. Then assigns the current value as minMax[0] and updates the UI
   """
   updateCurrentValue()
   value =  cmds.floatField('current', query=True, value=True)
   minMax[0] = value   
   cmds.floatField('min', edit=True, value=value)
def assignRight():
   """
   Function to set the current value of the translation to the maximum limit
   Updates the current value field first in case it hasnt been updated for whatever reason. Then assigns the current value as minMax[1] and updates the UI
   """
   updateCurrentValue()
   value = cmds.floatField('current', query=True, value=True)
   minMax[1] = value
   cmds.floatField('max', edit=True, value=value)
def updateCurrentValue():
   """
   Function to update the UI float field to the current translation value whenever the field becomes active 
   """
   if(cmds.ls(sl=True)):   
      selection = cmds.ls(sl=True)
      cmds.floatField('current', edit=True, value=cmds.getAttr(selection[0]+'.'+axis[chosenAxis-1]))

def generateKeyframes():
   """
   Function to create all the keyframes for the entire length of audio data using the current settings.
   It will not create keys if the audio file hasn't been loaded and if the object has been locked via its 'lock' attribute.
   
   ---------- calculations for the Left audio channel are as follows ----------
    
    minimum bound + power of the signal scaled in relation to the max bound. 128 is the max value that 8 bit audio data can take so to scale we use max/128
    power of the signal is root mean square of the raw audio data (audioop.rms(fragment, width))
    this is 8 bit audio so the width is always 1. The fragment is the current data we are trying to read so the step, i, times params[0] (number of channels), minus 1 to take us back to the left channel.
    the audio data is organised in parallel e.g. [1L, 1R, 2L, 2R, 3L, 3R] so we need to step through in steps of 2 and subtract 1 to get the the left channel.
    this means that it accomodates for both mono and stereo tracks. If mono the params[0] = 1, so the (params[0]-1)=0 and has no effect.
    (see line 353)          
   
   """
   if(wavFile != 0):
  
      #loop through all selected objects
      for a in cmds.ls(sl=True):
         cmds.select(a)
         
         #-------- if the object is locked break out and don't create keys -----#
         if(cmds.objExists(a+'.lock') and cmds.getAttr(a+'.lock')):
            print "Keys have already been set. Turn off the lock attribute to override them."
            break
         #-------- if the object is unlocked delete the keys --------#
         elif(cmds.objExists(a+'.lock') and cmds.getAttr(a+'.lock')==0):
            mel.eval('cutKey -cl -t ":" -f ":" -at '+rpaxes[chosenAxis-1]+' '+a+';')
         #otherwise create a new lock attribute to signify that it has had keys generated for it.
         else:                   
            cmds.addAttr(ln="lock", at="bool", k=True)
            
         #reset the progress bar
         cmds.progressBar('progress', edit=True, progress=0)
         
         #make keyframes
         for i in range(0, params[3], detail):
            #increment the progress bar
            cmds.progressBar('progress', edit=True, step=detail)
            
            #if the channel is Left calculate the currect data to use. (see detailed description of generateKeyframes function)
            if(chosenChannel == 1 ):
               value = minMax[0]+(128-audioop.rms(frames[(i*params[0])-(params[0]-1)],1))*(minMax[1]/128.0)
            
            #calculate the correct data to use if the Right channel is selected
            # same as left channel but no need to subtract 1.
            elif(chosenChannel == 2 ):
               value = minMax[0]+(128-audioop.rms(frames[i*params[0]],1))*(minMax[1]/128.0)
            
            #calculate the correct average value between the Left and Right channels by taking the calculations for( Left + Right ) / 2
            elif(chosenChannel == 3):
               average = (audioop.rms(frames[i*params[0]-(params[0]-1)],1)+audioop.rms(frames[(i*params[0])],1))/2
               value = minMax[0]+(128-average)*(minMax[1]/128.0)
            
            #the time step for the keyframe at 24 frames per second
            time = 24*(i/float(params[2]))           
            
            # set the keyframe at the time and value calculated
            cmds.setKeyframe(a, v=value,at=rpaxes[chosenAxis-1], t=time)
         
         #if autolock is on, lock the object, display the keyed channel in the channels box and revert the object to its original position.
         cmds.setAttr(a+'.lock', autoLock)
         cmds.setAttr(a+'.'+rpaxes[chosenAxis-1], k=True)
         cmds.setAttr(a+'.'+axis[chosenAxis-1], 0)
         
   else:
      print "Please choose an audio file!"   

def deleteKeyframes():
   """
   Deletes all the keyframes for the selected object and the selected axis.
   """
   for a in cmds.ls(sl=True):
      mel.eval('cutKey -cl -t ":" -f ":" -at '+rpaxes[chosenAxis-1]+' '+a+';')
      cmds.setAttr(a+'.'+rpaxes[chosenAxis-1], 0)
      cmds.setAttr(a+'.lock', 0) 
      

createUI()