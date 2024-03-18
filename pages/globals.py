############################
# ICSB Dashboard - Globals #
############################
# author:   jbetley (https://github.com/jbetley)
# version:  1.15
# date:     02/21/24

max_display_years = 5

# Colors
# https://codepen.io/ctf0/pen/BwLezW
color = [
    "#7b6888",
    "#df8f2d",
    "#a8b462",
    "#ebbb81",
    "#74a2d7",
    "#d4773f",
    "#83941f",
    "#f0c33b",
    "#bc986a",
    "#96b8db",
]

subject = ["Math", "ELA"]

info_categories = ["School Name", "Low Grade", "High Grade"]

ethnicity = [
    "American Indian",
    "Asian",
    "Black",
    "Hispanic",
    "Multiracial",
    "Native Hawaiian or Other Pacific Islander",
    "White",
]

subgroup = [
    "Special Education",
    "General Education",
    "Paid Meals",
    "Free or Reduced Price Meals",
    "English Language Learners",
    "Non English Language Learners",
]

grades = ["Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8"]

grades_all = ["Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Total"]

grades_ordinal = ["3rd", "4th", "5th", "6th", "7th", "8th"]

# default table styles
table_style = {"border": "none", "fontFamily": "Inter, sans-serif"}

table_cell = {
    "whiteSpace": "normal",
    "height": "auto",
    "textAlign": "center",
    "color": "#6783a9",
    "minWidth": "25px",
    "width": "25px",
    "maxWidth": "25px",
}

table_header = {
    "backgroundColor": "#ffffff",
    "fontSize": "12px",
    "fontFamily": "Montserrat, sans-serif",
    "color": "#6783a9",
    "textAlign": "center",
    "fontWeight": "bold",
    "border": "none",
}

# K8 Not yet included: 1.3.a, 1.3.b (Mission Specific)
# K8 Deprecated: 1.2.a, 1.2.b, 1.5.a, 1.5.b
# HS Depracted:  1.7.d, 1.7.e
# AHS Deprecated: 1.2.a, 1.2b
# AHS Not Calculated (K8 standards 1.4a & 1.4b)

metric_strings = {
    # AHS
    "1.1": [
        "The school received an A on under the State's Adult Accountability system.",
        "The school received an B on under the State's Adult Accountability system.",
        "The school received an C on under the State's Adult Accountability system.",
        "The school received an D on under the State's Adult Accountability system.",
    ],
    # AHS
    "1.3": [
        "Fifty percent (50%) or more of graduates achieved at least one CCR indicator.",
        "Between (36.8-49.9%) of graduates achieved at least one CCR indicator.",
        "Between (23.4-36.7%) of graduates achieved at least one CCR indicator.",
        "Less than (23.4%) of of graduates achieved at least one CCR indicator.",
    ],
    # same ratings as 1.1.b
    "1.1.a": [
        "Above the school corporation average.",
        "At or within one percent (1%) of the school corporation average.",
        "",
        "More than one percent (1%) below the school corporation average.",
    ],
    # combined 1.1.c and 1.1.d
    "1.1.c": [
        "More than ninety percent (90%) of the students eligible to return to the school re-enrolled the next year (85% re-enrolled year over year).",
        "Between eighty and ninety percent (80-90%) of the students eligible to return to the school re-enrolled the next year (75-85% re-enrolled year over year).",
        "Between seventy and eighty percent (70-80%) of the students eligible to return to the school re-enrolled the next year (70-75% re-enrolled year over year).",
        "Less than seventy percent (70%) of the students eligible to return to the school re-enrolled the next year (70% re-enrolled year over year).",
    ],
    "1.1.d": [
        "More than eighty-five percent (85%) of the students eligible to return to the school re-enrolled over time.",
        "Between seventy-five and eighty-five percent (75-85%) of the students eligible to return to the school re-enrolled over time.",
        "Between seventy and seventy-five percent (70-75%) of the students eligible to return to the school re-enrolled over time.",
        "Less than seventy percent (70%) of the students eligible to return to the school re-enrolled over time.",
    ],
    "1.4.a": [
        "Increase of more than five percent (5%) from the previous year.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year.",
        "Decrease from the previous school year.",
    ],
    "1.4.b": [
        "Increase of more than five percent (5%) from the previous year.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year.",
        "Decrease from the previous school year.",
    ],
    "1.4.c": [
        "Ten percent (10%) or higher than comparable public schools.",
        "Between two and ten percent (2-10%) higher than comparable schools.",
        "Between the same as and two percent (2%) higher than comparable schools.",
        "Less than comparable schools.",
    ],
    "1.4.d": [
        "Ten percent (10%) or higher than comparable public schools.",
        "Between two and ten percent (2-10%) higher than comparable schools.",
        "Between the same as and two percent (2%) higher than comparable schools.",
        "Less than comparable schools.",
    ],
    # same ratings as 1.4.f
    "1.4.e": [
        "More than eighty percent (80%).",
        "Between seventy and eighty percent (70-80%).",
        "Between sixty and seventy percent (60-70%).",
        "Less than sixty percent (60%).",
    ],
    "1.4.g": [
        "More than ninety percent (90%).",
        "Between eighty and ninety percent (80-90%).",
        "Between seventy and eighty percent (70-80%).",
        "Less than seventy percent (70%).",
    ],
    "1.5.c": [
        "The median SGP for all students is more than sixty (60).",
        "The median SGP for all students is between fifty (50) and sixty (60).",
        "The median SGP for all students is between thirty (30) and fifty (50).",
        "The median SGP for all students is less than thirty (30).",
    ],
    "1.5.d": [
        "The median SGP for all students is more than sixty (60).",
        "The median SGP for all students is between fifty (50) and sixty (60).",
        "The median SGP for all students is between thirty (30) and fifty (50).",
        "The median SGP for all students is less than thirty (30).",
    ],
    "1.6.a": [
        "Ten percent (10%) or higher than comparable public schools for the subgroup.",
        "Between two and ten percent (2-10%) higher than comparable schools for the subgroup.",
        "Between the same as and two percent (2%) higher than comparable schools for the subgroup.",
        "Less than comparable schools for the subgroup.",
    ],
    "1.6.b": [
        "Ten percent (10%) or higher than comparable public schools for the subgroup.",
        "Between two and ten percent (2-10%) higher than comparable schools for the subgroup.",
        "Between the same as and two percent (2%) higher than comparable schools for the subgroup.",
        "Less than comparable schools for the subgroup.",
    ],
    "1.6.c": [
        "Increase of more than five percent (5%) from the previous year for the subgroup.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year for the subgroup.",
        "Decrease from the previous school year for the subgroup.",
    ],
    "1.6.d": [
        "Increase of more than five percent (5%) from the previous year for the subgroup.",
        "Increase of between two and five percent (2-5%) from the previous year.",
        "Less than a two percent (2%) increase from the previous year for the subgroup.",
        "Decrease from the previous school year for the subgroup.",
    ],
    # combined 1.7.a and 1.7.b
    "1.7.a": [
        "Equal to or greater than the state average (than traditional public school(s)).",
        "Within five percent (5%) of the state average (of traditional public school(s)).",
        "Between six and fifteen percent (6-15%) below the state average (6-10% below traditional public school(s)).",
        "More than fifteen percent (15%) below the state average (10% below traditional public school(s)).",
    ],
    "1.7.b": [
        "Equal to or greater than traditional public school(s).",
        "Within five percent (5%) of traditional public school(s).",
        "Between six and ten percent (6-10%) below traditional public school(s).",
        "More than ten percent (10%) below traditional public school(s).",
    ],
    # same ratings as 1.7.d
    "1.7.c": [
        "Ninety-five percent (95%) or more.",
        "Between eighty-five and ninety-five percent (85-95%).",
        "Between seventy-five and eighty-five percent (75-85%).",
        "Less than seventy-five percent (75%).",
    ],
}