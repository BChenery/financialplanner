import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Family Finance Portal", page_icon="🔒")

# 1. Load Config
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 2. Setup Authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# 3. Show Login Form
st.title("🔒 Family Portal Login")
name, authentication_status, username = authenticator.login("main")

# 4. Handle Login State
if authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
elif authentication_status is True:
    st.success(f'Welcome back, {name}!')

    st.markdown("### 🧭 Dashboard Navigation")
    st.info("👈 **Select a module from the sidebar menu to begin.**")

    st.markdown("""
    * **💰 Personal Finance:** Track Net Worth, Budget, and Runway.
    * **🇦🇺 Family Legacy:** Plan multi-generational wealth preservation.
    * **🚀 Wealth Accelerator:** Simulate DCA strategies and ROI.
    """)

    authenticator.logout('Logout', 'main')
