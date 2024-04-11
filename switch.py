import pytz
import requests
import base64
import hashlib
import html
import json
import os
import re
import urllib.parse
import datetime
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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

    nz_timezone = pytz.timezone('Pacific/Auckland')
    redirect_uri = "https://dashboard.flickelectric.co.nz/auth/callback"
    client_id = "dms9ggo44k101o4b31j4zlb60w22mbr"
    state = "fooobarbaz"
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    code_challenge, len(code_challenge)

    session = requests.Session()

    print("Visiting sign in page")
    # https://www.stefaanlippens.net/oauth-code-flow-pkce.html
    url = "https://api.flick.energy/identity/users/sign_in"
    url += "?client_id=" + client_id 
    url += "&code_challenge=" + code_challenge 
    url += "&code_challenge_method=S256" 
    url += "&redirect_uri=" + urllib.parse.quote(redirect_uri)
    url += "&response_type=code" 
    url += "&state=" + state
    response = session.get(url)
    assert response.status_code == 200, response.status_code
    assert "https://api.flick.energy/identity/users/sign_in" in response.url, response.url

    print("Signing in")
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
    response = session.post(url, data=form_data, allow_redirects=False)
    assert response.status_code == 302, response.status_code

    print("Getting token")
    url = "https://api.flick.energy/identity/oauth/token"
    form_data = {}
    form_data["code"] = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers['Location']).query)['code'][0]
    form_data["grant_type"] = "authorization_code"
    form_data["redirect_uri"] = redirect_uri
    form_data["client_id"] = client_id
    form_data["code_verifier"] = code_verifier
    response = session.post(url, data=form_data)
    assert response.status_code == 200, response.status_code

    print("Getting account info")
    url = "https://api.flick.energy/customer/user_accounts_info"
    id_token =response.json()["id_token"]
    response = requests.get(url, headers={"Authorization":"Bearer " + id_token})
    assert response.status_code == 200, response.status_code
    attributes = response.json()["data"][0]["attributes"]
    party_ref = "/customer/customers/" + attributes["main_customer"]
    supply_node_ref = attributes["supply_node_ref"]

    print("Getting plans")
    url = "https://api.flick.energy/contract_manager/plans"
    url += "?as_at=" + urllib.parse.quote(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z')
    url += "&brand=" + "flick"
    url += "&existing_customer_plans=" + "true"
    url += "&party_ref=" + urllib.parse.quote(party_ref)
    url += "&supply_node_ref=" + urllib.parse.quote(supply_node_ref)
    response = requests.get(url, headers={"Authorization":"Bearer " + id_token})
    assert response.status_code == 200, response.status_code

    print("Getting plan id")
    product_id = None
    for item in response.json()['included']:
        if item['attributes']['code'] == plan:
            product_id = item['id']
            break
    assert product_id is not None, "product_id not found"
    plan_id = None
    for item in response.json()['data']:
        if item['relationships']['product']['data']['id'] == product_id:
            print(item['attributes']['name'])
            plan_id = item['id']
            break
    assert plan_id is not None, "product_id not found"

    print("Switcing plan")
    next_midnight = (datetime.now(nz_timezone) + timedelta(days=1)) \
        .replace(hour=0, minute=0, second=0, microsecond=0) \
        .astimezone(pytz.utc)
    url = "https://api.flick.energy/contract_manager/create_contracts"
    url += "?start_at=" + urllib.parse.quote(next_midnight.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z')
    url += "&plan_id=" + plan_id
    url += "&party_ref=" + urllib.parse.quote(party_ref)
    url += "&supply_node_ref=" + urllib.parse.quote(supply_node_ref)
    response = requests.post(url, headers={"Authorization":"Bearer " + id_token})
    assert response.status_code == 201, response.status_code
    assert plan in response.text, response.text

    print("Switched to", plan.upper(), "plan (effect tomorrow)")
    return plan