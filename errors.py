# test_broken_code.py

def divide_numbers(a, b)
    return a / b

def get_user_age():
    age = input("Enter your age: ")
    return age + 5

numbers = [1, 2, 3, 4]

print("Division result:", divide_numbers(10, 0))

print("Your age in 5 years:", get_user_age())

for i in range(len(numbers)):
    print(numbers[i + 1])

data = {
    "name": "Alice",
    "age": 25
}

print(data["email"])
