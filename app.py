import os
import logging
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from programme_manager import ProgrammeManager
from image_uploader import ImageUploader
from markdown_handler import MarkdownHandler

load_dotenv()

LOG_DIR = os.getenv("LOGS", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "iffk_planner.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logging.info("---- Streamlit App Started ----")

try:
    programme_manager = ProgrammeManager()
except Exception as e:
    st.error("Failed to load Programme Manager. Check logs.")
    st.stop()

try:
    image_uploader = ImageUploader()
except Exception as e:
    st.error("Failed to load Image Uploader. Check logs.")
    st.stop()

st.set_page_config(page_title="IFFK Planner", layout="wide")

view_names = ["View Programmes", "Add Programme", "Select Films", "Scoring Overview"]
menu = st.sidebar.radio("Navigation", view_names, index=0)

@st.cache_data
def load_data_with_cache(sheet_name):
    try:
        sheet = programme_manager.get_sheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except Exception as e:
        logging.error(f"Error loading Google Sheets ({sheet_name}): {e}")
        st.error(f"Failed to load {sheet_name} data. Check logs.")
        return pd.DataFrame()

def load_data_without_cache(sheet_name):
    try:
        sheet = programme_manager.get_sheet(sheet_name)
        df = pd.DataFrame(sheet.get_all_records())
        return df
    except Exception as e:
        logging.error(f"Error loading Google Sheets ({sheet_name}): {e}")
        st.error(f"Failed to load {sheet_name} data. Check logs.")
        return pd.DataFrame()

films_df = load_data_with_cache(programme_manager.FILMS_LIST_SHEET)
talks_df = load_data_with_cache(programme_manager.TALKS_SHEET)

if menu == view_names[0]:
    st.title("🎞️ All Programmes")

    # Category filter
    st.sidebar.subheader("Filter by Category")
    all_categories = list(programme_manager.CATEGORY_CODES.keys())
    categories_with_all = ["All"] + all_categories
    selected_categories = st.sidebar.multiselect(
        "Select categories:",
        categories_with_all,
        default=["All"]
    )
    if "All" in selected_categories:
        selected_categories = all_categories

    for cat in selected_categories:
        if cat != "Talks & Conversations":
            st.subheader(f"🎬 {cat}")
            filtered_films_df = films_df[films_df["CATEGORY"] == cat]
            cols = st.columns(3)
            index = 0
            for _, row in filtered_films_df.iterrows():
                with cols[index % 3]:
                    try:
                        # DETAILS
                        st.html(MarkdownHandler.render_programme_details(row.to_dict()))

                    except Exception as e:
                        st.error(f"Error rendering film: {e}")

                index += 1

    if "Talks & Conversations" in selected_categories:
        st.subheader("🎤 Talks & Conversations")
    cols = st.columns(3)
    index = 0
    for _, row in talks_df.iterrows():
        with cols[index % 3]:
            try:
                st.image(row["IMAGE_URL"])

                st.markdown(f"**{row['TOPIC']}**")
                st.markdown(f"**Duration:** {row.get('DURATION', '-')}")

            except Exception as e:
                st.error(f"Error rendering talk: {e}")

        index += 1

if menu == view_names[1]:
    st.title("🎬 Add Entry")

    try:
        category = st.selectbox(
            "CATEGORY", 
            list(programme_manager.CATEGORY_CODES.keys()),
            index=None,
            placeholder="Search categories..."
        )
    except Exception:
        logging.exception("Failed to load categories in dropdown")
        st.error("Could not load categories. Check logs.")
        st.stop()

    is_category_talks_and_conversations = category == "Talks & Conversations"

    if category:
        col1, col2 = st.columns(2)

        with col1:
            if is_category_talks_and_conversations:
                topic = st.text_input("TOPIC")
            else:
                intl_title = st.text_input("INTERNATIONAL TITLE")
                orig_title = st.text_input("ORIGINAL TITLE")
                year = st.number_input("YEAR", step=1, value=2025)
                run_time = st.number_input("RUNNING TIME (Minutes)", step=1, value=120)
                letterboxd_url = st.text_input("LETTERBOXD LINK")

        with col2:
            if is_category_talks_and_conversations:
                duration = st.number_input("DURATION (Minutes)", step=1, value=60)
            else:
                try:
                    language = st.selectbox(
                        "LANGUAGE",
                        sorted(programme_manager.LANGUAGES),
                        index=None,
                        placeholder="Search languages..."
                    )
                    country = st.selectbox(
                        "COUNTRY",
                        sorted(programme_manager.COUNTRIES),
                        index=None,
                        placeholder="Search countries..."
                    )
                except Exception:
                    logging.exception("Failed to load language/country dropdowns")
                    st.error("Could not load language/country lists.")

                director = st.text_input("DIRECTOR")
                synopsis = st.text_area("SYNOPSIS")

        uploaded_image = st.file_uploader("Upload Poster", type=['png', 'jpg', 'jpeg'])

        if st.button("Add Entry"):

            logging.info(f"Add Entry clicked for category: {category}")

            if is_category_talks_and_conversations and not topic:
                st.error("Please enter the TOPIC.")
                logging.warning("Topic missing for Talks entry")
                st.stop()

            if not is_category_talks_and_conversations and not intl_title:
                st.error("Please enter the INTERNATIONAL TITLE.")
                logging.warning("International title missing for film entry")
                st.stop()

            if not uploaded_image:
                st.error("Please upload an image.")
                logging.warning("Image not uploaded")
                st.stop()

            try:
                image_bytes = uploaded_image.read()
                image_url = image_uploader.upload_bytes(image_bytes, uploaded_image.name)
                logging.info("Image uploaded successfully")
            except Exception as e:
                logging.exception("Image upload failed")
                st.error("Image upload failed. Check logs.")
                st.stop()

            if is_category_talks_and_conversations:
                data = {
                    "category": category,
                    "topic": topic,
                    "duration": duration,
                    "image_url": image_url
                }
            else:
                data = {
                    "category": category,
                    "international_title": intl_title,
                    "original_title": orig_title,
                    "year": year,
                    "runtime": run_time,
                    "language": language,
                    "country": country,
                    "director": director,
                    "synopsis": synopsis,
                    "image_url": image_url,
                    "letterboxd_url": letterboxd_url
                }

            logging.info(f"Data prepared for category {category}")

            try:
                programme_id = programme_manager.add_programme_entry(data)
                st.success(f"Programme added successfully! PROGRAMME ID: {programme_id}")
                st.image(image_url, caption="Uploaded Poster")
                logging.info(f"Entry added successfully. Programme ID: {programme_id}")
            except Exception:
                st.error("Failed to save the entry. Check logs.")

if menu == view_names[2]:
    st.title("🎬 Film Scoring & Selection")
    selection_df = load_data_with_cache(programme_manager.PROGRAMME_SELECTION_SHEET)

    categories = sorted(films_df["CATEGORY"].unique())
    category = st.selectbox("Select Category", categories)

    filtered_films_df = films_df[films_df["CATEGORY"] == category]
    filtered = filtered_films_df.copy()
    filtered["TEMP_TITLE"] = filtered['INTERNATIONAL_TITLE'] + " (" +filtered['ORIGINAL_TITLE'] + ")"
    film_titles = filtered["TEMP_TITLE"].tolist()

    film_choice = st.selectbox("Select Film", film_titles)
    film = filtered[filtered["TEMP_TITLE"] == film_choice].iloc[0]
    programme_id = film["PROGRAMME_ID"]

    existing = None
    if not selection_df.empty:
        existing = selection_df[selection_df["PROGRAMME_ID"] == programme_id]
    if existing is not None and not existing.empty:
        existing = existing.iloc[0]

    col1, col2 = st.columns([1, 1])

    with col1:
        if existing is not None and not existing.empty:
            scores = [existing["SYNOPSIS"], existing["TRAILER"], existing["DIRECTOR_PROFILE"], existing["WRITER_PROFILE"], existing["LETTERBOXD_REVIEWS"]]
            valid_scores = [s for s in scores if s > 0]
            avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
            col1l, col1r = st.columns([1, 1])
            with col1l:
                st.markdown(f"""
                    <h2 style='font-size: 25px; font-weight: bold; text-align: left;'>
                        Average<br>Score
                    </h2>
                    """, unsafe_allow_html=True
                )
            with col1r:
                st.markdown(f"""
                    <h2 style='font-size: 52px; font-weight: bold; text-align: center;'>
                        {avg_score:.2f}
                    </h2>
                    """, unsafe_allow_html=True
                )

        st.html(MarkdownHandler.render_programme_image(film.to_dict()))

    with col2:
        def get_val(col):
            return int(existing[col]) if existing is not None and not existing.empty else 0

        synopsis_score = st.selectbox("Synopsis", list(range(0, 6)), index=get_val("SYNOPSIS"))
        trailer_score = st.selectbox("Trailer", list(range(0, 6)), index=get_val("TRAILER"))
        director_score = st.selectbox("Director Profile", list(range(0, 6)), index=get_val("DIRECTOR_PROFILE"))
        writer_score = st.selectbox("Writer Profile", list(range(0, 6)), index=get_val("WRITER_PROFILE"))
        letterboxd_score = st.selectbox("Letterboxd Reviews", list(range(0, 6)), index=get_val("LETTERBOXD_REVIEWS"))

        is_selected = st.checkbox("Selected", value=bool(existing["IS_SELECTED"]) if existing is not None and not existing.empty else False)

        scores = [synopsis_score, trailer_score, director_score, writer_score, letterboxd_score]
        valid_scores = [s for s in scores if s > 0]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        save_entry_button = st.button("💾 Save Entry")

    if save_entry_button:
        new_entry = {
            "PROGRAMME_ID": programme_id,
            "SYNOPSIS": synopsis_score,
            "TRAILER": trailer_score,
            "DIRECTOR_PROFILE": director_score,
            "WRITER_PROFILE": writer_score,
            "LETTERBOXD_REVIEWS": letterboxd_score,
            "AVERAGE_SCORE": avg_score,
            "IS_SELECTED": is_selected,
        }

        # Remove old entry and append new one
        if not selection_df.empty:
            selection_df = selection_df[selection_df["PROGRAMME_ID"] != programme_id]
        selection_df = pd.concat([selection_df, pd.DataFrame([new_entry])], ignore_index=True)

        logging.info(f"Data prepared for programme {programme_id}")

        try:
            programme_manager.replace_sheet_data(programme_manager.PROGRAMME_SELECTION_SHEET, selection_df)
            st.success(f"Scoring added successfully! PROGRAMME ID: {programme_id}")
        except Exception:
            st.error("Failed to save the scoring. Check logs.")

if menu == view_names[3]:
    st.title("🎬 Film Scores Overview")
    selection_df = load_data_with_cache(programme_manager.PROGRAMME_SELECTION_SHEET)

    # Category filter
    st.sidebar.subheader("Filter by Category")
    all_categories = list(programme_manager.CATEGORY_CODES.keys())
    categories_with_all = ["All"] + all_categories
    selected_categories = st.sidebar.multiselect(
        "Select categories:",
        categories_with_all,
        default=["All"]
    )
    if "All" in selected_categories:
        selected_categories = all_categories

    filtered_films_df = films_df[films_df["CATEGORY"].isin(selected_categories)]
    merged_df = filtered_films_df.merge(selection_df, on="PROGRAMME_ID", how="left")
    merged_df = merged_df.sort_values(["IS_SELECTED", "AVERAGE_SCORE","YEAR", "RUNNING_TIME", "PROGRAMME_ID"], 
                                        ascending=[False, False, False, True, True])
    display_df = merged_df[[
        "CATEGORY",
        "INTERNATIONAL_TITLE",
        "ORIGINAL_TITLE",
        "YEAR",
        "RUNNING_TIME",
        "AVERAGE_SCORE",
        "IS_SELECTED"
    ]].copy()
    
    display_df["AVERAGE_SCORE"] = display_df["AVERAGE_SCORE"].fillna(0).round(2)
    display_df["IS_SELECTED"] = display_df["IS_SELECTED"].map(
        lambda x: True if str(x).strip().upper() == "TRUE" else False
    )

    display_df = display_df.rename(columns={
        "CATEGORY": "Category",
        "INTERNATIONAL_TITLE": "Intl. Title",
        "ORIGINAL_TITLE": "Original Title",
        "YEAR": "Year",
        "RUNNING_TIME": "Running Time",
        "AVERAGE_SCORE": "Average Score",
        "IS_SELECTED": "✔"
    })

    st.dataframe(
        display_df,
        width="content",
        hide_index=True
    )

