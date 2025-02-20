import lib.parkrun_api.parkrun_api as parkrun

countries = parkrun.Country.GetAllCountries()
print([country.url for country in countries])

events = parkrun.Event.GetAllEvents()
print([(event.latitude, event.longitude) for event in events])