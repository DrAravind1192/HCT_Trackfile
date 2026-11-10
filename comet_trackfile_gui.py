import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from astroquery.jplhorizons import Horizons
import pandas as pd
import numpy as np
import re
import time
from datetime import datetime, timedelta
import os
import csv
import shutil
import threading
import subprocess
import sys
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import matplotlib as mpl
import smplotlib

stop_flag = False

# ---------------------------------------------------------
# GUI SETUP
# ---------------------------------------------------------
root = tk.Tk()
root.title("Comet Trackfile Creator for HCT – GUI Version")
root.geometry("600x650")
root.config(bg="#f2f4f7")

title = tk.Label(root, text="COMET TRACKFILE CREATOR FOR HCT, HANLE",
                 font=("Helvetica", 16, "bold"), bg="#f2f4f7")
title.pack(pady=6)

# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
HCT = {'lon': 78.96, 'lat': 32.78, 'elevation': 4500}
months_dict = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

# ---------------------------------------------------------
# INPUT FRAME
# ---------------------------------------------------------
frame = tk.Frame(root, bg="#ffffff", relief="groove", bd=2, padx=10, pady=10)
frame.pack(pady=6, fill="both")

# Month
tk.Label(frame, text="Select Observing Month:", bg="#ffffff").pack(anchor="w")
month_var = tk.StringVar()
month_menu = ttk.Combobox(frame, textvariable=month_var,
                          values=list(months_dict.keys()), state="readonly")
month_menu.pack(fill="x", pady=3)

#warning
tk.Label(
    frame,
    text="* Remember to update this whenever you change the observation date below.",
    bg="#ffffff",
    fg="red",
    font=("Arial", 9, "italic")
).pack(anchor="w")

# Date
tk.Label(frame, text="Enter date of observation [YYYY-MM-DD]:", bg="#ffffff").pack(anchor="w")
date_entry = tk.Entry(frame)
date_entry.insert(0, "YYYY-MM-DD")
date_entry.pack(fill="x", pady=3)

# Object type
tk.Label(frame, text="Select Object Type (Comet/Asteroid):", bg="#ffffff").pack(anchor="w")
obj_type_var = tk.StringVar()
type_menu = ttk.Combobox(frame, textvariable=obj_type_var,
                         values=["Comet", "Asteroid"], state="readonly")
type_menu.pack(fill="x", pady=3)

# Number of objects
tk.Label(frame, text="Number of objects to be observed? (1-10):", bg="#ffffff").pack(anchor="w")
num_var = tk.StringVar()
num_menu = ttk.Combobox(frame, textvariable=num_var,
                        values=[str(i) for i in range(1, 11)], state="readonly")
num_menu.pack(fill="x", pady=3)

# Names frame (dynamic)
names_frame = tk.Frame(frame, bg="#ffffff")
names_frame.pack(pady=5, fill="both")

name_entries = []               # list of Entry widgets
disintegrated_vars = []         # list of BooleanVar for each entry (True = disintegrated)

def generate_name_entries(*args):
    # Clear previous widgets
    for w in names_frame.winfo_children():
        w.destroy()
    name_entries.clear()
    disintegrated_vars.clear()

    try:
        count = int(num_var.get())
    except:
        return

    for i in range(count):
        row = tk.Frame(names_frame, bg="#ffffff")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text=f"Enter name of object {i+1}:", bg="#ffffff")
        lbl.pack(side="left")

        e = tk.Entry(row, width=40)
        e.pack(side="left", padx=8)
        name_entries.append(e)

        # Per-comet disintegration tickbox (Checkbutton)
        var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(row, text="Disintegrated (Check box if True)", variable=var, bg="#ffffff")
        cb.pack(side="left", padx=8)
        disintegrated_vars.append(var)

num_menu.bind("<<ComboboxSelected>>", generate_name_entries)

# ---------------------------------------------------------
# VISIBILITY PLOT TOGGLE
# ---------------------------------------------------------

visibility_var = tk.BooleanVar(value=True)
visibility_chk = tk.Checkbutton(frame, text="Generate Visibility Plot?", variable=visibility_var, bg="#ffffff")
visibility_chk.pack(anchor="w", pady=5)

# ---------------------------------------------------------
# CONSOLE OUTPUT
# ---------------------------------------------------------
console_label = tk.Label(root, text="Console Output:", bg="#f2f4f7", anchor="w")
console_label.pack(fill="x", padx=12)
console = scrolledtext.ScrolledText(root, height=8, width=110, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
console.pack(padx=12, pady=4)

def log(msg):
    console.configure(state="normal")
    console.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}\n")
    console.see(tk.END)
    console.configure(state="disabled")
    root.update_idletasks()

# ---------------------------------------------------------
# PROGRESS BAR
# ---------------------------------------------------------
progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=680)
progress.pack(pady=6)

# ---------------------------------------------------------
# OPEN FINAL FOLDER BUTTON (disabled until completion)
# ---------------------------------------------------------
def open_final_folder():
    folder = os.path.abspath("Final")
    if not os.path.exists(folder):
        messagebox.showerror("Error", "Final folder does not exist yet.")
        return
    if sys.platform.startswith("darwin"):
        subprocess.call(["open", folder])
    elif os.name == "nt":
        os.startfile(folder)
    else:
        subprocess.call(["xdg-open", folder])

open_final_btn = tk.Button(root, text="Open Final Folder", command=open_final_folder, state="disabled")
open_final_btn.pack(pady=3)

# ---------------------------------------------------------
# VISIBILITY: container to store ephemerides for plotting
# ---------------------------------------------------------
visibility_eph = []   # list of dicts {name, dates (datetime list), elev (list)}


# ---------------------------------------------------------
# PROCESSING FUNCTION (runs in separate thread)
# ---------------------------------------------------------
def run_process_thread():
    #t = threading.Thread(target=run_process, daemon=True)
    #t.start()
    run_process()
    
def done():
    print("Finished work, closing GUI...")

    # Close all Matplotlib figures before destroying Tkinter
    try:
        plt.close('all')
    except Exception as e:
        print("Error closing matplotlib figures:", e)

    # Quit the Tkinter main loop
    root.quit()

    # Destroy the main Tkinter window
    root.destroy()

def run_process():

    # Input validation
    if month_var.get() == "":
        messagebox.showerror("Error", "Select month.")
        return

    try:
        start_date = datetime.strptime(date_entry.get(), "%Y-%m-%d")
    except Exception:
        messagebox.showerror("Error", "Date must be in YYYY-MM-DD format.")
        return

    stop_date = start_date + timedelta(days=2)  
    month = month_var.get()
    month_no = months_dict[month]

    if obj_type_var.get() == "":
        messagebox.showerror("Error", "Select object type.")
        return

    try:
        n = int(num_var.get())
    except Exception:
        messagebox.showerror("Error", "Select number of objects.")
        return

    if len(name_entries) < n:
        messagebox.showerror("Error", "Please generate and fill all name entries.")
        return

    names = [e.get().strip() for e in name_entries]
    if any(name == "" for name in names):
        messagebox.showerror("Error", "All names must be filled.")
        return

    # Determine idtype
    if obj_type_var.get() == "Comet":
        idtype_default = "designation"
    else:
        idtype_default = "name"

    # Prepare Final folder
    os.makedirs("Final", exist_ok=True)
    date_tag = start_date.strftime("%Y_%m_%d")
    date_tag_compact = start_date.strftime("%Y%m%d")
    generated_trackfiles = []

    def write_jpl_error(object_name, error):
        object_name_clean = re.sub(r'[ /]', '', object_name)
        error_file = os.path.join(
            "Final", f"{object_name_clean}_{date_tag_compact}_jplerror.log"
        )
        with open(error_file, "a", encoding="utf-8") as error_handle:
            error_handle.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{object_name}: {error}\n"
            )

    progress["value"] = 0
    progress["maximum"] = n
    log("Starting processing...")

    # Clear any previous visibility data
    visibility_eph.clear()

    for i in range(n):
        comet_name = names[i]
        dis_flag = disintegrated_vars[i].get()   # True if disintegrated
        log(f"Processing: {comet_name}    Disintegrated: {'Yes' if dis_flag else 'No'}")

        # -------------------- Trackfile ephemeris (original step '5760') --------------------
        try:
            if not dis_flag:
                # NOT disintegrated -> include id_type
                obj = Horizons(id=comet_name, location=HCT,
                               epochs={'start': str(start_date),
                                       'stop': str(stop_date),
                                       'step': '5760'},
                               id_type=idtype_default)
            else:
                # Disintegrated -> omit id_type
                obj = Horizons(id=comet_name, location=HCT,
                               epochs={'start': str(start_date),
                                       'stop': str(stop_date),
                                       'step': '5760'})
            eph = obj.ephemerides(quantities='4,5', closest_apparition=True,
                                  skip_daylight=False, airmass_lessthan=3.0)
        except Exception as e:
            log(f"ERROR retrieving ephemeris for trackfile {comet_name}: {e}")
            write_jpl_error(comet_name, e)
            progress["value"] = i + 1
            root.update_idletasks()
            continue

        comet_name_clean = re.sub(r'[ /]', '', comet_name)

        # find start and end lines 
        try:
            for j in range(len(eph['datetime_str']) - 1):
                if int(eph['datetime_str'][j+1][12:14]) - int(eph['datetime_str'][j][12:14]) > 1:
                    line_start = j + 1
                    break
            else:
                line_start = 0

            for j in range(line_start, len(eph['datetime_str']) - 1):
                if int(eph['datetime_str'][j+1][12:14]) - int(eph['datetime_str'][j][12:14]) > 1:
                    line_end = j + 1
                    break
            else:
                line_end = len(eph['datetime_str'])
        except Exception as e:
            log(f"ERROR parsing ephemeris table for {comet_name}: {e}")
            progress["value"] = i + 1
            root.update_idletasks()
            continue

        # Write initial TXT 
        txt = comet_name_clean + ".txt"
        try:
            with open(txt, "w") as f:
                w = csv.writer(f, delimiter=" ")
                f.write('Date_(UT) HR:MN:SC Azi Elev dAZ*cosE d(ELV)/dt\n')
                w.writerows(list(zip(
                    eph['datetime_str'][line_start:line_end],
                    eph['AZ'][line_start:line_end],
                    eph['EL'][line_start:line_end],
                    eph['AZ_rate'][line_start:line_end],
                    eph['EL_rate'][line_start:line_end]
                )))
        except Exception as e:
            log(f"ERROR writing initial txt for {comet_name}: {e}")
            progress["value"] = i + 1
            root.update_idletasks()
            continue

        txt1 = comet_name_clean + "_1.txt"
        try:
            with open(txt, "r") as f, open(txt1, "w") as fo:
                for line in f:
                    fo.write(line.replace('"', '').replace("'", ""))
        except Exception as e:
            log(f"ERROR creating {txt1} for {comet_name}: {e}")
            progress["value"] = i + 1
            root.update_idletasks()
            continue

        # Read and rewrite columns
        try:
            data = pd.read_csv(txt1, sep=' ')
            data.columns = ['Date', 'Time', 'Azi', 'Elev', 'Azi_cosE', 'Elev_rate']
            data.to_csv(txt1, sep=' ', index=False)
        except Exception as e:
            log(f"ERROR processing CSV for {comet_name}: {e}")
            progress["value"] = i + 1
            root.update_idletasks()
            continue

        time.sleep(0.5)

        # Trackfile computations
        try:
            data = pd.read_csv(txt1, sep=' ')
            zeroes = np.zeros(len(data.Date), dtype=np.int64)
            num_arr = np.arange(0, len(data.Date), 1)
            num_1 = [x * 30 for x in num_arr]

            az_rate = [x / (np.cos(np.deg2rad(y))) for x, y in zip(data.Azi_cosE, data.Elev)]
            az_rate_final = [x / (60 * 60 * 60) for x in az_rate]
            el_rate_final = [x / (60 * 60 * 60) for x in data.Elev_rate]

            trk = comet_name_clean + "_final.trk"
            with open(trk, "w") as f:
                w = csv.writer(f, delimiter="\t")
                date_1 = re.sub('-', '/', data.Date[0])
                date_1 = date_1.replace(month, month_no)

                f.write("%s %s\n" % (date_1, data.Time[0][:-4]))
                f.write(str(len(data.Date)) + "\n")
                w.writerows(zip(
                    num_1, np.round(data.Azi, 5), np.round(az_rate_final, 5),
                    zeroes, zeroes, np.round(data.Elev, 5),
                    np.round(el_rate_final, 5),
                    zeroes, zeroes, zeroes, zeroes, zeroes, zeroes
                ))
        except Exception as e:
            log(f"ERROR while creating trackfile for {comet_name}: {e}")
            progress["value"] = i + 1
            root.update_idletasks()
            continue

        try:
            awk_out = f"{comet_name_clean}_{date_tag}.trk"
            cmd = (
                "awk ' {if (NR<3) print $0; else { "
                "{ if ($2 > 325) {az=$2-360} else {az=$2}} ;  "
                "printf \"%d\t%8.5f\t%8.5f\t0\t0\t%8.5f\t%8.5f\t0\t0\t0\t0\t0\t0\\n\",$1,az,$3,$6,$7 }}' "
                + trk + " > " + awk_out
            )
            os.system(cmd)
            if os.path.exists(awk_out):
                generated_trackfiles.append(awk_out)
        except Exception as e:
            log(f"ERROR executing awk for {comet_name}: {e}")
        progress["value"] = i + 1
        root.update_idletasks()
        log(f"Finished: {comet_name}")

        # -------------------- Visibility ephemeris (10m step, 1-day range) --------------------
        # We call Horizons again with step='10m' to build a smooth visibility curve for each comet.
        
    if visibility_var.get():
        names.append('301')
        disintegrated_vars.append(disintegrated_vars[0])
        # For each comet
        for i in range(n+1):
            comet_name = names[i]
            dis_flag = disintegrated_vars[i].get()
            try:
                vis_stop = start_date + timedelta(days=1)
                if not dis_flag and i!=n:
                    obj_vis = Horizons(id=comet_name, location=HCT,epochs={'start': str(start_date), 'stop': str(vis_stop), 'step': '10m'},id_type=idtype_default)        
                else:
                    obj_vis = Horizons(id=comet_name, location=HCT,epochs={'start': str(start_date), 'stop': str(vis_stop), 'step': '10m'})
                eph_vis = obj_vis.ephemerides(quantities='4,5', closest_apparition=True, skip_daylight=False)
                # Convert times and elevations into datetime and float arrays for plotting
                UT_list = list(eph_vis['datetime_str'])
                AZ_list = list(eph_vis['AZ'])
                EL_list = list(eph_vis['EL'])
                # detect first continuous block
                line_num = 0
                for j in range(0, len(UT_list)-1):
                    try:
                        if int(UT_list[j+1][12:14]) - int(UT_list[j][12:14]) > 1:
                            line_num = j+1
                    except:
                        continue
                # Use the remainder from line_num to end
                times_block = UT_list[line_num:]
                times_block[-1] = times_block[-1][:-5] + "23:59" if times_block[-1].endswith("00:00") else times_block[-1]
                elev_block = EL_list[line_num:]
                # convert HH:MM strings into datetime objects (date = start_date)
                # UT strings are 'YYYY-MMM-DD HH:MM' or similar; to be robust parse using datetime
                dt_list = []
                for tstr in times_block:
                    # try parsing ISO-like string
                    try:
                        dt = datetime.strptime(tstr.split()[0] + ' ' + tstr.split()[1], '%Y-%m-%d %H:%M')
                    except Exception:
                        # fallback: try to parse just time and combine with start_date
                        try:
                            hhmm = tstr.split()[1]
                            dt = datetime.combine(start_date.date(), datetime.strptime(hhmm, '%H:%M').time())
                        except:
                            continue
                    dt_list.append(dt)
                
                visibility_eph.append({'name': comet_name, 'dt': dt_list, 'elev': elev_block})
            except Exception as e:
                    log(f"ERROR retrieving ephemeris for visibility {comet_name}: {e}")
                    write_jpl_error(comet_name, e)
            # do not abort; continue

            # Update progress
            progress["value"] = i + 1
            root.update_idletasks()
            log(f"Finished: {comet_name}")

    # Finalize: move generated trackfiles to Final.
    try:
        os.makedirs("Final", exist_ok=True)
        for trackfile in generated_trackfiles:
            shutil.move(trackfile, os.path.join("Final", os.path.basename(trackfile)))
    except Exception as e:
        log(f"ERROR moving files to Final/: {e}")
    
    
    for i in range(0,len(names)-1):
        comet_name = names[i]
        comet_name_clean = re.sub(r'[ /]', '', comet_name)
        os.system("rm "+comet_name_clean+".txt")
        os.system("rm "+comet_name_clean+"_1.txt")
        os.system("rm "+comet_name_clean+"_final.trk")


    log("Processing completed. Files created - Check folder Final/")
    messagebox.showinfo("Done", "Trackfiles successfully created.\nCheck the folder: Final/")
    open_final_btn.config(state="normal")

    # After processing, automatically show visibility plot for all comets collected
    try:
        if len(visibility_eph) > 0:
            show_visibility_plot(visibility_eph, start_date)
    except Exception as e:
        log(f"ERROR while plotting visibility: {e}")
        


# ---------------------------------------------------------
# VISIBILITY PLOTTING FUNCTION (opens separate matplotlib window)
# ---------------------------------------------------------
def show_visibility_plot(visibility_list, start_date):
    """
    visibility_list: list of dicts {'name':..., 'dt': [datetime,...], 'elev': [...]}
    """
    fig, ax = plt.subplots(layout='tight')
    # plot each comet's elevation curve
    for entry in visibility_list:
        name = entry['name']
        dt_list = entry['dt']
        elev_list = [float(x) for x in entry['elev']] if len(entry['elev']) == len(dt_list) else [float(x) for x in entry['elev'][:len(dt_list)]]
        
        
        if name == '301':
            ax.plot(matplotlib.dates.date2num(dt_list), elev_list, 'r--', label='Moon')
        else:
            ax.plot(matplotlib.dates.date2num(dt_list), elev_list, '-', label=name)

    # night vertical line at 13:30 UT
    night_time = '13:30'
    night_obj = datetime.strptime(night_time, '%H:%M').time()
    plot_night = datetime.combine(start_date, night_obj)
    night = matplotlib.dates.date2num(plot_night)

    # x limits: start_date 05:00 to start_date+1 00:00
    start_obj = datetime.strptime('08:00', '%H:%M').time()
    end_obj = datetime.strptime('00:00', '%H:%M').time()
    plot_start = datetime.combine(start_date, start_obj)
    plot_end = datetime.combine(start_date + timedelta(days=1), end_obj)

    start_num = matplotlib.dates.date2num(plot_start)
    end_num = matplotlib.dates.date2num(plot_end)
    
    ax.axhline(20,xmin=0,xmax=1,ls='--',color='k')
    ax.axvline(night,ymin=0,ymax=1,ls='--',color='k')
    ax.text(night,75,'Night',rotation=90,fontsize=20)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(which='both', width=1)
    ax.tick_params(axis='both',which='major', length=10,color='k')
    ax.tick_params(axis='both',which='minor', length=6, color='k')
    xlabel = start_date.strftime('%Y-%m-%d') + ' UT'
    ax.set_xlabel(xlabel,fontsize=22)
    ax.set_ylabel('Elevation (deg)',fontsize=22)
    ax.tick_params(axis='x',which='both',direction='in', bottom=True, top=True,labelsize=20)
    ax.tick_params(axis='y',which='both',direction='in', left=True, right=True,labelsize=20)
    ax.grid(False)
    ax.spines['bottom'].set_color('black')
    ax.spines['top'].set_color('black')
    ax.spines['left'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    ax.tick_params(axis='both', colors='black')
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=120))
    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.set_xlim(start_num, end_num)
    ax.set_ylim(7,90)
    ax.legend(fontsize=20,loc='upper right',frameon=True)
    
    ax.set_title('Visibility curve', fontsize=24)
    fig.set_size_inches(12, 8)

    # show plot in external window
    plt.show(block='True')

    # ask user whether to save
    save = messagebox.askyesno("Save plot", "Do you want to save the visibility plot as 'Visibility_date.png' in the Final folder?")
    if save:
        try:
            fig.savefig(os.getcwd()+'/Final/Visibility_'+xlabel[:-3]+'.png', bbox_inches='tight', dpi=100)
            log("Visibility plot saved as Visibility_"+xlabel[:-3]+".png")
        except Exception as e:
            log(f"ERROR saving visibility plot: {e}")
    #else:
    #    plt.close()



# ---------------------------------------------------------
# RUN BUTTON
# ---------------------------------------------------------
run_button = tk.Button(root, text="Run Trackfile Generator",
                       command=run_process_thread, bg="#008753", fg="white",
                       font=("Arial", 11, "bold"), padx=10, pady=6)
run_button.pack(pady=5)

# ---------------------------------------------------------
# RED WARNING MESSAGE
# ---------------------------------------------------------
warning = tk.Label(root,
    text="If you encounter the error 'ValueError: Ambiguous target name; provide unique id:',\n"
         "choose the appropriate unique id (Record #) shown in the terminal and re-run.",
    fg="red", bg="#f2f4f7",
    font=("Arial", 8, "bold")
)
warning.pack(pady=4)

root._after_id = root.after(1, lambda: None)

btn = tk.Button(root, text="Finish", command=done)
btn.pack()

root.mainloop()

print("GUI closed, terminal back to normal in few seconds.")
