import os
import sqlite3
import streamlit as st
from postgrest.exceptions import APIError
from supabase import create_client
from supabase_auth.errors import AuthApiError

DB_FILES = "clubSignUp.db"
CLUBS_LIST = [
    "",
    "Art Club",
    "Music Club",
    "Drama Club",
    "Sports Club",
    "Science Club",
    "Math Club",
    "Literature Club",
    "Debate Club",
    "Photography Club",
    "Coding Club",
]


def setting(name):
    try:
        value = st.secrets.get(name)
    except FileNotFoundError:
        value = None
    return value or os.environ.get(name)


def club_db():
    conn = sqlite3.connect(DB_FILES)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS club_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            club_name TEXT
        )"""
    )
    conn.commit()
    conn.close()


def cloud_user(client):
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")
    if access and refresh:
        try:
            response = client.auth.set_session(access, refresh)
            if response.session:
                st.session_state["access_token"] = response.session.access_token
                st.session_state["refresh_token"] = response.session.refresh_token
                user = client.auth.get_user()
                return user.user if user else None
        except AuthApiError as exc:
            st.session_state.pop("access_token", None)
            st.session_state.pop("refresh_token", None)
            st.error(f"Your session expired. Please sign in again: {exc}")
            return None

    action = st.radio("Account", ["Sign in", "Create account"], horizontal=True)
    with st.form("account_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(action)
    if submitted:
        try:
            if action == "Sign in":
                response = client.auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
            else:
                response = client.auth.sign_up(
                    {"email": email.strip(), "password": password}
                )
            if response.session:
                st.session_state["access_token"] = response.session.access_token
                st.session_state["refresh_token"] = response.session.refresh_token
                st.rerun()
            st.info("Account created. Confirm your email, then sign in.")
        except AuthApiError as exc:
            st.error(f"Could not authenticate: {exc}")
    return None


def main():
    st.title("Club Sign-Up Form")
    st.subheader("Please fill out the form below to sign up for a club.")

    url, key = setting("SUPABASE_URL"), setting("SUPABASE_ANON_KEY")
    client, can_edit, can_view, is_owner = None, True, True, False
    if url or key:
        if not url or not key:
            st.error("Set both SUPABASE_URL and SUPABASE_ANON_KEY.")
            return
        client = create_client(url, key)
        user = cloud_user(client)
        if not user:
            return
        st.caption(f"Signed in as {user.email}")
        if st.button("Sign out"):
            client.auth.sign_out()
            st.session_state.pop("access_token", None)
            st.session_state.pop("refresh_token", None)
            st.rerun()
        try:
            access = (
                client.table("club_members")
                .select("access_level")
                .eq("user_id", user.id)
                .execute()
                .data
            )
            is_owner = bool(
                client.table("club_owners")
                .select("user_id")
                .eq("user_id", user.id)
                .execute()
                .data
            )
        except APIError as exc:
            st.error(f"Could not check your access: {exc}")
            return
        role = access[0]["access_level"] if access else None
        can_view = is_owner or role in ("viewer", "editor")
        can_edit = is_owner or role == "editor"

        if is_owner:
            with st.expander("Manage collaborator access"):
                with st.form("access_form"):
                    email = st.text_input("Collaborator account email")
                    permission = st.selectbox(
                        "Permission", ["View only", "Can edit", "Revoke access"]
                    )
                    change = st.form_submit_button("Save")
                if change:
                    try:
                        client.rpc(
                            "set_club_access",
                            {
                                "member_email": email.strip(),
                                "requested_access": {
                                    "View only": "viewer",
                                    "Can edit": "editor",
                                    "Revoke access": "none",
                                }[permission],
                            },
                        ).execute()
                        st.success("Collaborator access updated.")
                    except APIError as exc:
                        st.error(f"Could not update access: {exc}")
        if not can_view:
            st.info("Ask the owner to grant your account access.")
            return
        if not can_edit:
            st.info("View-only access.")
    else:
        st.warning("Local SQLite mode is not shared. Add Supabase settings to share.")
        club_db()

    if can_edit:
        with st.form("club_signup_form", clear_on_submit=True):
            student_id = st.text_input("Student ID: ")
            student_name = st.text_input("Student Name: ")
            club_name = st.selectbox("Select Club", CLUBS_LIST)
            submit_button = st.form_submit_button("Sign Up")
        if submit_button:
            if student_id and student_name and club_name:
                try:
                    if client:
                        client.table("club_signups").insert(
                            {
                                "student_id": student_id,
                                "student_name": student_name,
                                "club_name": club_name,
                            }
                        ).execute()
                    else:
                        conn = sqlite3.connect(DB_FILES)
                        conn.execute(
                            "INSERT INTO club_signups "
                            "(student_id, student_name, club_name) VALUES (?, ?, ?)",
                            (student_id, student_name, club_name),
                        )
                        conn.commit()
                        conn.close()
                    st.success(
                        f"Successfully signed up {student_name} for {club_name}!"
                    )
                except (APIError, sqlite3.Error) as exc:
                    st.error(f"Could not save the sign-up: {exc}")
            else:
                st.error("Please fill out all fields before submitting.")

    st.subheader("Current Sign-Ups")
    try:
        if client:
            signups = (
                client.table("club_signups")
                .select("id, student_id, student_name, club_name")
                .order("id")
                .execute()
                .data
            )
        else:
            conn = sqlite3.connect(DB_FILES)
            signups = conn.execute(
                "SELECT id, student_id, student_name, club_name "
                "FROM club_signups ORDER BY id"
            ).fetchall()
            conn.close()
    except (APIError, sqlite3.Error) as exc:
        st.error(f"Could not load sign-ups: {exc}")
        return

    if client and can_edit and os.path.exists(DB_FILES):
        if st.button("Import local SQLite sign-ups"):
            try:
                local = sqlite3.connect(DB_FILES)
                rows = local.execute(
                    "SELECT id, student_id, student_name, club_name "
                    "FROM club_signups"
                ).fetchall()
                local.close()
                existing = client.table("club_signups").select("local_id").execute().data
                imported = {row["local_id"] for row in existing if row["local_id"]}
                rows_to_add = [
                    {
                        "local_id": row[0],
                        "student_id": row[1],
                        "student_name": row[2],
                        "club_name": row[3],
                    }
                    for row in rows
                    if row[0] not in imported
                ]
                if rows_to_add:
                    client.table("club_signups").insert(rows_to_add).execute()
                st.success(f"Imported {len(rows_to_add)} local sign-up(s).")
                st.rerun()
            except (APIError, sqlite3.Error) as exc:
                st.error(f"Could not import local sign-ups: {exc}")

    if signups:
        for signup in signups:
            if isinstance(signup, dict):
                row_id = signup["id"]
                student_id = signup["student_id"]
                student_name = signup["student_name"]
                club_name = signup["club_name"]
            else:
                row_id, student_id, student_name, club_name = signup
            st.write(
                f"ID: {row_id}, Student ID: {student_id}, "
                f"Name: {student_name}, Club: {club_name}"
            )
            st.markdown(
                f"• **{student_name}** (ID: {student_id}) joined **{club_name}**"
            )

        if client and can_edit:
            with st.expander("Edit or delete a sign-up"):
                selected = st.selectbox(
                    "Choose a sign-up",
                    signups,
                    format_func=lambda row: (
                        f"{row['id']}: {row['student_name']} ({row['club_name']})"
                    ),
                )
                clubs = CLUBS_LIST[1:]
                if selected["club_name"] not in clubs:
                    clubs = [selected["club_name"]] + clubs
                with st.form("edit_signup_form"):
                    new_id = st.text_input(
                        "Student ID", value=selected["student_id"] or ""
                    )
                    new_name = st.text_input(
                        "Student Name", value=selected["student_name"] or ""
                    )
                    new_club = st.selectbox(
                        "Club", clubs, index=clubs.index(selected["club_name"])
                    )
                    save = st.form_submit_button("Save changes")
                    delete = st.form_submit_button("Delete sign-up")
                if save:
                    if not new_id.strip() or not new_name.strip():
                        st.error("Please fill out all fields before saving.")
                    else:
                        try:
                            client.table("club_signups").update(
                                {
                                    "student_id": new_id.strip(),
                                    "student_name": new_name.strip(),
                                    "club_name": new_club,
                                }
                            ).eq("id", selected["id"]).execute()
                            st.success("Sign-up updated.")
                            st.rerun()
                        except APIError as exc:
                            st.error(f"Could not update the sign-up: {exc}")
                elif delete:
                    try:
                        client.table("club_signups").delete().eq(
                            "id", selected["id"]
                        ).execute()
                        st.success("Sign-up deleted.")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Could not delete the sign-up: {exc}")
    else:
        st.write("No sign-ups yet.")


if __name__ == "__main__":
    main()
