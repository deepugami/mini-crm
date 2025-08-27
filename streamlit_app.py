import streamlit as st
import requests
from typing import Optional

st.set_page_config(page_title="Mini CRM Demo", layout="wide")

st.title("Mini CRM Demo")

api_base = st.sidebar.text_input("API base URL", value="http://localhost:8000")

st.sidebar.markdown("### Auth")
username = st.sidebar.text_input("Username", value="admin")
password = st.sidebar.text_input("Password", value="password", type="password")

@st.cache_data(ttl=300)
def get_token(api_base: str, username: str, password: str) -> Optional[str]:
	try:
		resp = requests.post(f"{api_base}/auth/token", data={"username": username, "password": password})
		if resp.status_code == 200:
			return resp.json().get("token")
		return None
	except Exception:
		return None

if st.sidebar.button("Get Token"):
	token = get_token(api_base, username, password)
	if token:
		st.sidebar.success("Token acquired")
		st.session_state["token"] = token
	else:
		st.sidebar.error("Failed to get token")

auth_token = st.session_state.get("token", "demo-token")
headers = {"Authorization": f"Bearer {auth_token}"}

st.header("Create Contact")
with st.form("create_contact"):
	name = st.text_input("Name", value="Riya Singh")
	phone = st.text_input("Phone", value="9123456789")
	email = st.text_input("Email", value="riya@example.com")
	company = st.text_input("Company", value="Riya's Store")
	sub = st.form_submit_button("Create Contact")
	if sub:
		resp = requests.post(f"{api_base}/contacts/", json={
			"name": name,
			"phone": phone,
			"email": email or None,
			"company": company or None,
		}, headers=headers)
		if resp.status_code in (200,201):
			st.success(f"Created contact: {resp.json()['id']}")
			st.session_state["last_contact_id"] = resp.json()["id"]
		else:
			st.error(resp.text)

st.header("Create Lead")
last_contact_id = st.session_state.get("last_contact_id", "")
with st.form("create_lead"):
	contact_id = st.text_input("Contact ID", value=last_contact_id)
	source = st.selectbox("Source", options=["organic", "ad", "referral", "manual"], index=0)
	assigned_to = st.text_input("Assigned To", value="me")
	notes = st.text_area("Notes", value="Walk-in - interested in WhatsApp commerce")
	sub = st.form_submit_button("Create Lead")
	if sub:
		resp = requests.post(f"{api_base}/leads/", json={
			"contact_id": contact_id,
			"source": source,
			"assigned_to": assigned_to,
			"notes": notes or None,
		}, headers=headers)
		if resp.status_code in (200,201):
			st.success(f"Created lead: {resp.json()['id']}")
			st.session_state["last_lead_id"] = resp.json()["id"]
		else:
			st.error(resp.text)

st.header("Leads")
status_filter = st.selectbox("Filter by status", options=["", "new", "contacted", "qualified", "unqualified"], index=0)
params = {}
if status_filter:
	params["status"] = status_filter
try:
	resp = requests.get(f"{api_base}/leads/", params=params, headers=headers)
	if resp.status_code == 200:
		leads = resp.json()
		st.write(leads)
	else:
		st.warning(resp.text)
except Exception as e:
	st.warning(str(e))

st.header("Update Lead Status")
lead_id = st.text_input("Lead ID", value=st.session_state.get("last_lead_id", ""))
new_status = st.selectbox("New Status", options=["new", "contacted", "qualified", "unqualified"], index=1)
if st.button("Update Status"):
	resp = requests.patch(f"{api_base}/leads/{lead_id}", json={"status": new_status}, headers=headers)
	if resp.status_code == 200:
		st.success("Lead updated")
	else:
		st.error(resp.text)
