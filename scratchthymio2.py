import dbus
import dbus.mainloop.glib
import gobject
import sys
import time
import scratch
import thread

from optparse import OptionParser
#store the current task
broad = 'null'
#store the input from the thymio front sensors
proxSensorsVal=[0,0,0,0,0]

def dbusReply():
    pass

def dbusError(e):
    print 'error %s'
    print str(e)
#function to deal with recieving commands from scratch
def scratchReceive():
    #loop forever
    while True:
        #waits until a command is received
        res = s.receive()
        #check if its one of the presets
        for r in res:
            if r == 'forward':
                #set broad(cast) variable for the other thread to use
                global broad
                broad = r
                #run the command for 1 second
                time.sleep(1)
                broad = 'null'
            if r == 'left':
                global broad 
                broad = r
                time.sleep(0.2)
                broad = 'null'
            if r == 'right':
                global broad 
                broad = r
                time.sleep(0.2)
                broad = 'null'
            if r == 'back':
                global broad 
                broad = r
                time.sleep(1)
                broad = 'null'
            #print the current command for debugging
            print r

def thymioscratchcontrol():
    #get the values of the sensors
    network.GetVariable("thymio-II", "prox.horizontal",reply_handler=get_variables_reply,error_handler=get_variables_error)
 
    #print the proximity sensors value in the terminal
    print proxSensorsVal[0],proxSensorsVal[1],proxSensorsVal[2],proxSensorsVal[3],proxSensorsVal[4]
    #update scratch
    s.sensorupdate({'prox0': proxSensorsVal[0], 'prox1': proxSensorsVal[1],'prox2': proxSensorsVal[2],'prox3': proxSensorsVal[3],'prox4': proxSensorsVal[4]})
    #broadcast to scratch to update the sensors
    s.broadcast("setprox")
    #print the current command for debugging
    print broad
    #run the apropriate command that is recieved from scratch in the other thread
    if broad == "forward":
	    network.SetVariable("thymio-II", "motor.left.target", [300])
            network.SetVariable("thymio-II", "motor.right.target", [300])
    elif broad == "left":
	    network.SetVariable("thymio-II", "motor.left.target", [-300])
            network.SetVariable("thymio-II", "motor.right.target", [300])
    elif broad == "right":
	    network.SetVariable("thymio-II", "motor.left.target", [300])
            network.SetVariable("thymio-II", "motor.right.target", [-300])
    elif broad == "back":
	    network.SetVariable("thymio-II", "motor.left.target", [-300])
            network.SetVariable("thymio-II", "motor.right.target", [-300])
    else:
            #set the motors to 0 if there is no command
            network.SetVariable("thymio-II", "motor.left.target", [0])
            network.SetVariable("thymio-II", "motor.right.target", [0])
    return True
 
def get_variables_reply(r):
    global proxSensorsVal
    proxSensorsVal=r
 
def get_variables_error(e):
    print 'error:'
    print str(e)
    loop.quit()
 
if __name__ == '__main__':
    #using scratchpy set the host for the scratch connection
    s = scratch.Scratch(host='localhost')
    #tell scratch to use these sensors
    s.sensorupdate({'prox0': '0', 'prox1': '0','prox2': '0','prox3': '0','prox4': '0'})
    
    parser = OptionParser()
    parser.add_option("-s", "--system", action="store_true", dest="system", default=False,help="use the system bus instead of the session bus")
 
    (options, args) = parser.parse_args()
 
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
 
    if options.system:
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()
 
    #Create Aseba network 
    network = dbus.Interface(bus.get_object('ch.epfl.mobots.Aseba', '/'), dbus_interface='ch.epfl.mobots.AsebaNetwork')
 
    #print in the terminal the name of each Aseba NOde
    print network.GetNodesList()  
    #GObject loop
    #print 'starting loop'
    loop = gobject.MainLoop()
    #call the callback of Braitenberg algorithm
    handle = gobject.timeout_add (100, thymioscratchcontrol) #every 0.1 sec
    #create a new thread to listen for commands from scratch
    thread.start_new_thread(scratchReceive,())
    loop.run()


