from django.shortcuts import render
import requests
from supersecrets import OURA_ACCESS_TOKEN


def home_page(request):

    headers = {
        'Authorization': f'Bearer {OURA_ACCESS_TOKEN}'
    }

    api_base_url = 'https://api.ouraring.com/v2/usercollection/'

    params = {
        'start_date': '2021-06-05',
        'end_date': '2022-06-08'
    }

    response = requests.request('GET', api_base_url+tag, headers=headers, params=params)

    tags_data = response.json()["data"]

    tags_and_days = _get_tags_and_dates_dict(tags_data)

    response = requests.request('GET', api_base_url + "heartrate", headers=headers, params=params)
    heart_rate_data = response.json()["data"]

    data = {"tags_days": tags_and_days,
            "tags_data": tags_data,
            "heart_rate_data": heart_rate_data}
    return render(request, "homepage.html", data)


def _get_tags_and_dates_dict(response_data):
    # flat_list = [x for xs in xss for x in xs]
    all_tags = [entry["tags"] for entry in response_data]
    all_tags_set = set([x for xs in all_tags for x in xs])

    all_text_set = set([entry["text"] for entry in response_data if entry["text"] != ""])

    tags_and_text = set.union(all_tags_set, all_text_set)

    tags_and_dates = {}
    for tag in tags_and_text:

        for entry in response_data:
            if tag in entry["tags"] or tag == entry["text"]:
                if not tags_and_dates.get(tag):
                    tags_and_dates[tag] = [entry["day"]]
                else:
                    day_list = tags_and_dates[tag]
                    day_list.append(entry["day"])
                    tags_and_dates[tag] = day_list

    return tags_and_dates


def _get_averages(response_data):
    return None
