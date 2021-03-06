# -*- coding: utf-8 -*-
import os
import re
import subprocess
import socket

from libqtile import bar, hook, layout
from libqtile.command import lazy
from libqtile.config import Drag, Group, Key, Screen, ScratchPad, DropDown
from libqtile.widget import (Battery, Clock, CurrentLayout, CurrentLayoutIcon,
                             GroupBox, Notify, Prompt, Sep, Systray, TaskList,
                             TextBox, LaunchBar, Wallpaper)
from libqtile.extension.dmenu import Dmenu

DEBUG = os.environ.get("DEBUG")
HOME = os.path.expanduser("~") + "/"

GREY = "#444444"
DARK_GREY = "#333333"
BLUE = "#007fcf"
DARK_BLUE = "#005083"
ORANGE = "#dd6600"
DARK_ORANGE = "#582c00"


def window_to_prev_group():
    @lazy.function
    def __inner(qtile):
        i = qtile.groups.index(qtile.currentGroup)
        if qtile.currentWindow and i != 0:
            group = qtile.groups[i - 1].name
            qtile.currentWindow.togroup(group)

    return __inner


def window_to_next_group():
    @lazy.function
    def __inner(qtile):
        i = qtile.groups.index(qtile.currentGroup)
        if qtile.currentWindow and i != len(qtile.groups):
            group = qtile.groups[i + 1].name
            qtile.currentWindow.togroup(group)

    return __inner


def window_to_prev_screen():
    @lazy.function
    def __inner(qtile):
        i = qtile.screens.index(qtile.currentScreen)
        if i != 0:
            group = qtile.screens[i - 1].group.name
            qtile.currentWindow.togroup(group)

    return __inner


def window_to_next_screen():
    @lazy.function
    def __inner(qtile):
        i = qtile.screens.index(qtile.currentScreen)
        if i + 1 != len(qtile.screens):
            group = qtile.screens[i + 1].group.name
            qtile.currentWindow.togroup(group)

    return __inner


def switch_screens():
    @lazy.function
    def __inner(qtile):
        i = qtile.screens.index(qtile.currentScreen)
        group = qtile.screens[i - 1].group
        qtile.currentScreen.setGroup(group)

    return __inner


@hook.subscribe.client_new
def set_floating(window):
    floating_types = ["notification", "toolbar", "splash", "dialog"]
    floating_roles = ["EventDialog", "Msgcompose", "Preferences"]
    floating_names = ["Terminator Preferences"]

    if (window.window.get_wm_type() in floating_types
            or window.window.get_wm_window_role() in floating_roles
            or window.window.get_name() in floating_names
            or window.window.get_wm_transient_for()):
        window.floating = True


def init_keys():
    keys = [
        Key([mod], "p", lazy.screen.prev_group(skip_managed=True)),
        Key([mod], "n", lazy.screen.next_group(skip_managed=True)),
        Key([mod, "shift"], "Left", window_to_prev_group()),
        Key([mod, "shift"], "Right", window_to_next_group()),
        Key([mod, "mod1"], "Left", lazy.prev_screen()),
        Key([mod, "mod1"], "Right", lazy.next_screen()),
        Key([mod, "shift", "mod1"], "Left", window_to_prev_screen()),
        Key([mod, "shift", "mod1"], "Right", window_to_next_screen()),
        Key([mod], "t", switch_screens()),
        Key([mod], "l", lazy.group.next_window()),
        Key([mod], "h", lazy.group.prev_window()),
        Key([mod], "space", lazy.next_layout()),
        Key([mod], "j", lazy.layout.up()),
        Key([mod], "k", lazy.layout.down()),
        Key([mod], "f", lazy.window.toggle_floating()),
        Key([mod], "r", lazy.spawncmd()),
        # yaourt i3lock
        Key([mod, "mod1"], "l", lazy.spawn("i3lock")),
        Key([mod], "u", lazy.spawn(browser_chromium)),
        Key([mod], "x", lazy.spawn(browser_firefox)),
        Key([mod], "Return", lazy.spawn(terminal)),
        Key([mod], "BackSpace", lazy.window.kill()),
        Key([mod, "control"], "r", lazy.restart()),
        Key([mod, "control"], "q", lazy.shutdown()),
        # region this "scrot" app can use -s to select an area of screen
        # Key([], "Print", lazy.spawn("scrot")),
        # Key([mod], "s", lazy.spawn("scrot -s '%Y-%m-%d_$wx$h.png' -e 'mv $f /home/dlwxxxdlw/Screenshots/'")),
        # Key([mod, "control"], "s", lazy.spawn("scrot -s '/home/dlwxxxdlw/Screenshots/%Y-%m-%d_$wx$h.png'")),
        # Key([mod], "s", lazy.spawn("scrot -e 'mv $f /home/dlwxxxdlw/Screenshots/'")),
        # Key([], "Scroll_Lock", lazy.spawn(HOME + ".local/bin/i3lock -d")),
        # endregion
        Key([mod], "Delete", lazy.spawn("amixer set Master toggle")),
        Key([mod], "Prior", lazy.spawn("amixer set Master 5+")),
        Key([mod], "Next", lazy.spawn("amixer set Master 5-")),
        Key([mod], "Insert",
            lazy.spawn(HOME + ".local/bin/spotify-dbus playpause")),
        Key([mod], "End", lazy.spawn(HOME + ".local/bin/spotify-dbus next")),
        Key([mod], "Home",
            lazy.spawn(HOME + ".local/bin/spotify-dbus previous")),
    ]
    if DEBUG:
        keys += [
            Key(["mod1"], "Tab", lazy.layout.next()),
            Key(["mod1", "shift"], "Tab", lazy.layout.previous())
        ]
    return keys


def init_mouse():
    return [
        Drag(
            [mod],
            "Button1",
            lazy.window.set_position_floating(),
            start=lazy.window.get_position()),
        Drag(
            [mod],
            "Button3",
            lazy.window.set_size_floating(),
            start=lazy.window.get_size())
    ]


def init_groups():
    def _inner(key, name):
        keys.append(Key([mod], key, lazy.group[name].toscreen()))
        keys.append(Key([mod, "shift"], key, lazy.window.togroup(name)))
        return Group(name)

    # groups = [("dead_grave", "00")]
    groups = [(str(i), "0" + str(i)) for i in range(1, 10)]
    groups += [("0", "10"), ("minus", "11"), ("equal", "12")]
    res_groups = [_inner(*i) for i in groups]
    res_groups += [
        ScratchPad("scratchpad",
                   [DropDown("fish", "roxterm", height=0.5, opacity=0.6)])
    ]
    keys.append(
        Key([], 'Pause', lazy.group['scratchpad'].dropdown_toggle('fish')))
    return res_groups


def init_floating_layout():
    return layout.Floating(border_focus=BLUE)


def init_widgets():
    prompt = "{0}@{1}: ".format(os.environ["USER"], hostname)
    widgets = [
        Prompt(
            prompt=prompt,
            font="DejaVu Sans Mono",
            padding=10,
            background=GREY),
        TextBox(
            text="◤ ",
            fontsize=45,
            padding=-8,
            foreground=GREY,
            background=DARK_GREY),
        CurrentLayoutIcon(scale=0.6, padding=-4),
        TextBox(text=" ", padding=2),
        GroupBox(
            fontsize=8,
            padding=4,
            borderwidth=1,
            urgent_border=DARK_BLUE,
            disable_drag=True,
            highlight_method="block",
            this_screen_border=DARK_BLUE,
            other_screen_border=DARK_ORANGE,
            this_current_screen_border=BLUE,
            other_current_screen_border=ORANGE),
        TextBox(
            text="◤",
            fontsize=45,
            padding=-1,
            foreground=DARK_GREY,
            background=GREY),
        TaskList(
            borderwidth=0,
            highlight_method="block",
            background=GREY,
            border=DARK_GREY,
            urgent_border=DARK_BLUE),
        Systray(background=GREY),
        Wallpaper(
            directory="/home/dlwxxxdlw/Pictures/wallpapers",
            random_selection=True,
            wallpaper_command=['feh', '--bg-max']
        ),
        # LaunchBar needs some dependencies, use yaourt to install them
        LaunchBar(progs=[
            (  # yaourt thunderbird virtualbox
                'thunderbird', 'thunderbird', 'launch thunderbird'),
            ('virtualbox', 'virtualbox', 'launch virtualbox'),
            ('thunar', 'thunar', 'launch thunar'),
            (
                'aria',  # get this from github
                'firefox --new-tab ~/Downloads/aria-ng/index.html',
                'aria'),
            ('shutter', 'shutter', 'launch shutter'),
            ('ss', 'ss-qt5', 'launch shadowsocks-qt5'),
            ('Tim', '/opt/deepinwine/apps/Deepin-TIM/run.sh', 'launch Tim'),
            ('Thunder', '/opt/deepinwine/apps/Deepin-ThunderSpeed/run.sh', 'launch Thunder')
        ]),
        TextBox(
            text="◤",
            fontsize=45,
            padding=-1,
            foreground=GREY,
            background=DARK_GREY),
        TextBox(text=" ⚠", foreground=BLUE, fontsize=18),
        Notify(),
        TextBox(text=" ⌚", foreground=BLUE, fontsize=18),
        Clock(format="%A %d-%m-%Y %H:%M")
    ]
    if hostname in ("spud", "saiga"):
        widgets[-2:-2] = [
            TextBox(text=" ↯", foreground=BLUE, fontsize=14),
            Battery(update_delay=2)
        ]
    if DEBUG:
        widgets += [Sep(), CurrentLayout()]
    return widgets


def init_top_bar():
    return bar.Bar(widgets=init_widgets(), size=22, opacity=1)


def init_widgets_defaults():
    return dict(font="DejaVu", fontsize=11, padding=2, background=DARK_GREY)


def init_screens(num_screens):
    for _ in range(num_screens - 1):
        screens.insert(0, Screen())


def init_layouts(num_screens):
    margin = 0
    if num_screens > 1:
        margin = 8
    layouts.extend([
        layout.Tile(
            ratio=0.5,
            margin=margin,
            border_width=1,
            border_normal="#111111",
            border_focus=BLUE)
    ])


# very hacky, much ugly
def main(qtile):
    num_screens = len(qtile.conn.pseudoscreens)
    init_screens(num_screens)
    init_layouts(num_screens)


def is_running(process):
    s = subprocess.Popen(["ps", "axuw"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x.decode()):
            return True
    return False


def execute_once(process):
    """
    execute a application once
    :Keyword Arguments:
     process -- application
    :return: None
    """
    if not is_running(process):
        return subprocess.Popen(process.split())


@hook.subscribe.startup
def startup():
    """
    start the applications when qtile startup
    :return: None
    """
    execute_once("nm-applet")  # yaourt network manager applet
    execute_once("fcitx")  # yaourt fcitx
    execute_once("aria2c --conf-path=/home/dlwxxxdlw/.config/aria2/aria2.conf")
    execute_once("source /home/dlwxxxdlw/.bashrc")


if __name__ in ["config", "__main__"]:
    if HOME + ".local/bin" not in os.environ["PATH"]:
        os.environ["PATH"] = HOME + ".local/bin:{}".format(os.environ["PATH"])

    mod = "mod4"
    browser_chromium = "chromium"  # yaourt chromium
    browser_firefox = "firefox"  # yaourt firefox
    terminal = "roxterm"  # yaourt roxterm
    hostname = socket.gethostname()
    # follow_mouse_focus = True # not sure what this means
    # never set "cursor_warp" True ,it will make your mouse
    # back to screen center when you clicked in the virtualbox
    cursor_warp = False

    keys = init_keys()
    mouse = init_mouse()
    # not sure what this means yet
    # focus_on_window_activation = "smart"
    groups = init_groups()
    floating_layout = init_floating_layout()
    layouts = [layout.Max()]
    screens = [Screen(top=init_top_bar())]
    widget_defaults = init_widgets_defaults()
    # region don't know how to use Dmenu
    Dmenu(command=["shutdown", "reboot"], dmenu_font="DejaVu Sans Mono"),
    # endregion

    if DEBUG:
        layouts += [
            floating_layout,
            layout.Stack(),
            layout.Zoomy(),
            layout.Matrix(),
            layout.TreeTab(),
            layout.MonadTall(),
            layout.RatioTile(),
            layout.Slice(
                'left',
                192,
                name='slice-test',
                role='gnome-terminal',
                fallback=layout.Slice(
                    'right',
                    256,
                    role='gimp-dock',
                    fallback=layout.Stack(stacks=1)))
        ]
