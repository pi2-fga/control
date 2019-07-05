import math
from gaia_router.map_route.map_route import MapRouter as Router
from gaia_router.macros import GPS_PRECISION
from gaia_communication import gaia_communication
import time
import os

TIME_BETWEEN_STOPS = "1"
MESSAGE_START_SIGNAL = "i"


def get_boat_evasion():
    status = input("Should i evade ? ")
    return status


def get_gps_position():
    os.system("sudo gpsd /dev/serial0 -F /var/run/gpsd.sock")
    lat, lon, speed = get_gps_position()
    os.system("sudo killall gpsd")
    return (lat, lon)


def send_activate_collection(activate_collection):
    print("esteira ativada ", activate_collection)
    if(activate_collection):
        message = '1,'
    else:
        message = '0,'

def send_angle(new_direction):
    print("sending angle", new_direction)
    message = str(new_direction)+','
    return message

def send_point(point_lat, point_long):
    message = str(point_lat) +','
    message += str(point_lang) +','
    return message

def send_go(go):
    sendprint("sending go",go)
    if(go):
        message = '1,'
    else:
        message = '0,'
    return message


class GaiaControl():

    def __init__(self):

        gaia_communication.open_serial_port()

        self.recive_first_message()

        self.route = self.router.trace_collection_route()
        self.state = 'collecting'
        self.was_collecting = False
        self.was_returning = False
        self.activate_collection = True

    def send_information(self):
        message = send_go(self.go)
        message += send_point(self.current_position[0],self.current_position[1])
        message += send_angle(self.angle_to_send)
        message += send_activate_collection(self.activate_collection)
        gaia_communication.data_sender(message)
        if(self.go = True):
            time.sleep(TIME_BETWEEN_STOPS)
            self.go = False
            self.send_information()

    def recive_first_message(self):
        gaia_communication.data_sender(MESSAGE_START_SIGNAL)
        message = gaia_communication.data_receiver()
        message = message.split(',')
        self.current_position = get_gps_position()

        self.router = Router((float(message[0]), float(message[1])), (float(message[2]), float(message[3])), self.current_position, self.current_position)
        self.direction = float(message[4])

    def recive_message():
        gaia_communication.data_sender(MESSAGE_START_SIGNAL)    
        gaia_communication.data_sender()
        message = gaia_communication.data_receiver()
        message = message.split(',')
        if(int(message[0]) == 1):
            is_too_heavy = True
        else:
            is_too_heavy = False
        distance = int(message[1])
        if(distance>4 and distance <15):
            is_full = True
        else:
            is_full = False
        self.status = is_full or is_too_heavy
        self.direction = message[2]

    def run(self):
        while(self.state != 'final'):
            self.send_information()
            if(self.state == 'collecting'):
                self.collecting()
            elif(self.state == 'evading'):
                self.evading()
            elif(self.state == 'returning_to_base'):
                self.returning_to_base()
            elif(self.state == 'waiting'):
                self.waiting()
            else:
                self.state = 'final'

    # This method is responsible to control the boat actions when in route
    def in_route(self):

        # TODO change this method to the eletronic method
        self.current_position = get_gps_position()
        
        evasion = get_boat_evasion()

        self.position_to_send=self.current_position
        self.angle_to_send=0
        self.activate_collection = self.activate_collection
        self.go = False

        print('gps return - ', self.current_position)
        self.router.current_position = self.current_position

        # TODO change to the communication method that gets
        # this information from eletronic

        if(self.status == 'yes' and (self.state != 'returning_to_base')):
            if(self.state == "collecting"):
                self.was_collecting = True
                self.current_position
                self.route = [self.current_position] + self.route
                self.collection_route = self.route
                self.activate_collection = False
            self.route = self.router.trace_route_to_base() + self.route
            self.state = 'returning_to_base'
            return
        
        new_direction = self.direction_change_angle()
        direction_diference = new_direction - self.direction
        print("---", new_direction, "---", self.direction)
        if(direction_diference != 0):
            if(direction_diference > 0):
                direction_diference += (2*math.pi)
            # TODO change to the communication method that
            # sends this information to eletronic
            # TODO wait for the response
            self.angle_to_send = float(direction_diference)
            self.direction = new_direction
            return

        # TODO change to the communication method that gets
        # this information from eletronic

        if(evasion == 'yes' and (self.state != 'evading')):
            if(self.state == "returning_to_base"):
                self.was_returning = True
                self.return_route = self.route
            elif(self.state == "collecting"):
                self.was_collecting = True
                self.collection_route = self.route
            self.state = 'evading'
            self.route = self.router.trace_evasion_route(
                self.route, self.direction)
            return

        # TODO change to the communication method that
        # sends this information to eletronic
        # TODO wait for the response
        print(self.current_position, type(self.current_position))
        print(self.route[0], type(self.route[0]))

        # chage this method to return only the real distance
        dist = (Router._calculate_real_distance(
            self.current_position, self.route[0]))[0]

        if(dist <= GPS_PRECISION):
            self.route.pop(0)
            return
        self.go=True

    # method responsible to control the boat when in the default collection
    # route
    def collecting(self):
        if(self.route == []):
            self.state = 'returning_to_base'
        self.in_route()

    # method responsible to control the boat when in tracing a evasion route
    def evading(self):

        if(self.route == []):
            if(self.was_returning):
                self.state = "returning_to_base"
                self.route = self.return_route
                self.was_returning = False
                self.return_route = []
            elif(self.was_collecting):
                self.state = "collecting"
                self.route = self.collection_route
                self. was_collecting = False
                self.collection_route = []
            return
        self.in_route()

    # method responsible to control the boat when going to base
    def returning_to_base(self):
        if(self.route == []):
            self.state = "waiting"
            return
        self.in_route()

    # method responsible to control the boat when in waiting
    def waiting(self):
        # wait signal

        signal = input("signal? ")
        if(signal != "end" and self.was_collecting):
            self.state = "collecting"
            self.route = self.collection_route
            self. was_collecting = False
            self.collection_route = []
        else:
            self.state = "final"

    def direction_change_angle(self):

        x0 = self.router.current_position[0]
        y0 = self.router.current_position[1]
        x1 = self.route[0][0]
        y1 = self.route[0][1]

        dist_x = x1 - x0
        dist_y = y1 - y0

        if(dist_x == 0 and dist_y == 0):
            return self.direction

        if(dist_x == 0):
            if(dist_y > 0):
                return math.pi/2
            else:
                return 3*math.pi/2

        if(dist_y == 0):
            if(dist_x > 0):
                return 0
            else:
                return math.pi

        tg = abs(dist_y/dist_x)
        angle = math.atan(tg)
        if(dist_x > 0):
            if(dist_y > 0):
                return angle
            else:
                return angle + (3*math.pi/4)
        else:
            if(dist_y > 0):
                return angle + math.pi/2
            else:
                return angle + math.pi/4

        return angle


if __name__ == '__main__':
    control = GaiaControl()
    control.run()
