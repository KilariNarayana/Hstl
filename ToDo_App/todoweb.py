import streamlit as st
import function as fc

todos=fc.get_todos()

def add_todo():
    new_todo=st.session_state["new_todo"] + "\n"
    todos.append(new_todo)
    fc.write_todos(todos)
    st.session_state["new_todo"] = ""


st.title("My Todo App")
st.subheader("This is my todo app")
st.write("This app to increase your productivity.")

for index,todo in enumerate(todos):
    checkbox=st.checkbox(todo,key=todo)
    if checkbox:
        todos.pop(index)
        fc.write_todos(todos)
        del st.session_state[todo]
        st.rerun()
st.text_input(label="",placeholder="Add new todo...",
              on_change=add_todo,key='new_todo')

