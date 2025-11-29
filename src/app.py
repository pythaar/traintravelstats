import pandas as pd
import json
from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import faicons as fa
import numpy as np
from ipyleaflet import Map, Marker
import sys
import os
from datetime import datetime, date
GIT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(GIT_PATH)
from config import DB_URL
from src.db_management import TrainsDB

#---------------- TO DO ---------------#
#Voir comment update auto le df pour la selection des données
#Map qui montre les trajets, plus pk pas un dégradé selon le nombre -> construire la database. Utiliser la database from rnf

database = TrainsDB(DB_URL)

unique_years = database.get_years()
unique_types = database.get_companies()
actual_year = datetime.now().year

def get_n_days(annees):
    aujourd_hui = date.today()
    total_jours = 0

    for annee in annees:
        annee = int(annee)
        if annee == 2024:
            debut = date(2024, 12, 13)
            fin = date(2024, 12, 31)
            total_jours += (fin - debut).days + 1
        elif annee < aujourd_hui.year:
            debut = date(annee, 1, 1)
            fin = date(annee, 12, 31)
            total_jours += (fin - debut).days + 1
        elif annee == aujourd_hui.year:
            debut = date(annee, 1, 1)
            total_jours += (aujourd_hui - debut).days + 1

    return total_jours

def get_n_month(annees):
    aujourd_hui = date.today()
    total_month = 0

    for annee in annees:
        annee = int(annee)
        if annee == 2024:
            total_month += 1
        elif annee < aujourd_hui.year:
            total_month += 12
        elif annee == aujourd_hui.year:
            debut = date(annee, 1, 1)
            fin = date(annee, 12, 31)
            n_days_spent = (aujourd_hui - debut).days + 1
            n_days_total = (fin - debut).days + 1
            
            total_month += n_days_spent * 12 / n_days_total

    return total_month

def minToString(minutes):
    heures = int(minutes // 60)
    mins_restantes = int(minutes % 60)
    
    if heures == 0:
        return f"{mins_restantes} mins"
    elif mins_restantes == 0:
        return f"{heures}h"
    else:
        return f"{heures}h {mins_restantes}mins"

def time_to_string(time):
    
    if not time:
        return "No data"
    days = int(time // (24 * 60))
    hours = int((time % (24 * 60)) // 60)
    minutes = int(time % 60)
    if not days and not hours:
        return f"{minutes}mins"
    elif not days:
        return f"{hours}h & {minutes}mins"
    else:
        return f"{days}d, {hours}h & {minutes}mins"    
    
def getOriginDestinationMax(df, column, text, unit):
    
    max_row = df.loc[df[column].idxmax()]
    col_max = max_row[column]
    origine_max = max_row['Origin']
    destination_max = max_row['Destination']
    if unit == 'hm':
        return f"Max {text}: {minToString(col_max)}, during {origine_max} - {destination_max}"
    else:
        return f"Max {text}: {col_max}{unit}, during {origine_max} - {destination_max}"
    
def getOriginDestinationMin(df):
    
    min_row = df.loc[df['Delay'].idxmin()]
    col_min = min_row['Delay']
    origine_min = min_row['Origin']
    destination_min = min_row['Destination']
    return f"Earliest train: {col_min*-1} mins in advance, during {origine_min} - {destination_min}"

def getMaxPerDay(df, column, name, unit):
    
    df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
    dfmax_value = df.groupby('Date', observed=False)[column].sum()
    date_max_value = dfmax_value.idxmax()
    max_value = round(dfmax_value.max(), 3)
    #date_max_distance.strftime('%d/%m/%Y')
    if unit == 'hm':
        return f"Max {name} in a day: {minToString(max_value)}"
    else:
        return f"Max {name} in a day: {max_value}{unit}"
    
    


app_ui = ui.page_fluid(
    ui.layout_sidebar(ui.sidebar(
            ui.input_checkbox_group("years", "Select years", choices=unique_years, selected=[actual_year]),
            ui.input_checkbox_group("company", "Select train company", choices=unique_types, selected=unique_types),
            width=300),
    ui.h1("Personal train stats", style="text-align: center"),
    ui.layout_columns(
        ui.value_box(
            "Number of train taken", ui.output_ui("ntrain"), showcase=fa.icon_svg("train")
        ),
        ui.value_box(
            "Total distance travelled", ui.output_ui("distance"), showcase=fa.icon_svg("route")
        ),
        ui.value_box(
            "Total time in train",
            ui.output_ui("time"),
            showcase=fa.icon_svg("clock", "regular"),
        ),
        fill=False,
    ),
    ui.layout_columns(
        ui.value_box(
            "Average speed", ui.output_ui("speed"), showcase=fa.icon_svg("gauge-high")
        ),
        ui.value_box(
            "Station visited", ui.output_ui("nstation"), showcase=fa.icon_svg("location-dot")
        ),
        ui.value_box(
            "Total delay",
            ui.output_ui("totaldelay"),
            showcase=fa.icon_svg("stopwatch-20"),
        ),
        fill=False,
    ),
    ui.layout_columns(
        ui.value_box(
            "Daily stats", ui.output_ui("daily_distance"),ui.output_ui("daily_time"), showcase=fa.icon_svg("calendar-days")
        ),
        ui.value_box(
            "Weekly stats", ui.output_ui("weekly_distance"),ui.output_ui("weekly_time"), showcase=fa.icon_svg("calendar-week")
        ),
        ui.value_box(
            "Monthly stats", ui.output_ui("monthly_distance"),ui.output_ui("monthly_time"), showcase=fa.icon_svg("calendar")
        ),
        fill=False,
    ),
    ui.layout_columns(ui.output_plot("piedelay"), 
                      #ui.output_plot("delayevolv")
                      ), 
    ui.layout_columns(ui.output_plot("traintaken_pl"), (ui.h2("Global stats", style="text-align: center"), ui.output_data_frame("stat_table"))),
    ui.h2("Visited station map"),
    ui.page_fluid(output_widget("map")),
    #ui.output_text("factos"),
    #ui.output_text("earliest"),
    #ui.output_text("factos1"),
    #ui.output_text("factos2"),
    #ui.output_text("factos3"),
    #ui.output_text("factos4"),
    #ui.output_text("factos5"),
    #ui.output_text("factos6"),
    #ui.output_text("kmperday"),
    #ui.output_text("timeperday"),
    #ui.output_data_frame("compagnytable"),
    
))

# Define the server logic
def server(input, output, session):
    @reactive.calc
    def update_db():
        database.update_filter(input.years(), input.company())

    @output
    @render.text
    def ntrain():
        update_db()
        n_trains = database.get_n_train()
        return n_trains
    
    @output
    @render.text
    def time():
        update_db()
        total_time = database.get_sum('traveltime')
        return time_to_string(total_time)
    
    @output
    @render.text
    def daily_time():
        update_db()
        total_time = database.get_sum('traveltime')
        total_days = get_n_days(input.years())
        return time_to_string(total_time/total_days) if total_days else "0 min"
    
    @output
    @render.text
    def weekly_time():
        update_db()
        total_time = database.get_sum('traveltime')
        total_week = get_n_days(input.years())/7
        return time_to_string(total_time/total_week) if total_week else "0 min"
    
    @output
    @render.text
    def monthly_time():
        update_db()
        total_time = database.get_sum('traveltime')
        total_month = get_n_month(input.years())
        return time_to_string(total_time/total_month) if total_month else "0 min"
    
    @output
    @render.text
    def totaldelay():
        update_db()
        total_delay = database.get_sum('delay')
        return time_to_string(total_delay)
    
    @output
    @render.text
    def speed():
        update_db()
        avg_speed = database.get_avg('speed')
        return round(avg_speed, 2) if avg_speed else "No data"
    
    @output
    @render.text
    def nstation():
        update_db()
        return database.get_n_station()
    
    @output
    @render.text
    def distance():
        update_db()
        total_distance = database.get_sum('distance')
        return f"{round(total_distance, 2)} km" if total_distance else "0 km"
    
    @output
    @render.text
    def daily_distance():
        update_db()
        total_distance = database.get_sum('distance')
        total_days = get_n_days(input.years())
        return f"{round(total_distance/total_days, 2)} km" if total_distance else "0 km"
    
    @output
    @render.text
    def weekly_distance():
        update_db()
        total_distance = database.get_sum('distance')
        total_week = get_n_days(input.years())/7
        return f"{round(total_distance/total_week, 2)} km" if total_distance else "0 km"
    
    @render.text
    def monthly_distance():
        update_db()
        total_distance = database.get_sum('distance')
        total_month = get_n_month(input.years())
        return f"{round(total_distance/total_month, 2)} km" if total_distance else "0 km"
    
    @output
    @render.text
    def maxrelative():
        total = filtered_data()["RelativeDuration"].max()
        return f"Max relative duration: {total} %"

    @render_widget  
    def map():
        update_db()
        unic_station = database.get_unic_station()
        with open(os.path.join(os.getcwd(), 'database', 'stations_info.json'), 'r') as jsonInp:
            stationdb = json.load(jsonInp)
        center = (54.5260, 15.2551)
        m = Map(center=center, zoom=4)
        
        for station in unic_station:
            if station in stationdb:  # Vérifie que le lieu existe dans le dictionnaire
                marker = Marker(location=stationdb[station]['Coords'], title=station)
                m.add_layer(marker)
        
        
        return m
    
    @render.text
    def factos():
        return "Facts:"
    @render.text
    def earliest():
        df = filtered_data()
        return getOriginDestinationMin(df)
    @render.text
    def factos1():
        df = filtered_data()
        return getOriginDestinationMax(df, "Delay", "delay", "hm")
    @render.text
    def factos2():
        df = filtered_data()
        return getOriginDestinationMax(df, "RelativeDuration", "relative duration", "%")
    @render.text
    def factos3():
        df = filtered_data()
        return getOriginDestinationMax(df, "Distance", "distance", "km")
    @render.text
    def factos4():
        df = filtered_data()
        return  getOriginDestinationMax(df, "TravelTime", "travel time", "hm")
    @render.text
    def factos5():
        df = filtered_data()
        return getMaxPerDay(df, "Distance", "distance", "km")
    @render.text
    def factos6():
        df = filtered_data()
        return getMaxPerDay(df, "TravelTime", "travel time", "hm")
        

    @output
    @render.plot
    def traintaken_pl():
        update_db()
        
        x_axis, y_values = database.get_monthly_train_counts()

        title = "Train taken by month"
        fig, ax = plt.subplots()
        ax.plot(x_axis, y_values, color="skyblue")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of train taken")
        ax.set_title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig
    
    @output
    @render.plot
    def piedelay():
        update_db()
        labels, values = database.get_delay_categories()
        if sum(values) == 0:
            values[1] = 1
        colors = mcolors.LinearSegmentedColormap.from_list("green_to_red", ["green", "yellow", "red"])(np.linspace(0, 1, len(labels)))
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(values, colors=colors, shadow=True, autopct='%1.1f%%')
        plt.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title("Delay pie chart")
        plt.tight_layout()
        
        return fig

    
    """@output
    @render.data_frame
    def compagnytable():
        
        df = filtered_data()
        
        stats = df.groupby('Type', observed=False)['Delay'].agg(['count', 'max', 'min', 'mean', 'median']).reset_index()
        stats['mean'] = stats['mean'].round(2)
        stats.columns = ['Compagny', 'N train', 'Max Delay', 'Min Delay',  'Mean Delay', 'Median Delay']
        stats = stats.sort_values(by='Compagny')
        
        statsRela = df.groupby('Type', observed=False)['RelativeDuration'].agg(['mean']).reset_index()
        statsRela['mean'] = statsRela['mean'].round(2)
        statsRela.columns = ['Compagny', 'mean rela']
        statsRela = statsRela.sort_values(by='Compagny')
        
        stats_df = pd.DataFrame(stats)
        reladf = pd.DataFrame(statsRela)
        stats_df["Mean Relative Duration [%]"] = reladf['mean rela']
        stats_df = stats_df.sort_values(by='N train')

        
        #return fig
        return render.DataGrid(stats_df)
        return stats_df"""
    
    @output
    @render.data_frame
    def stat_table():
            
        update_db()
        return render.DataTable(database.get_stat_table())
    
    @output
    @render.plot
    def delayevolv():
        update_db()
        grouped_percentage = database.get_delay_evolution()

        labels = ['Early', 'On time', 'Low delay (<5 min)', 
                'Delay (between 5 and 10)', 'Big delay (between 10 and 30)', 'Very big delay (>30 min)']
        colors = mcolors.LinearSegmentedColormap.from_list("green_to_red", ["green", "yellow", "red"])(np.linspace(0, 1, len(labels)))

        fig, ax = plt.subplots()
        labels_x = [str(month).zfill(2) + "-" + str(year) for month, year in grouped_percentage.index]

        for i, category in enumerate(labels):
            if category in grouped_percentage.columns:
                ax.plot(labels_x, grouped_percentage[category], label=category, color=colors[i])

        ax.set_xlabel('Date')
        ax.set_ylabel('Delay [%]')
        ax.set_title('Delay evolution')
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig




app = App(app_ui, server)