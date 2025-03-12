import streamlit as st
import send_email as se

st.header("Contact Us")

with st.form(key="email_forms"):
    user_email=st.text_input("Enter your Email!")
    raw_message=st.text_area("Enter your query")
    message=f"""\
Subject: New email from {user_email}

From: {user_email}
{raw_message}
"""
    submit_button=st.form_submit_button("Submit")
    if submit_button:
        se.send_email(message)
        st.info("Email Successfully sent")
