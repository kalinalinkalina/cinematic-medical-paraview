#!/usr/local/bin/python

import hou
import sys
import numpy
import os
import os.path
import ntpath
import collections
import math
from decimal import *
import tfm # This was created by Stuart Levy at the University of Illinois at Urbana-Champaign
import subprocess


# 50 is the Houdini default, but this could be anything and it will still work
defaultFocal = 50.0

# If the change in rotation in the .vd file is greater than this threshold, 
# add/subtract 360
rotationThreshold = 190.0
rotationCounter = [0,0,0] # rx, ry, rz

# Keeps track of previous rotation
prevRotation = [0.0,0.0,0.0]



def exportChannel(cameraPath=None, filePath=None, startFrame=1, endFrame=-1):
    """Exports a single channel to a file"""
    if(filePath == None or cameraPath == None):
        print("exportChannel(cameraPath, filePath, startFrame=1, endFrame=1)")
        return
    
    camNode = hou.node(cameraPath)
    if not camNode:
        print("ERROR: Camera " + cameraPath + " does not exist.", file=sys.stderr)
        return

    myChannel = camNode.parm(channel)
    if not(myChannel):
        print("ERROR: Channel " + channel + " does not exist in camera node " + cameraPath, file=sys.stderr)
        return

    keyframes = myChannel.keyframes()
    if endFrame == -1:
        endFrame = max( [ i.frame() for i in myChannel.keyframes() ] )

    with open(filePath, "w") as outFile:
        for i in range(startFrame, endFrame+1):
            value = camNode.parm(channel).evalAtFrame(i)
            print(value, file=outFile)



     
def exportCamera(cameraPath=None, filePath=None, startFrame=1, endFrame=-1):
    """Exports an existing camera in Houdini to a text file. Only use start/end when exporting a .wf file."""
    
    if(cameraPath==None or filePath==None):
        print("exportCamera(cameraPath, filePath, startFrame=1, endFrame=-1)")
        return

    # Get the camera object
    camNode = _canonCameraNode( cameraPath )

    if not camNode:
        print("ERROR: Camera " + cameraPath + " does not exist.", file=sys.stderr)
        return

    outFile = open(filePath, "w")

    # Check file extension
    extension = os.path.splitext(filePath)[1]
    if extension == ".vd":
        _exportKeys(camNode, outFile)
    elif extension == ".wf":
        _exportFrames(camNode, outFile, startFrame, endFrame)
    else:
        print("ERROR: File extension must be .vd or .wf", file=sys.stderr)

    outFile.close()
    


def _transformRotationOrder(camNode, time):
        
    # Get the transform for the xyz camera
    worldxform = camNode.worldTransformAtTime(time)

    explode = worldxform.explode('srt', 'zxy')
    tx = explode['translate'][0]
    ty = explode['translate'][1]
    tz = explode['translate'][2]

    worldxformnp = numpy.array([ [worldxform.at(0,0), worldxform.at(0,1), worldxform.at(0,2)], [worldxform.at(1,0), worldxform.at(1,1), worldxform.at(1,2)], [worldxform.at(2,0), worldxform.at(2,1), worldxform.at(2,2)] ])
    rxryrz = tfm.t2meuler( "zxy", worldxformnp )
    rx = rxryrz[0]
    ry = rxryrz[1]
    rz = rxryrz[2]

    return rx, ry, rz, tx, ty, tz

def _canonCameraNode(cameraPath):

    if cameraPath.startswith('/out/'):
        outno = hou.node(cameraPath)
        if outno is None:
            raise ValueError("%s isn't an /out node" % cameraPath)
        camparm = outno.parm("camera")
        if camparm is None:
            raise ValueError("%s doesn't have a 'camera' parameter" % cameraPath)

        return hou.node( camparm.unexpandedString() )

    if cameraPath.startswith('/obj/'):
        return hou.node( cameraPath )

    if hou.node('/obj/' + cameraPath) is not None:
        return hou.node( '/obj/' + cameraPath )

    return None
    

def _exportKeys(camNode, outFile):
    
    fps = hou.fps()
    resx = camNode.parm("resx").eval()
    resy = camNode.parm("resy").eval()
    aspect = resx/float(resy)
    focal = camNode.parm("focal").eval()

    txkeys = camNode.parm("tx").keyframes()
    tykeys = camNode.parm("ty").keyframes()
    tzkeys = camNode.parm("tz").keyframes()
    txkeylen = len(txkeys)
    tykeylen = len(tykeys)
    tzkeylen = len(tzkeys)

    if txkeylen == 0 or tykeylen == 0 or tzkeylen == 0:
        print("ERROR: This camera has zero tx, ty, or tz keyframes. Make sure to add at least one keyframe for each of these parameters and try again.")
        return
    
    hasEaseIn = False
    hasEaseOut = False
    try:
        hasEaseIn = txkeys[0].value() == txkeys[1].value() and tykeys[0].value() == tykeys[1].value() and tzkeys[0].value() == tzkeys[1].value()
        hasEaseOut = txkeys[txkeylen-1].value() == txkeys[txkeylen-2].value() and tykeys[tykeylen-1].value() == tykeys[tykeylen-2].value() and tzkeys[tzkeylen-1].value() == tzkeys[tzkeylen-2].value()
    except:
        pass

    rxkeys = camNode.parm("rx").keyframes()
    rykeys = camNode.parm("ry").keyframes()
    rzkeys = camNode.parm("rz").keyframes()

    txframes = set([ i.frame() for i in txkeys ])
    tyframes = set([ i.frame() for i in tykeys ])
    tzframes = set([ i.frame() for i in tzkeys ])
    rxframes = set([ i.frame() for i in rxkeys ])
    ryframes = set([ i.frame() for i in rykeys ])
    rzframes = set([ i.frame() for i in rzkeys ])


    union = txframes | tyframes | tzframes | rxframes | ryframes | rzframes
    keys = len(union)
    exportKeys = keys

    if hasEaseIn:
        exportKeys = exportKeys - 1
    if hasEaseOut:
        exportKeys = exportKeys - 1 

    outFile.write("fps " + repr(fps) + "\n")
    outFile.write("keys " + repr(exportKeys) + "\n")
    

    for keyNum in range(keys):
        # Don't write out first frame if there is an easein, or last frame if there is an easeout
        if not ( (hasEaseIn and keyNum == 0) or (hasEaseOut and keyNum == keys-1) ):            

            # Find the lowest keyframe time and eval all parameters at that time
            timeTx = None
            timeTy = None
            timeTz = None
            timeRx = None
            timeRy = None
            timeRz = None
            timeAperture = None
            try:
                timeTx = camNode.parm("tx").keyframes()[keyNum].time()
            except:
                pass
            try:
                timeTy = camNode.parm("ty").keyframes()[keyNum].time()
            except:
                pass
            try:
                timeTz = camNode.parm("tz").keyframes()[keyNum].time()
            except:
                pass
            try:
                timeRx = camNode.parm("rx").keyframes()[keyNum].time()
            except:
                pass
            try:
                timeRy = camNode.parm("ry").keyframes()[keyNum].time()
            except:
                pass
            try:
                timeRz = camNode.parm("rz").keyframes()[keyNum].time()
            except:
                pass
            try:
                timeAperture = camNode.parm("aperture").keyframes()[keyNum].time()
            except:
                pass

            times = [timeTx, timeTy, timeTz, timeRx, timeRy, timeRz, timeAperture]

            # Sometimes the union of times gives a number larger than the number of keys.
            if not all(x is None for x in times):        
                time = min(x for x in times if x is not None)

                aperture = camNode.parm("aperture").evalAtTime(time)

                rOrder = camNode.parm("rOrd").eval()
                #if(rOrder != 4):
                rx, ry, rz, tx, ty, tz = _transformRotationOrder(camNode, time)

                fovy = numpy.degrees( 2.0 * numpy.arctan( aperture / (2.0*aspect*focal) ) )
                outFile.write("\t" + repr(time) + " : " + repr(tx) + " " + repr(ty) + " " + repr(tz) + " " + repr(rx) + " " + repr(ry) + " " + repr(rz) + " " + repr(fovy) + "\n" )
        
    if hasEaseIn:
        outFile.write("easein\n")
    if hasEaseOut:
        outFile.write("easeout\n")
    
    
    
def _exportFrames(camNode, outFile, startFrame=1, endFrame=-1):

    if endFrame == -1:
        for p in "tx", "ty", "tz", "rx", "ry", "rz":
            endFrame = max( endFrame, max( [ i.frame() for i in camNode.parm(p).keyframes() ] ) )
        endFrame = int(math.ceil(endFrame))

    print("Exporting frames %d .. %d from %s into %s" % (startFrame, endFrame, camNode.path(), (outFile.name if hasattr(outFile, 'name') else outFile)))


    resx = camNode.parm("resx").eval()
    resy = camNode.parm("resy").eval()
    focal = camNode.parm("focal").eval()
    aspect = resx/float(resy)
    
    endFrame = endFrame+1  # Since we are subtracting 1 from frame later

    for frame in range(startFrame, endFrame):

        aperture = camNode.parm("aperture").evalAtFrame(frame)
        fovy = numpy.degrees( 2.0 * numpy.arctan( aperture / (2.0*aspect*focal) ) )

        rOrder = camNode.parm("rOrd").eval()

        # Houdini frame=1 is time=0
        if frame == 1:
            time = 0
        else:
            time = math.pow( hou.fps() * 1.0/float(frame-1) , -1)
        rx, ry, rz, tx, ty, tz = _transformRotationOrder(camNode, time)

        outFile.write( repr(tx) + " " + repr(ty) + " " + repr(tz) + " " + repr(rx) + " " + repr(ry) + " " + repr(rz) + " " + repr(fovy) + "\n" )
       
