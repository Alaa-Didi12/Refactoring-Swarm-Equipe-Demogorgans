import sys

def process_data(data):
    results=[]
    for item in data:
        if item>0:
            results.append(item*2)
    return results

class DataProcessor:
    def __init__(self,name):
        self.name=name
        self.data=[]
    
    def add_data(self,value):
        self.data.append(value)
    
    def process(self):
        return process_data(self.data)
    
    def print_results(self):
        for i in self.process():
            print(i)

def validate_input(x):
    if type(x)==int:
        return True
    return False