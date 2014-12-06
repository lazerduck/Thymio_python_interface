import dbus
import dbus.mainloop.glib
import gobject
import sys
import time
import scratch
import thread

from optparse import OptionParser

#variables
#length of operation
global duration
duration = 0.5
#speed of both wheels
global wheelSpeed
wheelSpeed = 500
#individual left speed
global Lspeed
Lspeed = 0
#individual right speed
global Rspeed
Rspeed = 0
#is the thymio reponding to wheel speeds or commands
global dirCont
dirCont = False
#what is the currently recieved broadcast
global broad
command = 'null'
#moving in an arch [radius,arch_length]
global archVar
archVar = [0,0]
#what sensors are we using
accBool = False
groundBool = False
proxBool = False
#arrays for recieving data
proxSensorsVal=[0,0,0,0,0,0,0]
groundDeltaVal=[0,0]
accVal=[0,0,0]
circLed = [0,0,0,0,0,0,0,0]
#list of recognised commands
commandList = ["forward","backward","left","right","null","direct","command","arch"]
ledCircle =['circ0','circ1','circ2','circ3','circ4','circ5','circ6','circ7']
#listen for scratch
def scratchReceiver():
    while True:
        res = s.receive()
        #print res
        #receive variables
        if res[0] == 'sensor-update':
            print 'sensor update'
            sensor = res[1]
            if 'duration' in sensor:
                global duration
                duration = sensor['duration']
                print 'duration set'
                print duration
            if 'speed' in sensor:
                global wheelSpeed
                wheelSpeed = sensor['speed']
                print 'speed set'
                print wheelSpeed
	    if 'LeftSpeed' in sensor:
                global Lspeed
                Lspeed = sensor['LeftSpeed']
                print 'Lspeed set'
                print wheelSpeed
	    if 'RightSpeed' in sensor:
                global Rspeed
                Rspeed = sensor['RightSpeed']
                print 'Rspeed set'
                print wheelSpeed
	    if 'Radius' in sensor:
                global archVar
                archVar[0] = sensor['Radius']
		if archVar[0] == 0:
		    archVar[0] = 1
                print 'radius set'
                print archVar[0]
	    if 'Length' in sensor:
                global archVar
                archVar[1] = sensor['Length']
                print 'arch length set'
                print archVar[1]
            for x in range(0,8):
                if ledCircle[x] in sensor:
                    circLed[x] = sensor[ledCircle[x]]
        for r in res:
            #set commands
            for c in commandList:
                if r == c:
                    global command
                    command = c
		    if command == "arch":
			global wheelSpeed
			radius = abs(archVar[0])
			archCenter = abs(archVar[1])
			theta = float(archCenter)/float(radius)
			archOuter = theta*(radius+5)
			archInner = theta*(radius)
			percent = float(archInner)/float(archOuter)
			vel = float(wheelSpeed)*percent / float(100.0/3.0)
			temp = vel/float(abs(archVar[1]))
			print (1.0/temp)
			time.sleep((1.0/temp))
			command = 'null'
                    elif duration != 0 :
                        time.sleep(duration)
                        command = 'null'
def get_variables_reply_prox(r):
    global proxSensorsVal
    proxSensorsVal=r

def get_variables_reply_delta(r):
    global groundDeltaVal
    groundDeltaVal=r

def get_variables_reply_acc(r):
    global accVal
    accVal=r
 
def get_variables_error(e):
    print 'error:'
    print str(e)
    loop.quit()

def thymioControl():
    network.SendEvent(0,circLed)
    if proxBool:
        network.GetVariable("thymio-II", "prox.horizontal",reply_handler=get_variables_reply_prox,error_handler=get_variables_error)
        s.sensorupdate({'prox0': proxSensorsVal[0], 'prox1': proxSensorsVal[1],'prox2': proxSensorsVal[2],'prox3': proxSensorsVal[3],'prox4': proxSensorsVal[4],'prox5': proxSensorsVal[5],'prox6': proxSensorsVal[6]})
    if groundBool:
        network.GetVariable("thymio-II", "prox.ground.delta",reply_handler=get_variables_reply_delta,error_handler=get_variables_error)
        s.sensorupdate({'delta0':groundDeltaVal[0],'delta1':groundDeltaVal[1]})
    if accBool:
        network.GetVariable("thymio-II", "acc",reply_handler=get_variables_reply_acc,error_handler=get_variables_error)
        s.sensorupdate({'acc0':accVal[0],'acc1':accVal[1],'acc2':accVal[2]})
        
    #print proxSensorsVal[0],proxSensorsVal[1],proxSensorsVal[2],proxSensorsVal[3],proxSensorsVal[4],proxSensorsVal[5],proxSensorsVal[6]
    #print groundDeltaVal[0], groundDeltaVal[1]
    #print accVal[0], accVal[1], accVal[2]
    
                   
    s.broadcast("setprox")
    if command == "direct":
	global dirCont
	dirCont = False
    if command == "command":
	global dirCont
	dirCont = True
    global dirCont
    if dirCont == True:
        if command == "forward":
	    network.SetVariable("thymio-II", "motor.left.target", [wheelSpeed])
            network.SetVariable("thymio-II", "motor.right.target", [wheelSpeed])
        elif command == "left":
	    network.SetVariable("thymio-II", "motor.left.target", [-wheelSpeed])
            network.SetVariable("thymio-II", "motor.right.target", [wheelSpeed])
        elif command == "right":
	    network.SetVariable("thymio-II", "motor.left.target", [wheelSpeed])
            network.SetVariable("thymio-II", "motor.right.target", [-wheelSpeed])
        elif command == "backward":
	    network.SetVariable("thymio-II", "motor.left.target", [-wheelSpeed])
            network.SetVariable("thymio-II", "motor.right.target", [-wheelSpeed])
        elif command == "null":
            network.SendEvent(1,[])
	    network.SetVariable("thymio-II", "motor.left.target", [0])
            network.SetVariable("thymio-II", "motor.right.target", [0])
        elif command == "arch":
	    #calculate the percentage difference between wheels
	    if archVar[0] > 0:
		radius = archVar[0]
		archCenter = archVar[1]
		theta = float(archCenter)/float(radius)
		archOuter = theta*(radius+5)
		archInner = theta*(radius-5)
		percent = float(archInner)/float(archOuter)
                network.SetVariable("thymio-II", "motor.left.target", [wheelSpeed*percent])
                network.SetVariable("thymio-II", "motor.right.target", [wheelSpeed])
	    else:
		radius = abs(archVar[0])
		archCenter = archVar[1]
		theta = float(archCenter)/float(radius)
		archOuter = theta*(radius+5)
		archInner = theta*(radius-5)
		percent = float(archInner)/float(archOuter)
                network.SetVariable("thymio-II", "motor.left.target", [wheelSpeed])
                network.SetVariable("thymio-II", "motor.right.target", [wheelSpeed*percent])
        else:
            #set the motors to 0 if there is no command
            network.SetVariable("thymio-II", "motor.left.target", [0])
            network.SetVariable("thymio-II", "motor.right.target", [0])
    else:
        network.SetVariable("thymio-II", "motor.left.target", [Lspeed])
        network.SetVariable("thymio-II", "motor.right.target", [Rspeed])
    return True

if __name__ == '__main__':
    print 'answer with \'y\' or \'n\''
    print 'use proximity sensors: '
    if sys.stdin.read(1) == 'y':
        proxBool = True
    sys.stdin.read(1)
    print 'use ground sensors: '
    if sys.stdin.read(1) == 'y':
        groundBool = True
    sys.stdin.read(1)
    print 'use acceleration sensors: '
    if sys.stdin.read(1) == 'y':
        accBool = True
    s = scratch.Scratch(host = 'localhost')
    s.sensorupdate({'prox0': '0', 'prox1': '0','prox2': '0','prox3': '0','prox4': '0','prox5': '0','prox6':'0','delta0':'0','delta1':'0','acc0':'0','acc1':'0','acc2':'0'})

    parser = OptionParser()
    parser.add_option("-s", "--system", action="store_true", dest="system", default=False,help="use the system bus instead of the session bus")
    (options, args) = parser.parse_args()

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    if options.system:
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()

    network = dbus.Interface(bus.get_object('ch.epfl.mobots.Aseba', '/'), dbus_interface='ch.epfl.mobots.AsebaNetwork')

    loop = gobject.MainLoop()

    handle = gobject.timeout_add(100,thymioControl)

    thread.start_new_thread(scratchReceiver,())
    loop.run()
