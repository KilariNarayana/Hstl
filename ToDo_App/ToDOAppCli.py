#from function import get_todos,write_todos
import function
import time

now=time.strftime("%b %m,%Y %H:%M:%S")
print("Date is below")
print("Date and Time",now)

while True:
    user_action = input("Enter todo add, edit, show, done, or exit ")
    user_action = user_action.strip()
    if user_action.startswith("add"):
        todo = user_action[4:]

        todos=function.get_todos()

        todos.append(todo + "\n")

        function.write_todos(todos)

    if user_action.startswith("show"):

        todos=function.get_todos()

        for i, j in enumerate(todos):
            j = j.strip('\n')
            print(f"{i + 1}.{j.capitalize()}")

    if user_action.startswith("edit"):
        try:
            number = int(user_action[4:])

            todos=function.get_todos()

            todos[number - 1] = input("Enter the edit Text here") + "\n"

            function.write_todos(todos)
        except ValueError:
            print("Please enter the integer value")

    if user_action.startswith("done"):

        try:
            number = int(user_action[4:])

            todos=function.get_todos()

            todos.pop(number - 1)

            function.write_todos(todos)
        except IndexError:
            print("Please enter the valid index values")

    if user_action.startswith("exit"):
        break