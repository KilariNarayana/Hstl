import FreeSimpleGUI as sg
import function as fc
import time

sg.theme("Black")
clock=sg.Text("",key="clock")

label=sg.Text("Type in a to-do")
input_box=sg.InputText(tooltip="Enter a to do",key="todo")
add_button=sg.Button("Add")

list_box=sg.Listbox(values=fc.get_todos(),key="todos",enable_events=True,size=[45,15])
edit_button=sg.Button("Edit")
complete_button=sg.Button("Complete")
exit_button=sg.Button("Exit")

window=sg.Window("My To Do App",
                 layout=[[clock],
                         [label],
                         [input_box,add_button],
                         [list_box,edit_button,complete_button],
                         [exit_button]],
                 font=("Helvetica",20))


while True:
    event, values = window.read(timeout=200)
    window["clock"].update(value=time.strftime("%b %m,%Y %H:%M:%S"))
    match event:
        case "Add":
            add_to_do=values["todo"] + "\n"
            todos=fc.get_todos()
            todos.append(add_to_do)
            fc.write_todos(todos)
            window["todos"].update(values=todos)
            window["todo"].update(value="")
        case "Edit":
            try:
                edit_to_do=values["todos"][0]
                new_to_do=values["todo"].replace("\n","")
                print(new_to_do)
                todos=fc.get_todos()
                index=todos.index(edit_to_do)
                todos[index]=new_to_do
                fc.write_todos(todos)
                window["todos"].update(values=todos)
            except IndexError:
                sg.popup("Select the edit item first",font=("Helvetica",20))
        case "Complete":
            try:
                com_to_do=values["todos"][0]
                todos=fc.get_todos()
                todos.remove(com_to_do)
                fc.write_todos(todos)
                window["todos"].update(values=todos)
                window["todo"].update(value="")
            except IndexError:
                sg.popup("Select the complete item first",font=("Helvetica",20))
        case "Exit":
            break
        case "todos":
            window["todo"].update(value=values["todos"][0])
        case sg.WINDOW_CLOSED:
            break





window.close()




