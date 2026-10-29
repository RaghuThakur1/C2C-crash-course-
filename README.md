# C2C-crash-course-

## Club sign-up app

The app runs locally with SQLite by default. Local mode is not shared. To share
the app with authenticated users and explicitly grant view or edit access,
connect it to Supabase:

1. Create a Supabase project and enable email/password sign-in. Require email
   confirmation if appropriate for your users.
2. In the Supabase SQL Editor, run [`supabase/schema.sql`](./supabase/schema.sql).
3. Configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` as environment variables,
   or add them to `.streamlit/secrets.toml`:

   ```toml
   SUPABASE_URL=https://nbiqyozkubafebzdleks.supabase.co
   SUPABASE_PUBLISHABLE_KEY=sb_publishable_ynQn4p5aBqDbL7H_SzSshw_Cz5-A5aX
   ```

   Never put a Supabase service-role key in the app or its repository. The app
   uses the public anon key with authenticated user sessions; row-level security
   enforces read and write permissions in the database.
4. Install dependencies with `pip install -r requirements.txt`. For local
   testing, start the app with `streamlit run full-stack.py`. To share it,
   deploy `full-stack.py` to a Streamlit host (for example Streamlit Community
   Cloud) and add the two settings above using the host's secret settings.
   Never commit `.streamlit/secrets.toml`.
5. Users can create accounts and sign in, but cannot view records until the
   owner grants them view-only or edit access. Editors can add, change, and
   delete sign-ups. The app enforces these permissions in Supabase row-level
   security, not just in its interface.
6. To initialize the first owner, create and confirm your account, find its
   user ID under **Authentication → Users** in Supabase, then run this in the
   SQL Editor, replacing the placeholder with that UUID:

   ```sql
   insert into public.club_owners (user_id)
   values ('YOUR_AUTH_USER_UUID');
   ```

   Sign in again. The **Manage access** section lets the owner grant view-only
   or edit access, or revoke access, for existing accounts by email.
   Collaborators must create and confirm their account before they can be
   granted access.
7. To copy the current local sign-ups, sign in as an owner/editor while running
   the app in the workspace and use **Import the local SQLite database**. The
   import keeps source IDs and skips already imported records.

Only explicitly granted accounts can view sign-ups; only editors and owners
can change them. Keep the Supabase project private, share the deployed app URL
with intended users, and use the Supabase dashboard to manage accounts.

`clubSignUp.db` remains on your machine but is ignored by Git. Existing Git
history is unchanged; if it contained real student information, review the
repository's access and consider separately cleaning its history.