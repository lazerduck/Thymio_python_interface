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
duration = 0.5
#speed of both wheels
wheelSpeed = 500
#individual left speed
Lspeed = 0
#individual right speed
Rspeed = 0
#is the thymio reponding to wheel speeds or commands
dirCont = False
#what is the currently recieved broadcast
command = 'null'
#moving in an arc [radius,arc_length]
arcVar = [0,0]
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
commandList = ["forward","backward","left","right","null","direct","command","arc"]
ledCircle =['circ0','circ1','circ2','circ3','circ4','circ5','circ6','circ7']
#strign to store commands sent
f = open('data.txt','w')
f.write("Data\n")
lastsent = ""

#listen for scratch
def scratchReceiver():
    global f
    while True:
        res = s.receive()
        #print res
        #receive variables
        if res[0] == 'sensor-update':
            print 'sensor update'
            sensor = res[1]
            if 'duration' in sensor:
                global duration
		if sensor['duration']<0:
		    duration = 0
		else:
                    duration = sensor['duration']
                print 'duration set'
		f.write(" V:duration") 
                print duration
		s.sensorupdate({'duration':duration})
            if 'speed' in sensor:
                global wheelSpeed
                wheelSpeed = sensor['speed']
                print 'speed set'
		f.write(" V:speed")
                print wheelSpeed
	    if 'LeftSpeed' in sensor:
                global Lspeed
                Lspeed = sensor['LeftSpeed']
                print 'Lspeed set'
		f.write(" V:Lspeed")
                print Lspeed
	    if 'RightSpeed' in sensor:
                global Rspeed
                Rspeed = sensor['RightSpeed']
                print 'Rspeed set'
		f.write(" V:Rspeed")
                print Rspeed
	    if 'Radius' in sensor:
                global arcVar
                arcVar[0] = sensor['Radius']
		if arcVar[0] > 0 and arcVar[0] < 1:
		    arcVar[0] = 1
    		if arcVar[0] < 0 and arcVar[0] > -1:
		    arcVar[0] = -1
                print 'radius set'
		f.write(" V:radius")
                print arcVar[0]
	    if 'Length' in sensor:
                arcVar[1] = sensor['Length']
                print 'arc length set'
		f.write(" V:length")
                print arcVar[1]
            for x in range(0,8):
                if ledCircle[x] in sensor:
                    circLed[x] = sensor[ledCircle[x]]
        for r in res:
            #set commands
            for c in commandList:
                if r == c:
                    global command
		    global lastsent
		    if duration == 0:
			if lastsent == c:
			    print 'repeat 0 command'
			else:
			    command = c
		    else:
                        command = c
		    
		    lastsent=c
		    f.write(" C:" + c)
		    if command == "arc":
		        radius = abs(arcVar[0])
		        arcCenter = abs(arcVar[1])
		        theta = float(arcCenter)/float(radius)
		        arcOuter = theta*(radius+5)
		        arcInner = theta*(radius)
		        percent = float(arcInner)/float(arcOuter)
		        vel = float(wheelSpeed)*percent / float(100.0/3.0)
		        temp = vel/float(abs(arcVar[1]))
		        print (1.0/temp)
                        time.sleep(abs(1.0/temp))
		        command = 'null'
                    elif duration != 0 :
                        time.sleep(abs(duration))
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
    s.broadcast("setprox")
    global dirCont
    if command == "direct":
	dirCont = False
    if command == "command":
	dirCont = True

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
        elif command == "arc":
	    #calculate the percentage difference between wheels
	    if arcVar[0] > 0:
		radius = arcVar[0]
		arcCenter = arcVar[1]
		theta = float(arcCenter)/float(radius)
		arcOuter = theta*(radius+5)
		arcInner = theta*(radius-5)
		percent = float(arcInner)/float(arcOuter)
                network.SetVariable("thymio-II", "motor.left.target", [wheelSpeed*percent])
                network.SetVariable("thymio-II", "motor.right.target", [wheelSpeed])
	    else:
		radius = abs(arcVar[0])
		arcCenter = arcVar[1]
		theta = float(arcCenter)/float(radius)
		arcOuter = theta*(radius+5)
		arcInner = theta*(radius-5)
		percent = float(arcInner)/float(arcOuter)
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
    sys.stdin.read(1)
    #ask the user for the address of scratch
    host = raw_input("What is the IP address of scratch?")
    
    s = scratch.Scratch(host = host)
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
