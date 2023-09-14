import pytz
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_superflat_plan():
    nz_timezone = pytz.timezone("Pacific/Auckland")
    current_weekday = datetime.now(nz_timezone).strftime("%A")
    plan = "flat"
    if current_weekday in ("Friday", "Saturday"):
        plan = "off_peak"
    return plan

def switch(email, password, plan):
    print("Switching plan for", email)
    if plan == "superflat":
        plan = get_superflat_plan()

    if plan not in ("flat", "off_peak"):
        raise Exception("Invalid plan: " + str(plan))

    session = requests.Session()

    url = "https://myflick.flickelectric.co.nz/accounts/plans/edit"
    response = session.get(url)
    assert response.status_code == 200, response.status_code
    assert "https://id.flickelectric.co.nz/identity/oauth/authorize" in response.url, response.url

    # Signing in
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form")
    form_action = form.get("action")
    form_data = {}
    for input_field in form.find_all("input"):
        input_name = input_field.get("name")
        input_value = input_field.get("value")
        form_data[input_name] = input_value
    form_data["user[email]"] = email
    form_data["user[password]"] = password

    response = session.post("https://id.flickelectric.co.nz" + form_action, data=form_data)
    assert response.status_code == 200, response.status_code
    assert "https://myflick.flickelectric.co.nz/accounts/plans/edit" in response.url, response.url

    # Swithcing plan
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form")
    form_action = form.get("action")
    form_data = {}
    for input_field in form.find_all("input"):
        input_name = input_field.get("name")
        input_value = input_field.get("value")
        if input_name == "plan_id" and input_field.get("data-product") != plan:
            continue
        form_data[input_name] = input_value
    assert "plan_id" in form_data

    response = session.patch("https://myflick.flickelectric.co.nz" + form_action, data=form_data)
    assert response.status_code == 200, response.status_code

    print("Switched to", plan.upper(), "plan (effect tomorrow)")
    return plan