from statistics import mean, median, StatisticsError

from django.contrib import messages
from django.shortcuts import render
import requests
from django.conf import settings
from django.utils import timezone
from django.utils.datetime_safe import date
from oura import OuraClientDataFrame
import pandas as pd
from .forms import TagSettingsForm

dateformat = '%Y-%m-%d'

wanted_scores = {
    "SLEEP": [
        "duration_in_hrs",
        "score",
        "temperature_deviation",
        "hr_lowest",
        "hr_average"],
    "READY": [
        "score",
        "score_hrv_balance"],
    "ACTIVITY": []
}


def index(request):
    if request.method == 'POST':
        form = TagSettingsForm(request.POST)
        data = {"form": form}
        if form.is_valid():
            formula = form.cleaned_data.get("formula")
            access_token = form.cleaned_data.get("access_token")
            start_date = form.cleaned_data.get("start_date").strftime(dateformat)
            end_date = form.cleaned_data.get("end_date").strftime(dateformat)

            # get some tags from the APIv2
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            api_base_url = 'https://api.ouraring.com/v2/usercollection/'
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            response = requests.request('GET', api_base_url+"tag", headers=headers, params=params)

            if response.status_code == 200:
                tags_data = response.json()["data"]
                tags_and_days = _get_tags_and_dates_dict(tags_data)

                # get some vitals from the API v1
                pd.set_option('display.max_columns', None)
                client = OuraClientDataFrame(personal_access_token=access_token)
                df = client.combined_df_edited(start=start_date, end=end_date)

                # get average scores and differences
                averages = _get_averages(tags_and_days, df, formula)

                data = {"tags_days": tags_and_days,
                        "tags_data": tags_data,
                        "available_scores": wanted_scores,
                        "averages": averages,
                        "form": form}
            else:
                messages.error(request, "Couldn't get data from Oura API, did you give the right access token?")

    else:
        end_date = timezone.now() - timezone.timedelta(days=1)
        start_date = timezone.now() - timezone.timedelta(days=365)
        form = TagSettingsForm(request.GET, initial={'start_date': start_date,
                                                     'end_date': end_date})
        data = {"form": form}
    return render(request, "index.html", data)


def _get_tags_and_dates_dict(response_data):
    """
    Returns dict of tags/notes with a list of dates when they have been used
    {
        'tag_sleep_alcohol': ['2021-12-06', '2021-12-24'],
        'Super duper relaxed': ['2021-12-25']
    }
    """

    # flat_list = [x for xs in xss for x in xs]
    all_tags = [entry["tags"] for entry in response_data]
    all_tags_set = set([x for xs in all_tags for x in xs])

    all_text_set = set([entry["text"] for entry in response_data if entry["text"] != ""])

    tags_and_text = set.union(all_tags_set, all_text_set)

    tags_and_dates = {}
    for tag in tags_and_text:
        if tag:
            for entry in response_data:
                if tag in entry["tags"] or tag == entry["text"]:
                    if not tags_and_dates.get(tag):
                        tags_and_dates[tag] = [entry["day"]]
                    else:
                        day_list = tags_and_dates[tag]
                        day_list.append(entry["day"])
                        tags_and_dates[tag] = day_list

    return tags_and_dates


def _get_averages(tags_and_days, df, formula="mean"):
    """
    Returns a dict of tags and averages for each metric and differences between wanted averages.
    e.g.
    {'tag_generic_cold':
        {'averages':
            {'SLEEP':
                {'duration_in_hrs':
                    {'average_all': 8.36787221217601,
                     '-1': {'average': 7.441666666666666,
                            'all_diff': -0.9262055455093439},
                     '0': {'average': 7.454166666666667,
                           'all_diff': -0.9137055455093437},
                     '1': {'average': 7.433333333333334,
                           'all_diff': -0.9345388788426767}},
                     'score': {'average_all': 72.7377938517179,
                               '-1': {'average': 71,
                                      'all_diff': -1.7377938517178961},
                               '0': {'average': 73,
                                     'all_diff': 0.26220614828210387},
                               '1': {'average': 70, ...
    """

    averages = {}
    # at least for sleep and readiness data it seems to be the case that the data of the upcoming night
    # is saved in the "day before". So sleep and readiness data you see in the app on date 2022-06-07 is entered
    # in 2022-06-06

    wanted_days = [-1, 0, 1]

    for tag in tags_and_days.keys():
        averages[tag] = {"averages": {}}
        for parent, scores in wanted_scores.items():
            averages[tag]["averages"][parent] = {}
            for t in scores:
                if formula == "mean":
                    average_all = df[f"{parent}:{t}"].mean()
                else:
                    average_all = df[f"{parent}:{t}"].median()
                averages[tag]["averages"][parent][t] = {"average_all": average_all}

                for d in wanted_days:
                    day_scores = []
                    for day in tags_and_days[tag]:
                        try:
                            day_score = df[f"{parent}:{t}"].loc[
                                date.fromisoformat(day) + timezone.timedelta(days=d)]
                            day_scores.append(day_score)
                        except KeyError:
                            pass

                    if len(day_scores) > 0:
                        if formula == "mean":
                            day_average = mean(day_scores)
                        else:
                            day_average = median(day_scores)
                    else:
                        day_average = None

                    all_diff = day_average - average_all if day_average else None
                    averages[tag]["averages"][parent][t][f"{d}"] = {
                        "average": day_average,
                        "all_diff": all_diff
                    }
    return averages
