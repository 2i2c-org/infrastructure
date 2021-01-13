import pytest
import requests
from bs4 import BeautifulSoup


def test_templates_loaded(hub):
    url = f'https://{hub.spec["domain"]}/hub/login'

    response = requests.get(url)
    if hub.spec["template"] == "base-hub":
        expected_logo_img = hub.spec["config"]["jupyterhub"]["homepage"]["templateVars"]["org"]["logo_url"]
    else:
        expected_logo_img = hub.spec["config"]["base-hub"]["jupyterhub"]["homepage"]["templateVars"]["org"]["logo_url"]

    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img')
    for image in images:
        if image.has_attr("class") and image["class"] == "hub-logo":
            assert image['src'] == expected_logo_img
