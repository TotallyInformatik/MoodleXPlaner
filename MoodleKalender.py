# gui config.
from tkinter import * 
from tkinter import messagebox
import calendar
import datetime

# webscraping
from lxml import html
import requests
from bs4 import BeautifulSoup
from webbrowser import open_new

# other
import re



scrollable_tuples = {}
def update_frame_width(scrollable_tuple):
    if not scrollable_tuples.get(scrollable_tuple):
        try:
            scrollable_tuple[0].configure(width=scrollable_tuple[2].winfo_width())
            scrollable_tuple[1].configure(width=scrollable_tuple[2].winfo_width() + 20)
            scrollable_tuples[scrollable_tuple] = True
        except:
            pass


# programm config.


add_window_initialized = False
now = datetime.datetime.now()


def setup_discarded_tasks():
    global all_discarded_tasks
    with open("file/personalDiscardedTasks.txt", "r") as f:
        all_discarded_tasks = f.readlines()


def setup_personal_tasks():
    global all_personal_tasks
    with open("file/personalTasks.txt", "r") as f:
        personal_tasks_list = f.readlines()
    
    for personal_task in personal_tasks_list:
        task_set = personal_task.split(" | ")

        date_string = task_set[0].split(", ")
        date = datetime.date(day=int(date_string[0]), month=int(date_string[1]), year=int(date_string[2]))

        time_string = task_set[1].split(", ")
        time = datetime.time(hour=int(time_string[0]), minute=int(time_string[1]))

        task_description = task_set[-1]
        task_description = task_description.strip("\n")

        # if a end time is given!
        deadline_time = None
        if len(task_set) == 4:
            deadline_time_string = task_set[2].split(", ")
            deadline_time = datetime.time(hour=int(deadline_time_string[0]), minute=int(deadline_time_string[1]))

        time_set = [time, deadline_time]

        if not all_personal_tasks.get(date):
            all_personal_tasks[date] = [[task_description, time_set]]
        else:
            new_personal_task = all_personal_tasks.get(date).copy()
            new_personal_task.append([task_description, time_set])
            all_personal_tasks[date] = new_personal_task




all_discarded_tasks = []
setup_discarded_tasks()
all_discarded_tasks = list(map(lambda task: task.strip("\n"), all_discarded_tasks))

all_personal_tasks = {}
setup_personal_tasks()


calendar_offset = 0

root = Tk()
root.iconbitmap("moodleReaderIcon.ico")
root.resizable(0, 0)
# root.configure(bg="#4d5157")
root.configure(bg="#282a2b", height=560, width=780)
root.title("Moodle-Kalender-Planer 1.1 von Rui Zhang")




# the calendar itself
current_calendar = LabelFrame(root, bd=0, bg="#282a2b", fg="white", height=500, width=440)
current_calendar.grid_propagate(False)
current_calendar.grid(row=0, column=0, sticky=NW, padx=20)

informations_display = LabelFrame(root, bd=0, bg="#3E4142", fg="white", width=350)
informations_display.grid(row=0, column=1, rowspan=2, sticky=NSEW)
no_info_label = Label(informations_display, text="Kein Inhalt hier! Clicke ein Datum an, ", bg="#3E4142", fg="white", font=("Arial", 11))
no_info_label.pack(padx=10, pady=10)
no_info_label2 = Label(informations_display, text="um Termine und Aufgaben für diesen Tag zu sehen!", bg="#3E4142", fg="white", font=("Arial", 11))
no_info_label2.pack(padx=10, pady=10)





# control frame
control_frame = LabelFrame(root, bd=0, bg="#4A5459")
control_frame.grid(row=1, column=0, sticky=S)

# pre button
Button(control_frame, text="<", command=lambda: calendar_init("pre"), bd=0, bg="#4A5459", fg="white").grid(row=0, column=0)

# calendar title
calendar_title = Label(control_frame, bg="#4A5459", fg="white")
calendar_title.grid(row=0, column=1)

# next button
Button(control_frame, text=">", command=lambda: calendar_init("next"), bd=0, bg="#4A5459", fg="white").grid(row=0, column=2)

refresh_button = Button(control_frame, text="refresh", bd=0, bg="#4A5459", fg="white")
refresh_button.grid(row=0, column=3, padx=10)

message = Label(root, text="von Rui Zhang", bg="#4A5459", fg="white", height=3)
message.grid(row=2, column=0, columnspan=4, sticky=NSEW)

AbgabeTermine = {}
termin_to_url = {}






# scrape Website
# einloggen und Webseiten Infos herauskriegen. (Abgabetermine und Themen aufschreiben)


def extract_info(username_data, password_data):
    global termin_to_url, AbgabeTermine


    login_url = "https://www.annettemoodle.de/Annette-Moodle/login/index.php"

    session_requests = requests.session()
    result = session_requests.get(login_url)
    tree = html.fromstring(result.text)
    authenticity_token = list(set(tree.xpath("//input[@name='logintoken']/@value")))[0]

    # post data into moodle

    data_ = {
        #"username": username_data,
        #"password": password_data,
        
        "username": username_data,
        "password": password_data,
        "logintoken": authenticity_token
    }


    with session_requests as s:
        result = session_requests.post(
            login_url,
            data = data_,
            headers = dict(referer=login_url)
        )
        
        # url_mit_links = "https://www.annettemoodle.de/Annette-Moodle/course/view.php?id=335"
        url_mit_fälligkeiten = "https://www.annettemoodle.de/Annette-Moodle/calendar/view.php?view=upcoming"
        

        result = session_requests.get(
            url_mit_fälligkeiten,
            headers = dict(referer=url_mit_fälligkeiten)
        )
        index_page = BeautifulSoup(result.text, "html.parser")


        kalender = index_page.find("div", {"class": "eventlist my-1"})
        termine = kalender.find_all("div", {"class": "event m-t-1"})


        # urls zu den Terminen aufschreiben
        #termin_to_url = {}
        for termin in termine:
            title = termin["data-event-title"]

            link_element = termin.find("a", {"class": "card-link"})
            url = link_element["href"]

            termin_to_url[title] = url


        def parseMonat(monat):
            de_en_map = {
                "Januar": "January",
                "Februar": "February",
                "März": "March",
                "Mai": "May",
                "Juni": "June",
                "Juli": "July",
                "August": "August",
                "Oktober": "October",
                "Dezember": "December"
            }

            return de_en_map.get(monat, monat)



        def parseTermin(zeit, beschreibung):
            global AbgabeTermine
            time_info = zeit.split(", ")

            # im Moment wird nur der Tag als Zahl dargestellt, also kann man keine Termine von
            # z.B. dem nächsten Monat sehen
            if time_info[0] == "Morgen":

                # old code kept just in case problems with now() function
                #now = datetime.datetime.now()

                zeit = now.date() + datetime.timedelta(days=1)
            elif time_info[0] == "Heute":

                #zeit = datetime.datetime.now().date()
                zeit = now.date()
            else:
                tag = time_info[1].split(". ")[0]
                monat = time_info[1].split(". ")[1]
                
                #date_str = f"{tag}-{parseMonat(monat)}-{datetime.datetime.now().year}"
                date_str = f"{tag}-{parseMonat(monat)}-{now.year}"
                
                zeit = datetime.datetime.strptime(date_str, "%d-%B-%Y").date()


            genaue_zeit = time_info[-1]
            genaue_zeit = datetime.datetime.strptime(genaue_zeit, "%H:%M").time()
            zeit = datetime.datetime.combine(zeit, genaue_zeit) 

            if not AbgabeTermine.get(zeit, False):
                AbgabeTermine[zeit] = [beschreibung]
            else:
                current_termin = AbgabeTermine.get(zeit).copy()
                current_termin.append(beschreibung)
                AbgabeTermine[zeit] = current_termin

        
        for termin in termine:
            
            termin_beschreibung = termin.find("h3", {"class": "name d-inline-block"}).text
            termin_fälligkeit = termin.find("div", {"class": "col-xs-11"}).text
            

            termin_fertig = False
            url = termin_to_url.get(termin_beschreibung)
            result = session_requests.get(
                url,
                headers = dict(referer=url)
            )
            try:
                content = BeautifulSoup(result.text, "html.parser")
                table = content.find("table", {"class": "generaltable"})
                abgabe_status_set = table.find_all("tr")[0]
                abgabe_status = abgabe_status_set.contents[3].text
                if abgabe_status == "Kein Versuch":
                    termin_fertig = False
                elif abgabe_status == "Zur Bewertung abgegeben":
                    termin_fertig = True
                else:
                    print("problem in function termin_fertig")
            except AttributeError:
                termin_fertig = True


            if not termin_fertig:
                parseTermin(termin_fälligkeit, termin_beschreibung)

    return AbgabeTermine

# termine etc. in Kalender eintraggen


# displaying tasks


def calendar_init(direction):
    global calendar_offset, current_calendar

    for widget in current_calendar.winfo_children():
        widget.destroy()

    if direction == "next":
        calendar_offset += 1
    elif direction == "pre":
        calendar_offset -= 1
    elif direction == None:
        calendar_offset = 0

    try:
        draw_current_month(now.year, now.month + calendar_offset, now.date())
    except:
        draw_current_month(now.year, now.month, now.date())
        calendar_offset = 0
        messagebox.showerror(title="Error", message="Nur Termine innerhalb dieses Jahres möglich")


def delete_display_no_tasks(current_frame):
    if len(current_frame.winfo_children()) == 1:
        current_frame.winfo_children()[0].destroy()

def display_no_tasks(current_frame):
    if len(current_frame.winfo_children()) == 0:
        info = Label(current_frame, text="Hier gibt es nicht viel zu sehen....", bg="#3E4142", fg="white")
        info.grid(row=1, column=0, padx=10, pady=10)

def link_to_give(text):
    open_new(termin_to_url.get(text))

def delete_set(_set, current_frame, _type, date=None):
    yesno = messagebox.askyesno("Title", "Bist du dir sicher, dass du diesen Termin / diese Aufgabe löschen möchtest?")
    if yesno:

        if _type == "moodle":
            with open("file/personalDiscardedTasks.txt", "a") as f:
                #f.write(_set[1].cget("text") + "\n")
                f.write(_set[1].cget("text")[:-6:] + "\n")
            
        elif _type == "personal":

            text = _set[0].cget("text")
            task, time_set = text.split(" | ")

            time_set = time_set.split(" ")

            day = date.split("-")[0]
            month = date.split("-")[1]
            year = now.year

            delete_task = f"{day}, {month}, {year} |" #  {hour}, {minute} | {task}

            for time in time_set:
                hour = time.split(":")[0]
                minute = time.split(":")[1]
                delete_task += f" {hour}, {minute} |"
            
            delete_task += f" {task}"

            with open("file/personalTasks.txt", "r") as f:
                tasks = f.readlines()

            #try:
            tasks.remove(delete_task + "\n")
            #except:
                #tasks.remove(delete_task)

            with open("file/personalTasks.txt", "w") as f:
                f.writelines(tasks)

        elif _type == "longterm":
            temp_longterm_plans = []
            remove_task_desc = _set[0].cget("text")
            with open("file/longtermplans.txt", "r") as f:
                temp_longterm_plans = f.readlines()

            #try:
            temp_longterm_plans.remove(remove_task_desc + "\n")
            #except:
                #temp_longterm_plans.remove(remove_task_desc)

            with open("file/longtermplans.txt", "w") as f:
                f.writelines(temp_longterm_plans)
        
        else:
            print("error at delete_set: invalid _type")


        for widget in _set:
            widget.destroy()

        display_no_tasks(current_frame)
    
        refresh(moodle_content)


current_add_row_index = 0
def add_personal_task(info_set, date, current_frame):
    global current_add_row_index
    all_buttons = []


    description = info_set[0].get()
    zeit_widgets = info_set[1]
    zeit = list(map(lambda widget: widget.get(), zeit_widgets))

    if ((not zeit[0].strip(" ")) or (not zeit[1].strip(" ")) or (not description.strip(" "))) or ("grey" in (zeit_widgets[0].cget("fg"), zeit_widgets[1].cget("fg"), info_set[0].cget("fg"))):
        messagebox.showerror(title="Error", message="Bitte keine Felder freilassen!")
    else:
        # 2nd part: parse into txt file

        date_set = date.split("-")
        store_text = f"{date_set[0]}, {date_set[1]}, {now.year} |" # {zeit_set[0]}, {zeit_set[1]} | {task_description}" + "\n"
        info_display_text = f"{description} |"

        # used for checking pattern of input
        time_set_pattern = r"\d\d:\d\d"
        for zeit_set in zeit:
            if zeit_set and re.search(time_set_pattern, zeit_set):

                zeit_set = zeit_set.split(":")

                if (len(zeit_set[0])) == 1:
                    zeit_set[0] = "0" + zeit_set[0]
                if (len(zeit_set[1])) == 1:
                    zeit_set[1] = "0" + zeit_set[1]  

                store_text += f" {zeit_set[0]}, {zeit_set[1]} |"
                info_display_text += f" {zeit_set[0]}:{zeit_set[1]}"

            else:
                messagebox.showerror(title="Error", message="Bitte geben sie die Zeit im Format 00:00 ein!")
                return False
        
        store_text += f" {description}" + "\n"
        

        with open("file/personalTasks.txt", "a") as f:
            f.write(store_text)

        # gets rid of no tasks
        delete_display_no_tasks(current_frame)


        info = Label(current_frame, text=info_display_text, bg="#3E4142", fg="white")
        info.grid(row=current_add_row_index, column=0, padx=10, pady=10, sticky=W)

        delete_button = Button(current_frame, text="-")
        delete_button.configure(command=lambda _set=(info, delete_button), current_frame=current_frame, _type="personal": delete_set(_set, current_frame, _type, date))
        delete_button.grid(row=current_add_row_index, column=1, padx=10, pady=10)
        current_add_row_index += 1

        all_buttons.append(delete_button)

        # refresh
        refresh(moodle_content)

        # let the other function handle the rest
def reset_add_win_init():
    global add_window_initialized
    add_window_initialized = False


def delete_placeholder(widget, *args):
    if widget.cget("fg") == "grey":
        widget.delete(0, END)
        widget.configure(fg="white")

def add_placeholder(widget, placeholder, *args):
    if not widget.get():
        widget.configure(fg="grey")
        widget.insert(0, placeholder)


def add_personal_task_win(current_date, current_frame):
    global add_window_initialized
    # 1st part: display window to configure task
    if add_window_initialized:
        messagebox.showerror(title="Error", message="Keine zwei 'Aufgabe konfigurieren' Fenster gleichzeitig erlaubt!")
    else:
        add_window_initialized = True
        configure_task_win = Toplevel()
        configure_task_win.resizable(0, 0)
        configure_task_win.configure(bg="#282a2b")
        configure_task_win.title("Neue Aufgabe konfigurieren")
        configure_task_win.iconbitmap("moodleReaderIcon.ico")

        Label(configure_task_win, bg="#282a2b", fg="white", text="Aufgabe / Termin Beschreibung: ").grid(row=0, column=0, sticky=W, padx=10)
        task_description = Entry(configure_task_win, bg="#575757", fg="white")
        #task_description.insert(0, "Mathe lernen")
        task_description.grid(row=0, column=1, padx=10, pady=10)

        add_placeholder(task_description, "Mathe lernen")
        task_description.bind("<FocusIn>", lambda event, widget=task_description: delete_placeholder(widget, event))
        task_description.bind("<FocusOut>", lambda event, widget=task_description, placeholder="Mathe lernen": add_placeholder(widget, placeholder, event))


        Label(configure_task_win, bg="#282a2b", fg="white", text="Zeit: ").grid(row=1, column=0, sticky=W, padx=10)
        zeit = Entry(configure_task_win, bg="#575757", fg="white")
        #zeit.insert(0, "17:30")
        zeit.grid(row=1, column=1, padx=10, pady=10)

        add_placeholder(zeit, "17:30")
        zeit.bind("<FocusIn>", lambda event, widget=zeit: delete_placeholder(widget, event))
        zeit.bind("<FocusOut>", lambda event, widget=zeit, placeholder="17:30": add_placeholder(widget, placeholder, event))


        Label(configure_task_win, bg="#282a2b", fg="white", text="Deadline: ").grid(row=2, column=0, sticky=W, padx=10)
        deadline_zeit = Entry(configure_task_win, bg="#575757", fg="white")
        #deadline_zeit.insert(0, "19:00")
        deadline_zeit.grid(row=2, column=1, padx=10, pady=10)

        add_placeholder(deadline_zeit, "19:00")
        deadline_zeit.bind("<FocusIn>", lambda event, widget=deadline_zeit: delete_placeholder(widget, event))
        deadline_zeit.bind("<FocusOut>", lambda event, widget=deadline_zeit, placeholder="19:00": add_placeholder(widget, placeholder, event))


        confirm_button = Button(configure_task_win, text="erstellen", command=lambda info_set=(task_description, [zeit, deadline_zeit]), frame=current_frame: add_personal_task(info_set, current_date, frame))
        confirm_button.grid(row=3, column=0, padx=10, pady=10, sticky=W)

        configure_task_win.bind("<Destroy>", lambda event: reset_add_win_init())




def onFrameConfigure(canvas, container, frame):
    canvas.configure(scrollregion=canvas.bbox("all"))
    update_frame_width((canvas, container, frame))


longterm_win_initialized = False
def reset_longterm_win_init():
    global longterm_win_initialized
    longterm_win_initialized = False

current_row_index_longterm = 0
def add_longterm_task(text_widget, deadline_widget, frame):
    global current_row_index_longterm
    # add to window
    
    all_buttons = []
    
    if deadline_widget.get().strip(" ") and text_widget.get().strip(" ") and ("grey" not in (deadline_widget.cget("fg"), text_widget.cget("fg"))):
        deadline_pattern = r"\d\d-\d\d-\d\d\d\d"
        if re.search(deadline_pattern, deadline_widget.get()):

            delete_display_no_tasks(frame)

            info = Label(frame, text=f"{text_widget.get()} | {deadline_widget.get()}", bg="#3E4142", fg="white")
            info.grid(row=current_row_index_longterm, column=0, padx=10, pady=10, sticky=W)

            delete_button = Button(frame, text="x")
            delete_button.grid(row=current_row_index_longterm, column=1, padx=10, pady=10, sticky=W)
            delete_button.configure(command=lambda _set=(info, delete_button), frame=frame, _type="longterm": delete_set(_set, frame, _type))
            
            all_buttons.append(delete_button)
            current_row_index_longterm += 1

            # add to txt.file

            with open("file/longtermplans.txt", "a") as f:
                f.write(f"{text_widget.get()} | {deadline_widget.get()}" + "\n")

            refresh(moodle_content)

        else:
            messagebox.showerror(title="Error", message="Deadline muss im Format tt-mm-jjjj sein!")
    else:
        messagebox.showerror(title="Error", message="Bitte keine Felder freilassen!")



def add_longterm_task_win(frame):
    global longterm_win_initialized
    if longterm_win_initialized:
        messagebox.showerror(title="Error", message="Keine zwei 'langfristige Aufgaben' Fenster gleichzeitig erlaubt!")
    else:
        longterm_win_initialized = True
        longterm_task_win = Toplevel()
        longterm_task_win.resizable(0, 0)
        longterm_task_win.configure(bg="#282a2b")
        longterm_task_win.iconbitmap("moodleReaderIcon.ico")
        longterm_task_win.title("langfristige Aufgaben")

        Label(longterm_task_win, bg="#282a2b", fg="white", text="Aufgabe Beschreibung: ").grid(row=0, column=0, sticky=W, padx=10)
        task_description = Entry(longterm_task_win, bg="#575757", fg="white")
        #task_description.insert(0, "Mathe lernen")
        task_description.grid(row=0, column=1, padx=10, pady=10)

        add_placeholder(task_description, "alle Programmiersprachen lernen")
        task_description.bind("<FocusIn>", lambda event, widget=task_description: delete_placeholder(widget, event))
        task_description.bind("<FocusOut>", lambda event, widget=task_description, placeholder="alle Programmiersprachen lernen": add_placeholder(widget, placeholder, event))


        Label(longterm_task_win, bg="#282a2b", fg="white", text="Deadline").grid(row=2, column=0, sticky=W, padx=10)
        deadline_zeit = Entry(longterm_task_win, bg="#575757", fg="white")
        deadline_zeit.grid(row=2, column=1, padx=10, pady=10)

        add_placeholder(deadline_zeit, "01-01-1890")
        deadline_zeit.bind("<FocusIn>", lambda event, widget=deadline_zeit: delete_placeholder(widget, event))
        deadline_zeit.bind("<FocusOut>", lambda event, widget=deadline_zeit, placeholder="01-01-1890": add_placeholder(widget, placeholder, event))


        confirm_button = Button(longterm_task_win, text="erstellen", command=lambda: add_longterm_task(task_description, deadline_zeit, frame))
        confirm_button.grid(row=3, column=0, padx=10, pady=10, sticky=W)        

        longterm_task_win.bind("<Destroy>", lambda event: reset_longterm_win_init())
    

def display_longterm_goals():
    global current_row_index_longterm
    all_buttons = []
    
    # clear frame:
    for widget in informations_display.winfo_children():
        widget.destroy()



    longterm_g_container = LabelFrame(informations_display, bg="#3E4142")
    longterm_g_container.grid(row=1, column=0, padx=10, pady=10, sticky=NSEW)

    longterm_g_canvas = Canvas(longterm_g_container, bg="#3E4142", bd=0, highlightthickness=0, relief="ridge", width=330, height=330)
    longterm_g_canvas.pack(side="left", fill="both", expand=True)
    
    longterm_g_scrollbar = Scrollbar(longterm_g_container, orient="vertical", command=longterm_g_canvas.yview)
    longterm_g_scrollbar.pack(side="right", fill="y")

    longterm_g_canvas.configure(yscrollcommand=longterm_g_scrollbar.set)

    longterm_g_frame = LabelFrame(longterm_g_container, bd=0, bg="#3E4142", fg="white")
    longterm_g_canvas.create_window((0,0), window=longterm_g_frame, anchor="nw")

    scrollable_tuples[(longterm_g_canvas, longterm_g_container, longterm_g_frame)] = False
    longterm_g_frame.bind("<Configure>", lambda event: onFrameConfigure(longterm_g_canvas, longterm_g_container, longterm_g_frame))

    Label(informations_display, text="Deine langfristigen Pläne / Aufgaben:", bg="#3E4142", fg="white", font=("Arial", 13)).grid(row=0, column=0, padx=20, pady=20) 

    add_longterm_task = Button(informations_display, text="+", width=5, command=lambda: add_longterm_task_win(longterm_g_frame))
    add_longterm_task.grid(row=2, column=0, padx=10, pady=10, sticky=W)

    
    delete_display_no_tasks(longterm_g_frame)

    # inhalt einfügen
    longterm_goals = []
    with open("file/longtermplans.txt") as f:
        longterm_goals = f.readlines()
    
    for goal in longterm_goals:

        goal = goal.strip("\n")
        goal_set = goal.split(" | ")

        info = Label(longterm_g_frame, text=f"{goal_set[0]} | {goal_set[1]}", bg="#3E4142", fg="white")
        info.grid(row=current_row_index_longterm, column=0, padx=10, pady=10, sticky=W)

        delete_button = Button(longterm_g_frame, text="x")
        delete_button.grid(row=current_row_index_longterm, column=1, padx=10, pady=10, sticky=W)
        delete_button.configure(command=lambda _set=(info, delete_button), frame=longterm_g_frame, _type="longterm": delete_set(_set, frame, _type))

        all_buttons.append(delete_button)
        current_row_index_longterm += 1
    
    display_no_tasks(longterm_g_frame)


def display_termin(content, current_date, personal_content, position):
    global current_add_row_index


    #all_buttons = [Button(text="Termin entfernen") for i in range(len(content))]
    all_buttons = []

    # clear frame:
    for widget in informations_display.winfo_children():
        widget.destroy()


    title = Label(informations_display, text=current_date, bg="#3E4142", fg="white", font=("Arial", 20))
    title.pack(padx=10, pady=5, fill="x")


    moodle_container = LabelFrame(informations_display, text="Moodle Termine:", bg="#3E4142", fg="white", height=180, width=350)
    moodle_container.pack(padx=10, pady=10, fill="x")

    moodle_canvas = Canvas(moodle_container, background="#3E4142", bd=0, relief="ridge", highlightthickness=0, width=330, height=180)
    moodle_canvas.pack(side="left", fill="both", expand=True)

    moodle_yscrollbar = Scrollbar(moodle_container, orient="vertical", command=moodle_canvas.yview)
    moodle_yscrollbar.pack(side="right", fill="y")

    moodle_canvas.configure(yscrollcommand=moodle_yscrollbar.set)

    moodle_termine = LabelFrame(moodle_canvas, bd=0, bg="#3E4142", fg="white")
    moodle_canvas.create_window((0, 0), window=moodle_termine, anchor="nw")
    
    scrollable_tuples[(moodle_canvas, moodle_container, moodle_termine)] = False
    moodle_termine.bind("<Configure>", lambda event: onFrameConfigure(moodle_canvas, moodle_container, moodle_termine))
    #moodle_termine.grid(row=0, column=0, padx=10, pady=10, columnspan=1)

    #if content:

    for i, termin in enumerate(content):
        
        # -3, so to get rid of the second
        info = Label(moodle_termine, text=termin[:-3:], bg="#3E4142", fg="white")
        info.grid(row=i, column=0, padx=10, pady=10)

        link_button = Button(moodle_termine, text="i", command=lambda text=info.cget("text")[:-6:]: link_to_give(text))
        link_button.grid(row=i, column=1, padx=10, pady=10)

        delete_button = Button(moodle_termine, text="-")
        delete_button.configure(command=lambda _set=(link_button, info, delete_button), current_frame=moodle_termine, _type="moodle": delete_set(_set, current_frame, _type))
        delete_button.grid(row=i, column=2, padx=10, pady=10)
        
        all_buttons.append(delete_button)


    display_no_tasks(moodle_termine)

    personal_container = LabelFrame(informations_display, text="eigene Aufgaben / Termine:", bg="#3E4142", fg="white", height=180)  #, width=350 
    #personal_container.grid_propagate(False)
    personal_container.pack(padx=10, pady=10, fill="x")

    personal_canvas = Canvas(personal_container, background="#3E4142", bd=0, highlightthickness=0, relief='ridge', height=180)  #width=330, 
    personal_canvas.pack(side="left", fill="both", expand=True)
    #personal_canvas.grid(row=1, column=0)

    personal_yscrollbar = Scrollbar(personal_container, orient="vertical", command=personal_canvas.yview)
    personal_yscrollbar.pack(side="right", fill="y")
    # yscrollbar.grid(row=1, column=1)

    personal_canvas.configure(yscrollcommand=personal_yscrollbar.set)

    personal_frame = LabelFrame(personal_canvas, bd=0, bg="#3E4142", fg="white")
    #personal_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    personal_canvas.create_window((0, 0), window=personal_frame, anchor="nw")

    scrollable_tuples[(personal_canvas, personal_container, personal_frame)] = False
    personal_frame.bind("<Configure>", lambda event: onFrameConfigure(personal_canvas, personal_container, personal_frame))
    
    #personal_frame.pack(fill="both", expand=True)


    if personal_content:

        for i, task in enumerate(personal_content):

            info_text = f"{task[0]} |"

            for time_point in task[1]:
            
                if time_point:
                    hour = time_point.hour
                    minute = time_point.minute

                    if len(str(hour)) == 1:
                        hour = "0" + str(hour)
                    if len(str(minute)) == 1:
                        minute = "0" + str(minute)
                    
                    info_text += f" {hour}:{minute}"


            info = Label(personal_frame, text=info_text, bg="#3E4142", fg="white")
            info.grid(row=i, column=0, padx=10, pady=10, sticky=W)

            delete_button = Button(personal_frame, text="-")
            delete_button.configure(command=lambda set=(info, delete_button), current_frame=personal_frame, _type="personal": delete_set(set, current_frame, _type, current_date))
            delete_button.grid(row=i, column=1, padx=10, pady=10, sticky=E)

            all_buttons.append(delete_button)

        current_add_row_index = len(personal_content)

    add_task_button = Button(informations_display, text="+", width=5, command=lambda: add_personal_task_win(current_date, personal_frame))
    #add_task_button.grid(row=int(len(personal_frame.winfo_children()) / 2 + 1), column=0, sticky=SW)
    #add_task_button.grid(row=3, column=0, sticky=E, padx=10)
    add_task_button.pack(side="left", padx=10, anchor="e")
    
    display_no_tasks(personal_frame)



def find_all_termine(date):
    current_termine = []
    for key in AbgabeTermine.keys():

        if date == key.date():
            for termin in AbgabeTermine.get(key):
                if termin not in all_discarded_tasks:
                    current_termine.append(f"{termin} {key.time()}")

    return current_termine


def draw_current_month(year, month, current_date):
    global calender_title
    all_buttons = [Button(current_calendar) for i in range(31)]

    # current_calendar.configure(text=f"Kalender: {month}-{year}")
    calendar_title.configure(text=f"Kalender: {month}-{year}")

    weekday_map = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}

    for i in range(7):
        Label(current_calendar, text=weekday_map.get(i), bg="#282a2b", fg="white").grid(row=0, column=i, pady="20")

    c_row = 1
    offset = 0
    days_in_month = calendar.monthrange(year, month)[1]

    first_day_weekday = datetime.date(year=year, month=month, day=1).weekday()


    last_row = 0
    for i in range(1 + first_day_weekday, days_in_month + 1 + first_day_weekday):
        last_row += 1

        all_buttons[i-1-first_day_weekday].configure(width=8, height=4, fg="white", bd=0, text=i-first_day_weekday)

        current_button_date = datetime.date(year=year, month=month, day=(i - first_day_weekday))
        personal_content = all_personal_tasks.get(current_button_date)
        content = find_all_termine(current_button_date)
        
        #if len(content) > 0 or personal_content:

            #content = find_all_termine(current_button_date)
        all_buttons[i-1-first_day_weekday].configure(command=lambda cont=content, date=f"{i-first_day_weekday}-{month}", 
                                                    per_cont=personal_content, position=10: display_termin(cont, date, per_cont, position), 
                                                    width=6, height=3)
        all_buttons[i-1-first_day_weekday].grid(row=c_row, column=i-1 - (offset * 7), padx=7, pady=7)
        #else:
            #all_buttons[i-1-first_day_weekday].configure(bg="#282a2b", command=lambda cont=None, date=f"{i-first_day_weekday}-{month}", per_cont=None, position=10: display_termin(cont, date, per_cont, position))

        if len(content) > 0 or personal_content:
            all_buttons[i-1-first_day_weekday].configure(bg="#660000")
        else:
            all_buttons[i-1-first_day_weekday].configure(bg="#282a2b")
            #all_buttons[i-1-first_day_weekday].configure(bg="#949494", width=6, height=3)

        if current_button_date == current_date:
            all_buttons[i-1-first_day_weekday].configure(underline=True, font=("Courier", 10), bd=1, relief=SUNKEN)
            #current_date_indicator = Label(current_calendar, bg="#949494", width=6, height=1)
            #current_date_indicator.grid(row=c_row, column=i-1 - (offset * 7), padx=12, pady=0, sticky=SW)

        if i % 7 == 0:
            c_row += 1
            offset += 1
            last_row = 0
    

    long_term_button = Button(current_calendar, text="L", bd=1, width=6, height=3, command=display_longterm_goals)
    long_term_button.grid(row=c_row, column=last_row, padx=7, pady=7)








# refresh button to reconfigure calendar to display tasks correctly
def refresh_sequence(loading_win, moodlelogin):
    global AbgabeTermine, all_discarded_tasks, all_personal_tasks


    all_discarded_tasks = []
    setup_discarded_tasks()
    all_discarded_tasks = list(map(lambda task: task.strip("\n"), all_discarded_tasks))

    all_personal_tasks = {}
    setup_personal_tasks()

    # quick part to set all values in the scrollable dictionary to false:
    for key in scrollable_tuples.keys():
        scrollable_tuples[key] = False
        update_frame_width(key)

    if moodlelogin:
        AbgabeTermine.clear()
        AbgabeTermine = extract_info(d1, d2)

    calendar_init(None)
    
    loading_win.destroy()


def refresh(moodlelogin):
    loading = Tk()
    loading.iconbitmap("moodleReaderIcon.ico")
    loading.title("Laden....")
    loading.configure(bg="#282a2b")
    loading_label = Label(loading, text="Programm lädt... Bitte haben Sie Geduld..", bg="#282a2b", fg="white").pack(padx=10, pady=10)

    loading.after(200, lambda: refresh_sequence(loading, moodlelogin=moodlelogin))
    loading.mainloop()





# asking for login information:

d1 = ""
d2 = ""
moodle_content = True
def login():
    global AbgabeTermine, moodle_content

    login_info_win = Toplevel()
    login_info_win.resizable(0, 0)
    login_info_win.configure(bg="#282a2b")
    login_info_win.title("Einloggen")
    login_info_win.iconbitmap("moodleReaderIcon.ico")
    login_info_win.resizable(0, 0)

    Label(login_info_win, text="Moodle Username: ", bg="#282a2b", fg="white").grid(row=0, column=0, pady=10, padx=10, sticky=W)
    username = Entry(login_info_win, bg="#575757", fg="white")
    username.grid(row=0, column=1, pady=10, padx=10)

    Label(login_info_win, text="Moodle Passwort: ", bg="#282a2b", fg="white").grid(row=1, column=0, pady=10, padx=10, sticky=W)
    password = Entry(login_info_win, show="*", bg="#575757", fg="white")
    password.grid(row=1, column=1, pady=10, padx=10)

    def submit(moodlelogin):
        global d1, d2, moodle_content
        
        d1 = username.get()
        d2 = password.get()

        login_info_win.destroy()

        try:
            if moodlelogin:
                moodle_content = True
                AbgabeTermine = extract_info(d1, d2)
            else:
                moodle_content = False

            refresh_button.configure(command=lambda: refresh(moodle_content))

            calendar_init(None)
        except:
            messagebox.showerror(title="Error", message="Problem beim einloggen (falsche Moodle Account Daten?), bitte versuchen sie es nochmal!")
            login()


    Button(login_info_win, text="fertig", command=lambda: submit(True)).grid(row=2, column=0, padx=10, pady=10, sticky=W)
    Button(login_info_win, text="ohne einloggen fortfahren", command=lambda: submit(False)).grid(row=2, column=1, padx=10, pady=10)

    login_info_win.mainloop()




login()
root.mainloop()
