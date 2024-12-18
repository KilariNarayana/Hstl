import FreeSimpleGUI as sg



label=sg.Text("Type in a to-do")
input_box=sg.InputText()
add_button=sg.Button("Add")

window=sg.Window("My To DO App",layout=[[label],[input_box,add_button]])
window.read()
window.close()



