
import streamlit as st
from openai import OpenAI
import pandas as pd
import io
import base64
import json
import os
from dotenv import load_dotenv

# ----------------------------------------------------
# 🔐  SET YOUR API KEY HERE
# ----------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Environment variable OPENAI_API_KEY is not set. Set it and rerun the app.")
    st.stop()
# ----------------------------------------------------

#OPENAI_API_KEY = "ADD YOUR KEY"
# ----------------------------------------------------

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="Legend → Plan Tag Counter", layout="wide")
st.title("Legend → Plan Tag Counter (GPT-5.1 Vision Based)")


legend_file = st.file_uploader("Upload Legend Image", type=["png","jpg","jpeg"])
plan_file = st.file_uploader("Upload Plan Image", type=["png","jpg","jpeg"])


def extract_text_from_image(image_bytes_b64: str, prompt: str):
    """
    Calls GPT-5-mini Vision to extract text from an image.
    """
    response = client.responses.create(
        model="gpt-5.1",
        
        #temperature=0.2,
        input=[
            {"role": "user", "content": prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{image_bytes_b64}"
                    }
                  
                ]
            }
        ]
    )
    return response.output_text


if legend_file and plan_file:

    # Convert both images to base64
    legend_bytes_b64 = base64.b64encode(legend_file.read()).decode()
    plan_bytes_b64 = base64.b64encode(plan_file.read()).decode()

    # -------------------------------------
    # STEP 1 — Extract TAGS from legend
    # -------------------------------------
    st.subheader("Step 1 — Extracting tags from legend…")

    legend_prompt = """
    Extract ALL TAG values that appear in this legend table.
    A TAG is typically something like F-01,F-02,F-03,X1,X2, D-01,D-02,F-08A,F-08B, etc.

    Return ONLY a JSON list of tags.
    Example:
   ["F-01", "F-02", "F-03", "X1","X2","F-08A"]

    No descriptions.
    No symbols.
    No extra text.
    """

    legend_raw = extract_text_from_image(legend_bytes_b64, legend_prompt)

    try:
        legend_tags = json.loads(legend_raw)
    except:
        st.error("Unable to parse TAGs from legend. GPT returned:")
        st.write(legend_raw)
        st.stop()

    st.success("Legend TAGs extracted successfully.")
    st.write("**Legend TAGs:**", legend_tags)

    # -------------------------------------
    # STEP 2 — Extract all text from plan
    # -------------------------------------
    st.subheader("Step 2 — Extracting all text from plan…")

    plan_prompt = """
    Extract ALL textual elements from this architectural plan image.
    Return ONLY a JSON list of text tokens found.
    Preserve duplicates.

    Example:
    ["F-01", "F-02", "F-03", "X1","X2","F-08A","F-08B"]

    """

    plan_raw = extract_text_from_image(plan_bytes_b64, plan_prompt)

    try:
        plan_tokens = json.loads(plan_raw)
    except:
        st.error("Unable to parse text from plan image. GPT returned:")
        st.write(plan_raw)
        st.stop()

    st.success("Plan text extraction completed successfully.")
    st.write("**Sample extracted tokens:**", plan_tokens[:20])

    # -------------------------------------
    # STEP 3 — Count tag occurrences
    # -------------------------------------
    st.subheader("Step 3 — Counting tag occurrences…")

    counts = {}
    for tag in legend_tags:
        counts[tag] = sum(1 for t in plan_tokens if t == tag)

    df = pd.DataFrame(list(counts.items()), columns=["Tag", "Count"])

    st.table(df)

    # -------------------------------------
    # Excel Download
    # -------------------------------------
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False)
    towrite.seek(0)

    st.download_button(
        label="Download Tag Counts (Excel)",
        data=towrite,
        file_name="tag_counts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Upload both Legend and Plan images to begin processing.")
