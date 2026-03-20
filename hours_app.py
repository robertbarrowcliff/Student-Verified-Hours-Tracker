import pandas as pd
import streamlit as st
import re

st.title("Student Hours Verification Tracker")

uploaded_file = st.file_uploader("Upload Hours Report (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:

    # Load file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, low_memory=False)
    else:
        df = pd.read_excel(uploaded_file)

    # --- Helper function ---
    def find_col(keyword):
        for col in df.columns:
            if keyword.lower() in col.lower():
                return col
        return None

    # --- Identify columns ---
    name_col = find_col("Respondent")
    placement_col = find_col("Response")
    verification_cols = [
        c for c in df.columns
        if "verification of hours" in c.lower()
        and "assessed" not in c.lower()
    ]

    # --- Find all Hours Log columns ---
    hours_log_cols = [c for c in df.columns if "hours log" in c.lower()]

    # --- Process data ---
    output = []

    for _, row in df.iterrows():

        # Name
        name = row[name_col] if name_col else ""
        name = "" if pd.isna(name) else str(name).strip()

        # Placement
        placement = row[placement_col] if placement_col else ""
        placement = "" if pd.isna(placement) else str(placement).strip()

        # Hours
        total_hours = 0

        for col in hours_log_cols:
            val = row[col]

            if pd.isna(val):
                continue

            text = str(val).lower()

            hours_match = re.search(r"(\d+)\s*hour", text)
            mins_match = re.search(r"(\d+)\s*min", text)

            h = int(hours_match.group(1)) if hours_match else 0
            m = int(mins_match.group(1)) if mins_match else 0

            total_hours += h + (m / 60)

        # Verification
        verify_val = ""

        for col in verification_cols:
            val = row[col]

            if pd.notna(val) and str(val).strip() != "":
                verify_val = val
                break

        if pd.isna(verify_val):
            verify_val = ""
        else:
            verify_val = str(verify_val).strip().lower()

        # Clean spacing / hidden characters
        verify_val = " ".join(verify_val.split())

        if "agree" in verify_val:

            verified = "Yes"
        else:
            verified = "No"

        output.append({
            "Student Name": name,
            "Placement": placement,
            "Total Hours": round(total_hours, 2),
            "Verified": verified
        })

    result_df = pd.DataFrame(output)
    # --- Add numeric columns for splitting ---
    result_df["Verified Hours"] = result_df.apply(
        lambda x: x["Total Hours"] if x["Verified"] == "Yes" else 0,
        axis=1
    )

    result_df["Unverified Hours"] = result_df.apply(
        lambda x: x["Total Hours"] if x["Verified"] == "No" else 0,
        axis=1
    )

    # --- Total hours per student ---
    student_totals = (
        result_df
        .groupby("Student Name", as_index=False)
        .agg({
            "Total Hours": "sum",
            "Verified Hours": "sum",
            "Unverified Hours": "sum"
        })
    )
    student_totals["All Hours Verified"] = student_totals.apply(
        lambda x: "Yes" if x["Unverified Hours"] == 0 else "No",
        axis=1
    )

    # --- Display ---
    st.subheader("Hours Overview")

    def highlight_verified(row):
        if row["Verified"] == "Yes":
            return ["background-color: #d4edda"] * len(row)
        else:
            return ["background-color: #f8d7da"] * len(row)

    display_main = result_df.copy()

    for col in ["Total Hours", "Verified Hours", "Unverified Hours"]:
        if col in display_main.columns:
            display_main[col] = display_main[col].map(
                lambda x: f"{x:.2f}".rstrip('0').rstrip('.')
            )

    styled_df = display_main.style.apply(highlight_verified, axis=1)

    st.dataframe(styled_df, use_container_width=True)

    st.subheader("Total Hours per Student")
    def highlight_totals(row):
        if row["All Hours Verified"] == "Yes":
            return ["background-color: #d4edda"] * len(row)
        else:
            return ["background-color: #f8d7da"] * len(row)
    totals_display = student_totals.copy()

    for col in ["Total Hours", "Verified Hours", "Unverified Hours"]:
        if col in totals_display.columns:
            totals_display[col] = totals_display[col].map(
                lambda x: f"{x:.2f}".rstrip('0').rstrip('.')
            )


    styled_totals = totals_display.style.apply(highlight_totals, axis=1)

    st.dataframe(styled_totals, use_container_width=True)

    # --- Filters ---
    st.subheader("Filters")

    # ✅ DEFINE FIRST
    search_name = st.text_input("Search by student name")

    show_verified = st.checkbox("Show Verified Only")
    show_unverified = st.checkbox("Show Unverified Only")

    filtered_df = result_df.copy()

    # ✅ THEN USE
    if search_name:
        filtered_df = filtered_df[
            filtered_df["Student Name"].str.contains(search_name, case=False, na=False)
        ]

    if show_verified and not show_unverified:
        filtered_df = filtered_df[filtered_df["Verified"] == "Yes"]

    elif show_unverified and not show_verified:
        filtered_df = filtered_df[filtered_df["Verified"] == "No"]
    display_df = filtered_df.copy()

    for col in ["Total Hours", "Verified Hours", "Unverified Hours"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].map(
                lambda x: f"{x:.2f}".rstrip('0').rstrip('.')
            )


    st.dataframe(display_df, use_container_width=True)
