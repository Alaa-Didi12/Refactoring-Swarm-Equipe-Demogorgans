# Messy calculator module with bugs and poor style

def add(x,y):
    return x+y

def subtract(a,b):
    result=a-b
    return result

def multiply(num1,num2):
    product=num1*num2
    return product

def divide(x,y):
    return x/y

class calculator:
    def __init__(self):
        self.history=[]
    
    def calculate(self,op,a,b):
        if op=='add':
            result=add(a,b)
        elif op=='subtract':
            result=subtract(a,b)
        elif op=='multiply':
            result=multiply(a,b)
        elif op=='divide':
            result=divide(a,b)
        else:
            result=None
        self.history.append(result)
        return result
    
    def get_history(self):
        return self.history

def main():
    calc=calculator()
    print(calc.calculate('add',5,3))
    print(calc.calculate('divide',10,0))

if __name__=='__main__':
    main()