import pandas as pd
import json
from shiny import App, render, ui, reactive
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import faicons as fa
import numpy as np
from datetime import datetime
GIT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(GIT_PATH)
from config import DB_URL
from src.db_management import TrainsDB

#---------------- TO DO ---------------#
#Voir comment update auto le df pour la selection des données
#Map qui montre les trajets, plus pk pas un dégradé selon le nombre -> construire la database. Utiliser la database from rnf

database = TrainsDB(DB_URL)

unique_years = sorted(init_df["Year"].unique().tolist())
unique_types = sorted(init_df["Type"].unique().tolist())

def minToString(minutes):
    heures = int(minutes // 60)
    mins_restantes = int(minutes % 60)
    
    if heures == 0:
        return f"{mins_restantes} mins"
    elif mins_restantes == 0:
        return f"{heures}h"
    else:
        return f"{heures}h {mins_restantes}mins"
    
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
    
def getNDaysSpent(yearList):
    
    ndays = 0
    today = datetime.now()
    actual_year = today.year
    for year in yearList:
        if year == 2024:
            ndays += 19
        elif year == actual_year:
            year_start = datetime(actual_year, 1, 1)
            ndays += (today - year_start).days + 1
        else:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                ndays += 366
            else:
                ndays += 365
    return ndays
    


app_ui = ui.page_fluid(
    ui.layout_sidebar(ui.sidebar(
            ui.input_checkbox_group("years", "Select years", choices=unique_years, selected=[2025]),
            ui.input_checkbox_group("types", "Select train types", choices=unique_types, selected=unique_types),
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
    ui.layout_columns(ui.output_plot("traintaken_pl"), (ui.h2("Global stats", style="text-align: center"), ui.output_data_frame("table"))),
    ui.layout_columns(ui.output_plot("piedelay"), ui.output_plot("delayevolv")), 
    ui.output_text("factos"),
    ui.output_text("earliest"),
    ui.output_text("factos1"),
    ui.output_text("factos2"),
    ui.output_text("factos3"),
    ui.output_text("factos4"),
    ui.output_text("factos5"),
    ui.output_text("factos6"),
    ui.output_text("kmperday"),
    ui.output_text("timeperday"),
    ui.output_data_frame("compagnytable"),
    
))

# Define the server logic
def server(input, output, session):
    @reactive.calc
    def filtered_data():
        with open('database.json', 'r') as json_input:
            json_db = json.load(json_input)
        df = pd.DataFrame(json_db["trainList"])
        yearsList = list(map(int, input.years()))
        df = df[df["Year"].isin(yearsList)]
        df = df[df["Type"].isin(input.types())]
        return df

    @output
    @render.text
    def ntrain():
        total = filtered_data().shape[0]
        return total
    
    @output
    @render.text
    def time():
        total = filtered_data()["TravelTime"].sum()
        days = total // (24 * 60)
        hours = (total % (24 * 60)) // 60
        minutes = total % 60
        return f"{days}d, {hours}h & {minutes}mins"
    
    @output
    @render.text
    def totaldelay():
        total = filtered_data()["Delay"].sum()
        days = total // (24 * 60)
        hours = (total % (24 * 60)) // 60
        minutes = total % 60
        return f"{days}d, {hours}h & {minutes}mins"
    
    @output
    @render.text
    def speed():
        total = round(filtered_data()["Speed"].mean(), 2)
        return f"{total} km/h"
    
    @output
    @render.text
    def meandelay():
        total = round(filtered_data()["Delay"].mean(), 2)
        return f"Average delay: {total} min"
    
    @output
    @render.text
    def mediandelay():
        total = filtered_data()["Delay"].median()
        return f"Median delay: {int(total)} min"
    
    @output
    @render.text
    def maxdelay():
        total = filtered_data()["Delay"].max()
        return f"Max delay: {total} min"
    
    @output
    @render.text
    def nstation():
        total = filtered_data()
        unique_values = pd.concat([total['Origin'], total['Destination']]).nunique()
        return unique_values
    
    @output
    @render.text
    def distance():
        total = round(filtered_data()["Distance"].sum(), 2)
        return f"{total} km"

    @output
    @render.text
    def averagerelative():
        total = round(filtered_data()["RelativeDuration"].mean(), 2)
        return f"Average relative duration: {total} %"
    
    @output
    @render.text
    def medianrelative():
        total = filtered_data()["RelativeDuration"].median()
        return f"Mean relative duration: {total} %"
    
    @output
    @render.text
    def maxrelative():
        total = filtered_data()["RelativeDuration"].max()
        return f"Max relative duration: {total} %"
    
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
    @render.text
    def kmperday():
        ndays = getNDaysSpent(list(map(int, input.years())))
        df = filtered_data()
        averageperday = round(df['Distance'].sum()/ndays, 2)
        return f'Average distance per day: {averageperday}km'
    @render.text
    def timeperday():
        ndays = getNDaysSpent(list(map(int, input.years())))
        df = filtered_data()
        averageperday = round(df['TravelTime'].sum()/ndays)
        return f'Average travel time per day: {minToString(averageperday)}'
        

    @output
    @render.plot
    def traintaken_pl():
        data = filtered_data()
        
        grouped_data = data.groupby(["Year", "Month"], observed=False).size().reset_index(name="count")
        grouped_data["year_month"] = grouped_data["Month"].astype(str).str.zfill(2) + "-" + grouped_data["Year"].astype(str)
        x_axis = grouped_data["year_month"]
            
        title = "Train taken by month"
        fig, ax = plt.subplots()
        ax.plot(x_axis, grouped_data["count"], color="skyblue")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of train taken")
        ax.set_title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig
    
    @output
    @render.plot
    def piedelay():
        df = filtered_data()
        
        bins = [-float('inf'), -1, 1, 5, 10, 30, float('inf')]
        labels = ['Early', 'On time', 'Low delay (<5 min)', 
                'Delay (between 5 and 10)', 'Big delay (between 10 and 30)', 'Very big delay (>30 min)']

        df['Catégorie'] = pd.cut(df['Delay'], bins=bins, labels=labels)

        category_counts = df['Catégorie'].value_counts()
        category_counts = category_counts.reindex(labels, fill_value=0)

        colors = mcolors.LinearSegmentedColormap.from_list("green_to_red", ["green", "yellow", "red"])(np.linspace(0, 1, len(labels)))
        label_color_dict = {label: color for label, color in zip(labels, colors)}
        colors_for_plot = [label_color_dict[label] for label in category_counts.index]
        fig, ax = plt.subplots()
        #ax.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', colors=colors_for_plot)
        wedges, texts, autotexts = ax.pie(category_counts, colors=colors, shadow=True, autopct='%1.1f%%')
        plt.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title("Delay pie chart")
        plt.tight_layout()
        
        return fig
    
    @output
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

        """fig, ax = plt.subplots()
        ax.axis("off")

        table = ax.table(
            cellText=stats_df.values,
            colLabels=stats_df.columns,
            cellLoc="center",
            loc="center",
            colColours=["#87CEEB"] * len(stats_df.columns),
            cellColours=[["#e9e9e9"] * len(stats_df.columns)] * len(stats_df)
        )

        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.2)

        plt.title("Global stats", pad=20, fontsize=14, fontweight="bold")

        plt.tight_layout()"""
        
        #return fig
        return render.DataGrid(stats_df)
        return stats_df
    
    @output
    @render.data_frame
    def table():
        
        df = filtered_data()
        
        stats =  {" ": ["Delay [min]", "Relative duration", "Distance [km]", "Travel time", "Speed [km/h]"],
            "Max": [df["Delay"].max(),
                    f"{df['RelativeDuration'].max()}%",
                    df["Distance"].max(),
                    minToString(df["TravelTime"].max()),
                    df["Speed"].max()],
            "Min": [df["Delay"].min(),
                    f"{df['RelativeDuration'].min()}%",
                    df["Distance"].min(),
                    minToString(df["TravelTime"].min()),
                    df["Speed"].min()],
            "Mean": [
                    round(df["Delay"].mean(), 2),
                    f"{round(df['RelativeDuration'].mean(), 2)}%",
                    round(df["Distance"].mean(), 2),
                    minToString(df["TravelTime"].mean()),
                    round(df["Speed"].mean(), 2)],
            "Median": [
                    df["Delay"].median(),
                    f"{df['RelativeDuration'].median()}%",
                    df["Distance"].median(),
                    minToString(df["TravelTime"].median()),
                    df["Speed"].median()
                    ]}

        stats_df = pd.DataFrame(stats)

        """fig, ax = plt.subplots()
        ax.axis("off")

        table = ax.table(
            cellText=stats_df.values,
            colLabels=stats_df.columns,
            cellLoc="center",
            loc="center",
            colColours=["#87CEEB"] * len(stats_df.columns),
            cellColours=[["#e9e9e9"] * len(stats_df.columns)] * len(stats_df)
        )

        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.2)

        plt.title("Global stats", pad=20, fontsize=14, fontweight="bold")

        plt.tight_layout()
        
        return fig"""
        return render.DataTable(stats_df)
    
    @output
    @render.plot
    def delayevolv():
        df = filtered_data()
        
        bins = [-float('inf'), -1, 1, 5, 10, 30, float('inf')]
        labels = ['Early', 'On time', 'Low delay (<5 min)', 
                'Delay (between 5 and 10)', 'Big delay (between 10 and 30)', 'Very big delay (>30 min)']

        df['DelayCat'] = pd.cut(df['Delay'], bins=bins, labels=labels)
        grouped = df.groupby(['Month', 'Year', 'DelayCat'], observed=False).size().unstack(fill_value=0)
        grouped_percentage = grouped.div(grouped.sum(axis=1), axis=0) * 100
        couples_mois_annee = grouped_percentage.index.to_list()
        couples_mois_annee.sort(key=lambda x: (x[1], x[0])) 
        grouped_percentage = grouped_percentage.loc[couples_mois_annee]
        
        colors = mcolors.LinearSegmentedColormap.from_list("green_to_red", ["green", "yellow", "red"])(np.linspace(0, 1, len(labels)))
        fig, ax = plt.subplots()
        labels_x = [str(month).zfill(2)+ "-" + str(year) for month, year in grouped_percentage.index]

        for i, category in enumerate(grouped_percentage.columns):
            ax.plot(labels_x, grouped_percentage[category], label=category, color=colors[i])

        ax.set_xlabel('Date')
        ax.set_ylabel('Delay [%]')
        ax.set_title('Delay evolution')
        #ax.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.xticks(rotation=45)
        #ax.grid(True, linestyle='--', alpha=0.6)

        plt.tight_layout()

        return fig



app = App(app_ui, server)