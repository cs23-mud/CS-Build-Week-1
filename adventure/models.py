from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import uuid


class Room(models.Model):
    title = models.CharField(max_length=50, default="DEFAULT TITLE")
    description = models.CharField(
        max_length=500, default="DEFAULT DESCRIPTION")
    n_to = models.IntegerField(default=200)
    s_to = models.IntegerField(default=200)
    e_to = models.IntegerField(default=200)
    w_to = models.IntegerField(default=200)
    # x = models.IntegerField(default=0)
    # y = models.IntegerField(default=0)

    def connectRooms(self, destinationRoom, direction):
        destinationRoomID = destinationRoom.id
        try:
            destinationRoom = Room.objects.get(id=destinationRoomID)
        except Room.DoesNotExist:
            print("That room does not exist")
        else:
            # print(self.id, destinationRoomID, direction)
            if direction == "n":
                self.n_to = destinationRoomID
                destinationRoom.s_to = self.id
            elif direction == "s":
                self.s_to = destinationRoomID
                destinationRoom.n_to = self.id
            elif direction == "e":
                self.e_to = destinationRoomID
                destinationRoom.w_to = self.id
            elif direction == "w":
                self.w_to = destinationRoomID
                destinationRoom.e_to = self.id
            else:
                print("Invalid direction")
                return
            self.save()
            destinationRoom.save()

    def playerNames(self, currentPlayerID):
        return [p.user.username for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]

    def playerUUIDs(self, currentPlayerID):
        return [p.uuid for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currentRoom = models.IntegerField(default=0)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    def initialize(self):
        if self.currentRoom == 0:
            self.currentRoom = Room.objects.first().id
            self.save()

    def room(self):
        try:
            return Room.objects.get(id=self.currentRoom)
        except Room.DoesNotExist:
            self.initialize()
            return self.room()


class World(models.Model):
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)

    def generate_rooms(self, size_x, size_y, num_rooms):
        '''
        Fill up the grid, bottom to top, in a zig-zag pattern
        '''

        # Initialize the grid
        grid = [None] * size_y
        self.width = size_x
        self.height = size_y
        for i in range(len(grid)):
            grid[i] = [None] * size_x

        # Start from lower-left corner (0,0)
        x = -1  # (this will become 0 on the first step)
        y = 0
        room_count = 0

        # Start generating rooms to the east
        direction = 1  # 1: east, -1: west

        # While there are rooms to be created...
        previous_room = None
        while room_count < num_rooms:

            # Calculate the direction of the room to be created
            if direction > 0 and x < size_x - 1:
                room_direction = "e"
                x += 1
            elif direction < 0 and x > 0:
                room_direction = "w"
                x -= 1
            else:
                # If we hit a wall, turn north and reverse direction
                room_direction = "s"
                y += 1
                direction *= -1

            # Create a room in the given direction
            # print(x, y)
            room = Room(room_count, f"Room {room_count}",
                        f"This is room #{room_count}.")
            # Note that in Django, you'll need to save the room after you create it

            # Save the room in the World grid
            grid[y][x] = room

            # Connect the new room to the previous room and save
            if previous_room is not None:
                # print("Room ID: ", room.id, "Previous room id: ",
                #       previous_room.id, "Direction from room to previous: ", room_direction)
                room.connectRooms(previous_room, room_direction)
            else:
                room.save()
            print(
                f"Saving room {room.id}... East: Room {room.e_to} North: Room {room.n_to} West: Room {room.w_to} South: Room {room.s_to}")
            # Update iteration variables
            previous_room = room
            room_count += 1
        return grid

    def print_rooms(self, grid):
        '''
        Print the rooms in room_grid in ascii characters.
        '''

        # Add top border
        map_string = "# " * ((3 + self.width * 5) // 2) + "\n"

        # The console prints top to bottom but our array is arranged
        # bottom to top.
        #
        # We reverse it so it draws in the right direction.
        reverse_grid = list(grid)  # make a copy of the list
        reverse_grid.reverse()
        for row in reverse_grid:
            # PRINT NORTH CONNECTION ROW
            map_string += "#"
            for room in row:
                if room is not None and room.n_to is not None:
                    map_string += "  |  "
                else:
                    map_string += "     "
            map_string += "#\n"
            # PRINT ROOM ROW
            map_string += "#"
            for room in row:
                if room is not None and room.w_to is not None:
                    map_string += "-"
                else:
                    map_string += " "
                if room is not None:
                    map_string += f"{room.id}".zfill(3)
                else:
                    map_string += "   "
                if room is not None and room.e_to is not None:
                    map_string += "-"
                else:
                    map_string += " "
            map_string += "#\n"
            # PRINT SOUTH CONNECTION ROW
            map_string += "#"
            for room in row:
                if room is not None and room.s_to is not None:
                    map_string += "  |  "
                else:
                    map_string += "     "
            map_string += "#\n"

        # Add bottom border
        map_string += "# " * ((3 + self.width * 5) // 2) + "\n"

        # Print string
        # print(map_string)
        return map_string


@receiver(post_save, sender=User)
def create_user_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=instance)
        Token.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_player(sender, instance, **kwargs):
    instance.player.save()
