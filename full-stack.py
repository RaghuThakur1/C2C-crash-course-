import sqlite3
import streamlit as st

DB_FILES="clubSignUp.db"
#AI USE Start :
def club_db():
    conn=sqlite3.connect(DB_FILES)
    cursor=conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS club_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            club_name TEXT
        )
    """)
    conn.commit()
    conn.close()
#AI USE END;
club_db()

CLUBS_LIST=["","Art Club","Music Club","Drama Club","Sports Club","Science Club","Math Club","Literature Club","Debate Club","Photography Club","Coding Club"]
st.title("Club Sign-Up Form")
st.subheader("Please fill out the form below to sign up for a club.")

#AI USE Start :
with st.form("club_signup_form", clear_on_submit=True):
    student_id = st.text_input("Student ID: ")
    student_name = st.text_input("Student Name: ")
    club_name = st.selectbox("Select Club", CLUBS_LIST)
    submit_button = st.form_submit_button("Sign Up")

    if submit_button:
        if student_id and student_name and club_name:
            conn = sqlite3.connect(DB_FILES)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO club_signups (student_id, student_name, club_name) VALUES (?, ?, ?)",
                           (student_id, student_name, club_name))
            conn.commit()
            conn.close()
            st.success(f"Successfully signed up {student_name} for {club_name}!")
        else:
            st.error("Please fill out all fields before submitting.")
st.subheader("Current Sign-Ups")
conn=sqlite3.connect(DB_FILES)
cursor=conn.cursor()
cursor.execute("SELECT * FROM club_signups")
signups=cursor.fetchall()
if signups:
    for signup in signups:
        st.write(f"ID: {signup[0]}, Student ID: {signup[1]}, Name: {signup[2]}, Club: {signup[3]}")
else:
    st.write("No sign-ups yet.")
conn.close()    

if signups:
    for signup in signups:
        # Changed st.write to st.markdown for a cleaner presentation list
        st.markdown(f"• **{signup[2]}** (ID: {signup[1]}) joined **{signup[3]}**")
else:
    st.write("No sign-ups yet.")

#streamlit run full-stack.py
