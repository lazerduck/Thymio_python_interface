import dbus
import dbus.mainloop.glib
import gobject
import sys
import time
import scratch
import thread

from optparse import OptionParser

#variables
global duration
duration = 0.5
global wheelSpeed
wheelSpeed = 500

global broad
command = 'null'
#will the sensors be used
accBool = False
groundBool = False
proxBool = False
#sensor values
proxSensorsVal=[0,0,0,0,0,0,0]
groundDeltaVal=[0,0]
accVal=[0,0,0]
circLed = [0,0,0,0,0,0,0,0]
#acceptable commands
commandList = ["forward","backward","left","right","null"]
#led names
ledCircle =['circ0','circ1','circ2','circ3','circ4','circ5','circ6','circ7']
#listen for scratch
def scratchReceiver():
    while True:
        #wait for a message
        res = s.receive()
        #print res
        #receive variables
        if res[0] == 'sensor-update':
            print 'sensor update'
            sensor = res[1]
            #check if the duration time has changed
            if 'duration' in sensor:
                global duration
                duration = sensor['duration']
                print 'duration set'
                print duration
            #check if the wheel speed has changed
            if 'speed' in sensor:
                global wheelSpeed
                wheelSpeed = sensor['speed']
                print 'speed set'
                print wheelSpeed
            #loop through all of the led names and update them if there's a change
            for x in range(0,8):
                if ledCircle[x] in sensor:
                    circLed[x] = sensor[ledCircle[x]]
        for r in res:
            #set commands
            for c in commandList:
                if r == c:
                    global command
                    command = c
                    if duration != 0 :
                        time.sleep(duration)
                        command = 'null'
#receive prox variables
def get_variables_reply_prox(r):
    global proxSensorsVal
    proxSensorsVal=r
#receive ground delta variables
def get_variables_reply_delta(r):
    global groundDeltaVal
    groundDeltaVal=r
#receive accelerometer variables
def get_variables_reply_acc(r):
    global accVal
    accVal=r
 #handle errors
def get_variables_error(e):
    print 'error:'
    print str(e)
    loop.quit()

#thymio control loop
def thymioControl():
    #update the leds on the thymio
    network.SendEvent(0,circLed)
    #get sensor input from thymio and send to scratch if enabled
    if proxBool:
        network.GetVariable("thymio-II", "prox.horizontal",reply_handler=get_variables_reply_prox,error_handler=get_variables_error)
        s.sensorupdate({'prox0': proxSensorsVal[0], 'prox1': proxSensorsVal[1],'prox2': proxSensorsVal[2],'prox3': proxSensorsVal[3],'prox4': proxSensorsVal[4],'prox5': proxSensorsVal[5],'prox6': proxSensorsVal[6]})
    if groundBool:
        network.GetVariable("thymio-II", "prox.ground.delta",reply_handler=get_variables_reply_delta,error_handler=get_variables_error)
        s.sensorupdate({'delta0':groundDeltaVal[0],'delta1':groundDeltaVal[1]})
    if accBool:
        network.GetVariable("thymio-II", "acc",reply_handler=get_variables_reply_acc,error_handler=get_variables_error)
        s.sensorupdate({'acc0':accVal[0],'acc1':accVal[1],'acc2':accVal[2]})
    #output for degugging
    #print proxSensorsVal[0],proxSensorsVal[1],proxSensorsVal[2],proxSensorsVal[3],proxSensorsVal[4],proxSensorsVal[5],proxSensorsVal[6]
    #print groundDeltaVal[0], groundDeltaVal[1]
    #print accVal[0], accVal[1], accVal[2]
    
    #tell scratch to update arrays of variables             
    s.broadcast("setprox")
    #respond to commands
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
    else:
            #set the motors to 0 if there is no command
            network.SetVariable("thymio-II", "motor.left.target", [0])
            network.SetVariable("thymio-II", "motor.right.target", [0])   
    return True

if __name__ == '__main__':
    #ask the user what they want to use
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
    #create connection to scratch
    s = scratch.Scratch(host = 'localhost')
    #initialise sensor variables to scratch
    s.sensorupdate({'prox0': '0', 'prox1': '0','prox2': '0','prox3': '0','prox4': '0','prox5': '0','prox6':'0','delta0':'0','delta1':'0','acc0':'0','acc1':'0','acc2':'0'})

    #setup and connect to asebamedulla using dbus
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
    #create the control loop
    handle = gobject.timeout_add(100,thymioControl)
    #start the listener thread and the control loop
    thread.start_new_thread(scratchReceiver,())
    loop.run()
