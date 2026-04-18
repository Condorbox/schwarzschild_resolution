"""
Shared visual style constants.
"""


class STYLE:
    # Reference circles / rings
    PHOTON_SPHERE_COLOR = "#fbbf24"
    PHOTON_SPHERE_LS = "--"
    PHOTON_SPHERE_LABEL = "Photon sphere (1.5 rs)"

    ISCO_COLOR = "#a78bfa"
    ISCO_LS = ":"
    ISCO_LABEL = "ISCO (3.0 rs)"

    # Geodesic path
    TRAJECTORY_COLOR = "#00d4ff"
    TRAJECTORY_LW = 1.5
    TRAJECTORY_ALPHA = 0.9
    TRAJECTORY_LABEL = "Geodesic path"

    # Start / end markers
    START_COLOR = "#39d353"
    END_COLOR = "#f472b6"
    PLUNGE_COLOR = "#ff6b35"

    # Grid / background
    GRID_COLOR = "#333344"
    HORIZON_COLOR = "black"
    HORIZON_EDGE = "#ffffff"

    # Window / panel backgrounds
    UI_BG       = "#18181b"
    UI_PANEL_BG = "#1f1f23"
    UI_BORDER   = "#2e2e35"
    UI_CANVAS_BG = "#0f0f12"
    UI_GRID     = "#1e1e26"
 
    # Text
    UI_TEXT       = "#e4e4e7"
    UI_TEXT_MUTED = "#71717a"

    # Accent colours
    UI_ACCENT = TRAJECTORY_COLOR        # "#00d4ff"
    UI_GREEN  = START_COLOR             # "#39d353"
    UI_PINK   = END_COLOR               # "#f472b6"
    UI_ORANGE = PLUNGE_COLOR            # "#ff6b35"
    UI_AMBER  = PHOTON_SPHERE_COLOR     # "#fbbf24"
    UI_PURPLE = ISCO_COLOR              # "#a78bfa"

    # UI typography
    FONT_FAMILY = "Inter"                    # macOS 12+ / Windows 11 built-in
    FONT_FAMILY_FALLBACK = "Helvetica Neue"  # older macOS / Linux

    FONT_TITLE   = (FONT_FAMILY, 13, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 11)
    FONT_LABEL   = (FONT_FAMILY, 10)
    FONT_LABEL_BOLD = (FONT_FAMILY, 10, "bold")
    FONT_SMALL   = (FONT_FAMILY, 9)
    FONT_SMALL_BOLD = (FONT_FAMILY, 9, "bold")
    FONT_STAT    = (FONT_FAMILY, 13, "bold")
    FONT_BTN     = (FONT_FAMILY, 11, "bold")
    FONT_LEGEND  = (FONT_FAMILY, 9)
    FONT_RADIOLABEL = (FONT_FAMILY, 10)
    FONT_CANVAS  = (FONT_FAMILY, 8)

