import sys
import os

from surp.src.simulation.vice_to_json import json_output


directory = sys.argv[1]

for name in os.listdir(directory):
    if name[-5:] == ".vice":
        print("pickle thyme")
        print(name)
        json_name = directory +  name[:-5] + ".json"
        file_name = directory + name
        print(file_name)
        json_output(file_name, json_name = json_name)
