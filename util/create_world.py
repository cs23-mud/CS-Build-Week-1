from django.contrib.auth.models import User
from adventure.models import Player, World

Room.objects.all().delete()

w = World()
num_rooms = 100
width = 10
height = 10
grid = w.generate_rooms(width, height, num_rooms)
w.print_rooms(grid)


players = Player.objects.all()
for p in players:
    p.currentRoom = grid[0][0].id
    p.save()
